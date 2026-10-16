import { describe, expect, test } from 'claude-code/testing'

import {
  TONE, blocksTone, bodyBudget, capGroup, cellWidth, kindTone, outcomeTone, recommendedKey, rowsFor, tableLayout,
} from './core'
import { FIXTURES } from './fixtures'

const ABC = [{ key: 'a' }, { key: 'b' }, { key: 'c' }]

describe('TONE', () => {
  test('theme keys', () => expect(TONE).toEqual({ good: 'success', bad: 'error', warn: 'warning' }))
})

describe('recommendedKey (V-11 table, expected values written out)', () => {
  const rows: [string, string | null][] = [
    ['(c), built (a) first: the long reason', 'c'],
    ['(c) yes', 'c'],
    ['  (c) yes', 'c'],
    ['\t(c) yes', 'c'],
    [' (c) yes', 'c'],
    ['(a) no, (b) is worse', 'a'],
    ['(C) yes', null],
    ['c) yes', null],
    ['Option c', null],
    ['c. yes', null],
    ['(a)+(b)', null],
    ['(a)/(b)', null],
    ['(a) / (b)', null],
    ['(a), (b)', null],
    ['(a),(b)', null],
    ['(a) and (b)', null],
    ['(a) AND (b)', null],
    ['(a) or (b)', null],
    ['(a)and(b)', null],
    ['(a)', 'a'],
    ['(a)text', 'a'],
    ['(b) yes (a) no', 'b'],
    ['(z) yes', null],
    ["Reply 'all recs' to take every recommendation", null],
    ['', null],
  ]
  for (const [rec, want] of rows) test(JSON.stringify(rec), () => expect(recommendedKey(rec, ABC)).toBe(want))
  test('(c) with options [a,b] is none', () => expect(recommendedKey('(c) yes', [{ key: 'a' }, { key: 'b' }])).toBeNull())
  test('(a) with options null is none', () => expect(recommendedKey('(a) yes', null)).toBeNull())
  test('(a) with options [] is none', () => expect(recommendedKey('(a) yes', [])).toBeNull())
  test('duplicate option keys is none', () => expect(recommendedKey('(a) yes', [{ key: 'a' }, { key: 'a' }])).toBeNull())
  test('rec null is none', () => expect(recommendedKey(null, ABC)).toBeNull())
})

describe('cellWidth', () => {
  const cases: [string, string, number][] = [
    ['ascii', 'abc', 3],
    ['empty', '', 0],
    ['cjk', '漢字', 4],
    ['hangul', '한', 2],
    ['ideographic comma', '、', 2],
    ['fullwidth A', 'Ａ', 2],
    ['emoji is one code point', '😀', 2],
    ['astral plus combining mark', '😀́', 2],
    ['combining accent', 'é', 1],
    ['zero-width space', 'a​b', 2],
    ['pinned: heart + VS16 is 1 + 0', '❤️', 1],
    ['pinned: ZWJ family is 2+2+2+2+2 (ZWJ 0)', '👨‍👩‍👧', 6],
  ]
  for (const [name, s, w] of cases) test(name, () => expect(cellWidth(s)).toBe(w))
})

describe('rowsFor', () => {
  test('empty is one row', () => expect(rowsFor('', 10)).toBe(1))
  test('exact fit is one row', () => expect(rowsFor('abcdefghij', 10)).toBe(1))
  test('one over is two', () => expect(rowsFor('abcdefghijk', 10)).toBe(2))
  test('words wrap on spaces', () => expect(rowsFor('aaaa bbbb', 5)).toBe(2))
  test('word fits with its space exactly', () => expect(rowsFor('aaaa bbbb', 9)).toBe(1))
  test('a long word is hard-wrapped', () => expect(rowsFor('a'.repeat(25), 10)).toBe(3))
  test('embedded newlines count per line, empty lines are one row', () => expect(rowsFor('a\n\nb', 10)).toBe(3))
  test('CJK counts two cells', () => expect(rowsFor('漢字漢字漢', 10)).toBe(1) && expect(rowsFor('漢字漢字漢字', 10)).toBe(2))
  test('leading and repeated spaces never shrink the count', () => expect(rowsFor('   a    b', 4)).toBeGreaterThan(1))
  test('cols 0 and negative do not hang', () => {
    expect(rowsFor('ab', 0)).toBe(2)
    expect(rowsFor('ab', -5)).toBe(2)
  })

  // 2.2b: never fewer rows than a reference greedy wrap (rounds up when unsure).
  test('is never smaller than a reference wrap (300 seeded strings, cols 30..100)', () => {
    let seed = 12345
    const rnd = (n: number) => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff), seed % n)
    const alpha = ['a', 'b', 'c', ' ', ' ', ' ', '漢', '字', '😀', '\n', 'x', 'y']
    const reference = (text: string, cols: number): number => {
      let rows = 0
      for (const line of text.split('\n')) {
        let used = 0
        let r = 1
        for (const word of line.split(' ')) {
          const w = [...word].reduce((n, ch) => n + (cellWidth(ch)), 0)
          if (used === 0) used = 0
          else if (used + 1 + w <= cols) { used += 1 + w; continue } else { r++; used = 0 }
          let left = w
          while (left > cols) { r++; left -= cols }
          used = left
        }
        rows += r
      }
      return rows
    }
    for (let i = 0; i < 300; i++) {
      let s = ''
      for (let j = rnd(200); j > 0; j--) s += alpha[rnd(alpha.length)]
      const cols = 30 + rnd(71)
      expect(rowsFor(s, cols)).toBeGreaterThanOrEqual(reference(s, cols))
    }
  })
})

describe('tableLayout', () => {
  // Formula under test: aligned total = sum(widest cell per column) + 2 * (columns - 1); aligned when cols >= 60 and total <= cols.
  const words = (v: unknown) => JSON.stringify(v).match(/[\p{L}\p{N}]+/gu) ?? []
  const T = { header: ['name', 'state'], rows: [['alpha', 'ok'], ['beta', 'blocked']] }
  for (const cols of [80, 60]) test(`aligned at ${cols}`, () => expect(tableLayout(T, cols).kind).toBe('aligned'))
  for (const cols of [59, 40, 30]) test(`stacked at ${cols}`, () => expect(tableLayout(T, cols).kind).toBe('stacked'))
  test('aligned widths are the widest cell per column', () => {
    expect(tableLayout(T, 80)).toEqual({ kind: 'aligned', widths: [5, 7] })
  })
  test('exactly fits and one over at 60', () => {
    const fit = { header: ['a', 'b'], rows: [['x'.repeat(29), 'y'.repeat(29)]] } // 29 + 2 + 29 = 60
    const over = { header: ['a', 'b'], rows: [['x'.repeat(30), 'y'.repeat(29)]] }
    expect(tableLayout(fit, 60).kind).toBe('aligned')
    expect(tableLayout(over, 60).kind).toBe('stacked')
  })
  test('CJK and emoji cells use cell widths', () => {
    const wide = { header: ['名前', '状態'], rows: [['漢字漢字', '😀😀']] }
    expect(tableLayout(wide, 80)).toEqual({ kind: 'aligned', widths: [8, 4] })
    const tight = { header: ['a', 'b'], rows: [['漢'.repeat(15), '字'.repeat(15)]] } // 30 + 2 + 30 = 62
    expect(tableLayout(tight, 60).kind).toBe('stacked')
    expect(tableLayout(tight, 62).kind).toBe('aligned')
    for (const cols of [59, 40, 30]) expect(tableLayout(wide, cols).kind).toBe('stacked')
  })
  test('stacked keeps every cell once, in order', () => {
    const l = tableLayout(T, 40)
    if (l.kind !== 'stacked') throw new Error('expected stacked')
    expect(l.rows[0]).toEqual([{ column: 'name', value: 'alpha' }, { column: 'state', value: 'ok' }])
    expect(words(l.rows.map((r) => r.map((c) => c.value)))).toEqual(['alpha', 'ok', 'beta', 'blocked'])
  })
  test('ragged rows: short rows get empty cells, long rows get an empty column name', () => {
    const l = tableLayout({ header: ['a', 'b'], rows: [['1'], ['1', '2', '3']] }, 30)
    if (l.kind !== 'stacked') throw new Error('expected stacked')
    expect(l.rows[0]).toEqual([{ column: 'a', value: '1' }, { column: 'b', value: '' }, { column: '', value: '' }])
    expect(l.rows[1]).toEqual([{ column: 'a', value: '1' }, { column: 'b', value: '2' }, { column: '', value: '3' }])
  })
  test('one column, zero rows, empty cells', () => {
    expect(tableLayout({ header: ['only'], rows: [['x'], ['']] }, 80)).toEqual({ kind: 'aligned', widths: [4] })
    expect(tableLayout({ header: ['a', 'b'], rows: [] }, 80)).toEqual({ kind: 'aligned', widths: [1, 1] })
    expect(tableLayout({ header: ['a', 'b'], rows: [] }, 30).kind).toBe('stacked')
  })
})

describe('capGroup', () => {
  const mk = (n: number) => Array.from({ length: n }, (_, i) => i)
  const cases: [number, number, number][] = [[0, 0, 0], [7, 7, 0], [8, 7, 1], [9, 7, 2], [12, 7, 5]]
  for (const [n, shown, hidden] of cases) {
    test(`${n} items: ${shown} shown, +${hidden}`, () => {
      const items = mk(n)
      const r = capGroup(items, false)
      expect(r.shown).toEqual(items.slice(0, shown))
      expect(r.hidden).toBe(hidden)
    })
  }
  test('expanded shows all, in order', () => expect(capGroup(mk(12), true)).toEqual({ shown: mk(12), hidden: 0 }))
  test('returns new arrays, input untouched', () => {
    const items = mk(5)
    const r = capGroup(items, false)
    expect(r.shown).not.toBe(items)
    r.shown.push(99)
    expect(items).toEqual(mk(5))
  })
})

describe('bodyBudget', () => {
  test('rows minus chrome', () => expect(bodyBudget(24, 10)).toBe(14))
  test('floor of 2', () => {
    expect(bodyBudget(10, 10)).toBe(2)
    expect(bodyBudget(5, 20)).toBe(2)
  })
  test('missing or NaN rows fall back to 20', () => {
    expect(bodyBudget(undefined, 5)).toBe(15)
    expect(bodyBudget(Number.NaN, 5)).toBe(15)
  })
})

describe('tones (V-15)', () => {
  test('kindTone', () => {
    expect(kindTone({ kind: 'answer', state: 'open' })).toBe('warn')
    expect(kindTone({ kind: 'read', state: 'open' })).toBe('none')
  })
  const NOTHING = ['', 'nothing', 'none', '-', '—', ' Nothing ']
  for (const b of NOTHING) test(`blocks ${JSON.stringify(b)} is dim`, () => expect(blocksTone(b)).toBe('dim'))
  for (const b of ['PI-04', 'spawning the pod', 'nothing else']) test(`blocks ${b} is bad`, () => expect(blocksTone(b)).toBe('bad'))

  test('outcomeTone over every done kind in the real contract fixtures', () => {
    const want: Record<string, string> = { answered: 'good', 'answered-file': 'warn', read: 'dim', withdrawn: 'dim', removed: 'dim' }
    const seen = new Set<string>()
    for (const text of Object.values(FIXTURES)) {
      for (const it of JSON.parse(text).items) {
        if (it.state === 'answered-waiting') expect(outcomeTone(it)).toBe('warn')
        if (it.done) {
          seen.add(it.done.kind)
          expect(outcomeTone(it)).toBe(want[it.done.kind])
        }
      }
    }
    expect([...seen].sort()).toEqual(Object.keys(want).sort())
  })
  test('answered in chat (source chat) is good', () => {
    expect(outcomeTone({ state: 'done', done: { kind: 'answered' } })).toBe('good')
  })
  test('unknown kind and no outcome are none, never throw', () => {
    expect(outcomeTone({ state: 'done', done: { kind: 'zzz' } })).toBe('none')
    expect(outcomeTone({ state: 'open', done: null })).toBe('none')
  })
})
