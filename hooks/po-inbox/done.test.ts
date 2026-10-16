// IV-05: the done list: outcome colours (V-15), newest first, the 7-row fold, wrapped reasons, the sanitiser.
import { expect, test } from 'claude-code/testing'

import { cellWidth } from './core'
import { FIXTURES } from './fixtures'
import { boot, dump, item, lines, pane, snap, styleOf, textOf } from './testkit'

const ANS = { text: '(b) go', option: 'b', note: null, ts: '2026-10-15T10:42:00', source: 'pane', delivered_ts: null }
const stampOf = (i: number) => `2026-10-14T${String(i % 24).padStart(2, '0')}:${String(10 + (i % 40)).padStart(2, '0')}:00`
const dn = (i: number, kind = 'read', o: Record<string, unknown> = {}, reason: string | null = null) =>
  item({ id: `E${i}`, title: `Done ${i}`, state: 'done', answer: kind === 'answered' ? ANS : null, done: { kind, ts: stampOf(i), reason }, ...o })
const many = (n: number) => Array.from({ length: n }, (_, i) => dn(i + 1))

const buttons = async (ui: any) => (await ui.findAll({ type: 'Button' })) as any[]
const moreOf = async (ui: any) => (await buttons(ui)).filter((b) => /\+\d+ more/.test(b.text))
const rowIds = async (ui: any) => (await buttons(ui)).map((b) => /\b(E\d+)\b/.exec(b.text)?.[1]).filter(Boolean)

async function open($: any, on: any, items: any[], cols = 80) {
  await boot($, on, snap(items))
  const ui = await $.ui.mount(pane('terminal', cols))
  await ui.press({ key: 'done' })
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

test('answered in chat is green and ids, stamps are dim', async ($, on) => {
  const ui = await open($, on, [dn(1, 'answered', { answer: { ...ANS, source: 'chat' } })])
  const tree = await ui.drawn()
  expect(styleOf(tree, 'answered in chat')).toEqual({ color: 'success' })
  expect(styleOf(tree, 'E1')).toEqual({ dimColor: true })
  expect(styleOf(tree, '2026-10-14')).toEqual({ dimColor: true })
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
for (const cols of [80, 59, 40, 30]) {
  test(`a long withdrawn reason is wrapped whole, never dropped, at ${cols} columns`, async ($, on) => {
    const ui = await open($, on, [dn(1, 'withdrawn', {}, LONG)], cols)
    const ls = lines(await ui.drawn())
    const sub = ls.filter((l) => l.startsWith('    '))
    expect(sub.length).toBeGreaterThan(0)
    expect(sub.join(' ')).toContain('withdrawn:')
    expect(sub.map((l) => l.trim()).join(' ').replace(/\s+/g, ' ')).toContain(LONG)
    for (const l of sub) expect(cellWidth(l)).toBeLessThanOrEqual(cols)
    expect(styleOf(await ui.drawn(), 'withdrawn:')).toEqual({ dimColor: true })
  })
}

test('a 300-character CJK reason wraps; the word withdrawn stays', async ($, on) => {
  const cjk = '理由'.repeat(150)
  const ui = await open($, on, [dn(1, 'withdrawn', {}, cjk)], 40)
  const text = await dump(ui)
  expect(text).toContain('withdrawn')
  expect(text.split('\n').filter((l) => l.startsWith('    ')).every((l) => cellWidth(l) <= 40)).toBe(true)
  expect(text.replace(/\s/g, '')).toContain(cjk)
})

test('ESC, OSC and U+202E in title and reason draw none', async ($, on) => {
  const dirty = 'x\u001b]0;pwn\u0007y\u001b[31mz‮w'
  const ui = await open($, on, [dn(1, 'withdrawn', { title: dirty }, dirty)])
  const text = await dump(ui)
  expect(text).not.toMatch(/[\u001b‮\u0007]/)
  expect(text).toContain('withdrawn:')
  expect(textOf(await ui.drawn())).not.toMatch(/[\u001b‮]/)
})

// Row 1 is `n: ` (3 cells the engine draws), the Button text, then the title clipped with `…`.
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
      expect(btn.text.endsWith('…')).toBe(true)
      expect(3 + cellWidth(btn.text)).toBeLessThanOrEqual(cols)
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
