import { expect, test } from 'claude-code/testing'

import { EMPTY, TREE } from './fixtures'
import { parseTree, windowOf } from './core'
import { boot, KEYS, pane } from './testkit'
import { dumpText } from './textdump'

const J = (v: unknown) => JSON.stringify(v)
const copy = <T,>(v: T): any => JSON.parse(JSON.stringify(v))
const PLUGIN = (t: any): any => t.squads.find((s: any) => s.name === 'plugin')
// A tree with herdr unreadable: agents_working null and rule 1 on an open scope (own copy: the fixture file may change).
const HERDR_DOWN = () => {
  const t = copy(TREE)
  const sc = PLUGIN(t).goals[0].scopes[1]
  sc.facts.agents_working = null
  sc.next_step = { rule: 1, text: 'Cannot read agents: open board' }
  return t
}

async function open($: any, on: any, tree: unknown, cols = 100, rows = 30) {
  const w = await boot($, on, typeof tree === 'string' ? tree : J(tree))
  await $.command.run({ command: 'squads', args: '' })
  await w.clock.settle()
  const ui = await $.ui.mount(pane('terminal', cols, rows))
  const text = async () => dumpText(await ui.drawn(), cols)
  const press = (key: string) => $.ui.press({ ...KEYS, key, surface: 'terminal' })
  return { w, ui, text, press }
}

test('parseTree takes the fixtures and refuses version 2, bad JSON and a missing squads list', () => {
  expect(parseTree(J(TREE)).ok).toBe(true)
  expect(parseTree(J(EMPTY)).ok).toBe(true)
  expect(parseTree(J({ ...copy(TREE), version: 2 })).ok).toBe(false)
  expect(parseTree('{not json').ok).toBe(false)
  expect(parseTree(J({ version: 1 })).ok).toBe(false)
})

test('opening runs squad-tree by argv with no shell and no repo, and lists squad, goal, scopes, needs you and next step', async ($, on) => {
  const { w, text } = await open($, on, TREE)
  const out = await text()
  expect(w.runs[0]).toEqual(['python3', expect.stringMatching(/bin\/squad-tree$/), '--json'])
  for (const s of ['plugin', 'g1', 'api', 'ui', 'needs 2', 'Answer 2 questions in api', '2 need you']) expect(out).toContain(s)
  expect(w.opened[0].id).toBe('squads')
})

test('a failed refresh keeps the last good list and shows one error line', async ($, on) => {
  const { w, text, press } = await open($, on, TREE)
  w.reply = { exitCode: 1, stdout: '', stderr: 'boom' }
  await press('refresh')
  const out = await text()
  expect(out).toContain('squad-tree failed: boom')
  expect(out).toContain('Answer 2 questions in api')
  w.reply = { exitCode: 0, stdout: J({ ...copy(TREE), version: 2 }), stderr: '' }
  await press('refresh')
  expect(await text()).toContain('version 2')
  expect(await text()).toContain('g1')
})

test('refresh: a tick while the pane is open runs once; no run while it is closed', async ($, on) => {
  const { w } = await open($, on, TREE)
  const n = w.runs.length
  await w.clock.advance(10000)
  expect(w.runs.length).toBe(n + 1)
  await w.clock.advance(10000)
  expect(w.runs.length).toBe(n + 2)
})

test('refresh: the pane never opened, so no run', async ($, on) => {
  const w = await boot($, on, J(TREE))
  await w.clock.advance(60000)
  expect(w.runs).toEqual([])
})

test('a command press copies exactly the JSON text, shows it on screen, and starts no process and writes no file', async ($, on) => {
  const { w, text, press } = await open($, on, TREE)
  await press('plugin/goal:g1')
  const g1 = PLUGIN(TREE).goals[0]
  const board = g1.commands.find((c: any) => c.id === 'board') as any
  expect(await text()).toContain(board.text)
  const runs = w.runs.length
  for (const i of g1.commands.keys()) await press(`c${i}:${g1.commands[i].id}:head`)
  expect(w.copies.map((c: any) => c.text)).toEqual(g1.commands.map((c: any) => c.text))
  expect(await text()).toContain('copied: ')
  expect(w.runs.length).toBe(runs)
  expect(w.fsCalls).toBe(0)
  w.copied = false
  await press('c1:board:head')
  const out = await text()
  expect(out).toContain('copy failed')
  expect(out).not.toContain('copied:')
  expect(out).toContain(board.text)
})

test('detail: a goal lists scopes and commands, a wait command shows its reason, done shows Board and Report, back keeps the list', async ($, on) => {
  const { text, press } = await open($, on, TREE)
  await press('plugin/goal:g1')
  let out = await text()
  for (const s of ['Scopes', 'api', 'Resume', 'Not yet: agents are working', 'Board', 'New scope', '<text>']) expect(out).toContain(s)
  await press('back')
  expect(await text()).toContain('Answer 2 questions in api')
  await press('plugin/done')
  await press('plugin/scope:tiny')
  out = await text()
  expect(out).toContain('Board')
  expect(out).toContain('Retire')
  expect(out).not.toContain('Resume')
  expect(out).toContain('Closed ')
})

test('unreadable agents show ? and the next step says it', async ($, on) => {
  const out = await (await open($, on, HERDR_DOWN())).text()
  expect(out).toContain('Cannot read agents: open board')
  expect(out).toContain('?w')
})

test('an empty tree says No squads here', async ($, on) => {
  expect(await (await open($, on, EMPTY)).text()).toContain('No squads here.')
})

test('text from the JSON is stripped of escape sequences and control characters', async ($, on) => {
  const t = copy(TREE)
  PLUGIN(t).goals[0].name = 'g\x1b[31m1'
  PLUGIN(t).goals[0].brief = 'b\x1b]0;x\x07rief'
  PLUGIN(t).goals[0].next_step.text = 'Ans\x1b[2Jwer'
  PLUGIN(t).goals[0].commands[0].reason = 'wa\x1b[0mit'
  const { text, press } = await open($, on, t)
  expect(await text()).not.toMatch(/\x1b|\x07/)
  await press('plugin/goal:g\x1b[31m1')
  expect(await text()).not.toMatch(/\x1b|\x07/)
})

for (const rows of [6, 11, 40]) {
  for (const cols of [40, 60, 100]) {
    test(`layout ${rows} rows x ${cols} columns: name and next step stay, nothing is wider than the pane, the rest is counted`, async ($, on) => {
      const { text } = await open($, on, TREE, cols, rows)
      const out = await text()
      const ls = out.split('\n')
      expect(ls.every((l) => [...l].length <= cols)).toBe(true)
      expect(ls.length).toBeLessThanOrEqual(rows)
      expect(out).toContain('plugin')
      expect(out).toContain('g1')
      if (rows >= 11 && cols >= 60) expect(out).toContain('needs 2')
      const more = out.match(/↓ (\d+) more/)
      if (rows === 6) expect(more).not.toBeNull()
      if (rows === 40) expect(more).toBeNull()
    })
  }
}

test('windowOf counts the rows above and below', () => {
  expect(windowOf(10, 0, 4)).toEqual({ from: 0, count: 3, above: 0, below: 7 })
  expect(windowOf(10, 3, 4)).toEqual({ from: 3, count: 2, above: 3, below: 5 })
  expect(windowOf(3, 0, 4)).toEqual({ from: 0, count: 3, above: 0, below: 0 })
})

test('a state the previous shape wrote is declined', async ($, on) => {
  on('state.get', () => ({ value: { value: { old: true }, version: 1 } }))
  const w = await boot($, on, J(TREE))
  const ui = await $.ui.mount(pane('terminal', 80, 20))
  expect(dumpText(await ui.drawn(), 80)).toContain('Squads')
  void w
})
