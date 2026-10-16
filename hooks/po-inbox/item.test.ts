// IV-03: the item screen, mounted through the real pane. Text and style are read from the drawn tree.
// `bodyRows` is 6 at 80x24 and at 40x24, 11 at 40x40: the numbers the engine hands the pane (evidence/IV-03/dev-evidence.md).
import { expect, test } from 'claude-code/testing'

import { cellWidth } from './core'
import { E1_OPTIONS, E1_REC, E1_TITLE, VISUAL } from './fixtures/visual'
import { boot, item, START, lines, pane, snap, styleOf } from './testkit'

const ROWS_24 = 6
const ROWS_40 = 11
const SIZES: [number, number][] = [[80, ROWS_24], [60, ROWS_24], [59, ROWS_24], [40, ROWS_24], [30, ROWS_24], [80, ROWS_40], [40, ROWS_40]]

const E1_OPTS: { key: string; text: string }[] = []
{
  let rest = E1_OPTIONS
  for (const k of ['a', 'b', 'c']) {
    const at = k === 'c' ? -1 : rest.indexOf(` (${String.fromCharCode(k.charCodeAt(0) + 1)}) `)
    E1_OPTS.push({ key: k, text: (at < 0 ? rest : rest.slice(0, at)).slice(4) })
    rest = at < 0 ? '' : rest.slice(at + 1)
  }
}
const E1 = item({
  id: 'E1', title: E1_TITLE, body: VISUAL.e1, options: E1_OPTS, recommendation: E1_REC,
  blocks: 'spawning the pod (BA, Tech Lead)', created: '2026-10-15T07:00:00',
})
const E2 = item({ id: 'E2', title: 'inbox-visual: clarify what the TUI inbox should show', body: VISUAL.e2, recommendation: "Reply 'all recs' to take every [rec] below, or name the numbers you change", blocks: 'nothing', created: '2026-10-15T07:00:00' })
const R1 = item({
  id: 'R1', kind: 'read', title: 'Markdown body sample', blocks: 'IV-06', created: '2026-10-15T11:23:00',
  body: '# Check-in summary\nBranch **squad/x** passed `qa-w`.\n\n- first bullet\n* second bullet\n1. numbered one\n2. numbered two\n\n| Task | State |\n|---|---|\n| IV-01 | passed |\n| IV-02 | building |\n\nline a\nline b\nline c\nline d\nline e',
})
const ANS = (o: Record<string, unknown> = {}) => ({ text: '(b) use **Tab**, no hotkey', option: 'b', note: null, ts: '2026-10-16T12:00:00', source: 'pane', delivered_ts: null, ...o })
const H_OPTS = [{ key: 'a', text: 'hotkey m' }, { key: 'b', text: 'Tab only' }, { key: 'c', text: 'both' }]
const handled = (state: string, done: any, answer: any, o: Record<string, unknown> = {}) =>
  item({ id: `H-${state}-${done ? done.kind : 'w'}-${answer ? answer.source : 'n'}`, title: 'IV-04 design: which fold key?', body: 'Which key folds a group?', options: H_OPTS, recommendation: '(b), fewer keys', blocks: 'IV-04', created: '2026-10-16T09:00:00', state, done, answer, ...o })
const WAITING = handled('answered-waiting', null, ANS())
const DELIVERED = handled('done', { kind: 'answered', ts: '2026-10-16T12:00:00', reason: null }, ANS({ delivered_ts: '2026-10-16T12:02:00' }))
const CHAT = handled('done', { kind: 'answered', ts: '2026-10-16T12:00:00', reason: null }, ANS({ source: 'chat' }))
const FILE = handled('done', { kind: 'answered-file', ts: '2026-10-16T12:00:00', reason: null }, null)
const WITHDRAWN = handled('done', { kind: 'withdrawn', ts: '2026-10-16T12:00:00', reason: 'asked twice' }, null)
const READ = item({ id: 'R5', kind: 'read', title: 'Old read', body: 'seen', state: 'done', blocks: 'IV-04', created: '2026-10-16T09:00:00', done: { kind: 'read', ts: '2026-10-16T12:00:00', reason: null } })
const REMOVED = handled('done', { kind: 'removed', ts: '2026-10-16T12:00:00', reason: null }, null)

// Press Show all when the screen offers it: a cut screen must offer it, a failing press must fail the test.
async function showAll(ui: any) {
  if (await ui.find({ key: 'show-all' })) await ui.press({ key: 'show-all' })
}

// --- helpers ----------------------------------------------------------------------------------

// One boot per test (the hooks are registered once): later opens in the same test reuse it, so a test passes the
// same universe of items every time.
const booted = new WeakMap<object, { w: any; ui: any }>()
async function open($: any, on: any, items: any[], id: string, cols = 80, rows = ROWS_24, cli?: (argv: string[], stdin?: string) => any) {
  let st = booted.get($)
  if (!st) booted.set($, (st = { w: await boot($, on, snap(items), cli), ui: null }))
  else {
    st.w.current = snap(items)
    await $.session.start(START)
  }
  if (st.ui) await st.ui.unmount().catch(() => undefined)
  await $.command.run({ command: 'inbox' })
  const ui = await $.ui.mount(pane('terminal', cols, rows))
  st.ui = ui
  const target = items.find((i) => i.id === id)
  if (target.state === 'done') {
    await ui.press({ key: 'done' })
    await ui.press({ key: `d-${id}` })
  } else await ui.press({ key: id })
  return { ui, w: st.w }
}

// Leaves of the tree in reading order; a row Box (a hanging block, the Back row) is one leaf.
function leaves(n: any, out: string[] = []): string[] {
  if (n === null || n === undefined || typeof n === 'string') return out
  if (Array.isArray(n)) {
    n.forEach((c) => leaves(c, out))
    return out
  }
  if (n.type === 'Box' && n.props?.flexDirection === 'row' && n.props?.width === undefined) {
    out.push((n.children ?? []).flatMap((c: any) => leaves(c)).join(''))
    return out
  }
  if (['Text', 'Button', 'Input', 'Select'].includes(n.type)) return (out.push(...lines(n)), out)
  return leaves(n.children ?? [], out)
}
const rowsOf = (tree: any): string[] => leaves(tree)
const textOf = (tree: any): string => rowsOf(tree).join('\n')

// An independent wrap (the reference of core-visual.test.ts 2.2b), not the screen's `rowsFor`.
function refRows(text: string, cols: number): number {
  let rows = 0
  for (const line of text.split('\n')) {
    const chars = [...line]
    let row = 1
    let col = 0
    let i = 0
    while (i < chars.length) {
      if (chars[i] === ' ') {
        if (col + 1 > cols) { row++; col = 0 }
        col++
        i++
        continue
      }
      let j = i
      let ww = 0
      while (j < chars.length && chars[j] !== ' ') ww += cellWidth(chars[j++])
      if (col + ww > cols && ww <= cols) { row++; col = 0 }
      for (; i < j; i++) {
        const cw = cellWidth(chars[i])
        if (col + cw > cols) { row++; col = 0 }
        col += cw
      }
    }
    rows += row
  }
  return rows
}

// Rows the tree takes at `cols`, by the reference wrap; a hanging block's text wraps in the width after its prefix.
function treeRows(n: any, cols: number): number {
  if (n === null || n === undefined || typeof n === 'string') return 0
  if (Array.isArray(n)) return n.reduce((a: number, c: any) => a + treeRows(c, cols), 0)
  if (n.type === 'Box' && n.props?.flexDirection === 'row') {
    const kids = n.children ?? []
    if (kids[0]?.props?.width !== undefined) return Math.max(treeRows(kids[0], kids[0].props.width), treeRows(kids.slice(1), cols - kids[0].props.width))
    return refRows(leaves(n).join(''), cols)
  }
  if (n.type === 'Box' && n.props?.width !== undefined) return treeRows(n.children, n.props.width)
  if (['Text', 'Button', 'Input', 'Select'].includes(n.type)) return lines(n).reduce((a, l) => a + refRows(l, cols), 0)
  return treeRows(n.children ?? [], cols)
}

function walk(n: any, fn: (n: any) => void) {
  if (n === null || n === undefined || typeof n === 'string') return
  if (Array.isArray(n)) return n.forEach((c) => walk(c, fn))
  fn(n)
  walk(n.children ?? [], fn)
}
const flat = (n: any): string => (n === null || n === undefined ? '' : typeof n === 'string' ? n : Array.isArray(n) ? n.map(flat).join('') : flat(n.children ?? []))

// Words only: markup characters and punctuation drop out, so a bold, chip or glyph does not break the order.
const words = (s: string) => s.replace(/[^\p{L}\p{N}]+/gu, ' ').split(' ').filter(Boolean)
// `needle` words appear in `hay` words in order, as a subsequence.
function inOrder(hay: string, needle: string): boolean {
  const h = words(hay)
  let i = 0
  for (const w of words(needle)) {
    while (i < h.length && h[i] !== w) i++
    if (i === h.length) return false
    i++
  }
  return true
}

// Style props removed everywhere: what a colourless terminal shows.
function colourless(n: any): any {
  if (n === null || n === undefined || typeof n === 'string') return n
  if (Array.isArray(n)) return n.map(colourless)
  const props: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(n.props ?? {})) if (!['color', 'dimColor', 'bold', 'weight', 'italic', 'underline', 'inverse', 'backgroundColor'].includes(k)) props[k] = v
  return { ...n, props, children: colourless(n.children ?? []) }
}

// --- 3.1 the top block, counted with the reference wrap --------------------------------------

test('V-01: the top block is first, in order, inside bodyRows 6 at 40 and 80 columns', async ($, on) => {
  for (const [cols, rows] of [[80, ROWS_24], [40, ROWS_24], [80, ROWS_40], [40, ROWS_40]]) {
    const { ui } = await open($, on, [E1], 'E1', cols, rows)
    const tree = await ui.drawn()
    const r = rowsOf(tree)
    const idx = (s: string) => r.findIndex((l) => l.includes(s))
    expect([idx('[← Back]'), idx('E1 · answer'), idx(E1_TITLE.slice(0, 20)), idx('✓ recommends (c)')]).toEqual([0, 2, 3, 4])
    // back (the Back row), header, title, pointer: the rows before the body start
    const top = 1 + treeRows((await ui.find({ type: 'Text', text: 'E1 · answer' }))?.node ?? [], cols)
    expect(top).toBeGreaterThan(0)
    const upto = rows7(tree, 'recommends (c)', cols)
    expect(upto, `cols ${cols} rows ${rows}\n${r.join("\n")}`).toBeLessThanOrEqual(rows)
    await ui.unmount()
  }
})

// Rows from the top through the leaf holding `marker`, by the reference wrap.
function rows7(tree: any, marker: string, cols: number): number {
  let n = 0
  let done = false
  const go = (x: any) => {
    if (done || x === null || x === undefined || typeof x === 'string') return
    if (Array.isArray(x)) return x.forEach(go)
    if (x.type === 'Box' && x.props?.flexDirection === 'column' && x.props?.width === undefined) return go(x.children ?? [])
    // an unflagged Box is Ink's default row: the Back button and its hint share one line
    n += x.type === 'Box' && x.props?.flexDirection === undefined && x.props?.width === undefined ? refRows(leaves(x).join(''), cols) : treeRows(x, cols)
    if (flat(x).includes(marker)) done = true
  }
  go(tree)
  return n
}

test('3.1c: the top block stays whole with no notice and with an error row, at both widths', async ($, on) => {
  for (const [cols, rows] of [[80, ROWS_24], [40, ROWS_24]]) {
    for (const withNotice of [false, true]) {
      const { ui } = await open($, on, [E1], 'E1', cols, rows)
      if (withNotice) await ui.press({ key: 'send' }) // an empty answer is refused: the real way to get an error row
      const tree = await ui.drawn()
      const r = rowsOf(tree)
      expect(r.some((l) => l.startsWith('⚠ '))).toBe(withNotice)
      expect(rows7(tree, 'recommends (c)', cols)).toBeLessThanOrEqual(ROWS_24)
      expect(r.findIndex((l) => l.includes('✓ recommends (c)'))).toBeLessThan(r.findIndex((l) => l.includes('Options')))
      await ui.unmount()
    }
  }
})

test('3.1d: bodyRows 14 and 10 (too small for the screen): no crash, every option drawn, the floor of body kept', async ($, on) => {
  for (const rows of [14, 10]) {
    const { ui } = await open($, on, [E1], 'E1', 80, rows)
    const text = textOf(await ui.drawn())
    for (const k of ['(a) ', '(b) ', '(c) ']) expect(text).toContain(k)
    expect(text).toContain('Brief: "the inbox only shows prose')
    expect(text).toContain('more lines')
    await ui.unmount()
  }
})

// --- design states: text, order, tokens -------------------------------------------------------

test('M1: E1 open at 80 columns, 6 rows: top block, hint, floor of body, options as blocks, nothing picked', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  const tree = await ui.drawn()
  const text = textOf(tree)
  expect(text).toContain('↓ more below')
  expect(text).toContain('E1 · answer · blocks spawning the pod (BA, Tech Lead) · created 5h ago')
  expect(text).toContain('… 7 more lines')
  expect(text).toContain('Options')
  expect(text).toContain('  (a) Attached page')
  expect(text).not.toContain('Picked:')
  expect(text).not.toContain('your pick')
  expect(text).not.toContain('<br>')
  // the full recommendation appears once, under the marked option (V-12)
  expect(text.split('✓ recommended: ').length - 1).toBe(1)
  expect(text.split(E1_REC).length - 1).toBe(1)
  expect(text.indexOf('(c) Both')).toBeLessThan(text.indexOf('✓ recommended: '))
  expect(text.indexOf('✓ recommended: ')).toBeLessThan(text.indexOf('Your answer'))
  expect(text).not.toContain('Manager recommends')
  expect(styleOf(tree, '↓ more below')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'E1')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'answer')).toEqual({ color: 'warning' })
  expect(styleOf(tree, 'blocks spawning the pod (BA, Tech Lead)')).toEqual({ color: 'error' })
  expect(styleOf(tree, ' · created 5h ago')).toEqual({ dimColor: true })
  expect(styleOf(tree, E1_TITLE)).toEqual({ bold: true })
  expect(styleOf(tree, '✓ recommends (c)')).toEqual({ color: 'success' })
  expect(styleOf(tree, '… 7 more lines')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'Options')).toEqual({ bold: true })
  expect(styleOf(tree, '(a)')).toEqual({ bold: true })
  expect(styleOf(tree, '✓ recommended: ')).toEqual({ color: 'success', bold: true })
  expect((await ui.find({ key: 'send' }))?.props?.variant).toBeUndefined()
  expect(await ui.find({ key: 'show-all' })).toBeDefined()
})

test('M3: picking (c) marks the block in words and the Select; picking (a) shows no warning (V-13)', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  await ui.select({ key: 'pick', value: 'c' })
  let tree = await ui.drawn()
  let text = textOf(tree)
  expect(text).toContain('▸ (c) Both: (a) for diagrams, (b) for options/recommendation layout ← your pick')
  expect(styleOf(tree, '← your pick')).toEqual({ bold: true })
  await ui.select({ key: 'pick', value: 'a' })
  tree = await ui.drawn()
  text = textOf(tree)
  expect(text).toContain('▸ (a) Attached page')
  expect(text).not.toMatch(/warn|differs|instead|not the recommended/i)
  expect(text).toContain('✓ recommended: (c)')
})

test('M4: E2 (rec not marked): pointer with the start of the rec, the full rec once after the body, Your reply', async ($, on) => {
  const { ui } = await open($, on, [E2], 'E2', 40, ROWS_24)
  const tree = await ui.drawn()
  const r = rowsOf(tree)
  expect(r[0]).toBe('[← Back]')
  expect(r.some((l) => l.startsWith('E2 · answer · blocks nothing · created'))).toBe(true)
  const ptr = r.find((l) => l.startsWith('✓ recommends: '))
  expect(ptr).toBeDefined()
  expect(cellWidth(ptr as string)).toBeLessThanOrEqual(40)
  expect((ptr as string).endsWith('…')).toBe(true)
  expect(styleOf(tree, '✓ recommends: ')).toEqual({ color: 'success' })
  expect(styleOf(tree, 'blocks nothing')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'answer')).toEqual({ color: 'warning' })
  const text = r.join('\n')
  expect(text).toContain("Manager recommends: Reply 'all recs' to take every [rec] below, or name the numbers you change")
  expect(styleOf(tree, 'Manager recommends: ')).toEqual({ color: 'success', bold: true })
  expect(text.split("name the numbers you change").length - 1).toBe(1)
  expect(r.indexOf('<Your reply>')).toBeGreaterThan(r.findIndex((l) => l.startsWith('Manager recommends')))
  expect(text).not.toContain('{Your answer')
  // a first block taller than the floor is clipped with an ellipsis; Show all reaches the rest
  const body = r.slice(r.findIndex((l) => l.startsWith('✓ recommends: ')) + 1, r.findIndex((l) => l.includes('more lines')))
  expect(body.length).toBeGreaterThan(0)
  expect(body.at(-1)?.endsWith('…')).toBe(true)
  await ui.press({ key: 'show-all' })
  const full = textOf(await ui.drawn())
  expect(full).toContain('✓ recommended the item screen')
  expect(inOrder(full, VISUAL.e2.replace(/<br>\s+\[rec\]/g, '<br>recommended').split('<br>').slice(1).join(' '))).toBe(true)
})

test('M5: read item with markdown: structure, glyphs, chips, table, Mark read last', async ($, on) => {
  const { ui } = await open($, on, [R1], 'R1', 80, ROWS_24)
  let tree = await ui.drawn()
  let text = textOf(tree)
  expect(text).toContain('R1 · read · blocks IV-06 · created 37m ago')
  expect(text).not.toContain('{Your answer')
  expect(styleOf(tree, 'read')).toEqual({})
  expect(styleOf(tree, 'blocks IV-06')).toEqual({ color: 'error' })
  expect(styleOf(tree, 'Check-in summary')).toEqual({ bold: true, underline: true })
  expect(styleOf(tree, 'squad/x')).toEqual({ bold: true })
  expect(styleOf(tree, ' qa-w ')).toEqual({ inverse: true })
  expect(text).toContain('• first bullet')
  expect(text).toContain('• second bullet')
  expect(text).toContain('1. numbered one')
  expect(styleOf(tree, '1.')).toEqual({ bold: true })
  expect(text).toContain('Task   State')
  expect(text).toContain('─────  ────────')
  expect(text).not.toMatch(/\|---|\*\*|`|^#/m)
  expect(styleOf(tree, 'Task   State')).toEqual({ bold: true })
  expect(text).toContain('↓ more below')
  expect((await ui.find({ key: 'mark-read' }))?.props?.hotkey).toBe('m')
  expect(rowsOf(tree).at(-1)).toBe('[Mark read (m)]')
  await ui.unmount()
  // 40 columns: the table is stacked, column names bold, a blank row between records
  const narrow = await open($, on, [R1], 'R1', 40, 40)
  tree = await narrow.ui.drawn()
  text = textOf(tree)
  expect(text).toContain('Task: IV-01')
  expect(text).toContain('State: passed')
  expect(text).not.toContain('Task   State')
  expect(styleOf(tree, 'Task')).toEqual({ bold: true })
  // a read item's body floor is 12 rows: with a tall pane it all fits and there is no hint
  const tall = await open($, on, [R1], 'R1', 80, 40)
  expect(textOf(await tall.ui.drawn())).not.toContain('↓ more below')
  expect(textOf(await tall.ui.drawn())).not.toContain('more lines')
})

const DESIGN_HANDLED: [string, any, string, string, Record<string, unknown>][] = [
  ['answered-waiting', WAITING, 'Answered 2026-10-16 12:00, waiting for the Manager.', 'warning', { color: 'warning' }],
  ['delivered', DELIVERED, 'Answered 2026-10-16 12:00, delivered 2026-10-16 12:02.', 'success', { color: 'success' }],
  ['answered in chat', CHAT, 'Answered in chat 2026-10-16 12:00.', 'success', { color: 'success' }],
  ['answered in the file', FILE, 'Answered in the file (not through the inbox).', 'warning', { color: 'warning' }],
  ['withdrawn', WITHDRAWN, 'Withdrawn by the Manager 2026-10-16 12:00: asked twice.', 'dim', { dimColor: true }],
  ['read', READ, 'Read 2026-10-16 12:00.', 'dim', { dimColor: true }],
  ['removed', REMOVED, 'Removed from escalations.md before an answer.', 'dim', { dimColor: true }],
]
for (const [name, it, line, , style] of DESIGN_HANDLED) {
  test(`handled ${name}: the state is right after the title, before the body (V-03 v3.1), token per V-15`, async ($, on) => {
    for (const [cols, rows] of SIZES) {
      const { ui } = await open($, on, [it], it.id, cols, rows)
      const tree = await ui.drawn()
      const r = rowsOf(tree)
      const at = (s: string) => r.findIndex((l) => l.includes(s))
      expect(at(it.title.slice(0, 15))).toBeGreaterThan(0)
      expect(at(line.slice(0, 20))).toBe(at(it.title.slice(0, 15)) + 1)
      if (it.answer) expect(at('Your answer')).toBe(at(line.slice(0, 20)) + 1)
      if (it.id === 'E3') expect(at('Which key folds a group?')).toBeGreaterThan(at(line.slice(0, 20)))
      expect(styleOf(tree, line.slice(0, 20))).toEqual(style)
      expect(await ui.find({ key: 'send' })).toBeUndefined()
      expect(await ui.find({ key: 'pick' })).toBeUndefined()
      expect((await ui.find({ key: 'back' }))?.props?.hotkey).toBe('b')
      await ui.unmount()
    }
  })
}

test('handled with options: blocks, the recommended mark stays, the PO pick in words (V-14a); answer shown plain (V-26)', async ($, on) => {
  const all = [WAITING, DELIVERED, READ]
  const { ui } = await open($, on, all, WAITING.id, 80, ROWS_24)
  const tree = await ui.drawn()
  const text = textOf(tree)
  expect(text).toContain('▸ (b) Tab only ← your pick')
  expect(text).toContain('  (a) hotkey m')
  expect(text).toContain('✓ recommended: (b), fewer keys')
  expect(text).toContain('(b) use **Tab**, no hotkey')
  expect(styleOf(tree, 'blocks IV-04')).toEqual({ color: 'error' })
  expect(styleOf(tree, 'Your answer')).toEqual({ bold: true })
  expect(styleOf(await (await open($, on, all, DELIVERED.id, 80, ROWS_24)).ui.drawn(), 'blocks IV-04')).toEqual({ dimColor: true })
  expect(styleOf(await (await open($, on, all, READ.id, 80, ROWS_24)).ui.drawn(), 'blocks IV-04')).toEqual({ dimColor: true })
})

test('handled: the kept line and the unconfirmed delivery keep today\'s words and tones', async ($, on) => {
  const kept = handled('answered-waiting', null, ANS(), { flags: ['cell-not-written'], id: 'K1' })
  const { ui } = await open($, on, [kept], 'K1', 80, ROWS_24)
  const t = await ui.drawn()
  expect(textOf(t)).toContain('Answer kept. escalations.md was not updated.')
  expect(styleOf(t, 'Answer kept.')).toEqual({ dimColor: true })
})

// --- header and title rules -------------------------------------------------------------------

test('header: created under a day is `5h ago`; from a day the date and age wide, the age alone compact; now', async ($, on) => {
  const old = item({ id: 'E5', created: '2026-10-12T09:00:00' })
  for (const [cols, want] of [[80, 'created 2026-10-12 (3d ago)'], [60, 'created 2026-10-12 (3d ago)'], [59, 'created 3d ago']] as const) {
    const { ui } = await open($, on, [old], 'E5', cols, ROWS_24)
    expect(textOf(await ui.drawn())).toContain(want)
  }
  const fresh = item({ id: 'E6', created: '2026-10-15T12:00:00' })
  expect(textOf(await (await open($, on, [fresh], 'E6')).ui.drawn())).toContain('created now')
  expect(textOf(await (await open($, on, [item({ id: 'E7', created: '2026-10-15T11:23:00' })], 'E7')).ui.drawn())).toContain('created 37m ago')
})

test('title of 300 characters: 3 rows with an ellipsis, a `full title` row, Show all draws it whole (V-09)', async ($, on) => {
  const long = item({ id: 'E8', title: VISUAL.title300, body: 'tail' })
  for (const cols of [80, 40, 30]) {
    const { ui } = await open($, on, [long], 'E8', cols, ROWS_24)
    const tree = await ui.drawn()
    const r = rowsOf(tree)
    const t = r.find((l) => l.startsWith('TTT')) as string
    expect(t.endsWith('…')).toBe(true)
    expect(refRows(t, cols)).toBeLessThanOrEqual(3)
    expect(r.join('\n')).toContain('… full title')
    expect(r.join('\n')).not.toContain('more lines')
    await ui.press({ key: 'show-all' })
    expect(textOf(await ui.drawn())).toContain('T'.repeat(300))
    expect(textOf(await ui.drawn())).not.toContain('full title')
    await ui.unmount()
  }
})

test('hint counts the `… full title` row: cut title, uncut body at 80x7 shows `↓ more below`, a size that fits shows none', async ($, on) => {
  const long = item({ id: 'E8', kind: 'read', title: VISUAL.title300, body: 'b' })
  const small = await open($, on, [long], 'E8', 80, 7)
  expect(textOf(await small.ui.drawn())).toContain('↓ more below')
  await small.ui.unmount()
  const fits = await open($, on, [long], 'E8', 80, 40)
  expect(textOf(await fits.ui.drawn())).not.toContain('↓ more below')
  await fits.ui.unmount()
})

test('QAB F1: 80-char titles whose first row is exactly 36 cells: title cut at 2 rows, the pointer is inside the 6-row viewport at 36 columns', async ($, on) => {
  const titles = ['inbox-visual: what should the visual mean in the terminal inbox for every kind of item', 'auth: do we accept the legacy tokens during the migration window for internal tools?']
  for (const [i, title] of titles.entries()) {
    const long = item({ id: `F1-${i}`, title, blocks: 'IV-02', created: '2026-10-16T09:00:00', body: VISUAL.e1, recommendation: E1_REC, options: E1_OPTS })
    const { ui } = await open($, on, [long], `F1-${i}`, 36, ROWS_24)
    const tree = await ui.drawn()
    const r = rowsOf(tree)
    const t = r.find((l) => l.startsWith(title.slice(0, 5))) as string
    expect(t.endsWith('…'), r.join('\n')).toBe(true)
    expect(refRows(t, 36)).toBe(2)
    expect(rows7(tree, 'recommends', 36), r.join('\n')).toBeLessThanOrEqual(ROWS_24)
    await ui.unmount()
  }
})

test('QAB F2: a `[rec]` line keeps its leading spaces', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'F2', body: 'intro\n   [rec] take (a)' })], 'F2', 80, ROWS_40)
  expect(rowsOf(await ui.drawn())).toContain('   ✓ recommended take (a)')
  await ui.unmount()
})

test('QAB F3: only the header is clipped: the row says `… full header`, a whole title is not named', async ($, on) => {
  const blocks = `${'work item '.repeat(12)}end`
  const { ui } = await open($, on, [item({ id: 'F3', blocks, body: 'b' })], 'F3', 40, ROWS_40)
  const text = textOf(await ui.drawn())
  expect(text).toContain('… full header')
  expect(text).not.toContain('full title')
  expect(text).not.toContain('header and title')
  await ui.unmount()
})

test('3.1e: 300-char title, 2-row header, 40 columns, 6 rows: the pointer is inside the first viewport, the title shows 2 rows', async ($, on) => {
  const blocks = `${'work item '.repeat(12)}end`
  const long = item({ id: 'E8', title: VISUAL.title300, blocks, body: VISUAL.e1, recommendation: E1_REC, options: E1_OPTS })
  // titleCap = clamp(bodyRows - 1 - headerRows - pointerRows, 1, 3), header 2 rows (clipped) and pointer 1 row in all three:
  // 40x6: 6-1-2-1 = 2; 80x6: 6-1-2-1 = 2; 40x11: 11-1-2-1 = 7, capped at 3
  for (const [cols, rows, cap] of [[40, ROWS_24, 2], [80, ROWS_24, 2], [40, ROWS_40, 3]]) {
    const { ui } = await open($, on, [long], 'E8', cols, rows).catch((e: any) => { throw new Error(`${cols}x${rows}: ${e.message}`) })
    const tree = await ui.drawn()
    const r = rowsOf(tree)
    expect(rows7(tree, 'recommends', cols), r.join('\n')).toBeLessThanOrEqual(rows)
    const t = r.find((l) => l.startsWith('TTT')) as string
    expect(t.endsWith('…')).toBe(true)
    expect(refRows(t, cols), `${cols}x${rows}`).toBe(cap)
    expect(r.join('\n')).toContain('… full header and title')
    if (cols === 40 && rows === ROWS_24) {
      expect(r.findIndex((l) => l.includes('… full header and title'))).toBeGreaterThan(r.findIndex((l) => l.includes('✓ recommends')))
      await ui.press({ key: 'show-title' })
      expect(textOf(await ui.drawn())).toContain('T'.repeat(300))
    }
    await ui.unmount()
  }
})

test('blocks of 120 characters: the header is clipped to 2 rows, Show all draws it whole', async ($, on) => {
  const blocks = `${'work item '.repeat(12)}end`
  for (const cols of [80, 40]) {
    const { ui } = await open($, on, [item({ id: 'E9', blocks })], 'E9', cols, ROWS_24)
    const header = rowsOf(await ui.drawn()).find((l) => l.startsWith('E9 · answer')) as string
    expect(refRows(header, cols)).toBeLessThanOrEqual(2)
    expect(header).toContain('…')
    await ui.press({ key: 'show-all' })
    expect(textOf(await ui.drawn())).toContain(blocks)
  }
})

test('empty body and a body equal to the title: no body rows, no Show all', async ($, on) => {
  const all = [item({ id: 'N1', body: '' }), item({ id: 'N2', body: 'Which branch merges first?' })]
  for (const id of ['N1', 'N2']) {
    const { ui } = await open($, on, all, id, 80, 40)
    expect(textOf(await ui.drawn())).not.toContain('more lines')
    expect(await ui.find({ key: 'show-all' })).toBeUndefined()
    expect(textOf(await ui.drawn())).not.toContain('↓ more below')
  }
})

// --- notice rows ------------------------------------------------------------------------------

test('notice: on the answer form directly above Your answer, the top block unchanged', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  await ui.press({ key: 'send' })
  const r = rowsOf(await ui.drawn())
  const n = r.findIndex((l) => l.startsWith('⚠ '))
  expect(n).toBeGreaterThan(0)
  expect(r[n + 1].startsWith('{Your answer')).toBe(true)
  expect(r.slice(0, 5)).toEqual(['[← Back]', r[1], r[2], E1_TITLE, '✓ recommends (c)'])
})

test('notice on a read item sits under the Back row and the title cap drops to 2 rows', async ($, on) => {
  const R3 = item({ id: 'R3', kind: 'read', title: VISUAL.title300, body: 'b' })
  const { ui } = await open($, on, [R3], 'R3', 40, ROWS_24, (argv) => (argv[0] === 'read' ? { exitCode: 2, stdout: '', stderr: 'R3 is locked\n' } : undefined))
  await ui.press({ key: 'mark-read' })
  const r = rowsOf(await ui.drawn())
  const n = r.findIndex((l) => l.startsWith('⚠ '))
  expect(r[n]).toBe('⚠ R3 is locked')
  expect(r.slice(0, n).filter((l) => !l.includes('more below'))).toEqual(['[← Back (b)]'])
  expect(r[n + 1].startsWith('R3 · read')).toBe(true)
  const t = r.find((l) => l.startsWith('TTT')) as string
  expect(refRows(t, 40)).toBeLessThanOrEqual(2)
})

// --- V-11 through the real screen ---------------------------------------------------------------

const V11: [string, string | null][] = [
  [E1_REC, 'c'], ['(c) yes', 'c'], ['  (c) yes', 'c'], ['(a) no, (b) is worse', 'a'],
  ['(C) yes', null], ['c) yes', null], ['Option c', null], ['c. yes', null],
  ['(a)+(b)', null], ['(a)/(b)', null], ['(a), (b)', null], ['(a) and (b)', null],
  ['(z) yes', null], ["Reply 'all recs' to take them", null], ['b: less rework', null],
]
test('V-11: each row through the screen: mark and success only on the marked option; the rec appears once (V-12)', async ($, on) => {
  for (const [rec, key] of V11) {
    const it = item({ id: 'E3', options: E1_OPTS, recommendation: rec })
    const { ui } = await open($, on, [it], 'E3', 80, 40)
    const tree = await ui.drawn()
    const label = (l: string) => {
      let c = 0
      walk(tree, (n) => {
        if (n.type === 'Text' && n.children?.length === 1 && n.children[0] === l) c++
      })
      return c
    }
    const r0 = rowsOf(tree)
    const trimmed = rec.trim()
    if (key) {
      expect(label('✓ recommended: ')).toBe(1)
      expect(r0.filter((l) => l.endsWith(`✓ recommended: ${trimmed}`))).toHaveLength(1)
      expect(styleOf(tree, '✓ recommended: ')).toEqual({ color: 'success', bold: true })
      expect(label('Manager recommends: ')).toBe(0)
      // the mark sits in the block of its own option, a separate Text from the key and the option text
      const r = rowsOf(tree)
      const at = r.findIndex((l) => l.includes('✓ recommended: '))
      expect(r.slice(0, at + 1).reverse().find((l) => /^[▸ ] \([a-z]\)/.test(l))?.[3]).toBe(key)
      expect(r.join('\n').split('✓ recommends (' + key + ')').length - 1).toBe(1)
    } else {
      expect(label('✓ recommended: ')).toBe(0)
      expect(r0.filter((l) => l === `Manager recommends: ${trimmed}`)).toHaveLength(1)
      expect(textOf(tree)).toContain('✓ recommends: ')
      expect(textOf(tree)).not.toContain('✓ recommends (')
    }
    expect(textOf(tree).split(trimmed).length - 1 - (key ? 0 : 1)).toBe(1) // the unmarked pointer shows its clipped start
    await ui.unmount()
  }
})

test('V-11: no rec at all: no pointer, no recommends line; options still drawn', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'E3', options: H_OPTS })], 'E3', 80, 40)
  const text = textOf(await ui.drawn())
  expect(text).not.toContain('recommend')
  expect(text).toContain('(c) both')
})

test('V-14: options not parsed: the raw text whole, then the rec line, then Your reply; no Select', async ($, on) => {
  const it = item({ id: 'E3', options_raw: '(a) one (b) two ;; weird', recommendation: 'go with one' })
  const { ui } = await open($, on, [it], 'E3', 80, 40)
  const r = rowsOf(await ui.drawn())
  const at = (s: string) => r.findIndex((l) => l.includes(s))
  expect(at('Options, as the Manager wrote them')).toBeLessThan(at('(a) one (b) two ;; weird'))
  expect(at('(a) one (b) two ;; weird')).toBeLessThan(at('Manager recommends: go with one'))
  expect(at('Manager recommends: go with one')).toBeLessThan(at('<Your reply'))
  expect(await ui.find({ key: 'pick' })).toBeUndefined()
})

// --- 4: the body cut by rows ------------------------------------------------------------------

test('body cut: E1 at 6 rows shows the floor, then N more lines, then the options; Show all draws every word in order', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  const more = r.findIndex((l) => l.includes('… 7 more lines'))
  expect(more).toBeGreaterThan(r.findIndex((l) => l.startsWith('✓ recommends')))
  expect(r.findIndex((l) => l === 'Options')).toBeGreaterThan(more)
  const shown = r.slice(r.findIndex((l) => l.startsWith('✓ recommends')) + 1, more)
  expect(shown.map((l) => refRows(l, 80)).reduce((a, b) => a + b, 0)).toBeLessThanOrEqual(3)
  await ui.press({ key: 'show-all' })
  const full = textOf(await ui.drawn())
  const body = VISUAL.e1.split('<br>').slice(1).join('\n')
  expect(inOrder(full, body)).toBe(true)
  expect(full).not.toContain('more lines')
  await ui.unmount()
})

test('body cut: a tall pane shows everything, no cut and no hint; the hint is on at 6 rows', async ($, on) => {
  const tall = await open($, on, [E1], 'E1', 80, 60)
  const text = textOf(await tall.ui.drawn())
  expect(text).not.toContain('more lines')
  expect(text).not.toContain('↓ more below')
  expect(await tall.ui.find({ key: 'show-all' })).toBeUndefined()
  expect(inOrder(text, VISUAL.e1.split('<br>').slice(1).join('\n'))).toBe(true)
  const mid = await open($, on, [E1], 'E1', 80, 20)
  expect(textOf(await mid.ui.drawn())).toContain('more lines')
  const short = await open($, on, [E1], 'E1', 80, ROWS_24)
  expect(textOf(await short.ui.drawn())).toContain('↓ more below')
})

test('body of 40 lines: the preview, N more lines, the answer controls still below the options', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'E3', body: VISUAL.forty, options: H_OPTS })], 'E3', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  expect(r.some((l) => /… \d+ more lines/.test(l))).toBe(true)
  expect(r.findIndex((l) => l === 'Options')).toBeGreaterThan(r.findIndex((l) => l.includes('more lines')))
  expect(r.some((l) => l.startsWith('{Your answer'))).toBe(true)
  expect(r.at(-1)).toBe('[Send answer]')
  await ui.press({ key: 'show-all' })
  const full = textOf(await ui.drawn())
  for (let i = 1; i <= 40; i++) expect(full).toContain(`line ${i} of a forty-line body`)
})

// --- 5: hostile fixtures ----------------------------------------------------------------------

const HOSTILE: Record<string, string> = {
  longLine: 'x'.repeat(10000),
  stars: '**'.repeat(5000),
  unclosedFence: VISUAL.unclosedFence,
  onlyPipe: VISUAL.onlyPipe,
  onlyPipes: VISUAL.onlyPipes,
  empty: '',
  indent: `${' '.repeat(5000)}- deep bullet\n${' '.repeat(5000)}1. deep number`,
  token200: `before ${'u'.repeat(200)} after`,
  code200: `\`\`\`\n${'c'.repeat(200)}\n\`\`\``,
  table20: `|${Array.from({ length: 20 }, (_, i) => ` c${i} `).join('|')}|\n|${Array.from({ length: 20 }, () => '---').join('|')}|\n|${Array.from({ length: 20 }, (_, i) => ` v${i} `).join('|')}|`,
  cjk: VISUAL.cjkTable,
}
test('hostile bodies mount in under 2 s each, draw as text, and leave E1 intact', async ($, on) => {
  for (const cols of [40, 30]) {
    for (const [name, body] of Object.entries(HOSTILE)) {
      const bad = item({ id: 'X1', title: 'hostile', body })
      const { ui } = await open($, on, [bad, E1], 'X1', cols, ROWS_24)
      const t0 = Date.now()
      await ui.drawn()
      await showAll(ui)
      const tree = await ui.drawn()
      expect(Date.now() - t0, name).toBeLessThan(2000)
      // nothing exceeds the pane: a hanging prefix is capped, every code row fits
      walk(tree, (n) => {
        if (n.type === 'Box' && n.props?.width !== undefined) expect(n.props.width, name).toBeLessThanOrEqual(Math.floor(cols / 2))
        if (n.type === 'Text' && flat(n).startsWith('  │ ')) expect(cellWidth(flat(n)), name).toBeLessThanOrEqual(cols)
      })
      if (name === 'longLine') expect(textOf(tree).replace(/\n/g, '')).toContain('x'.repeat(10000))
      await ui.unmount()
      const other = await open($, on, [bad, E1], 'E1', cols, ROWS_24)
      expect(textOf(await other.ui.drawn())).toContain('✓ recommends (c)')
      await other.ui.unmount()
    }
  }
})

// --- 6, 3.7: V-27 ----------------------------------------------------------------------------

const BAD = 'a\u001b[31mb\u001b]0;pwned\u0007c‮d'
const clean = (s: string) => expect(s).not.toMatch(/[\u001b‮\u0007]/)
test('V-27: ESC, OSC and U+202E in every drawn source are removed', async ($, on) => {
  const sources: [string, Record<string, unknown>][] = [
    ['title', { title: `T ${BAD}` }],
    ['body', { body: `line ${BAD}\n**b ${BAD}**` }],
    ['code fence line', { body: `\`\`\`${BAD}\n${BAD}\n\`\`\`` }],
    ['[rec] line', { body: `[rec] ${BAD}` }],
    ['table cell', { body: `| h |\n|---|\n| ${BAD} |` }],
    ['option text', { options: [{ key: 'a', text: `opt ${BAD}` }, { key: 'b', text: 'two' }] }],
    ['option key', { options: [{ key: `a${BAD}`, text: 'one' }, { key: 'b', text: 'two' }] }],
    ['rec', { options: E1_OPTS, recommendation: `(c) rec ${BAD}` }],
    ['unmarked rec', { recommendation: `rec ${BAD}` }],
    ['id', { id: `E3${BAD}` }],
    ['blocks', { blocks: `blk ${BAD}` }],
    ['options_raw', { options_raw: `raw ${BAD}` }],
  ]
  for (const [name, o] of sources) {
    const it = item({ id: 'E3', ...o })
    const { ui } = await open($, on, [it], it.id, 80, 40)
    expect(textOf(await ui.drawn()), name).not.toBe('')
    await showAll(ui)
    clean(`${name}: ${textOf(await ui.drawn())}`.replace(name, ''))
    await ui.unmount()
  }
  const w = handled('done', { kind: 'withdrawn', ts: '2026-10-16T12:00:00', reason: `why ${BAD}` }, null)
  clean(textOf(await (await open($, on, [w], w.id, 80, 40)).ui.drawn()))
  const a = handled('answered-waiting', null, ANS({ text: `typed ${BAD}` }))
  clean(textOf(await (await open($, on, [a], a.id, 80, 40)).ui.drawn()))
})

// --- QA whitebox survivors: each test below goes red on one named mutation -------------------

test('bullet glyph by depth: 0 is •, 1 is ◦, 2 and deeper are ▪', async ($, on) => {
  const body = ['- d0', '  - d1', '    - d2', '          - d5'].join('\n')
  const { ui } = await open($, on, [item({ id: 'G1', kind: 'read', body })], 'G1', 80, 40)
  const r = rowsOf(await ui.drawn())
  expect(r.filter((l) => /d\d$/.test(l)).map((l) => l.trim())).toEqual(['• d0', '◦ d1', '▪ d2', '▪ d5'])
})

test('a tab in a code line draws as four spaces and counts rows that way', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'G2', kind: 'read', body: '```\na\tb\n```' })], 'G2', 80, 40)
  expect(textOf(await ui.drawn())).toContain('  │ a    b')
  const wide = `\`\`\`\n${'\t'.repeat(10)}x\n\`\`\``
  const w = await open($, on, [item({ id: 'G2', kind: 'read', body: wide })], 'G2', 30, 40)
  expect(textOf(await w.ui.drawn())).not.toContain('\t')
})

test('blank runs in a body draw one blank row, none at either end', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'G3', kind: 'read', title: 'T3', body: '\n\nA\n\n\n\nB\n\n' })], 'G3', 80, 40)
  const r = rowsOf(await ui.drawn())
  expect(r.slice(r.indexOf('T3') + 1)).toEqual(['A', ' ', 'B', '[Mark read (m)]'])
})

const LONG_BODY = Array.from({ length: 10 }, (_, i) => `line ${i}`).join('\n\n')
test('FLOOR_ANSWER: an answer item keeps exactly 3 body rows at 6 rows, then the count of the lines left', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'G4', title: 't', blocks: 'x', body: LONG_BODY })], 'G4', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  const at = r.indexOf('t')
  expect(r.slice(at + 1, at + 5)).toEqual(['line 0', ' ', 'line 1', '… 16 more lines'])
})

test('"N more lines" counts a fence as lines + 2 and a table as rows + 2', async ($, on) => {
  const body = 'one\n\n```\nc1\nc2\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |'
  const { ui } = await open($, on, [item({ id: 'G5', title: 't', blocks: 'x', body })], 'G5', 80, ROWS_24)
  // left: blank 1 + fence (2 lines + 2) 4 + blank 1 + table (2 rows + 2) 4
  expect(textOf(await ui.drawn())).toContain('… 10 more lines')
})

test('a first block taller than the budget is clipped to at most budget (3) rows', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'G6', title: 't', blocks: 'x', body: 'word '.repeat(58) })], 'G6', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  const p = r.find((l) => l.startsWith('word ')) as string
  expect(p.endsWith('…')).toBe(true)
  expect(refRows(p, 80)).toBe(3)
  expect(r.join('\n')).toContain('… 1 more lines')
})

test('the PO answer keeps a blank line between paragraphs, and `**`, `#`, `|` literally', async ($, on) => {
  const typed = '**not bold**\n\n# not a heading\n| a | b |'
  const it = handled('answered-waiting', null, ANS({ text: typed, option: null }), { id: 'G7' })
  const { ui } = await open($, on, [it], 'G7', 80, 40)
  const tree = await ui.drawn()
  const r = rowsOf(tree)
  const at = r.indexOf('Your answer')
  expect(r.slice(at + 1, at + 5)).toEqual(['**not bold**', ' ', '# not a heading', '| a | b |'])
  expect(styleOf(tree, '**not bold**')).toEqual({})
})

test('the unsent note label is dim, the note is plain; a refused send keeps both', async ($, on) => {
  const q = item({ id: 'U1', options: E1_OPTS, recommendation: '(c) yes' })
  let w: any
  const cli = (argv: string[]) => {
    if (argv[0] !== 'answer') return undefined
    w.current = snap([item({ ...q, state: 'done', answer: ANS({ source: 'chat' }), done: { kind: 'answered', ts: '2026-10-16T12:00:00', reason: null } })])
    return { exitCode: 3, stdout: '', stderr: 'U1 was answered by chat\n' }
  }
  const o = await open($, on, [q], 'U1', 80, 40, cli)
  w = o.w
  await o.ui.select({ key: 'pick', value: 'a' })
  await o.ui.input({ key: 'note', text: 'my words', kind: 'change' })
  await o.ui.press({ key: 'send' })
  const tree = await o.ui.drawn()
  expect(styleOf(tree, 'Your unsent note (not sent):')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'my words')).toEqual({})
  expect(styleOf(tree, 'This item changed while you were reading it.')).toEqual({ color: 'warning' })
})

test('a notice is clipped to 2 rows and a refusal draws in the error tone (V-15)', async ($, on) => {
  const R4 = item({ id: 'R4', kind: 'read', title: 't', body: 'b' })
  const said = Array.from({ length: 60 }, (_, i) => `w${i}`).join(' ')
  const { ui } = await open($, on, [R4], 'R4', 30, ROWS_24, (argv) => (argv[0] === 'read' ? { exitCode: 2, stdout: '', stderr: `${said}\n` } : undefined))
  await ui.press({ key: 'mark-read' })
  const tree = await ui.drawn()
  const n = rowsOf(tree).find((l) => l.startsWith('⚠ ')) as string
  expect(n.endsWith('…')).toBe(true)
  expect(refRows(n, 30)).toBe(2)
  expect(styleOf(tree, '⚠ ')).toEqual({ color: 'error' })
})

test('Select labels are cut to cols - 18 cells (at least 8), ending in …', async ($, on) => {
  const opts = [{ key: 'a', text: 'x'.repeat(100) }, { key: 'b', text: 'y' }]
  for (const [cols, width] of [[30, 12], [40, 22], [80, 62]]) {
    const { ui } = await open($, on, [item({ id: 'S1', options: opts, recommendation: null })], 'S1', cols, 40)
    const labels = (await ui.find({ key: 'pick' }))?.props?.options.map((o: any) => o.label)
    expect(cellWidth(labels[0]), `${cols}`).toBe(width)
    expect(labels[0].endsWith('…')).toBe(true)
    expect(labels[1]).toBe('(b) y')
    await ui.unmount()
  }
})

// --- 7, 3.6, 3.9: colour, truncation, colourless ----------------------------------------------

const STRUCT = '# Head\n## Two\n### Three\nplain **bold** and `code`\n- bullet\n```ts\nconst a = 1\n```\n| A | B |\n|---|---|\n| 1 | 2 |\n[rec] pick this'
test('V-18: no meaning colour on structure (heading, code, bold, table, bullet); only the [rec] tag is green', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'E3', body: STRUCT, title: 'S' })], 'E3', 80, 40)
  const tree = await ui.drawn()
  for (const t of ['Head', 'Two', 'Three', 'bold', ' code ', 'const a = 1', 'bullet', 'A  B', '1  2']) {
    const s = styleOf(tree, t)
    expect(s, t).not.toBeNull()
    expect(s?.color, t).toBeUndefined()
  }
  expect(styleOf(tree, 'Three')).toEqual({ bold: true, italic: true })
  expect(styleOf(tree, 'Two')).toEqual({ bold: true })
  expect(styleOf(tree, 'ts')).toEqual({ italic: true })
  expect(styleOf(tree, '✓ recommended')).toEqual({ color: 'success', bold: true })
  expect(textOf(tree)).toContain('✓ recommended pick this')
  const colours = new Set<string>()
  walk(tree, (n) => {
    for (const k of ['color', 'backgroundColor', 'borderColor']) if (n.props?.[k] !== undefined) colours.add(String(n.props[k]))
  })
  for (const c of colours) expect(['success', 'error', 'warning']).toContain(c)
})

test('3.6: no Text that draws body, code, table, option or recommendation text truncates', async ($, on) => {
  for (const it of [E1, E2, R1, WAITING, item({ id: 'E3', body: STRUCT, options: E1_OPTS, recommendation: 'x'.repeat(200) })]) {
    for (const [cols, rows] of [[80, ROWS_24], [40, ROWS_24], [30, 40]]) {
      const { ui } = await open($, on, [it], it.id, cols, rows)
      await showAll(ui)
      walk(await ui.drawn(), (n) => {
        if (n.type === 'Text') expect(String(n.props?.wrap ?? ''), flat(n)).not.toMatch(/truncate/)
      })
      await ui.unmount()
    }
  }
})

test('3.9 colourless: blocked vs not, recommended, waiting vs delivered, error vs ok keep their words and glyphs', async ($, on) => {
  const text = async (it: any) => textOf(colourless(await (await open($, on, [it], it.id, 80, 40)).ui.drawn()))
  expect(await text(E1)).toContain('blocks spawning the pod')
  expect(await text(E2)).toContain('blocks nothing')
  expect(await text(E1)).toContain('✓ recommended: (c)')
  expect(await text(E1)).toContain('✓ recommends (c)')
  expect(await text(E2)).toContain('Manager recommends:')
  expect(await text(WAITING)).toContain('waiting for the Manager')
  expect(await text(DELIVERED)).toContain('delivered 2026-10-16 12:02')
  expect(await text(WAITING)).not.toContain('delivered')
  const { ui } = await open($, on, [E1], 'E1', 80, 40)
  await ui.press({ key: 'send' })
  expect(textOf(colourless(await ui.drawn()))).toMatch(/⚠ /)
})

// --- 11, 3.8: keys ----------------------------------------------------------------------------

test('V-30: the item screen key map is today\'s (hotkeys, keys, no two Buttons share a hotkey)', async ($, on) => {
  const keys = async (it: any) => {
    const { ui } = await open($, on, [it], it.id, 80, 40)
    const out: Record<string, unknown> = {}
    walk(await ui.drawn(), (n) => {
      if (['Button', 'Select', 'Input'].includes(n.type) && n.props?.key) out[`${n.type}:${n.props.key}`] = n.props.hotkey ?? null
    })
    const hot = Object.values(out).filter((h) => h !== null)
    expect(new Set(hot).size).toBe(hot.length)
    return out
  }
  expect(await keys(E1)).toEqual({ 'Button:back': null, 'Select:pick': null, 'Input:note': null, 'Button:send': null })
  expect(await keys(E2)).toEqual({ 'Button:back': null, 'Button:show-all': null, 'Input:reply': null, 'Button:send': null })
  expect(await keys(R1)).toEqual({ 'Button:back': 'b', 'Button:mark-read': 'm' })
  expect(await keys(WAITING)).toEqual({ 'Button:back': 'b' })
  expect(await keys(item({ id: 'E3', body: VISUAL.forty }))).toEqual({ 'Button:back': null, 'Button:show-all': null, 'Input:reply': null, 'Button:send': null })
})

// V-26: the literals below were recorded from the base d5593f4 (before this ticket) and from this branch: same argv, same stdin.
test('V-26: pick + note and a free reply reach the CLI with the same argv and stdin as before', async ($, on) => {
  const opts = [{ key: 'a', text: 'one' }, { key: 'b', text: 'two' }, { key: 'c', text: 'Both: (a) and (b)' }]
  const ok = (argv: string[]) => (argv[0] === 'answer' ? { exitCode: 0, stdout: '', stderr: '' } : undefined)
  const items = [item({ id: 'E1', options: opts, recommendation: '(c) yes' }), item({ id: 'E2' })]
  const { ui, w } = await open($, on, items, 'E1', 80, 40, ok)
  await ui.select({ key: 'pick', value: 'c' })
  await ui.input({ key: 'note', text: 'a "q" $HOME `x` \\n é 日本\nline2', kind: 'change' })
  await ui.press({ key: 'send' })
  const sent = () => w.runs.filter((r: any) => r.argv[1] === 'answer').map((r: any) => [r.argv.slice(1), r.stdin])
  expect(sent()).toEqual([[['answer', 'E1', '--option', 'c', '--source', 'pane'], 'a "q" $HOME `x` \\n é 日本\nline2']])
  const second = await open($, on, items, 'E2', 80, 40, ok)
  await second.ui.input({ key: 'reply', text: '  free reply: --option z; rm -rf /  ', kind: 'change' })
  await second.ui.press({ key: 'send' })
  expect(sent()[1]).toEqual([['answer', 'E2', '--source', 'pane'], '  free reply: --option z; rm -rf /  '])
  expect(sent()).toHaveLength(2)
})

// V-26, the rest of 3.3: markup characters, blank runs and a trailing newline are sent byte for byte (actions.ts is
// unchanged since d5593f4, which sent `typed` as is), and the recommended and another pick make the same call shape.
test('V-26: `**`, `#`, `|`, two blank lines and a trailing newline reach stdin byte for byte; any pick has the same shape', async ($, on) => {
  const opts = [{ key: 'a', text: 'one' }, { key: 'b', text: 'two' }, { key: 'c', text: 'three' }]
  const ok = (argv: string[]) => (argv[0] === 'answer' ? { exitCode: 0, stdout: '', stderr: '' } : undefined)
  const items = [item({ id: 'E1', options: opts, recommendation: '(c) yes' }), item({ id: 'E2', options: opts, recommendation: '(c) yes' }), item({ id: 'E3' })]
  const note = '**bold** # head | a | b |\n\n\nlast line\n'
  const first = await open($, on, items, 'E1', 80, 40, ok)
  const w = first.w
  await first.ui.select({ key: 'pick', value: 'c' }) // the recommended option
  await first.ui.input({ key: 'note', text: note, kind: 'change' })
  await first.ui.press({ key: 'send' })
  const second = await open($, on, items, 'E2', 80, 40, ok)
  await second.ui.select({ key: 'pick', value: 'a' }) // not the recommended one
  await second.ui.input({ key: 'note', text: note, kind: 'change' })
  await second.ui.press({ key: 'send' })
  const third = await open($, on, items, 'E3', 80, 40, ok)
  await third.ui.input({ key: 'reply', text: note, kind: 'change' })
  await third.ui.press({ key: 'send' })
  const sent = w.runs.filter((r: any) => r.argv[1] === 'answer').map((r: any) => [r.argv.slice(1), r.stdin])
  expect(sent).toEqual([
    [['answer', 'E1', '--option', 'c', '--source', 'pane'], '**bold** # head | a | b |\n\n\nlast line\n'],
    [['answer', 'E2', '--option', 'a', '--source', 'pane'], '**bold** # head | a | b |\n\n\nlast line\n'],
    [['answer', 'E3', '--source', 'pane'], '**bold** # head | a | b |\n\n\nlast line\n'],
  ])
})

test('Send is a plain Button: no variant', async ($, on) => {
  for (const it of [E1, E2]) {
    const { ui } = await open($, on, [it], it.id, 80, 40)
    expect((await ui.find({ key: 'send' }))?.props?.variant).toBeUndefined()
    await ui.unmount()
  }
})
