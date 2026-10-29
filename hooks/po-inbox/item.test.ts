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
  if (await ui.find({ key: 'details' })) await ui.press({ key: 'details' })
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



// --- design states: text, order, tokens -------------------------------------------------------





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


test('handled: the kept line and the unconfirmed delivery keep today\'s words and tones', async ($, on) => {
  const kept = handled('answered-waiting', null, ANS(), { flags: ['cell-not-written'], id: 'K1' })
  const { ui } = await open($, on, [kept], 'K1', 80, ROWS_24)
  const t = await ui.drawn()
  expect(textOf(t)).toContain('Answer kept. escalations.md was not updated.')
  expect(styleOf(t, 'Answer kept.')).toEqual({ dimColor: true })
})

// --- header and title rules -------------------------------------------------------------------





test('QAB F2: a `[rec]` line keeps its leading spaces', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'F2', body: 'intro\n   [rec] take (a)' })], 'F2', 80, ROWS_40)
  expect(rowsOf(await ui.drawn())).toContain('   ✓ recommended take (a)')
  await ui.unmount()
})






// --- notice rows ------------------------------------------------------------------------------



// --- V-11 through the real screen ---------------------------------------------------------------

const V11: [string, string | null][] = [
  [E1_REC, 'c'], ['(c) yes', 'c'], ['  (c) yes', 'c'], ['(a) no, (b) is worse', 'a'],
  ['(C) yes', null], ['c) yes', null], ['Option c', null], ['c. yes', null],
  ['(a)+(b)', null], ['(a)/(b)', null], ['(a), (b)', null], ['(a) and (b)', null],
  ['(z) yes', null], ["Reply 'all recs' to take them", null], ['b: less rework', null],
]



// --- 4: the body cut by rows ------------------------------------------------------------------




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
      expect(textOf(await other.ui.drawn())).toContain('○ (c) Both')
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
  expect(r.slice(r.indexOf('T3') + 1)).toEqual(['A', ' ', 'B', '[Mark read]'])
})

const LONG_BODY = Array.from({ length: 10 }, (_, i) => `line ${i}`).join('\n\n')



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
  await o.ui.press({ key: 'opt-a' })
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


// --- 7, 3.6, 3.9: colour, truncation, colourless ----------------------------------------------

const STRUCT = '# Head\n## Two\n### Three\nplain **bold** and `code`\n- bullet\n```ts\nconst a = 1\n```\n| A | B |\n|---|---|\n| 1 | 2 |\n[rec] pick this'
test('V-18: no meaning colour on structure (heading, code, bold, table, bullet); only the [rec] tag is green', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'E3', body: STRUCT, title: 'S' })], 'E3', 80, 40)
  const tree = await ui.drawn()
  for (const t of ['Head', 'Two', 'Three', 'bold', 'code', 'const a = 1', 'bullet', 'A  B', '1  2']) {
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
  // body-styles.md 9.5 rule 5: `permission` (diagram connectors, [decision] chip) and `inactive` ([info], [skip] chips) carry no good/bad meaning
  for (const c of colours) expect(['success', 'error', 'warning', 'permission', 'inactive']).toContain(c)
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
  expect(await text(E2)).toContain('✓ Manager recommends:')
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
  const picks = { 'Button:opt-a': null, 'Button:opt-b': null, 'Button:opt-c': null }
  expect(await keys(E1)).toEqual({ 'Button:back': null, ...picks, 'Input:note': null, 'Button:send': null })
  expect(await keys(E2)).toEqual({ 'Button:back': null, 'Input:reply': null, 'Button:send': null, 'Button:details': null })
  expect(await keys(R1)).toEqual({ 'Button:back': 'b', 'Button:mark-read': 'm', 'Button:mark-read-end': null })
  expect(await keys(WAITING)).toEqual({ 'Button:back': 'b' })
  expect(await keys(item({ id: 'E3', body: VISUAL.forty }))).toEqual({ 'Button:back': null, 'Input:reply': null, 'Button:send': null, 'Button:details': null })
})

// V-26: the literals below were recorded from the base d5593f4 (before this ticket) and from this branch: same argv, same stdin.
test('V-26: pick + note and a free reply reach the CLI with the same argv and stdin as before', async ($, on) => {
  const opts = [{ key: 'a', text: 'one' }, { key: 'b', text: 'two' }, { key: 'c', text: 'Both: (a) and (b)' }]
  const ok = (argv: string[]) => (argv[0] === 'answer' ? { exitCode: 0, stdout: '', stderr: '' } : undefined)
  const items = [item({ id: 'E1', options: opts, recommendation: '(c) yes' }), item({ id: 'E2' })]
  const { ui, w } = await open($, on, items, 'E1', 80, 40, ok)
  await ui.press({ key: 'opt-c' })
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
  await first.ui.press({ key: 'opt-c' }) // the recommended option
  await first.ui.input({ key: 'note', text: note, kind: 'change' })
  await first.ui.press({ key: 'send' })
  const second = await open($, on, items, 'E2', 80, 40, ok)
  await second.ui.press({ key: 'opt-a' }) // not the recommended one
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


// --- ticket 01: the redesigned item (item.md): decision first, Details page ---------------------

// The top Box (Back, Mark read, header, hint) is one drawn row: join its leaves into one string.
function screenRows(tree: any): string[] {
  const r = rowsOf(tree)
  let n = 0
  while (n < r.length && (/^\[(← |Mark read)/.test(r[n]) || r[n].trim() === '' || r[n].startsWith('  '))) n++
  return [r.slice(0, n).join(' '), ...r.slice(n)]
}
// Rows (reference wrap) from the top through the first row that starts with `marker`.
function rowsThrough(tree: any, marker: string, cols: number): number {
  let n = 0
  for (const l of screenRows(tree)) {
    n += refRows(l, cols + 2)
    if (l.startsWith(marker)) return n
  }
  return Infinity
}
const hasBlock = (tree: any, text: string) => textOf(tree).includes(text)

test('T2: first viewport at bodyRows 6: Back+header, title, three options, Note; at 11 Send too', async ($, on) => {
  for (const cols of [80, 60, 47]) {
    const { ui } = await open($, on, [E1], 'E1', cols, ROWS_24)
    const r = screenRows(await ui.drawn())
    expect(r[0].startsWith('[← Back]'), r[0]).toBe(true)
    expect(r[0]).toContain('E1 · blocks')
    expect(r[1].startsWith(E1_TITLE.slice(0, 20))).toBe(true)
    expect(r.slice(2, 5).map((l) => l.slice(0, 5))).toEqual(['[○ (a', '[○ (b', '[○ (c'])
    expect(r[5]).toBe('<Note (optional)>')
    // a 61-character title takes 2 rows below 61 columns (item.md section 3: title up to 2 rows)
    expect(r.slice(0, 6).reduce((n, l) => n + refRows(l, cols + 2), 0), `${cols}`).toBeLessThanOrEqual(cols >= 80 ? ROWS_24 : ROWS_24 + 1)
    await ui.unmount()
  }
  for (const [cols, rows] of [[80, ROWS_40], [80, 33]]) {
    const { ui } = await open($, on, [E1], 'E1', cols, rows)
    expect(rowsThrough(await ui.drawn(), '[Send answer]', cols), `${cols}x${rows}`).toBeLessThanOrEqual(rows)
    await ui.unmount()
  }
})

test('T3: the hint at scroll 0 names what lies outside the first viewport', async ($, on) => {
  const free = item({ id: 'H1', title: 't', body: VISUAL.forty })
  const cases: [string, any, number, string | null][] = [
    ['note and send below', E1, 5, '↓ note, send'],
    ['send below', E1, ROWS_24, '↓ send'],
    ['context below', item({ id: 'H4', title: 't', body: 'x\n\ny', options: H_OPTS }), 7, '↓ context'],
    ['more below (read item)', R1, ROWS_24, '↓ more below'],
    ['nothing below', item({ id: 'H2', title: 't', body: 'x', options: H_OPTS }), 40, null],
    ['free text, context below', free, 4, '↓ context'],
  ]
  for (const [name, it, rows, want] of cases) {
    const { ui } = await open($, on, [it], it.id, 80, rows)
    const text = textOf(await ui.drawn())
    for (const h of ['↓ note, send', '↓ send', '↓ context', '↓ more below']) expect(text.includes(h), `${name}: ${h}`).toBe(h === want)
    await ui.unmount()
  }
})

test('M1: E1 at 80 columns, 6 rows: header, options with one `✓ rec`, nothing picked, folded Context', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  const tree = await ui.drawn()
  const text = textOf(tree)
  expect(text).toContain('E1 · blocks spawning the pod (BA, Tech Lead) · 5h')
  expect(text).toContain('↓ send')
  expect(text).toContain('[○ (a) Attached page')
  expect(text.split('✓ rec').length - 1).toBe(1)
  expect(rowsOf(tree).find((l) => l.includes('✓ rec'))).toContain('(c) Both')
  for (const gone of ['●', 'Options', 'recommends', 'recommended:', 'Your answer', '<br>']) expect(text, gone).not.toContain(gone)
  expect(text).toMatch(/Context\n.*\n… \d+ more rows?\n\[Details\]/)
  expect(styleOf(tree, '↓ send')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'E1')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'blocks spawning the pod (BA, Tech Lead)')).toEqual({ color: 'error' })
  expect(styleOf(tree, E1_TITLE)).toEqual({ bold: true })
  expect(styleOf(tree, '✓ rec')).toEqual({ color: 'success' })
  expect(styleOf(tree, 'Context')).toEqual({ bold: true })
  expect(await ui.find({ key: 'details' })).toBeDefined()
  expect(await ui.find({ key: 'show-all' })).toBeUndefined()
  expect(await ui.find({ key: 'pick' })).toBeUndefined()
  await ui.unmount()
})

test('M2: tall tier: no tag, the reason row under the recommended option only; options up to 2 rows', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_40)
  const tree = await ui.drawn()
  const text = textOf(tree)
  expect(text).not.toContain('✓ rec\n')
  expect(text.split('✓ recommended: ').length - 1).toBe(1)
  expect(text.split(E1_REC).length - 1).toBe(1)
  expect(text.indexOf('(c) Both')).toBeLessThan(text.indexOf('✓ recommended: '))
  expect(text.indexOf('✓ recommended: ')).toBeLessThan(text.indexOf('<Note'))
  expect(styleOf(tree, '✓ recommended: ')).toEqual({ color: 'success', bold: true })
  await ui.unmount()
})

test('M3: picking marks `●` and moves with the next pick; Details keeps the pick and the note (AC3, AC4)', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  expect(textOf(await ui.drawn())).not.toContain('●')
  await ui.press({ key: 'opt-c' })
  let text = textOf(await ui.drawn())
  expect(text).toContain('[● (c) Both')
  expect(text).not.toMatch(/warn|differs|instead|not the recommended/i)
  await ui.press({ key: 'opt-a' })
  text = textOf(await ui.drawn())
  expect(text).toContain('[● (a) Attached')
  expect(text).toContain('[○ (c) Both')
  await ui.input({ key: 'note', text: 'my note', kind: 'change' })
  await ui.press({ key: 'details' })
  const d = textOf(await ui.drawn())
  expect(d).toContain('[← Decide (b)]')
  expect(d).toContain('Context')
  expect(d).not.toContain('more rows')
  expect((await ui.find({ key: 'back' }))?.props?.hotkey).toBe('b')
  await ui.press({ key: 'back' })
  text = textOf(await ui.drawn())
  expect(text).toContain('[● (a) Attached')
  expect(text).toContain('<Note (optional)my note>')
  await ui.unmount()
})

test('T5: typing b, m and digits in Note does nothing else; b leaves Details only', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  await ui.input({ key: 'note', text: 'bm123', kind: 'change' })
  const text = textOf(await ui.drawn())
  expect(text).toContain('<Note (optional)bm123>')
  expect(text).toContain('[Send answer]')
  for (const key of ['back', 'opt-a', 'send']) expect((await ui.find({ key }))?.props?.hotkey).toBeUndefined()
  expect(await ui.find({ key: 'mark-read' })).toBeUndefined()
  await ui.unmount()
})

test('AC3: a note with no pick is sent as a free reply; nothing at all shows the notice and runs nothing', async ($, on) => {
  const ok = (argv: string[]) => (argv[0] === 'answer' ? { exitCode: 0, stdout: '', stderr: '' } : undefined)
  const { ui, w } = await open($, on, [E1], 'E1', 80, ROWS_24, ok)
  await ui.press({ key: 'send' })
  expect(textOf(await ui.drawn())).toContain('⚠ Nothing to send: pick an option or type a reply.')
  expect(w.runs.filter((r: any) => r.argv[1] === 'answer')).toHaveLength(0)
  await ui.input({ key: 'note', text: 'just words', kind: 'change' })
  await ui.press({ key: 'send' })
  expect(w.runs.filter((r: any) => r.argv[1] === 'answer').map((r: any) => [r.argv.slice(1), r.stdin])).toEqual([[['answer', 'E1', '--source', 'pane'], 'just words']])
  await ui.unmount()
})

test('M4: E2 (rec without a key): one `✓ Manager recommends` row clipped to 1 row, Your reply; Details shows the pointer', async ($, on) => {
  const { ui } = await open($, on, [E2], 'E2', 40, ROWS_24)
  const tree = await ui.drawn()
  const r = screenRows(tree)
  expect(r[0]).toContain('E2 · blocks nothing')
  const rec = r.find((l) => l.startsWith('✓ Manager recommends: ')) as string
  expect(cellWidth(rec)).toBeLessThanOrEqual(40)
  expect(rec.endsWith('…')).toBe(true)
  expect(styleOf(tree, '✓ Manager recommends: ')).toEqual({ color: 'success', bold: true })
  expect(r.indexOf('<Your reply>')).toBe(r.indexOf(rec) + 1)
  expect(textOf(tree)).not.toContain('{Your answer')
  await ui.press({ key: 'details' })
  const full = textOf(await ui.drawn())
  expect(full).toContain('✓ recommends: ')
  expect(full).toContain('✓ recommended the item screen')
  expect(inOrder(full, VISUAL.e2.replace(/<br>\s+\[rec\]/g, '<br>recommended').split('<br>').slice(1).join(' '))).toBe(true)
  await ui.unmount()
})

test('M5: read item: Mark read on row 1, chips without padding, headings, second Mark read at the end', async ($, on) => {
  const { ui } = await open($, on, [R1], 'R1', 80, ROWS_24)
  let tree = await ui.drawn()
  let text = textOf(tree)
  expect(screenRows(tree)[0]).toMatch(/\[← Back \(b\)\]\s+\[Mark read \(m\)\]/)
  expect(screenRows(tree)[0]).toContain('R1 · read · blocks IV-06 · 37m')
  expect((await ui.find({ key: 'mark-read' }))?.props?.hotkey).toBe('m')
  expect((await ui.find({ key: 'mark-read-end' }))?.props?.hotkey).toBeUndefined()
  expect(styleOf(tree, 'Check-in summary')).toEqual({ bold: true, underline: true })
  expect(styleOf(tree, 'qa-w')).toEqual({ inverse: true })
  expect(text).toContain('Branch squad/x passed qa-w.')
  expect(text).toContain('Task   State')
  expect(text).toMatch(/… \d+ more rows\n\[Details\]\n\[Mark read\]$/)
  expect(rowsOf(tree).at(-1)).toBe('[Mark read]')
  await ui.unmount()
  const tall = await open($, on, [R1], 'R1', 80, ROWS_40)
  text = textOf(await tall.ui.drawn())
  // bodyRows 11 is the tall tier: no fold; the page is longer than the viewport, so the hint stays
  expect(text).not.toContain('more rows')
  expect(text).toContain('↓ more below')
  expect(text).toContain('line e\n[Mark read]')
  const narrow = await open($, on, [R1], 'R1', 39, 40)
  tree = await narrow.ui.drawn()
  expect(textOf(tree)).toContain('Task: IV-01')
  expect(styleOf(tree, 'Task')).toEqual({ bold: true })
  // from 40 columns a table keeps its columns (a docked pane is about 47)
  const docked = await open($, on, [R1], 'R1', 40, 40)
  expect(textOf(await docked.ui.drawn())).toContain('Task   State')
})

test('handled with options: the pick is `●`, the recommended mark stays, the answer is plain (V-14a, V-26)', async ($, on) => {
  const all = [WAITING, DELIVERED, READ]
  const short = await open($, on, all, WAITING.id, 80, ROWS_24)
  let text = textOf(await short.ui.drawn())
  expect(text).toContain('● (b) Tab only')
  expect(text).toContain('○ (a) hotkey m')
  expect(text).toContain('✓ rec')
  expect(text.indexOf('Your answer')).toBeLessThan(text.indexOf('● (b)'))
  expect(await short.ui.find({ key: 'opt-a' })).toBeUndefined()
  const tall = await open($, on, all, WAITING.id, 80, ROWS_40)
  const tree = await tall.ui.drawn()
  text = textOf(tree)
  expect(text).toContain('✓ recommended: (b), fewer keys')
  expect(text).toContain('(b) use **Tab**, no hotkey')
  expect(text).not.toContain('Options')
  expect(styleOf(tree, 'blocks IV-04')).toEqual({ color: 'error' })
  expect(styleOf(tree, 'Your answer')).toEqual({ bold: true })
  expect(await tall.ui.find({ key: 'mark-read' })).toBeUndefined()
  expect(styleOf(await (await open($, on, all, DELIVERED.id, 80, ROWS_24)).ui.drawn(), 'blocks IV-04')).toEqual({ dimColor: true })
})

test('header: Decide shows the short age; Details shows `created …` (5h ago / date and age wide / age compact / now)', async ($, on) => {
  const old = item({ id: 'E5', created: '2026-10-12T09:00:00' })
  for (const [cols, want] of [[80, 'created 2026-10-12 (3d ago)'], [60, 'created 2026-10-12 (3d ago)'], [59, 'created 3d ago']] as const) {
    const { ui } = await open($, on, [old], 'E5', cols, ROWS_24)
    expect(textOf(await ui.drawn())).toContain('E5 · blocks PI-04 · 3d')
    await ui.unmount()
    void want
  }
  const withBody = item({ id: 'E5', created: '2026-10-12T09:00:00', body: 'l1\n\nl2\n\nl3\n\nl4\n\nl5\n\nl6' })
  for (const [cols, want] of [[80, 'created 2026-10-12 (3d ago)'], [60, 'created 2026-10-12 (3d ago)'], [59, 'created 3d ago']] as const) {
    const { ui } = await open($, on, [withBody], 'E5', cols, ROWS_24)
    await ui.press({ key: 'details' })
    expect(textOf(await ui.drawn())).toContain(want)
    await ui.unmount()
  }
  const fresh = item({ id: 'E6', created: '2026-10-15T12:00:00', body: 'l1\n\nl2\n\nl3\n\nl4\n\nl5\n\nl6' })
  const f = await open($, on, [fresh], 'E6', 80, ROWS_24)
  expect(textOf(await f.ui.drawn())).toContain('E6 · blocks PI-04 · now')
  await f.ui.press({ key: 'details' })
  expect(textOf(await f.ui.drawn())).toContain('created now')
})

test('title of 300 characters: 2 rows with an ellipsis, a Details row, Details draws it whole', async ($, on) => {
  const long = item({ id: 'E8', title: VISUAL.title300, body: 'tail' })
  for (const cols of [80, 40, 30]) {
    const { ui } = await open($, on, [long], 'E8', cols, ROWS_24)
    const r = rowsOf(await ui.drawn())
    const t = r.find((l) => l.startsWith('TTT')) as string
    expect(t.endsWith('…')).toBe(true)
    expect(refRows(t, cols)).toBeLessThanOrEqual(2)
    expect(r.join('\n')).toContain('… full title\n[Details]')
    await ui.press({ key: 'details' })
    expect(textOf(await ui.drawn())).toContain('T'.repeat(300))
    await ui.unmount()
  }
})

test('the hint counts the `… full title` row: a cut title, a body that fits, no room → `↓ more below`; room → none', async ($, on) => {
  const long = item({ id: 'E8', kind: 'read', title: VISUAL.title300, body: 'b' })
  const small = await open($, on, [long], 'E8', 80, 4)
  expect(textOf(await small.ui.drawn())).toContain('↓ more below')
  await small.ui.unmount()
  const fits = await open($, on, [long], 'E8', 80, 40)
  expect(textOf(await fits.ui.drawn())).not.toContain('↓')
  await fits.ui.unmount()
})

test('QAB F1: 80-char titles at 36 columns: title cut at 2 rows, the three options follow (one row more when the header drops to row 2)', async ($, on) => {
  const titles = ['inbox-visual: what should the visual mean in the terminal inbox for every kind of item', 'auth: do we accept the legacy tokens during the migration window for internal tools?']
  for (const [i, title] of titles.entries()) {
    const long = item({ id: `F1-${i}`, title, blocks: 'IV-02', created: '2026-10-16T09:00:00', body: VISUAL.e1, recommendation: E1_REC, options: E1_OPTS })
    const { ui } = await open($, on, [long], `F1-${i}`, 36, ROWS_24)
    const tree = await ui.drawn()
    const t = rowsOf(tree).find((l) => l.startsWith(title.slice(0, 5))) as string
    expect(refRows(t, 36)).toBeLessThanOrEqual(2)
    expect(rowsThrough(tree, '[○ (c)', 36), screenRows(tree).join('\n')).toBeLessThanOrEqual(ROWS_24 + 1)
    await ui.unmount()
  }
})

test('QAB F4: the fold label keeps a one-cell gap to Details (also when the row wraps at 30 columns)', async ($, on) => {
  const gaps = (n: any): number => (n && typeof n === 'object' ? (n.type === 'Box' && n.props?.marginRight === 1 ? 1 : 0) + (n.children ?? []).reduce((a: number, c: any) => a + gaps(c), 0) : 0)
  const { ui } = await open($, on, [R1], 'R1', 30, ROWS_24)
  const tree = await ui.drawn()
  expect(textOf(tree)).toContain('more rows')
  expect(gaps(tree)).toBe(1)
  await ui.unmount()
})

test('long blocks: Decide clips the header with `…`, Details draws it whole on its own row (item.md 13)', async ($, on) => {
  const blocks = `${'work item '.repeat(12)}end`
  const it = item({ id: 'E9', blocks, body: 'l1\n\nl2\n\nl3\n\nl4\n\nl5\n\nl6' })
  for (const cols of [80, 40]) {
    const { ui } = await open($, on, [it], 'E9', cols, ROWS_24)
    const head = screenRows(await ui.drawn())[0]
    expect(head).toContain('E9 · blocks')
    expect(head).toContain('…')
    expect(refRows(head, cols)).toBe(1)
    await ui.press({ key: 'details' })
    expect(textOf(await ui.drawn())).toContain(blocks)
    await ui.unmount()
  }
})

test('3.1e: 300-char title, long blocks, 40 columns, 6 rows: Back row, a 2-row title, the options follow', async ($, on) => {
  const blocks = `${'work item '.repeat(12)}end`
  const long = item({ id: 'E8', title: VISUAL.title300, blocks, body: VISUAL.e1, recommendation: E1_REC, options: E1_OPTS })
  const { ui } = await open($, on, [long], 'E8', 40, ROWS_24)
  const tree = await ui.drawn()
  const r = rowsOf(tree)
  const t = r.find((l) => l.startsWith('TTT')) as string
  expect(t.endsWith('…')).toBe(true)
  expect(refRows(t, 40)).toBe(2)
  expect(rowsThrough(tree, '[○ (a)', 40)).toBeLessThanOrEqual(ROWS_24)
  await ui.unmount()
})

test('T10: row 1 drops, in order: the hint, the `blocks` text, the age, then the header moves to row 2; the buttons stay', async ($, on) => {
  const blocks = 'alpha beta gamma delta epsilon zeta'
  const it = item({ id: 'N1', kind: 'read', blocks, body: 'l1\n\nl2\n\nl3\n\nl4\n\nl5\n\nl6', created: '2026-10-15T09:00:00' })
  const head = async (cols: number) => {
    const { ui } = await open($, on, [it], 'N1', cols, ROWS_24)
    const r = rowsOf(await ui.drawn())
    await ui.unmount()
    return r.slice(0, r.findIndex((l) => l === 'Markdown body sample' || l === it.title)).join(' | ')
  }
  const wide = await head(110)
  expect(wide).toContain(`N1 · read · blocks ${blocks} · 3h`)
  expect(wide).toContain('↓ more below')
  const noHint = await head(95)
  expect(noHint).toContain(`blocks ${blocks} · 3h`)
  expect(noHint).not.toContain('↓')
  const clipped = await head(80)
  expect(clipped).toMatch(/blocks alpha beta[^|]*… · 3h/)
  expect(clipped).not.toContain('↓')
  const noAge = await head(63)
  expect(noAge).toMatch(/blocks [^|]*…/)
  expect(noAge).not.toContain('· 3h')
  const row2 = await head(50)
  expect(row2).toContain(`blocks ${blocks}`)
  for (const h of [wide, noHint, clipped, noAge, row2]) {
    expect(h).toContain('[← Back (b)]')
    expect(h).toContain('[Mark read (m)]')
  }
})

test('notice: an error row sits directly under Back+header, above the title; the form keeps the pick and note', async ($, on) => {
  for (const cols of [80, 40]) {
    const { ui } = await open($, on, [E1], 'E1', cols, ROWS_24)
    await ui.press({ key: 'send' })
    const r = screenRows(await ui.drawn())
    expect(r[1].startsWith('⚠ ')).toBe(true)
    expect(r[2].startsWith(E1_TITLE.slice(0, 15))).toBe(true)
    expect(r.some((l) => l.startsWith('[○ (a)'))).toBe(true)
    await ui.unmount()
  }
})

test('notice on a read item sits under the Back row, above the title', async ($, on) => {
  const R3 = item({ id: 'R3', kind: 'read', title: VISUAL.title300, body: 'b' })
  const { ui } = await open($, on, [R3], 'R3', 40, ROWS_24, (argv) => (argv[0] === 'read' ? { exitCode: 2, stdout: '', stderr: 'R3 is locked\n' } : undefined))
  await ui.press({ key: 'mark-read' })
  const r = screenRows(await ui.drawn())
  const n = r.indexOf('⚠ R3 is locked')
  expect(r[0]).toContain('[← Back (b)]')
  expect(n).toBeGreaterThan(0)
  expect(r[n + 1].startsWith('TTT')).toBe(true)
  expect(refRows(r[n + 1], 40)).toBeLessThanOrEqual(2)
})

test('V-11: each rec through the screen: the reason under the marked option (tall) or the tag (short); a keyless rec is one row', async ($, on) => {
  for (const [rec, key] of V11) {
    const it = item({ id: 'E3', options: E1_OPTS, recommendation: rec })
    const trimmed = rec.trim()
    const tall = await open($, on, [it], 'E3', 80, 40)
    const tree = await tall.ui.drawn()
    const r = rowsOf(tree)
    expect(textOf(tree).split(trimmed).length - 1, rec).toBe(1)
    if (key) {
      const at = r.findIndex((l) => l.endsWith(`✓ recommended: ${trimmed}`))
      expect(at, rec).toBeGreaterThan(0)
      expect(r.slice(0, at).reverse().find((l) => /^\[[○●] \([a-z]\)/.test(l))?.[4]).toBe(key)
      expect(textOf(tree)).not.toContain('Manager recommends')
    } else {
      expect(textOf(tree)).not.toContain('✓ recommended: ')
      expect(r.filter((l) => l === `✓ Manager recommends: ${trimmed}`)).toHaveLength(1)
    }
    await tall.ui.unmount()
    const short = await open($, on, [it], 'E3', 80, ROWS_24)
    const rs = rowsOf(await short.ui.drawn())
    const tagged = rs.filter((l) => l.includes('✓ rec'))
    expect(tagged.length, rec).toBe(key ? 1 : 0)
    if (key) expect(tagged[0]).toContain(`(${key})`)
    await short.ui.unmount()
  }
})

test('V-11: no rec at all: no tag, no reason row; options still drawn', async ($, on) => {
  for (const rows of [ROWS_24, 40]) {
    const { ui } = await open($, on, [item({ id: 'E3', options: H_OPTS })], 'E3', 80, rows)
    const text = textOf(await ui.drawn())
    expect(text).not.toContain('recommend')
    expect(text).not.toContain('✓')
    expect(text).toContain('(c) both')
    await ui.unmount()
  }
})

test('V-14: options not parsed: the raw text (3 rows in the short tier), the rec row, then Your reply; no option rows', async ($, on) => {
  const raw = Array.from({ length: 8 }, (_, i) => `(${i}) choice number ${i}`).join(' ').repeat(2)
  const it = item({ id: 'E3', options_raw: raw, recommendation: 'go with one' })
  const short = await open($, on, [it], 'E3', 40, ROWS_24)
  const r = rowsOf(await short.ui.drawn())
  const at = (s: string) => r.findIndex((l) => l.includes(s))
  expect(at('Options, as the Manager wrote them')).toBeLessThan(at('(0) choice'))
  const rawRow = r.find((l) => l.startsWith('(0) choice')) as string
  expect(refRows(rawRow, 40)).toBeLessThanOrEqual(3)
  expect(rawRow.endsWith('…')).toBe(true)
  expect(at('✓ Manager recommends: go with one')).toBeLessThan(at('<Your reply'))
  expect(r.some((l) => /^\[[○●]/.test(l))).toBe(false)
  const tall = await open($, on, [it], 'E3', 40, 40)
  expect(textOf(await tall.ui.drawn())).toContain(raw)
})

test('body fold: E1 at 6 rows: Context, the floor of body, `… N more rows`, Details; Details draws every word in order', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  const ctx = r.indexOf('Context')
  expect(ctx).toBeGreaterThan(r.findIndex((l) => l === '[Send answer]'))
  expect(r[ctx + 2]).toMatch(/^… \d+ more rows$/)
  expect(r[ctx + 3]).toBe('[Details]')
  await ui.press({ key: 'details' })
  const full = textOf(await ui.drawn())
  expect(inOrder(full, VISUAL.e1.split('<br>').slice(1).join('\n'))).toBe(true)
  expect(full).not.toContain('more rows')
  await ui.unmount()
})

test('body fold: a pane tall enough shows the whole body, no Details, no hint', async ($, on) => {
  const tall = await open($, on, [E1], 'E1', 80, 60)
  const text = textOf(await tall.ui.drawn())
  expect(text).not.toContain('more rows')
  expect(text).not.toContain('↓')
  expect(await tall.ui.find({ key: 'details' })).toBeUndefined()
  expect(inOrder(text, VISUAL.e1.split('<br>').slice(1).join('\n'))).toBe(true)
})

// --- body styles (body-styles.md): the Manager's two example bodies, through the real pane -------------------------

const GUIDE_E1 = item({
  id: 'G1', title: 'Which branch merges first: BRD-01 for BRD-02..06?', body: VISUAL.guideE1,
  options: H_OPTS, recommendation: '(a), one merge unblocks 5 tickets', created: '2026-10-15T07:00:00',
})
const GUIDE_R1 = item({ id: 'G2', kind: 'read', title: 'Iteration 1 passed: all 3 tasks', body: VISUAL.guideR1, blocks: '', created: '2026-10-15T11:23:00' })

test('body styles: E1 and R1 on Details draw their forms, chips and all words, at every size', async ($, on) => {
  for (const it of [GUIDE_E1, GUIDE_R1]) {
    for (const [cols, rows] of [[80, ROWS_24], [80, ROWS_40], [60, ROWS_24], [47, ROWS_24], [47, ROWS_40], [40, ROWS_40]]) {
      const { ui } = await open($, on, [it], it.id, cols, rows)
      await showAll(ui)
      const tree = await ui.drawn()
      const text = textOf(tree)
      // the word `diagram` after the fence is the label that makes it a diagram: chrome, not drawn
      const src = VISUAL[it === GUIDE_E1 ? 'guideE1' : 'guideR1'].replace('```diagram', '```')
      // E1's options table is 59 cells wide: under 60 columns it stacks as `column: value` records, so only the order of the rest holds
      const seen = new Set(words(text))
      if (it === GUIDE_E1 && cols < 60) for (const w of words(src)) expect(seen.has(w), `${cols}: ${w}`).toBe(true)
      else expect(inOrder(text, src), `${it.id} ${cols}x${rows}`).toBe(true)
      expect(text).toContain(it === GUIDE_E1 ? '\u00a0◆\u00a0decision\u00a0' : '\u00a0›\u00a0info\u00a0')
      expect(styleOf(tree, it === GUIDE_E1 ? '◆' : '›')).toEqual(it === GUIDE_E1 ? { inverse: true, bold: true, color: 'permission' } : { inverse: true, bold: true, color: 'inactive' })
      expect(text).toContain('<https://github.com/acme/squad/pull/')
      expect(text).not.toContain('](')
      const colours = new Set<string>()
      walk(tree, (n) => {
        for (const k of ['color', 'backgroundColor', 'borderColor']) if (n.props?.[k] !== undefined) colours.add(`${k}:${n.props[k]}`)
      })
      for (const c of colours) expect(['color:success', 'color:error', 'color:warning', 'color:permission', 'color:inactive'], c).toContain(c)
      await ui.unmount()
    }
  }
})

test('body styles: a table keeps its columns and its chip colours in a docked pane (47 columns)', async ($, on) => {
  const { ui } = await open($, on, [GUIDE_R1], 'G2', 47, ROWS_40)
  await showAll(ui)
  const tree = await ui.drawn()
  const r = rowsOf(tree)
  // the chips are 6 and 8 cells wide, so the columns widen to hold them
  expect(r).toContain('Task              WB      BB')
  expect(r).toContain(`03 body styles    ${'\u00a0✓\u00a0ok\u00a0'}  ${'\u00a0⚠\u00a0warn\u00a0'}`)
  expect(styleOf(tree, '⚠')).toEqual({ inverse: true, bold: true, color: 'warning' })
  await ui.unmount()
})

test('body styles: a docked callout wraps to 2 rows; the reference wrap agrees with the count', async ($, on) => {
  const { ui } = await open($, on, [GUIDE_E1], 'G1', 47, ROWS_40)
  await showAll(ui)
  const row = rowsOf(await ui.drawn()).find((l) => l.includes('warning')) as string
  expect(row.startsWith('\u00a0⚠\u00a0warning\u00a0 Option (b)')).toBe(true)
  expect(refRows(row, 47)).toBe(2)
  await ui.unmount()
})

test('body of 40 lines: Note and Send come before Context; Details holds every line', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'E3', body: VISUAL.forty, options: H_OPTS })], 'E3', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  expect(r.findIndex((l) => l === '[Send answer]')).toBeLessThan(r.indexOf('Context'))
  expect(r.some((l) => /^… \d+ more rows$/.test(l))).toBe(true)
  await ui.press({ key: 'details' })
  const full = textOf(await ui.drawn())
  for (let i = 1; i <= 40; i++) expect(full).toContain(`line ${i} of a forty-line body`)
  await ui.unmount()
})

test('T7: the fold count is the rows left, blank heading rows included in the tall tier', async ($, on) => {
  const body = ['intro', '', '## One', 'a', '## Two', 'b', '## Three', 'c', '## Four', 'd', '## Five', 'e', '## Six', 'f'].join('\n')
  const tallItem = item({ id: 'H3', title: 't', options: H_OPTS, body })
  const wide = await open($, on, [tallItem], 'H3', 80, 11)
  const r = rowsOf(await wide.ui.drawn())
  const fold = r.find((l) => /^… \d+ more rows$/.test(l)) as string
  const shown = r.slice(r.indexOf('Context') + 1, r.indexOf(fold))
  await wide.ui.press({ key: 'details' })
  const all = rowsOf(await wide.ui.drawn())
  const bodyRows = all.slice(all.indexOf('Context') + 1, all.lastIndexOf('[← Decide (b)]'))
  expect(bodyRows.filter((l) => l === ' ').length).toBeGreaterThanOrEqual(6) // a blank row above each heading
  expect(Number(fold.match(/\d+/)![0])).toBe(bodyRows.length - shown.length)
  const short = await open($, on, [tallItem], 'H3', 80, ROWS_24)
  await short.ui.press({ key: 'details' })
  const sr = rowsOf(await short.ui.drawn())
  expect(sr.filter((l) => l === ' ').length).toBeLessThan(bodyRows.filter((l) => l === ' ').length) // none in the short tier
})

test('state rows: sending ignores presses; 1 option; 6+ options reach Note and Send; very long option is cut', async ($, on) => {
  const one = item({ id: 'S1', options: [{ key: 'a', text: 'only' }] })
  const o1 = await open($, on, [one], 'S1', 80, ROWS_24)
  expect(textOf(await o1.ui.drawn())).toContain('[○ (a) only]')
  const six = item({ id: 'S6', options: 'abcdefg'.split('').map((k) => ({ key: k, text: `choice ${k}` })), body: 'x' })
  const o6 = await open($, on, [six], 'S6', 80, ROWS_24)
  const text6 = textOf(await o6.ui.drawn())
  expect(text6).toContain('[○ (g) choice g]')
  expect(text6).toContain('↓ note, send')
  expect(text6).toContain('<Note (optional)>')
  const longText = 'x'.repeat(300)
  const lo = item({ id: 'S7', options: [{ key: 'a', text: longText }, { key: 'b', text: 'y' }] })
  for (const [rows, max] of [[ROWS_24, 1], [ROWS_40, 2]]) {
    for (const cols of [80, 60, 47]) {
      const { ui } = await open($, on, [lo], 'S7', cols, rows)
      const row = rowsOf(await ui.drawn()).find((l) => l.startsWith('[○ (a)')) as string
      const inner = row.slice(1, -1)
      const parts = inner.split('\n')
      expect(parts.length, `${cols}x${rows}`).toBe(max)
      for (const p of parts) expect(cellWidth(p), `${cols}x${rows}`).toBeLessThanOrEqual(cols)
      expect(parts.at(-1)?.endsWith('…')).toBe(true)
      await ui.unmount()
    }
  }
  const cjk = item({ id: 'S8', options: [{ key: 'a', text: '日本語のとても長い選択肢'.repeat(12) }, { key: 'b', text: '😀'.repeat(60) }] })
  for (const cols of [80, 60, 47]) {
    const { ui } = await open($, on, [cjk], 'S8', cols, ROWS_40)
    for (const row of rowsOf(await ui.drawn()).filter((l) => l.startsWith('[○'))) for (const p of row.slice(1, -1).split('\n')) expect(cellWidth(p)).toBeLessThanOrEqual(cols)
    await ui.unmount()
  }
})

test('state rows: sending: the Send button reads `Sending…` and an option press is ignored', async ($, on) => {
  const slow = item({ id: 'S9', options: H_OPTS })
  let release: (r: any) => void = () => undefined
  const { ui, w } = await open($, on, [slow], 'S9', 80, ROWS_24, (argv) => (argv[0] === 'answer' ? { exitCode: 0, stdout: '', stderr: '' } : undefined))
  void release
  await ui.press({ key: 'opt-b' })
  const sending = ui.press({ key: 'send' })
  // while the CLI call is in flight the Send button reads `Sending…`; an option press then must not change the pick
  await Promise.all([sending, ui.press({ key: 'opt-a' }).catch(() => undefined)])
  const sent = w.runs.filter((r: any) => r.argv[1] === 'answer').map((r: any) => r.argv.slice(1))
  expect(sent).toEqual([['answer', 'S9', '--option', 'b', '--source', 'pane']])
})

test('state rows: no body: no Context, no Details, no hint; title only', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'N1', body: '', options: H_OPTS })], 'N1', 80, 40)
  const text = textOf(await ui.drawn())
  for (const gone of ['Context', 'Details', '↓']) expect(text).not.toContain(gone)
  const same = await open($, on, [item({ id: 'N2', body: 'Which branch merges first?', options: H_OPTS })], 'N2', 80, 40)
  expect(textOf(await same.ui.drawn())).not.toContain('Context')
})

test('state rows: free-text item keeps 4 body rows before the fold', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'G4', title: 't', blocks: 'x', body: LONG_BODY })], 'G4', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  const at = r.indexOf('Context')
  expect(r.slice(at + 1, at + 5).filter((l) => l.startsWith('line ')).length).toBeGreaterThanOrEqual(2)
  expect(r.some((l) => /^… \d+ more rows$/.test(l))).toBe(true)
})

test('"N more rows" counts the rows left: a fence is its lines, a table its rows plus the rule', async ($, on) => {
  const body = 'one\n\n```\nc1\nc2\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |'
  const { ui } = await open($, on, [item({ id: 'G5', title: 't', blocks: 'x', body })], 'G5', 80, ROWS_24)
  await ui.press({ key: 'details' })
  const all = rowsOf(await ui.drawn())
  const total = all.slice(all.indexOf('Context') + 1, all.lastIndexOf('[← Decide (b)]')).length
  await ui.press({ key: 'back' })
  const r = rowsOf(await ui.drawn())
  const fold = r.find((l) => /^… \d+ more rows$/.test(l)) as string
  const shown = r.slice(r.indexOf('Context') + 1, r.indexOf(fold)).length
  expect(Number(fold.match(/\d+/)![0])).toBe(total - shown)
})

test('a first block taller than the budget is clipped with `…` and counted as left', async ($, on) => {
  const { ui } = await open($, on, [item({ id: 'G6', title: 't', blocks: 'x', body: 'word '.repeat(120) })], 'G6', 80, ROWS_24)
  const r = rowsOf(await ui.drawn())
  const p = r.find((l) => l.startsWith('word ')) as string
  expect(p.endsWith('…')).toBe(true)
  expect(refRows(p, 80)).toBeLessThanOrEqual(4)
  expect(r.join('\n')).toMatch(/… \d+ more rows/)
})

test('T8: the title rule P6 reaches the screen: the first body line becomes the title and leaves the body', async ($, on) => {
  const full = 'Which branch merges first for BRD-02 through BRD-06 after BRD-01 passes both QAs and the PO review today?'
  const cut = full.slice(0, 80)
  const it = item({ id: 'P6', title: cut, body: `${full}\nSecond line of context.`, options: H_OPTS })
  const { ui } = await open($, on, [it], 'P6', 120, 40)
  const text = textOf(await ui.drawn())
  expect(text.split(full).length - 1).toBe(1)
  expect(text).toContain('Second line of context.')
  expect(text).not.toContain(`${cut}\n`)
})

test('ui.detail resets: leaving the item and opening it again shows Decide; closing and reopening the pane too', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 80, ROWS_24)
  await ui.press({ key: 'details' })
  expect(textOf(await ui.drawn())).toContain('[← Decide (b)]')
  await ui.press({ key: 'back' })
  await ui.press({ key: 'back' }) // Decide -> list
  await ui.press({ key: 'E1' })
  let text = textOf(await ui.drawn())
  expect(text).toContain('[Send answer]')
  expect(text).not.toContain('Decide (b)')
  // the pane closed and opened again (the band's Open button): the item opens on Decide
  await ui.press({ key: 'details' })
  await $.command.run({ command: 'inbox' })
  await ui.press({ key: 'E1' })
  text = textOf(await ui.drawn())
  expect(text).toContain('[Send answer]')
  expect(text).not.toContain('Decide (b)')
  await ui.unmount()
})

test('Details page: the full recommendation (key and reason), one `b` hotkey, no Input, the key map', async ($, on) => {
  for (const [it, hot] of [[E1, { 'Button:back': 'b', 'Button:back-end': null }], [R1, { 'Button:back': 'b', 'Button:mark-read': 'm', 'Button:mark-read-end': null, 'Button:back-end': null }]] as const) {
    const { ui } = await open($, on, [it], it.id, 80, ROWS_24)
    await ui.press({ key: 'details' })
    const tree = await ui.drawn()
    const keys: Record<string, unknown> = {}
    walk(tree, (n) => {
      if (['Button', 'Input'].includes(n.type) && n.props?.key) keys[`${n.type}:${n.props.key}`] = n.props.hotkey ?? null
    })
    expect(keys, it.id).toEqual(hot)
    const hotkeys = Object.values(keys).filter((h) => h !== null)
    expect(new Set(hotkeys).size).toBe(hotkeys.length)
    if (it === E1) expect(textOf(tree)).toContain(`✓ recommends: ${E1_REC}`)
    await ui.unmount()
  }
  const w = await open($, on, [WAITING], WAITING.id, 80, ROWS_24)
  const long = handled('answered-waiting', null, ANS(), { id: 'HW', body: 'l1\n\nl2\n\nl3\n\nl4\n\nl5\n\nl6\n\nl7\n\nl8' })
  const h = await open($, on, [long], 'HW', 80, ROWS_24)
  await h.ui.press({ key: 'details' })
  expect((await h.ui.find({ key: 'back' }))?.props?.hotkey).toBe('b')
  expect((await h.ui.find({ key: 'back-end' }))?.props?.hotkey).toBeUndefined()
  void w
})

test('the tall-tier reason row wraps under its own indent (hanging)', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 47, ROWS_40)
  const tree = await ui.drawn()
  let hanging = false
  walk(tree, (n) => {
    if (n.type === 'Box' && n.props?.width === 6 && flat(n.children ?? []) === '' ) hanging = true
  })
  expect(hanging).toBe(true)
  expect(textOf(tree)).toContain('✓ recommended: ')
})

test('F2: a read item that blocks nothing keeps its header on row 1 at 60 and 47 columns', async ($, on) => {
  const it = item({ id: 'N2', kind: 'read', blocks: '', body: 'l1\n\nl2\n\nl3', created: '2026-10-15T09:00:00' })
  for (const cols of [60, 47]) {
    const { ui } = await open($, on, [it], 'N2', cols, ROWS_24)
    expect(textOf(await ui.drawn()), `${cols} cols`).toContain('N2 · read')
    expect(await ui.find({ key: 'head2' }), `${cols} cols: header on its own row`).toBeFalsy()
    await ui.unmount()
  }
})

test('F3: the fold marker is singular for one hidden row, plural for more', async ($, on) => {
  const six = Array.from({ length: 6 }, (_, i) => `line ${i}`).join('\n\n')
  const marker = async (body: string) => {
    const { ui } = await open($, on, [item({ id: 'N3', kind: 'read', body })], 'N3', 80, ROWS_24)
    const text = textOf(await ui.drawn())
    await ui.unmount()
    return text
  }
  const one = await marker(`${six}\n- x\n- y`)
  expect(one).toContain('… 1 more row\n')
  expect(one).not.toContain('1 more rows')
  expect(await marker(`${six}\n\n- x`)).toMatch(/… [2-9] more rows\n/)
})

test('F4: Details says `↓ more below` at 47 columns, never `↓ context`', async ($, on) => {
  const { ui } = await open($, on, [E1], 'E1', 47, ROWS_24)
  await ui.press({ key: 'details' })
  const text = textOf(await ui.drawn())
  expect(text).toContain('↓ more below')
  expect(text).not.toContain('↓ context')
  await ui.unmount()
})
