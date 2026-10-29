import { describe, expect, test } from 'claude-code/testing'

import {
  TONE, blocksTone, bodyBudget, capGroup, cellWidth, kindTone, outcomeTone, recommendedKey, clipCells, rowsFor, tableLayout,
} from './core'
import { clipRows, drawBody } from './draw'
import { parseBody } from './markup'
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
    ['check mark and warning sign stay 1 (the inbox glyphs)', '✓⚠', 2],
    ['emoji presentation: check, cross, star, hourglass, melting face', '✅❌⭐⌛🫠', 10],
    ['emoji presentation: low ranges', '\u231a\u23e9\u25fd\u2614\u2648\u267f\u2693\u26a1\u26aa\u26bd\u26c4\u26ce\u26d4\u26ea\u26f2\u26fa\u26fd', 34],
    ['emoji presentation: dingbats', '\u2705\u270a\u2728\u274c\u274e\u2753\u2757\u2795\u27b0\u27bf\u2b1b\u2b50\u2b55', 26],
    ['regional indicators and the 1FA70 block', '\u{1f1e6}\u{1fa70}\u{1faff}', 6],
    ['test tube', '🧪', 2],
    ['pinned: heart + VS16 is 1 + 0', '❤️', 1],
    ['pinned: ZWJ family is 2+2+2 plus two zero-width joiners (0)', '👨‍👩‍👧', 6],
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
  test('CJK counts two cells', () => {
    expect(rowsFor('漢字漢字漢', 10)).toBe(1)
    expect(rowsFor('漢字漢字漢字', 10)).toBe(2)
  })
  test('a wide char at the end of a row starts the next row', () => {
    expect(rowsFor('aaaa漢', 5)).toBe(2)
    expect(rowsFor('aaaa 漢', 5)).toBe(2)
    expect(rowsFor('漢漢a漢', 5)).toBe(2)
  })
  test('a wide char never splits across rows', () => {
    expect(rowsFor('漢'.repeat(10), 5)).toBe(5)
    expect(rowsFor('漢'.repeat(200), 31)).toBe(14)
    expect(rowsFor('漢'.repeat(3), 3)).toBe(3)
  })
  test('after a row filled to the full width the next row starts one cell in (QAB F1)', () => {
    expect(rowsFor('aaaa bb', 4)).toBe(2)
    expect(rowsFor('aaaa bbb', 4)).toBe(2)
    expect(rowsFor('aaaa bbbb', 4)).toBe(3)
    expect(rowsFor('aaaa bbbb', 5)).toBe(2)
    expect(rowsFor('a'.repeat(8), 4)).toBe(2)
    expect(rowsFor('a'.repeat(7), 4)).toBe(2)
    // real captures (qa-w-live/11b4b3d/hardwrap-40x40.txt, inner width 36): a broken token carries no space
    expect(rowsFor('a'.repeat(72), 36)).toBe(2)
    expect(rowsFor('b'.repeat(108), 36)).toBe(3)
    expect(rowsFor('漢字 漢字', 4)).toBe(3)
  })
  test('the two real titles whose first row is 36 cells: 3 rows uncut, 2 after clipRows (QAB F1)', () => {
    for (const t of ['inbox-visual: what should the visual mean in the terminal inbox for every kind of item', 'auth: do we accept the legacy tokens during the migration window for internal tools?']) {
      expect(rowsFor(t, 36)).toBe(3)
      const c = clipRows(t, 36, 2)
      expect(rowsFor(c, 36)).toBe(2)
      expect(c.endsWith('…')).toBe(true)
    }
  })
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
    // Independent reference: place one code point at a time. A word moves to the next row when it fits an empty
    // row but not the rest of this one; a longer word fills rows, a wide char that does not fit starts a new row.
    const width = (ch: string): number => cellWidth(ch)
    const reference = (text: string, cols: number): number => {
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
          while (j < chars.length && chars[j] !== ' ') ww += width(chars[j++])
          if (col + ww > cols && ww <= cols) { row++; col = 0 }
          for (; i < j; i++) {
            const cw = width(chars[i])
            if (col + cw > cols) { row++; col = 0 }
            col += cw
          }
        }
        rows += row
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
  test('floor defaults to 3', () => {
    expect(bodyBudget(10, 10)).toBe(3)
    expect(bodyBudget(5, 20)).toBe(3)
  })
  test('floor is an argument', () => {
    expect(bodyBudget(10, 10, 2)).toBe(2)
    expect(bodyBudget(10, 10, 5)).toBe(5)
    expect(bodyBudget(30, 10, 5)).toBe(20)
  })
  test('missing or NaN rows fall back to 20', () => {
    expect(bodyBudget(undefined, 5)).toBe(15)
    expect(bodyBudget(Number.NaN, 5)).toBe(15)
  })
})

describe('clipCells', () => {
  const SAMPLES = ['a'.repeat(300), '漢字'.repeat(150), '😀'.repeat(150), '漢a😀'.repeat(80)]
  for (const cols of [30, 40]) {
    for (const s of SAMPLES) {
      test(`clipCells ${cols} cols of ${s.slice(0, 4)}…`, () => {
        const c = clipCells(s, cols)
        expect(cellWidth(c)).toBeLessThanOrEqual(cols)
        expect(c.endsWith('…')).toBe(true)
      })
    }
  }
  test('a wide char at the cut is dropped whole', () => expect(clipCells('漢字漢', 4)).toBe('漢…'))
  test('exact fit has no ellipsis', () => {
    expect(clipCells('a'.repeat(30), 30)).toBe('a'.repeat(30))
    expect(clipCells('漢'.repeat(15), 30)).toBe('漢'.repeat(15))
  })
  test('one over is cut', () => expect(clipCells('a'.repeat(31), 30)).toBe(`${'a'.repeat(29)}…`))
  test('cols < 1 is empty', () => {
    expect(clipCells('abc', 0)).toBe('')
    expect(clipCells('abc', -3)).toBe('')
  })
})

describe('tones (V-15)', () => {
  test('kindTone', () => {
    expect(kindTone({ kind: 'answer', state: 'open' })).toBe('warn')
    expect(kindTone({ kind: 'read', state: 'open' })).toBe('none')
  })
  test('kindTone: only an open answer item is amber, over every kind/state in the contract fixtures', () => {
    const seen = new Set<string>()
    for (const text of Object.values(FIXTURES)) {
      for (const it of JSON.parse(text).items) {
        seen.add(`${it.kind}/${it.state}`)
        expect(kindTone(it)).toBe(it.kind === 'answer' && it.state === 'open' ? 'warn' : 'none')
      }
    }
    for (const k of ['answer/open', 'answer/answered-waiting', 'answer/done', 'read/open']) expect(seen.has(k)).toBe(true)
    expect(kindTone({ kind: 'answer', state: 'answered-waiting' })).toBe('none')
    expect(kindTone({ kind: 'answer', state: 'done' })).toBe('none')
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

describe('[rec] indent (QAB F2): counted and clipped with the indent', () => {
  const T = { Box: 'Box', Text: 'Text', Button: 'Button' }
  const plan = { expanded: false, fitRows: 5, budget: 5 }
  test('an indent that pushes the line over a row boundary adds the row', () => {
    // '✓ recommended abcdef' is 20 cells: one row at 20 columns, two with 2 spaces in front
    expect(drawBody(parseBody('[rec] abcdef'), 20, T, plan).rows).toBe(1)
    expect(drawBody(parseBody('  [rec] abcdef'), 20, T, plan).rows).toBe(2)
  })
  test('the indent is capped at 8 spaces', () => {
    const text = (src: string) => JSON.stringify(drawBody(parseBody(src), 80, T, plan).nodes)
    expect(text(`${' '.repeat(12)}[rec] x`)).toContain(`"${' '.repeat(8)}"`)
    expect(text(`${' '.repeat(12)}[rec] x`)).not.toContain(`"${' '.repeat(9)}"`)
  })
  test('a rec line taller than the budget is clipped with its indent', () => {
    const d = drawBody(parseBody('    [rec] aaaa bbbb cccc dddd eeee'), 20, T, { expanded: false, fitRows: 0, budget: 1 })
    expect(d.nodes[0].children[0]).toBe('\u00a0\u00a0\u00a0\u00a0✓ recommended a…')
  })
})

describe('chips and headings (item.md section 5)', () => {
  const T = { Box: 'Box', Text: 'Text', Button: 'Button' }
  const plan = { expanded: false, fitRows: 50, budget: 50 }
  test('a code chip is exactly its text, no padding', () => {
    const d = drawBody(parseBody('merge `squad/x` into'), 80, T, plan)
    expect(JSON.stringify(d.nodes)).toContain('"squad/x"')
    expect(JSON.stringify(d.nodes)).not.toContain('" squad/x "')
  })
  test('a blank row above a heading in the tall tier only, never above the first block, counted in rows', () => {
    const body = parseBody('# One\na\n## Two\nb')
    const short = drawBody(body, 80, T, plan)
    const tall = drawBody(body, 80, T, { ...plan, tall: true })
    expect(short.rows).toBe(4)
    expect(tall.rows).toBe(5)
    expect(tall.nodes).toHaveLength(5)
  })
  test('hiddenRows counts the rows left, blank heading rows included', () => {
    const body = parseBody('# One\na\n## Two\nb\n## Three\nc')
    const d = drawBody(body, 80, T, { expanded: false, fitRows: 0, budget: 2, tall: true })
    expect(d.cut).toBe(true)
    expect(d.rows + d.hiddenRows).toBe(drawBody(body, 80, T, { expanded: true, fitRows: 0, budget: 0, tall: true }).rows)
  })
})
