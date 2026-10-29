// IV-05: the done list: outcome colours (V-15), newest first, the 7-row fold, wrapped reasons, the sanitiser.
import { expect, test } from 'claude-code/testing'

import { cellWidth } from './core'
import { FIXTURES } from './fixtures'
import { START, boot, dump, item, lines, pane, snap, styleOf, textOf } from './testkit'

const ANS = { text: '(b) go', option: 'b', note: null, ts: '2026-10-15T10:42:00', source: 'pane', delivered_ts: null }
const stampOf = (i: number) => `2026-10-14T${String(i % 24).padStart(2, '0')}:${String(10 + (i % 40)).padStart(2, '0')}:00`
const dn = (i: number, kind = 'read', o: Record<string, unknown> = {}, reason: string | null = null) =>
  item({ id: `E${i}`, title: `Done ${i}`, state: 'done', answer: kind === 'answered' ? ANS : null, done: { kind, ts: stampOf(i), reason }, ...o })
const many = (n: number) => Array.from({ length: n }, (_, i) => dn(i + 1))

const buttons = async (ui: any) => (await ui.findAll({ type: 'Button' })) as any[]
const moreOf = async (ui: any) => (await buttons(ui)).filter((b) => /\+\d+ more/.test(b.text))
const rowIds = async (ui: any) => (await buttons(ui)).map((b) => /\b(E\d+)\b/.exec(b.text)?.[1]).filter(Boolean)

async function open($: any, on: any, items: any[], cols = 80, bodyRows = 20) {
  await boot($, on, snap(items))
  const ui = await $.ui.mount(pane('terminal', cols, bodyRows))
  await ui.press({ key: 'done' })
  return ui
}

// Another mount of the same booted pane: a new snapshot, a size; the Done list is opened if the list shows.
async function again($: any, w: any, items: any[], cols: number, bodyRows: number) {
  w.current = snap(items)
  await $.session.start(START)
  const ui = await $.ui.mount(pane('terminal', cols, bodyRows))
  if (await ui.find({ key: 'done' })) await ui.press({ key: 'done' })
  return ui
}

const FIXTURE_DONE = Object.values(FIXTURES).flatMap((t) => JSON.parse(t).items.filter((it: any) => it.done) as any[])
const TONE_OF: Record<string, Record<string, unknown>> = {
  answered: { color: 'success' }, 'answered-file': { color: 'warning' }, read: { dimColor: true }, withdrawn: { dimColor: true }, removed: { dimColor: true },
}

test('the contract fixtures hold every done kind', () => {
  expect([...new Set(FIXTURE_DONE.map((it) => it.done.kind))].sort()).toEqual(Object.keys(TONE_OF).sort())
})

FIXTURE_DONE.forEach((it, n) => {
  test(`outcome word colour: fixture done item ${n} (${it.done.kind})`, async ($, on) => {
    const ui = await open($, on, [{ ...it, id: 'E100' }])
    const word = it.done.kind === 'answered-file' ? 'answered in the file' : it.done.kind === 'answered' && it.answer?.source === 'chat' ? 'answered in chat' : it.done.kind
    expect(styleOf(await ui.drawn(), word)).toEqual(TONE_OF[it.done.kind])
  })
})

test('answered in chat is green and ids, ages are dim', async ($, on) => {
  const ui = await open($, on, [dn(1, 'answered', { answer: { ...ANS, source: 'chat' } })])
  const tree = await ui.drawn()
  expect(styleOf(tree, 'answered in chat')).toEqual({ color: 'success' })
  expect(styleOf(tree, 'E1')).toEqual({ dimColor: true })
  expect(styleOf(tree, '1d')).toEqual({ dimColor: true })
})

test('heading carries the total, dim; newest first, equal stamps keep their order', async ($, on) => {
  const same = { done: { kind: 'read', ts: '2026-10-15T09:00:00', reason: null } }
  const ui = await open($, on, [dn(1), dn(2, 'read', same), dn(3, 'read', same), dn(4, 'read', same), dn(5)])
  const tree = await ui.drawn()
  expect(await dump(ui)).toContain('Done · newest first (5)')
  expect(styleOf(tree, '(5)')).toEqual({ dimColor: true, bold: false })
  expect(await rowIds(ui)).toEqual(['E2', 'E3', 'E4', 'E5', 'E1'])
})

for (const [n, shown, more] of [[7, 7, []], [8, 7, ['+1 more']], [12, 7, ['+5 more']]] as const) {
  test(`fold edge: ${n} rows show ${shown}${more.length ? ` and ${more[0]}` : ' and no button'}`, async ($, on) => {
    const ui = await open($, on, many(n))
    expect(await rowIds(ui)).toHaveLength(shown)
    expect((await moreOf(ui)).map((b) => b.text.trim())).toEqual(more)
  })
}

test('+N more opens in place, is dim with no hotkey; digits stay on the first nine; leaving folds it again (T10)', async ($, on) => {
  const ui = await open($, on, many(12))
  const [m] = await moreOf(ui)
  expect(m.props.hotkey).toBeUndefined()
  expect(styleOf(await ui.drawn(), '+5 more')).toEqual({ dimColor: true })
  await ui.press(m)
  expect(await rowIds(ui)).toHaveLength(12)
  expect(await moreOf(ui)).toHaveLength(0)
  const hot = (await buttons(ui)).map((b: any) => b.props.hotkey).filter(Boolean)
  expect(hot).toEqual(['b', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
  const ids = await rowIds(ui)
  const tenth = (await buttons(ui)).find((b: any) => b.text.includes(ids[9] as string))
  expect(tenth.text.startsWith('   ')).toBe(true)
  await ui.press({ key: 'back' })
  await ui.press({ key: 'done' })
  expect(await rowIds(ui)).toHaveLength(7)
  expect((await moreOf(ui)).map((b) => b.text.trim())).toEqual(['+5 more'])
  await ui.press((await moreOf(ui))[0])
  await ui.press({ key: 'd-E12' })
  await ui.press({ key: 'back' })
  expect(await rowIds(ui)).toHaveLength(7)
})

const LONG = 'the PO answered it in chat before anybody read the question so this reason keeps going and going'
const SHORT_ROWS = 6 // a 24-row terminal
for (const cols of [80, 59, 40, 30]) {
  test(`tall tier: a long withdrawn reason is one clipped sub-row, dim, within ${cols} columns`, async ($, on) => {
    const ui = await open($, on, [dn(1, 'withdrawn', {}, LONG)], cols)
    const ls = lines(await ui.drawn())
    const sub = ls.filter((l) => l.startsWith('    '))
    expect(sub).toHaveLength(1)
    expect(sub[0].trim().startsWith('withdrawn: ')).toBe(true)
    expect(sub[0].endsWith('…')).toBe(true)
    expect(cellWidth(sub[0])).toBeLessThanOrEqual(cols)
    expect(styleOf(await ui.drawn(), 'withdrawn:')).toEqual({ dimColor: true })
  })
  test(`short tier: no sub-row at all (the reason is on the done item) at ${cols} columns`, async ($, on) => {
    const ui = await open($, on, [dn(1, 'withdrawn', {}, LONG), dn(2, 'answered'), dn(3)], cols, SHORT_ROWS)
    expect(lines(await ui.drawn()).filter((l) => l.startsWith('    '))).toEqual([])
    expect(await dump(ui)).not.toContain('withdrawn:')
  })
}

test('tall tier: only a withdrawn item with a reason gets a sub-row', async ($, on) => {
  const ui = await open($, on, [dn(1, 'withdrawn', {}, 'asked twice'), dn(2, 'withdrawn'), dn(3, 'answered'), dn(4)])
  expect(lines(await ui.drawn()).filter((l) => l.startsWith('    '))).toEqual(['    withdrawn: asked twice'])
})

test('a 300-character CJK reason is clipped to one sub-row; the word withdrawn stays', async ($, on) => {
  const cjk = '理由'.repeat(150)
  const ui = await open($, on, [dn(1, 'withdrawn', {}, cjk)], 40)
  const text = await dump(ui)
  expect(text).toContain('withdrawn')
  const sub = text.split('\n').filter((l) => l.startsWith('    '))
  expect(sub).toHaveLength(1)
  expect(cellWidth(sub[0])).toBeLessThanOrEqual(40)
  expect(sub[0].endsWith('…')).toBe(true)
})

test('ESC, OSC and U+202E in title and reason draw none', async ($, on) => {
  const dirty = 'x\u001b]0;pwn\u0007y\u001b[31mz‮w'
  const ui = await open($, on, [dn(1, 'withdrawn', { title: dirty }, dirty)])
  const text = await dump(ui)
  expect(text).not.toMatch(/[\u001b‮\u0007]/)
  expect(text).toContain('withdrawn:')
  expect(textOf(await ui.drawn())).not.toMatch(/[\u001b‮]/)
})

// Row 1 is `n: ` (3 cells the engine draws), the Button text, then the title clipped with `…` and the age at the right end.
// The design's floor of 10 title cells can push a row past `cols` only when id + outcome word are long;
// with `E1  read` it still fits at 30, so every width is asserted.
const TITLES: [string, string][] = [
  ['ASCII', 'a'.repeat(300)],
  ['CJK', '题目'.repeat(150)],
  ['emoji', '🙂x'.repeat(100)],
]
for (const cols of [80, 59, 40, 30]) {
  for (const [name, title] of TITLES) {
    test(`title clipping: ${name} title ends with … and row 1 fits ${cols} columns`, async ($, on) => {
      const ui = await open($, on, [dn(1, 'read', { title })], cols)
      const btn = (await buttons(ui)).find((b: any) => b.key === 'd-E1')
      expect(btn.text).toContain('…')
      expect(3 + cellWidth(btn.text)).toBeLessThanOrEqual(cols)
      expect(btn.text.endsWith('1d')).toBe(true)
    })
  }
}

test('hotkey 9 and the three-space lead: the ninth row has digit 9 and no lead, the tenth the lead and no digit', async ($, on) => {
  const ui = await open($, on, many(12))
  await ui.press((await moreOf(ui))[0])
  const rows = (await buttons(ui)).filter((b: any) => /^(   )?E\d+ /.test(b.text))
  expect(rows).toHaveLength(12)
  expect(rows[8].props.hotkey).toBe('9')
  expect(rows[8].text.startsWith('   ')).toBe(false)
  expect(rows[9].props.hotkey).toBeUndefined()
  expect(rows[9].text.startsWith('   ')).toBe(true)
})

test('an old atom without `more` draws the done list and expands without a crash', async ($, on) => {
  // every write of the ui atom drops `more`, as an atom saved before IV-04 has it
  on('state.set', (_$: any, e: any, next: any) => {
    if (e.key !== 'ui' || !e.value) return next(e)
    const { more: _drop, ...old } = e.value
    return next({ ...e, value: old })
  })
  const ui = await open($, on, many(9))
  expect(await dump(ui)).toContain('Done · newest first (9)')
  expect((await moreOf(ui)).map((b) => b.text.trim())).toEqual(['+2 more'])
  await ui.press((await moreOf(ui))[0])
  expect(await rowIds(ui)).toHaveLength(7)
})

// --- ticket 02: the Done list heading, the short age, the done item (done.md) -------------------------

// Row 1 as the engine draws it: texts joined, a Button as `[ label ]`.
function top(tree: any): { text: string; rows: number } {
  const root = Array.isArray(tree) ? tree[0] : tree
  const first = root.children[0]
  const side = (n: any): string =>
    Array.isArray(n) ? n.map(side).join('') : n && n.type === 'Button' ? `[ ${n.props?.label ?? textOf(n)} ]` : n && n.type === 'Box' ? (n.children ?? []).map(side).join('') : textOf(n)
  if (first.props?.flexDirection === 'column') return { text: first.children.map(side).join('\n'), rows: first.children.length }
  return { text: side(first.children), rows: 1 }
}

test('heading row: Back and `Done · newest first (N)` share row 1; narrow: the count goes, then the heading moves under Back', async ($, on) => {
  const want: Record<number, { text: string; rows: number }> = {
    80: { text: '[ ← Back (b) ]   Done · newest first (3)', rows: 1 },
    40: { text: '[ ← Back (b) ]   Done · newest first (3)', rows: 1 },
    39: { text: '[ ← Back (b) ]   Done · newest first', rows: 1 },
    36: { text: '[ ← Back (b) ]   Done · newest first', rows: 1 },
    35: { text: '[ ← Back (b) ]\nDone · newest first', rows: 2 },
    30: { text: '[ ← Back (b) ]\nDone · newest first', rows: 2 },
  }
  const w = await boot($, on, snap([dn(1), dn(2), dn(3)]))
  for (const cols of [80, 40, 39, 36, 35, 30]) {
    const ui = await again($, w, [dn(1), dn(2), dn(3)], cols, SHORT_ROWS)
    expect({ cols, ...top(await ui.drawn()) }).toEqual({ cols, ...want[cols] })
    await ui.unmount()
  }
})

test('short tier: 3 items take 4 rows (heading + 3), each row ends with the dim short age on the last cell', async ($, on) => {
  const items = [dn(1, 'withdrawn', {}, LONG), dn(2, 'answered', { answer: { ...ANS, source: 'chat' } }), dn(3)]
  const w = await boot($, on, snap(items))
  for (const cols of [80, 60, 47]) {
    const ui = await again($, w, items, cols, SHORT_ROWS)
    const ls = lines(await ui.drawn())
    expect(ls.filter((l) => l.startsWith('[') && /E\d/.test(l))).toHaveLength(3)
    expect(ls.filter((l) => !l.startsWith('[') && !l.startsWith('Done') && l.trim() !== '')).toEqual([])
    for (const b of await buttons(ui)) {
      if (!/^E\d/.test(b.text)) continue
      expect(3 + cellWidth(b.text)).toBe(cols)
      expect(b.text).toMatch(/ \d+[mhd]$/)
    }
    expect(styleOf(await ui.drawn(), '1d')).toEqual({ dimColor: true })
    await ui.unmount()
  }
})

test('a done row without a time has no age column and the title takes the width', async ($, on) => {
  const ui = await open($, on, [dn(1, 'read', { done: { kind: 'read', ts: 'garbage', reason: null }, title: 'T'.repeat(200) })], 60, SHORT_ROWS)
  const btn = (await buttons(ui)).find((b: any) => b.key === 'd-E1')
  expect(3 + cellWidth(btn.text)).toBe(60)
  expect(btn.text.endsWith('…')).toBe(true)
})

// The done item: the outcome line right under the title, in its colour, up to 4 rows (done.md section 3).
const OUT = 'Withdrawn by the Manager 2026-10-14 01:11: '
async function openItem($: any, w: any, it: any, cols: number, bodyRows: number) {
  const ui = await again($, w, [it], cols, bodyRows)
  await ui.press({ key: 'd-E1' })
  return ui
}
const rowText = (tree: any) => lines(tree).join('\n')

test('done item, 24 rows: the withdrawn reason is whole in the first viewport, right under the title', async ($, on) => {
  const reason = 'Superseded by E1, the Manager decided alone after the PO delegated.'
  const w = await boot($, on, snap([]))
  const ui = await openItem($, w, dn(1, 'withdrawn', {}, reason), 80, SHORT_ROWS)
  const ls = lines(await ui.drawn())
  const at = ls.findIndex((l) => l.startsWith('Withdrawn by the Manager'))
  expect(at).toBe(ls.findIndex((l) => l === 'Done 1') + 1)
  expect(ls.slice(at, at + 3).join(' ')).toContain(reason)
  expect(styleOf(await ui.drawn(), 'Withdrawn by the Manager')).toEqual({ dimColor: true })
})

test('done item: an outcome of more than 4 rows ends with … and a Details row; Details shows it whole', async ($, on) => {
  const long = 'x'.repeat(40) + (' word'.repeat(80))
  const w = await boot($, on, snap([]))
  for (const [cols, rows] of [[80, SHORT_ROWS], [47, SHORT_ROWS], [80, 11]] as const) {
    const ui = await openItem($, w, dn(1, 'withdrawn', {}, long), cols, rows)
    const decide = rowText(await ui.drawn())
    const outcome = decide.split('\n').filter((l) => l !== '')
    const at = outcome.findIndex((l) => l.startsWith('Withdrawn by the Manager'))
    expect(at).toBeGreaterThan(-1)
    expect(outcome.slice(at, at + 5).some((l) => l.endsWith('…'))).toBe(true)
    expect(decide).toContain('full text')
    expect(await ui.find({ key: 'details' })).toBeDefined()
    await ui.press({ key: 'details' })
    const page = rowText(await ui.drawn())
    expect(page).toContain(OUT)
    expect(page.replace(/\s+/g, ' ')).toContain(long.replace(/\s+/g, ' '))
    await ui.unmount()
  }
})

test('done item: a short outcome is never clipped and offers no `full text` row; answered kinds keep their tone', async ($, on) => {
  const w = await boot($, on, snap([]))
  const ui = await openItem($, w, dn(1, 'answered', { answer: { ...ANS, source: 'chat' } }), 40, SHORT_ROWS)
  const t = rowText(await ui.drawn())
  expect(t).toContain('Answered in chat')
  expect(t).not.toContain('full text')
  expect(styleOf(await ui.drawn(), 'Answered in chat')).toEqual({ color: 'success' })
})
