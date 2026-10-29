// IV-04: the band and the list: V-15 colour per element, the band ladder, the 7-row fold, row text widths.
import { expect, test } from 'claude-code/testing'

import { cellWidth } from './core'
import { START, band, boot, dump, item, lines, pane, rowsOfTree, snap, styleOf, textOf } from './testkit'

const ANS = { text: '(b) go', option: 'b', note: null, ts: '2026-10-15T10:42:00', source: 'pane', delivered_ts: null }
const ans = (i: number, o: Record<string, unknown> = {}) => item({ id: `E${i}`, title: `Question ${i}`, created: `2026-10-13T09:${String(10 + i).padStart(2, '0')}:00`, ...o })
const rd = (i: number, o: Record<string, unknown> = {}) => item({ id: `R${i}`, kind: 'read', title: `Read ${i}`, blocks: 'nothing', ...o })
const wt = (i: number) => item({ id: `E${50 + i}`, title: `Waiting ${i}`, state: 'answered-waiting', answer: ANS })
const many = (n: number, mk: (i: number) => any) => Array.from({ length: n }, (_, i) => mk(i + 1))

// The drawn band as one string: the Text, then the Button as the engine draws it, `[ label ]`.
async function bandOf(ui: any) {
  const tree = await ui.drawn()
  const button = await ui.find({ type: 'Button', key: 'open' })
  const label = button.props.label
  const box = tree.type === 'Box' ? tree : tree[0]
  const text = textOf(box.children[0])
  return { tree, text, label, box, width: cellWidth(text) + cellWidth(`[ ${label} ]`) }
}

// --- the band: the ladder, written out per state ----------------------------------------------
// Rungs: 1 `Inbox  `, long words, `Open inbox (i)`; 2 same, `Open (i)`; 3 `Inbox `, short words, one-space gap;
// 4 no head; 5 `wait`, space separator; 6 as 5, the button on a second row. The first whose width fits `bodyColumns`.

const Q = ans(1)
const R = rd(1)
const W3 = many(3, wt)
const BAND_CASES: { name: string; items: any[]; errors?: any[]; at75: string; label75: string; at35: string; label35: string }[] = [
  { name: 'answers + reads', items: [ans(1), ans(2), R], at75: 'Inbox  2 to answer · 1 to read   ', label75: 'Open inbox (i)', at35: '2 answer · 1 read ', label35: 'Open (i)' },
  { name: 'reads only', items: many(3, rd), at75: 'Inbox  3 to read   ', label75: 'Open inbox (i)', at35: 'Inbox  3 to read   ', label35: 'Open (i)' },
  { name: 'answers only', items: [Q], at75: 'Inbox  1 to answer   ', label75: 'Open inbox (i)', at35: 'Inbox  1 to answer   ', label35: 'Open (i)' },
  { name: 'waiting only', items: W3, at75: 'Inbox  3 answered, waiting for the Manager   ', label75: 'Open inbox (i)', at35: 'Inbox 3 waiting ', label35: 'Open (i)' },
  { name: 'answers + waiting', items: [ans(1), ans(2), wt(1)], at75: 'Inbox  2 to answer · 1 waiting   ', label75: 'Open inbox (i)', at35: '2 answer · 1 waiting ', label35: 'Open (i)' },
  { name: 'problems only', items: [], errors: [{ file: 'f', row: 1, message: 'm' }, { file: 'f', row: 2, message: 'm' }], at75: 'Inbox  2 problems   ', label75: 'Open inbox (i)', at35: 'Inbox  2 problems   ', label35: 'Open (i)' },
]

for (const c of BAND_CASES) {
  test(`band ${c.name}: the rung the width rule picks at 75 and 35 columns, one row`, async ($, on) => {
    await boot($, on, snap(c.items, c.errors ?? []))
    for (const [cols, text, label] of [[75, c.at75, c.label75], [35, c.at35, c.label35]] as const) {
      const ui = await $.ui.mount(band('terminal', cols))
      const b = await bandOf(ui)
      expect([cols, b.text, b.label]).toEqual([cols, text, label])
      expect(b.width).toBeLessThanOrEqual(cols)
      expect(rowsOfTree(b.tree, cols)).toBe(1)
      await ui.unmount()
    }
  })
}

test('band: the four-kinds, two-digit case at 75 is rung 2, at 35 it wraps to exactly two rows with every count', async ($, on) => {
  const items = [...many(12, ans), ...many(3, (i) => rd(i)), ...many(2, wt)]
  await boot($, on, snap(items, [{ file: 'f', row: 1, message: 'm' }]))
  const wide = await $.ui.mount(band('terminal', 75))
  const w = await bandOf(wide)
  expect([w.text, w.label]).toEqual(['Inbox  12 to answer · 3 to read · 2 waiting · 1 problem   ', 'Open (i)'])
  expect(rowsOfTree(w.tree, 75)).toBe(1)
  const narrow = await $.ui.mount(band('terminal', 35))
  const tree = await narrow.drawn()
  const t = tree.type === 'Box' ? tree : tree[0]
  expect(t.props.flexDirection).toBe('column')
  expect(t.children.map((n: any) => n.type)).toEqual(['Text', 'Button'])
  expect(textOf(t.children[0])).toBe('12 answer 3 read 2 wait 1 problem')
  expect(rowsOfTree(tree, 35)).toBe(2)
})

test('band 4.8: 120 to answer, 15 waiting, 3 problems keeps every count at 40 and 35 columns (rung 6 wraps: the line is 42 cells), and survives 30', async ($, on) => {
  const items = [...many(120, ans), ...many(15, wt)]
  const errors = [1, 2, 3].map((row) => ({ file: 'f', row, message: 'm' }))
  await boot($, on, snap(items, errors))
  for (const cols of [40, 35]) {
    const ui = await $.ui.mount(band('terminal', cols))
    const b = await bandOf(ui)
    expect(b.text).toBe('120 answer 15 wait 3 problems')
    expect(b.box.props.flexDirection).toBe('column')
    expect(rowsOfTree(b.tree, cols)).toBe(2)
    await ui.unmount()
  }
  const tiny = await $.ui.mount(band('terminal', 30))
  const t = await dump(tiny)
  expect(t.indexOf('120')).toBeLessThan(t.indexOf('[Open'))
  for (const part of ['120 answer', '15 wait', '3 problems']) expect(t).toContain(part)
})

test('band V-15: amber answer and waiting, red problems, reads and head uncoloured, separators plain; no `suggestion` anywhere', async ($, on) => {
  const w = await boot($, on, snap([Q, R, wt(1), wt(2)], [{ file: 'f', row: 1, message: 'm' }]))
  const ui = await $.ui.mount(band('terminal', 100))
  const tree = await ui.drawn()
  expect(styleOf(tree, '1 to answer')).toEqual({ color: 'warning' })
  expect(styleOf(tree, '1 to read')).toEqual({})
  expect(styleOf(tree, '2 waiting')).toEqual({ color: 'warning' })
  expect(styleOf(tree, '1 problem')).toEqual({ color: 'error' })
  expect(styleOf(tree, 'Inbox')).toEqual({ bold: true })
  expect(styleOf(tree, ' · ')).toEqual({})
  expect(JSON.stringify(tree)).not.toContain('suggestion')
  await ui.unmount()
  w.current = snap(W3)
  await $.session.start(START)
  const only = await $.ui.mount(band('terminal', 100))
  expect(styleOf(await only.drawn(), 'answered, waiting for the Manager')).toEqual({ color: 'warning' })
})

test('band: an error alone draws `1 problem` in red', async ($, on) => {
  const w = await boot($, on, snap([]))
  w.current = null
  await $.session.start(START)
  const ui = await $.ui.mount(band('terminal', 75))
  const b = await bandOf(ui)
  expect(b.text).toBe('Inbox  1 problem   ')
  expect(styleOf(await ui.drawn(), '1 problem')).toEqual({ color: 'error' })
})

// --- the list: colour ---------------------------------------------------------------------------

test('list V-15: kind, blocks, age, ids, group titles and the heading carry their tone', async ($, on) => {
  await boot($, on, snap([ans(1, { blocks: 'IV-06 (Developer 1)' }), ans(2, { blocks: 'nothing' }), rd(2, { blocks: 'IV-06' }), wt(1), rd(3)]))
  const ui = await $.ui.mount(pane('terminal', 80))
  const tree = await ui.drawn()
  const inRow = async (key: string) => (await ui.find({ key })).children
  expect(styleOf(await inRow('E1'), 'answer')).toEqual({ color: 'warning' })
  expect(styleOf(await inRow('E51'), 'answered')).toEqual({ color: 'warning' })
  expect(styleOf(await inRow('R2'), 'read')).toEqual({})
  expect(styleOf(await inRow('E1'), 'E1')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'blocks IV-06 (Developer 1)')).toEqual({ color: 'error' })
  expect(styleOf(tree, 'blocks nothing')).toEqual({ dimColor: true })
  expect(styleOf(tree, ' · created')).toEqual({ dimColor: true })
  expect(styleOf(tree, '(your answer sent')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'Blocks work')).toMatchObject({ bold: true })
  expect(styleOf(tree, ' (2)')).toMatchObject({ dimColor: true })
  expect(styleOf(tree, 'Answered, waiting for the Manager')).toMatchObject({ bold: true, color: 'warning' })
  expect(styleOf(tree, '1 waiting')).toEqual({ color: 'warning' })
  expect(styleOf(tree, '2 to answer')).toEqual({})
  expect(JSON.stringify(tree)).not.toContain('suggestion')
  // a read item that blocks (V-16): the kind word has no colour, `blocks IV-06` is red, on one row
  expect(styleOf(tree, 'blocks IV-06')).toEqual({ color: 'error' })
})

// --- the fold (V-20) ---------------------------------------------------------------------------

const buttons = async (ui: any) => (await ui.findAll({ type: 'Button' })) as any[]
const moreOf = async (ui: any) => (await buttons(ui)).filter((b) => /\+\d+ more/.test(b.text))
const rowIds = async (ui: any) => (await buttons(ui)).map((b) => /\b([ER]\d+)\b/.exec(b.text)?.[1]).filter(Boolean)

test('fold edges: 0, 7, 8, 12+9, 7+0, 7+8 and the heading and band totals', async ($, on) => {
  const cases: [string, any[], string[]][] = [
    ['0', [], []],
    ['7', many(7, ans), []],
    ['8', many(8, ans), ['+1 more']],
    ['12+9', [...many(12, ans), ...many(9, rd)], ['+5 more', '+2 more']],
    ['7+0', many(7, ans), []],
    ['7+8', [...many(7, ans), ...many(8, rd)], ['+1 more']],
  ]
  const w = await boot($, on, snap([]))
  for (const [name, items, more] of cases) {
    w.current = snap(items)
    await $.session.start(START)
    const ui = await $.ui.mount(pane('terminal', 80))
    const b = await $.ui.mount(band('terminal', 100))
    const m = await moreOf(ui)
    expect({ name, more: m.map((x) => x.text.trim()) }).toEqual({ name, more })
    const text = await dump(ui)
    const bt = await dump(b)
    const a = items.filter((i) => i.kind === 'answer').length
    const r = items.length - a
    if (a) for (const t of [text, bt]) expect(t).toContain(`${a} to answer`)
    if (r) for (const t of [text, bt]) expect(t).toContain(`${r} to read`)
    if (a) expect(text).toContain(`Blocks work (${a})`)
    if (name === '7+0') expect(text).not.toContain('Blocks nothing')
    if (name === '0') expect(text).toContain('Nothing waits on you.')
    await ui.unmount()
    await b.unmount()
  }
})

test('fold: the shown rows are the first 7 of the CLI order, the hidden count is the total minus 7, digits stay on 1-9', async ($, on) => {
  await boot($, on, snap([...many(12, ans), ...many(9, rd)]))
  const ui = await $.ui.mount(pane('terminal', 80))
  expect(await rowIds(ui)).toEqual(['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7'])
  const bs = await buttons(ui)
  expect(bs.map((b: any) => b.props.hotkey).filter(Boolean)).toEqual(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
  const [m1, m2] = await moreOf(ui)
  expect(m1.text).toContain('+5 more')
  expect(m2.text).toContain('+2 more')
  expect(m1.props.hotkey).toBeUndefined()
  expect(m2.props.hotkey).toBeUndefined()
  expect(m1.key).not.toBe(m2.key)
  const tree = await ui.drawn()
  expect(styleOf(tree, '+5 more')?.dimColor).toBe(true)
  expect(styleOf(tree, '+2 more')?.dimColor).toBe(true)
})

test('+N more opens only its group, in place; going to an item and back folds both again (T10)', async ($, on) => {
  await boot($, on, snap([...many(12, ans), ...many(9, rd)]))
  const ui = await $.ui.mount(pane('terminal', 80))
  await ui.press((await moreOf(ui))[0])
  expect((await rowIds(ui)).slice(0, 12)).toEqual(Array.from({ length: 12 }, (_, i) => `E${i + 1}`))
  expect((await moreOf(ui)).map((b) => b.text.trim())).toEqual(['+2 more'])
  expect(await rowIds(ui)).toHaveLength(12 + 7)
  expect(await dump(ui)).toContain('12 to answer · 9 to read')
  // the 8th blocking item is reachable now, and opens
  await ui.press({ key: 'E8' })
  expect(await dump(ui)).toContain('Question 8')
  await ui.press({ key: 'back' })
  expect((await moreOf(ui)).map((b) => b.text.trim())).toEqual(['+5 more', '+2 more'])
})

test('fold: rows past 9 are pressable by key and carry three spaces instead of a digit; +N more is in the Tab order after the last shown row', async ($, on) => {
  await boot($, on, snap(many(12, ans)))
  const ui = await $.ui.mount(pane('terminal', 80))
  const folded = (await buttons(ui)).map((b: any) => b.key)
  expect(folded.indexOf('more-blocks')).toBe(folded.indexOf('E7') + 1)
  await ui.press((await moreOf(ui))[0])
  const bs = await buttons(ui)
  const tenth = bs.find((b: any) => b.text.includes('E10'))
  expect(tenth.props.hotkey).toBeUndefined()
  expect(tenth.text.startsWith('   ')).toBe(true)
  await ui.press({ key: 'E10' })
  expect(await dump(ui)).toContain('Question 10')
})

test('fold: a refresh while expanded that drops the group to 7 has no stale +N more and no crash', async ($, on) => {
  const w = await boot($, on, snap(many(9, ans)))
  const ui = await $.ui.mount(pane('terminal', 80))
  await ui.press((await moreOf(ui))[0])
  expect(await rowIds(ui)).toHaveLength(9)
  w.current = snap(many(7, ans))
  w.mtime++
  await w.clock.advance(2000)
  await ui.redraw()
  expect(await moreOf(ui)).toEqual([])
  expect(await rowIds(ui)).toHaveLength(7)
  w.current = snap(many(9, ans))
  w.mtime++
  await w.clock.advance(2000)
  await ui.redraw()
  expect(await moreOf(ui)).toEqual([])
  expect(await rowIds(ui)).toHaveLength(9)
  w.current = snap([])
  w.mtime++
  await w.clock.advance(2000)
  await ui.redraw()
  expect(await dump(ui)).toContain('Nothing waits on you.')
})

test('fold: the waiting group folds too (own key) ', async ($, on) => {
  await boot($, on, snap(many(9, wt)))
  const ui = await $.ui.mount(pane('terminal', 80))
  const m = await moreOf(ui)
  expect(m.map((b) => b.text.trim())).toEqual(['+2 more'])
  await ui.press(m[0])
  expect(await moreOf(ui)).toEqual([])
})

test('2.10 an old atom without `more` draws, expands and navigates without a crash', async ($, on) => {
  // every write of the ui atom drops `more`, as an atom saved before IV-04 has it
  on('state.set', (_$: any, e: any, next: any) => {
    if (e.key !== 'ui' || !e.value) return next(e)
    const { more: _drop, ...old } = e.value
    return next({ ...e, value: old })
  })
  await boot($, on, snap(many(9, ans)))
  const ui = await $.ui.mount(pane('terminal', 80))
  expect((await moreOf(ui)).map((b) => b.text.trim())).toEqual(['+2 more'])
  await ui.press((await moreOf(ui))[0])
  await ui.press({ key: 'E1' })
  await ui.press({ key: 'back' })
  expect(await rowIds(ui)).toHaveLength(7)
})

// --- keys (V-30) -------------------------------------------------------------------------------

test('keys: the list screen map is d on the heading row, then 1-9 over shown rows; the band has i; none repeats', async ($, on) => {
  const waiting = many(2, wt)
  const items = [...many(8, ans), ...many(3, rd), ...waiting, item({ id: 'E90', state: 'done', done: { kind: 'read', ts: '2026-10-15T10:00:00', reason: null } })]
  await boot($, on, snap(items))
  const ui = await $.ui.mount(pane('terminal', 80))
  const hot = (await buttons(ui)).map((b: any) => b.props.hotkey).filter(Boolean)
  expect(hot).toEqual(['d', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
  expect(new Set(hot).size).toBe(hot.length)
  expect(hot).not.toContain('i')
  expect(hot).not.toContain('b')
  const b = await $.ui.mount(band('terminal', 100))
  expect((await b.find({ type: 'Button', key: 'open' })).props.hotkey).toBe('i')
  await ui.press({ key: 'done' })
  expect(await dump(ui)).toContain('Done · newest first')
})

// --- row text widths ---------------------------------------------------------------------------

const WIDE = [
  ['ascii', 'T'.repeat(300), 'B'.repeat(300)],
  ['cjk', '日本語のとても長い質問のタイトルです'.repeat(6), '日本語のブロック先'.repeat(30)],
  ['emoji', '🚀 launch '.repeat(30), '🚀🚀 pod '.repeat(40)],
] as const

test('row text: nothing wider than the pane at 80, 60, 59, 40 and 30; kind and blocks both visible; long text ends in an ellipsis', async ($, on) => {
  const w = await boot($, on, snap([]))
  for (const [name, title, blocks] of WIDE) {
    w.current = snap([ans(1, { title, blocks }), rd(1, { title }), wt(1), ans(2, { title: 'short', blocks: 'X' })])
    await $.session.start(START)
    for (const cols of [80, 60, 59, 40, 30]) {
      const ui = await $.ui.mount(pane('terminal', cols))
      const tree = await ui.drawn()
      const ls = lines(tree)
      const texts: string[] = []
      const walk = (n: any) => {
        if (n === null || typeof n !== 'object') return
        if (Array.isArray(n)) return n.forEach(walk)
        if (n.type === 'Button') {
          texts.push(`${n.props.hotkey && n.props.hotkey !== 'd' ? '1: ' : ''}${textOf(n)}`)
        } else if (n.type === 'Text' && textOf(n).startsWith('    ')) texts.push(textOf(n))
        else walk(n.children)
      }
      walk(tree)
      for (const t of texts) {
        if (/Done \(/.test(t)) continue
        expect({ name, cols, t, w: cellWidth(t) <= cols }).toEqual({ name, cols, t, w: true })
      }
      expect(texts[0]).toContain('…')
      expect(texts[0]).toMatch(/E1\s+answer\s/)
      const at = ls.findIndex((l) => /E1\s+answer/.test(l))
      const sub = ls.slice(at + 1, at + 3)
      expect(sub.join('')).toContain('blocks')
      expect(sub[sub.length - 1].endsWith('…') || sub.join('').includes('…')).toBe(true)
      expect(ls.some((l) => l.includes('(your answer sent'))).toBe(true)
      await ui.unmount()
    }
  }
})

test('row text: age shows only when the whole line fits one row, short form under 60 columns', async ($, on) => {
  await boot($, on, snap([ans(1, { blocks: 'IV-03 (Developer 1)', created: '2026-10-15T02:00:00' }), ans(2, { blocks: 'the spawning of the pod (BA, Tech Lead)', created: '2026-10-15T02:00:00' })]))
  const at = async (cols: number) => {
    const ui = await $.ui.mount(pane('terminal', cols))
    const out = lines(await ui.drawn()).filter((l) => l.startsWith('    '))
    await ui.unmount()
    return out
  }
  expect(await at(80)).toEqual(['    blocks IV-03 (Developer 1) · created 10h ago', '    blocks the spawning of the pod (BA, Tech Lead) · created 10h ago'])
  expect(await at(52)).toEqual(['    blocks IV-03 (Developer 1) · 10h', '    blocks the spawning of the pod (BA, Tech Lead)'])
  expect(await at(40)).toEqual(['    blocks IV-03 (Developer 1) · 10h', '    blocks the spawning of the pod (BA,', '    Tech Lead)'])
})

test('row text: the heading and group titles wrap (never clipped); the short words come only when the long ones do not fit', async ($, on) => {
  await boot($, on, snap([ans(1), rd(1), wt(1)]))
  const long = await $.ui.mount(pane('terminal', 60))
  expect(await dump(long)).toContain('Inbox · 1 to answer · 1 to read · 1 waiting')
  await long.unmount()
  const roomy = await $.ui.mount(pane('terminal', 44))
  expect(await dump(roomy)).toContain('Inbox · 1 to answer · 1 to read · 1 waiting')
  await roomy.unmount()
  const short = await $.ui.mount(pane('terminal', 42))
  expect(await dump(short)).toContain('Inbox · 1 answer · 1 read · 1 waiting')
  const tree = await short.drawn()
  expect(JSON.stringify(tree)).not.toContain('"wrap":"truncate"')
})

// --- ticket 02: one row per item, the heading row, the hint (list.md) -----------------------------

const SHORT = 6 // bodyRows of a 24-row terminal
const TALL = 11 // bodyRows of a 40-row terminal

// The seeded list of the design: 2 blocking answers, 1 answer that blocks nothing, 2 reads.
const seeded = () => [
  ans(1, { id: 'E1', title: 'Which branch merges first: BRD-01 for BRD-02..06?', blocks: 'BRD-02..06', created: '2026-10-15T04:00:00' }),
  ans(2, { id: 'E2', title: 'Usage limits: account 2 is at 94% 7d', blocks: 'All remaining work', created: '2026-10-15T04:00:00' }),
  ans(5, { id: 'E5', title: 'What name should the new mode have in the CLI and in the docs?', blocks: 'nothing', created: '2026-10-15T04:00:00' }),
  rd(1, { id: 'R1', title: 'Iteration 1 passed: all 3 tasks', created: '2026-10-15T11:57:00' }),
  rd(2, { id: 'R2', title: 'Long plan with many sections to read', created: '2026-10-15T11:57:00' }),
]
const done3 = [1, 2, 3].map((i) => item({ id: `D${i}`, state: 'done', done: { kind: 'read', ts: '2026-10-15T10:00:00', reason: null } }))

// Row 1 as the engine draws it: texts joined, a Button as `[ label ]`.
function top(tree: any): { text: string; rows: number } {
  const root = Array.isArray(tree) ? tree[0] : tree
  const first = root.children[0]
  const side = (n: any): string =>
    Array.isArray(n) ? n.map(side).join('') : n && n.type === 'Button' ? `[ ${n.props?.label ?? textOf(n)} ]` : n && n.type === 'Box' ? (n.children ?? []).map(side).join('') : textOf(n)
  if (first.props?.flexDirection === 'column') return { text: first.children.map(side).join('\n'), rows: first.children.length }
  return { text: side(first.children), rows: 1 }
}

// `left`, then `hint` ending on the last of `cols` cells (at least 2 spaces between).
const withHint = (left: string, hint: string, cols: number): string => `${left}${' '.repeat(Math.max(2, cols - cellWidth(left) - cellWidth(hint)))}${hint}`
const subRows = (ls: string[]): string[] => ls.filter((l) => l.startsWith('    ') && !l.trim().startsWith('↓'))

const rowButtons = async (ui: any) => ((await buttons(ui)) as any[]).filter((b) => /^(   )?[ER]\d+ /.test(b.text))

test('short tier: one row per item, the short age at the right end of the row, the sub-row gone', async ($, on) => {
  await boot($, on, snap(seeded()))
  for (const cols of [80, 60, 47]) {
    const ui = await $.ui.mount(pane('terminal', cols, SHORT))
    const rows = await rowButtons(ui)
    expect(rows.map((b: any) => /^(E\d+|R\d+)/.exec(b.text)?.[0])).toEqual(['E1', 'E2', 'E5', 'R1', 'R2'])
    for (const b of rows) {
      expect(3 + cellWidth(b.text)).toBe(cols) // `n: ` + text: the age ends on the last cell
      expect(b.text).toMatch(/ (8h|3m)$/)
    }
    expect(rows[0].text).toMatch(/^E1 {2}answer {2}Which branch merges first/)
    expect(subRows(lines(await ui.drawn()))).toEqual([])
    expect(await dump(ui)).not.toContain('blocks BRD-02..06')
    expect(styleOf(await ui.drawn(), '8h')).toEqual({ dimColor: true })
    await ui.unmount()
  }
})

test('short tier at 24 rows: heading, 2 group headings and 3 items fit the 6 body rows (was 2 items)', async ($, on) => {
  await boot($, on, snap([...seeded(), ...done3]))
  const ui = await $.ui.mount(pane('terminal', 80, SHORT))
  const ls = lines(await ui.drawn())
  // rows 1-6: heading, Blocks work, E1, E2, Blocks nothing, E5; each item is one row, the others lie below
  const at = (s: string) => ls.findIndex((l) => l.includes(s))
  expect([at('Blocks work'), at('E1'), at('E2'), at('Blocks nothing'), at('E5'), at('R1')].every((x, i, a) => x > -1 && (i === 0 || x > a[i - 1]))).toBe(true)
  expect(top(await ui.drawn()).text).toBe(withHint('Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]', '↓ 2 more', 80))
})

test('tall tier: the item rows keep their two rows and no age at the right end; only the heading row changes', async ($, on) => {
  await boot($, on, snap([...seeded(), ...done3]))
  const ui = await $.ui.mount(pane('terminal', 80, TALL))
  const rows = await rowButtons(ui)
  for (const b of rows) expect(b.text).not.toMatch(/ (8h|3m)$/)
  const ls = lines(await ui.drawn())
  expect(ls.filter((l) => l.startsWith('    blocks '))).toHaveLength(5)
  expect(ls).toContain('    blocks BRD-02..06 · created 8h ago')
  expect(top(await ui.drawn()).text).toBe(withHint('Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]', '↓ 1 more', 80))
})

test('the Done button is on the heading row only, with its hotkey; the bottom one is gone', async ($, on) => {
  await boot($, on, snap([...seeded(), ...done3]))
  for (const rows of [SHORT, TALL]) {
    const ui = await $.ui.mount(pane('terminal', 80, rows))
    const dones = (await buttons(ui)).filter((b: any) => b.key === 'done')
    expect(dones).toHaveLength(1)
    expect(dones[0].props.hotkey).toBe('d')
    expect(top(await ui.drawn()).text).toContain('[ Done (3) (d) ]')
    const all = lines(await ui.drawn())
    expect(all[all.length - 1]).not.toContain('Done (')
    await ui.unmount()
  }
})

test('heading hint: `↓ N more` counts the items below the first viewport and is dim', async ($, on) => {
  await boot($, on, snap([...seeded(), ...done3]))
  const short = await $.ui.mount(pane('terminal', 80, SHORT))
  expect(top(await short.drawn()).text).toMatch(/\[ Done \(3\) \(d\) \] +↓ 2 more$/)
  expect(cellWidth(top(await short.drawn()).text)).toBe(80)
  expect(styleOf(await short.drawn(), '↓ 2 more')).toEqual({ dimColor: true })
  await short.unmount()
  const tall = await $.ui.mount(pane('terminal', 80, TALL))
  expect(top(await tall.drawn()).text).toMatch(/↓ 1 more$/) // R2 starts on row 12
  await tall.unmount()
  const roomy = await $.ui.mount(pane('terminal', 80, 30))
  expect(top(await roomy.drawn()).text).not.toContain('↓')
})

test('heading hint: a `+N more` fold below counts its hidden items; none shown when only a sub-row lies below', async ($, on) => {
  const w = await boot($, on, snap(many(12, ans)))
  const ui = await $.ui.mount(pane('terminal', 80, SHORT))
  // rows: heading, group heading, E1..E4 fill 6; E5..E7 start below (3) and `+5 more` (5)
  expect(top(await ui.drawn()).text).toBe(withHint('Inbox · 12 to answer', '↓ 8 more', 80))
  await ui.unmount()
  w.current = snap([ans(1), ans(2)])
  await $.session.start(START)
  const two = await $.ui.mount(pane('terminal', 80, 5)) // heading, group, E1 (2 rows) = 4; E2 starts on row 5 and is seen
  expect(top(await two.drawn()).text).not.toContain('↓')
})

test('heading row, drop order: hint, then the long words, then the Done button on its own row (80, 60, 59, 56, 47, 40 columns)', async ($, on) => {
  await boot($, on, snap(seeded().concat(done3)))
  const want: Record<number, { text: string; rows: number }> = {
    80: { text: withHint('Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]', '↓ 2 more', 80), rows: 1 },
    60: { text: withHint('Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]', '↓ 2 more', 60), rows: 1 },
    59: { text: withHint('Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]', '↓ 2 more', 59), rows: 1 },
    // a 60-column terminal: the body is 56. The long counts and the button fit, the hint does not: the hint goes, the counts stay long
    56: { text: 'Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]', rows: 1 },
    47: { text: 'Inbox · 3 answer · 2 read  [ Done (3) (d) ]', rows: 1 },
    40: { text: 'Inbox · 3 answer · 2 read\n[ Done (3) (d) ]', rows: 2 },
  }
  for (const cols of [80, 60, 59, 56, 47, 40]) {
    const ui = await $.ui.mount(pane('terminal', cols, SHORT))
    const got = top(await ui.drawn())
    expect({ cols, ...got }).toEqual({ cols, ...want[cols] })
    for (const l of got.text.split('\n')) expect(cellWidth(l)).toBeLessThanOrEqual(cols)
    await ui.unmount()
  }
})

test('heading row: three counts at 47 columns put the Done button under the heading; without done items there is no button', async ($, on) => {
  const w = await boot($, on, snap([ans(1), rd(1), wt(1), ...done3]))
  const ui = await $.ui.mount(pane('terminal', 47, TALL))
  expect(top(await ui.drawn())).toEqual({ text: 'Inbox · 1 answer · 1 read · 1 waiting\n[ Done (3) (d) ]', rows: 2 })
  await ui.unmount()
  w.current = snap([ans(1), rd(1)])
  await $.session.start(START)
  const none = await $.ui.mount(pane('terminal', 47, TALL))
  expect(top(await none.drawn())).toEqual({ text: 'Inbox · 1 to answer · 1 to read', rows: 1 })
  expect((await buttons(none)).filter((b: any) => b.key === 'done')).toEqual([])
})

test('empty list with done items: the heading row still carries the Done button; the empty text stays', async ($, on) => {
  await boot($, on, snap(done3))
  const ui = await $.ui.mount(pane('terminal', 80, SHORT))
  expect(top(await ui.drawn()).text).toBe('Inbox  [ Done (3) (d) ]')
  expect(await dump(ui)).toContain('Nothing waits on you.')
})

test('short tier: the waiting group keeps its sub-row and carries no age on the row', async ($, on) => {
  await boot($, on, snap([wt(1)]))
  const ui = await $.ui.mount(pane('terminal', 80, SHORT))
  const [b] = await rowButtons(ui)
  expect(b.text).toMatch(/E51 {2}answered {2}Waiting 1$/)
  expect(lines(await ui.drawn())).toContain('    (your answer sent 2026-10-15 10:42)')
})

test('short tier: a missing age leaves the title the whole width; 10+ rows keep three spaces and no digit', async ($, on) => {
  await boot($, on, snap([ans(1, { created: 'garbage', title: 'T'.repeat(200) }), ...many(11, (i) => ans(i + 1))]))
  const ui = await $.ui.mount(pane('terminal', 60, SHORT))
  const [first] = await rowButtons(ui)
  expect(3 + cellWidth(first.text)).toBe(60)
  expect(first.text.endsWith('…')).toBe(true)
  await ui.press((await moreOf(ui))[0])
  const tenth = (await rowButtons(ui))[9]
  expect(tenth.props.hotkey).toBeUndefined()
  expect(tenth.text.startsWith('   ')).toBe(true)
})

for (const [name, title] of [['ascii', 'T'.repeat(300)], ['cjk', '日本語のとても長い質問のタイトルです'.repeat(6)], ['emoji', '🚀 launch '.repeat(30)]] as const) {
  test(`short tier ${name}: no row is wider than the pane at 80, 60, 47, 40 and 30 columns; the age stays`, async ($, on) => {
    await boot($, on, snap([ans(1, { title, created: '2026-10-15T04:00:00' }), rd(1, { title, created: '2026-10-15T11:57:00' })]))
    for (const cols of [80, 60, 47, 40, 30]) {
      const ui = await $.ui.mount(pane('terminal', cols, SHORT))
      for (const b of await rowButtons(ui)) {
        expect({ cols, w: 3 + cellWidth(b.text) <= cols }).toEqual({ cols, w: true })
        expect(b.text).toMatch(/(8h|3m)$/)
        expect(b.text).toContain('…')
      }
      await ui.unmount()
    }
  })
}

// --- the sanitiser (V-27) ----------------------------------------------------------------------

// eslint-disable-next-line no-control-regex
const BAD = /[\u0000-\u0008\u000b-\u001f\u007f-\u009f‪-‮⁦-⁩]/

test('sanitiser V-27: ESC, OSC and U+202E in title, blocks and an error row draw none, in the band and the list', async ($, on) => {
  const w = await boot($, on, snap([]))
  for (const bad of ['\u001b[31mred', '\u001b]0;x\u0007t', '‮evil']) {
    w.current = snap([ans(1, { title: `T${bad}`, blocks: `X${bad}` })], [{ file: `f${bad}`, row: 1, message: `m${bad}` }])
    await $.session.start(START)
    const ui = await $.ui.mount(pane('terminal', 80))
    const b = await $.ui.mount(band('terminal', 80))
    expect(BAD.test(await dump(ui))).toBe(false)
    expect(BAD.test(await dump(b))).toBe(false)
    expect(BAD.test(JSON.stringify(await ui.drawn()))).toBe(false)
    await ui.unmount()
    await b.unmount()
  }
})
