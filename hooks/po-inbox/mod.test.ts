import { expect, mock, test } from 'claude-code/testing'

import { answerItem } from './actions'
import { FIXTURES } from './fixtures'

const START = { cwd: '/w', surface: null, isInteractive: true } as const
const HOME = '/h/scope'
const MANAGER = { SQUAD_ROLE: 'manager', SCOPE_DIR: HOME }
const MIXED = FIXTURES['contract-provisional-mixed']
const EMPTY = FIXTURES['contract-provisional-empty']

type Reply = { exitCode: number; stdout: string; stderr: string }
const ok = (stdout: string): Reply => ({ exitCode: 0, stdout, stderr: '' })

// A world beneath the plugin: the CLI, the file system and the session are answered here and recorded.
function world(on: any, env: Record<string, string>, cli: (argv: string[], stdin?: string) => Reply | Promise<Reply>) {
  const w = {
    runs: [] as { argv: string[]; stdin?: string }[],
    stats: [] as string[],
    toasts: [] as string[],
    submits: [] as string[],
    registered: [] as string[],
    opened: [] as string[],
    timers: 0,
    writes: 0,
    mtime: 1000,
    size: 10,
    submit: (text: string): unknown => ({ text }),
    clock: undefined as any,
    state: {} as Record<string, any>,
  }
  mock.env(on, env)
  w.clock = mock.clock(on)
  on('session.start', (_$: any, e: any) => ({ cwd: e.cwd }))
  on('process.run', (_$: any, e: any) => {
    w.runs.push({ argv: [...e.argv], stdin: e.init?.stdin })
    return Promise.resolve(cli(e.argv.slice(1), e.init?.stdin)).then((r) => ({
      value: { ...r, isStdoutTruncated: false, isStderrTruncated: false },
    }))
  })
  on('fs.stat', (_$: any, e: any) => {
    w.stats.push(e.path)
    return { value: { kind: 'file', size: w.size, mtimeMs: w.mtime, isLink: false } }
  })
  on('ui.toast', (_$: any, e: any) => (w.toasts.push(e.text), { value: undefined }))
  on('prompt.submit', (_$: any, e: any) => {
    w.submits.push(e.text)
    return w.submit(e.text)
  })
  on('command.register', (_$: any, e: any) => (w.registered.push(e.name), { value: { command: e.name } }))
  on('ui.open', (_$: any, e: any) => (w.opened.push(e.id), { value: { isPlaced: true } }))
  on('turn.complete', () => ({ text: '' }))
  on('session.id', () => ({ value: 'sess-1' }))
  on('state.set', (_$: any, e: any, next: any) => (w.writes++, (w.state[e.key] = e.value), next(e)))
  return w
}

const TURN = (turnId: string) => ({ reason: 'answer', answer: '', durationMs: 1, isAborted: false, turnId }) as any

// answerItem is what the pane (PI-04) calls from a handler; the test's engine `$` has no process or
// plugin noun, so it gets a hand-made `$` that records the same things `world` does.
function fakeDollar(w: any, cli: (argv: string[], stdin?: string) => Reply | Promise<Reply>) {
  const mem: Record<string, { value: unknown; version: number }> = {}
  return {
    plugin: { name: 'squad', root: '/p' },
    process: {
      run: async (argv: string[], init?: { stdin?: string }) => {
        w.runs.push({ argv: [...argv], stdin: init?.stdin })
        return { ...(await cli(argv.slice(1), init?.stdin)), isStdoutTruncated: false, isStderrTruncated: false }
      },
    },
    prompt: {
      submit: async ({ text }: { text: string }) => {
        w.submits.push(text)
        return w.submit(text)
      },
    },
    session: { id: async () => 'sess-1' },
    ui: { toast: async (text: string) => void w.toasts.push(text) },
    state: {
      get: async (a: { key: string }) => mem[a.key] ?? { value: undefined, version: 0 },
      set: async (a: { key: string }, value: unknown) => {
        mem[a.key] = { value, version: (mem[a.key]?.version ?? 0) + 1 }
        return { isSet: true, version: mem[a.key].version }
      },
    },
  } as any
}

const verb = (w: { runs: { argv: string[] }[] }, name: string) => w.runs.filter((r) => r.argv[1] === name)

// --- (a) inert --------------------------------------------------------------------------------

const INERT: [string, Record<string, string>][] = [
  ['no env', {}],
  ['SQUAD_ROLE=dev with a home', { SQUAD_ROLE: 'dev', SCOPE_DIR: HOME, GOAL_DIR: '/h/goal' }],
  ['manager without a home', { SQUAD_ROLE: 'manager' }],
  ['a home without a role', { SCOPE_DIR: HOME }],
]
for (const [name, env] of INERT) {
  test(`inert: ${name}`, async ($, on) => {
    const w = world(on, env, () => ok(EMPTY))
    await $.session.start(START)
    await w.clock.advance(10000)
    expect(w.runs).toEqual([])
    expect(w.stats).toEqual([])
    expect(w.registered).toEqual([])
    expect(w.writes).toBe(0)
    const ran = await $.command.run({ command: 'inbox' })
    expect(w.opened).toEqual([])
    expect(ran.text).toBe(undefined)
  })
}

// --- (b) active -------------------------------------------------------------------------------

for (const [name, env, home] of [
  ['manager with SCOPE_DIR', MANAGER, HOME],
  ['manager with only GOAL_DIR', { SQUAD_ROLE: 'manager', GOAL_DIR: '/h/goal' }, '/h/goal'],
] as const) {
  test(`active: ${name}`, async ($, on) => {
    const w = world(on, env, () => ok(MIXED))
    await $.session.start(START)
    expect(w.registered).toEqual(['inbox'])
    expect(verb(w, 'list').length).toBe(1)
    expect(w.runs[0].argv).toEqual([w.runs[0].argv[0], 'list', '--json'])
    expect(w.runs[0].argv[0].endsWith('/bin/squad-inbox')).toBe(true)
    expect(w.stats).toEqual([`${home}/inbox.jsonl`, `${home}/escalations.md`])
    await $.command.run({ command: 'inbox' })
    expect(w.opened).toEqual(['inbox'])
  })
}

// --- (c) poll, AC6, AC7, AC16 -----------------------------------------------------------------

const lists = (w: any) => verb(w, 'list').length

// open items only: no redelivery, so every `list` run is a poll run
const OPEN_ONLY = JSON.stringify({ ...JSON.parse(MIXED), items: JSON.parse(MIXED).items.slice(0, 2) })

test('poll: the CLI runs only when a mtime or size changed; an idle tick is two stats', async ($, on) => {
  const w = world(on, MANAGER, () => ok(OPEN_ONLY))
  await $.session.start(START)
  expect(lists(w)).toBe(1)
  w.stats.length = 0
  await w.clock.advance(2000)
  expect(w.stats.length).toBe(2)
  expect(lists(w)).toBe(1)
  await w.clock.advance(2000)
  expect(w.stats.length).toBe(4)
  expect(lists(w)).toBe(1)
  w.mtime += 5
  await w.clock.advance(2000)
  expect(lists(w)).toBe(2)
  await w.clock.advance(2000)
  expect(lists(w)).toBe(2)
})

test('poll: two writes in one mtime tick with a different size are noticed', async ($, on) => {
  const w = world(on, MANAGER, () => ok(OPEN_ONLY))
  await $.session.start(START)
  w.size += 7
  await w.clock.advance(2000)
  expect(lists(w)).toBe(2)
})

test('poll: no second CLI run while one is pending (slow CLI)', async ($, on) => {
  let release: () => void = () => {}
  let slow = false
  const w = world(on, MANAGER, () =>
    slow ? new Promise<Reply>((r) => (release = () => r(ok(OPEN_ONLY)))) : ok(MIXED),
  )
  await $.session.start(START)
  slow = true
  w.mtime += 1
  await w.clock.advance(2000)
  expect(lists(w)).toBe(2)
  w.mtime += 1
  w.stats.length = 0
  await w.clock.advance(6000)
  expect(lists(w)).toBe(2)
  expect(w.stats).toEqual([])
  release()
  await w.clock.settle()
  await w.clock.advance(2000)
  expect(lists(w)).toBe(3)
})

// --- (d) toasts -------------------------------------------------------------------------------

function snapWith(ids: string[]): string {
  const m = JSON.parse(MIXED)
  const proto = m.items[0]
  m.items = ids.map((id) => ({ ...proto, id, title: `Question ${id}`, state: 'open' }))
  return JSON.stringify(m)
}

test('toast: a first load none, an unchanged snapshot none, a new open id exactly one', async ($, on) => {
  let out = snapWith(['E1', 'E2'])
  const w = world(on, MANAGER, () => ok(out))
  await $.session.start(START)
  expect(w.toasts).toEqual([])
  w.mtime += 1
  await w.clock.advance(2000)
  expect(w.toasts).toEqual([])
  out = snapWith(['E1', 'E2', 'E3'])
  w.mtime += 1
  await w.clock.advance(2000)
  expect(w.toasts).toEqual(['Inbox E3: Question E3'])
  w.mtime += 1
  await w.clock.advance(2000)
  expect(w.toasts.length).toBe(1)
})

// --- (e) delivery -----------------------------------------------------------------------------

const E3_ANSWER = { text: 'yes\nplease "do"', option: 'a', note: null, ts: 't', source: 'pane', delivered_ts: null }
const ANSWERED = (() => {
  const m = JSON.parse(MIXED)
  m.items = [{ ...m.items[0], state: 'answered-waiting', answer: E3_ANSWER }]
  return JSON.stringify(m)
})()
const BOTH_WAITING = (() => {
  const m = JSON.parse(MIXED)
  m.items[0] = { ...m.items[0], state: 'answered-waiting', answer: E3_ANSWER }
  return JSON.stringify(m)
})()

test('delivery: answer exit 0 submits once with describePrompt text, then delivered', async (_$, on) => {
  let answered = false
  const cli = (argv: string[]) => {
    if (argv[0] === 'answer') return (answered = true, ok(''))
    if (argv[0] === 'delivered') return ok('')
    return ok(answered ? ANSWERED : MIXED)
  }
  const w = world(on, MANAGER, cli)
  const r = await answerItem(fakeDollar(w, cli), { id: 'E3', option: 'a', text: 'yes\nplease "do"' })
  await new Promise((r) => setTimeout(r, 20))
  expect(r).toEqual({ ok: true })
  expect(w.submits).toEqual(['PO answered inbox item E3 ("Merge the inbox branch?") in the inbox. Answer, exactly as typed:\n\nyes\nplease "do"'])
  const ans = verb(w, 'answer')
  expect(ans.length).toBe(1)
  expect(ans[0].argv.slice(1)).toEqual(['answer', 'E3', '--option', 'a', '--source', 'pane'])
  expect(ans[0].stdin).toBe('yes\nplease "do"')
  const del = verb(w, 'delivered')
  expect(del.length).toBe(1)
  expect(del[0].argv.slice(1)).toEqual(['delivered', 'E3', '--session', 'sess-1'])
  // submit comes before delivered
  expect(w.runs.findIndex((x) => x.argv[1] === 'delivered')).toBeGreaterThan(w.runs.findIndex((x) => x.argv[1] === 'answer'))
})

test('delivery: exit 3 shows the message and submits nothing', async (_$, on) => {
  const cli = (argv: string[]) =>
    argv[0] === 'answer' ? { exitCode: 3, stdout: '', stderr: 'E3 was answered by chat at 10:02\n' } : ok(MIXED)
  const w = world(on, MANAGER, cli)
  const r = await answerItem(fakeDollar(w, cli), { id: 'E3', text: 'yes' })
  await w.clock.settle()
  expect(r).toEqual({ ok: false, message: 'E3 was answered by chat at 10:02' })
  expect(w.submits).toEqual([])
  expect(verb(w, 'delivered')).toEqual([])
})

// --- (f) redelivery at session.start ----------------------------------------------------------

test('redelivery: every answered-waiting item is submitted once at session.start', async ($, on) => {
  const w = world(on, MANAGER, (argv) => (argv[0] === 'delivered' ? ok('') : ok(BOTH_WAITING)))
  await $.session.start(START)
  await w.clock.settle()
  expect(w.submits.length).toBe(2)
  expect(w.submits.some((t) => t.includes('item E3') && t.endsWith('\n\nyes\nplease "do"'))).toBe(true)
  expect(w.submits.some((t) => t.includes('item E2') && t.endsWith('\n\n8080'))).toBe(true)
  expect(verb(w, 'delivered').map((r) => r.argv[2]).sort()).toEqual(['E2', 'E3'])
  // the poll does not submit them again while the snapshot still says waiting
  w.mtime += 1
  await w.clock.advance(2000)
  expect(w.submits.length).toBe(2)
})

// --- (h) CLI failures keep the last good snapshot ---------------------------------------------

for (const [name, bad] of [
  ['a crash', { exitCode: 1, stdout: '', stderr: 'Traceback (most recent call last)\nboom' }],
  ['invalid JSON', ok('{not json')],
  ['another version', ok(MIXED.replace('"version": 1', '"version": 2'))],
  ['a wrong type', ok(MIXED.replace('"answer_open": 1', '"answer_open": "1"'))],
] as [string, Reply][]) {
  test(`failure: ${name} keeps the last good snapshot and sets the error state`, async ($, on) => {
    let reply: Reply = ok(MIXED)
    const w = world(on, MANAGER, () => reply)
    await $.session.start(START)
    const good = w.state.inbox
    expect(good.items.length).toBe(4)
    reply = bad
    w.mtime += 1
    await w.clock.advance(2000)
    expect(w.state.inbox).toEqual(good)
    expect(typeof w.state.inboxError).toBe('string')
    reply = ok(MIXED)
    await w.clock.advance(2000)
    expect(w.state.inboxError).toBe(null)
  })
}

// --- M2 failed submit, M3 timers --------------------------------------------------------------

test('failed submit: no delivered, one retry at the next turn.complete, none in flight twice', async ($, on) => {
  const w = world(on, MANAGER, (argv) => (argv[0] === 'delivered' ? ok('') : ok(ANSWERED)))
  w.submit = () => Promise.reject(new Error('busy'))
  await $.session.start(START)
  await w.clock.settle()
  expect(w.submits.length).toBe(1)
  expect(verb(w, 'delivered')).toEqual([])
  w.mtime += 1
  await w.clock.advance(10000)
  expect(w.submits.length).toBe(1)
  w.submit = (text: string) => ({ text })
  await $.turn.complete(TURN('t1'))
  await w.clock.settle()
  expect(w.submits.length).toBe(2)
  expect(verb(w, 'delivered').length).toBe(1)
  await $.turn.complete(TURN('t2'))
  await w.clock.settle()
  expect(w.submits.length).toBe(2)
})

test('in flight: a queued submit that is still pending is not submitted again', async ($, on) => {
  let release: (v: unknown) => void = () => {}
  const w = world(on, MANAGER, (argv) => (argv[0] === 'delivered' ? ok('') : ok(ANSWERED)))
  w.submit = (text: string) => new Promise((r) => (release = () => r({ text })))
  await $.session.start(START)
  await w.clock.settle()
  w.mtime += 1
  await w.clock.advance(6000)
  await $.turn.complete(TURN('t1'))
  expect(w.submits.length).toBe(1)
  release(undefined)
  await w.clock.settle()
  expect(verb(w, 'delivered').length).toBe(1)
})

test('timers: two session.start leave one timer and one /inbox registration', async ($, on) => {
  const w = world(on, MANAGER, () => ok(MIXED))
  await $.session.start(START)
  await $.session.start(START)
  expect(w.registered).toEqual(['inbox'])
  w.stats.length = 0
  await w.clock.advance(2000)
  expect(w.stats.length).toBe(2)
})

test('timers: session.end stops the poll, a clear does not', async ($, on) => {
  const w = world(on, MANAGER, () => ok(MIXED))
  on('session.end', () => ({ sessionId: 's' }))
  await $.session.start(START)
  await $.session.end({ reason: 'clear' } as any)
  w.stats.length = 0
  await w.clock.advance(2000)
  expect(w.stats.length).toBe(2)
  await $.session.end({ reason: 'other' } as any)
  w.stats.length = 0
  await w.clock.advance(10000)
  expect(w.stats.length).toBe(0)
})
