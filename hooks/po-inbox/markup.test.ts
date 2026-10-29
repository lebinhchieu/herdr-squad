import { describe, expect, test } from 'claude-code/testing'

import { E1_OPTIONS, E1_REC, E1_TITLE, VISUAL } from './fixtures/visual'
import { type Block, bodyBlocks, itemTitle, parseBody, parseInline, plainOf } from './markup'

const types = (text: string) => parseBody(text).map((b) => b.type)
const first = (text: string): Block => parseBody(text)[0]
const spansOf = (b: Block) => ('spans' in b ? b.spans : [])

describe('must stay plain (V-05)', () => {
  for (const text of ['#1 priority', '2024-10-16', '1.5', '-5', '*italic*', '_x_', 'a ** b', 'a lone ** here', 'well-known', '-x no space', '#### four']) {
    test(`"${text}" is a plain paragraph, text unchanged`, () => {
      const blocks = parseBody(text)
      expect(blocks.length).toBe(1)
      expect(blocks[0].type).toBe('para')
      expect(plainOf(blocks)).toBe(text)
      expect(spansOf(blocks[0]).every((s) => s.kind === 'text')).toBe(true)
    })
  }
})

describe('recognised elements', () => {
  test('headings 1 to 3', () => {
    for (const level of [1, 2, 3] as const) {
      expect(first(`${'#'.repeat(level)} Title`)).toEqual({ type: 'heading', level, spans: [{ kind: 'text', text: 'Title' }] })
    }
  })

  test('bullets with - and *, nested bullets keep depth', () => {
    expect(first('- a')).toEqual({ type: 'bullet', depth: 0, spans: [{ kind: 'text', text: 'a' }] })
    expect(first('* a').type).toBe('bullet')
    const nested = parseBody('- a\n  - b\n    - c')
    expect(nested.map((b) => (b.type === 'bullet' ? b.depth : -1))).toEqual([0, 1, 2])
  })

  test('numbered list', () => {
    const b = parseBody('1. one\n2. two')
    expect(b).toEqual([
      { type: 'number', n: 1, depth: 0, spans: [{ kind: 'text', text: 'one' }] },
      { type: 'number', n: 2, depth: 0, spans: [{ kind: 'text', text: 'two' }] },
    ])
  })

  test('bold and code spans', () => {
    expect(parseInline('a **b** c `d` e')).toEqual([
      { kind: 'text', text: 'a ' },
      { kind: 'bold', text: 'b' },
      { kind: 'text', text: ' c ' },
      { kind: 'code', text: 'd' },
      { kind: 'text', text: ' e' },
    ])
  })

  test('an unclosed or empty bold or code stays literal', () => {
    expect(plainOf(parseBody('**a b'))).toBe('**a b')
    expect(plainOf(parseBody('`a b'))).toBe('`a b')
    expect(plainOf(parseBody('**** ``'))).toBe('**** ``')
    expect(plainOf(parseBody('** a **'))).toBe('** a **')
  })

  test('a fenced block with a closing fence', () => {
    const b = parseBody('x\n```ts\nconst a = 1\n  - not a bullet\n```\ny')
    expect(b.map((x) => x.type)).toEqual(['para', 'code', 'para'])
    expect(b[1]).toEqual({ type: 'code', lang: 'ts', lines: ['const a = 1', '  - not a bullet'] })
  })

  test('a fenced block without a closing fence runs to the end', () => {
    const b = parseBody('x\n```\nlast\n- also code')
    expect(b[1]).toEqual({ type: 'code', lang: '', lines: ['last', '- also code'] })
    expect(b.length).toBe(2)
  })

  test('a pipe table: header, separator, rows', () => {
    const b = first('| A | B |\n|---|:--:|\n| 1 | **2** |\n| 3 | 4 |')
    expect(b.type).toBe('table')
    if (b.type !== 'table') return
    expect(b.header.map((c) => c[0].text)).toEqual(['A', 'B'])
    expect(b.rows.length).toBe(2)
    expect(b.rows[0][1]).toEqual([{ kind: 'bold', text: '2' }])
    expect(plainOf([b])).toBe('A B\n1 2\n3 4')
  })

  test('a table with a malformed separator is paragraphs', () => {
    for (const sep of ['|--x|---|', '| a | b |', '|---|', '|---|---|---|', '']) {
      const text = `| A | B |\n${sep}\n| 1 | 2 |`
      expect(types(text).every((t) => t === 'para' || t === 'blank')).toBe(true)
      expect(plainOf(parseBody(text))).toBe(text)
    }
  })

  test('[rec] with leading spaces is a rec block; the tag itself is not kept', () => {
    expect(first('[rec] take (a)')).toEqual({ type: 'rec', spans: [{ kind: 'text', text: 'take (a)' }] })
    expect(first('   [rec] yes').type).toBe('rec')
    expect(first('   [rec] yes')).toEqual({ type: 'rec', spans: [{ kind: 'text', text: 'yes' }], indent: 3 })
    expect(first('[rec]').type).toBe('rec')
  })

  test('[REC], mid-line [rec] and [rec]x stay literal', () => {
    for (const text of ['[REC] yes', 'see [rec] yes', '[rec]x yes']) {
      expect(types(text).includes('rec')).toBe(false)
      expect(plainOf(parseBody(text))).toBe(text)
    }
    expect(types('- [rec] in a bullet')).toEqual(['bullet'])
  })

  test('<br> is a line break', () => {
    expect(types('a<br>b<BR/>c')).toEqual(['para', 'para', 'para'])
  })
})

// --- never drop (V-07) --------------------------------------------------------------------------------------
// Oracle, independent of the parser: the alphanumeric words (/[\p{L}\p{N}]+/gu) of the source, in order (`<br>` and
// \r\n are line breaks), minus only (1) the `rec` of a line whose first text is `[rec]` + space or end, and (2) the
// digits of a line-start `N. ` list marker with text after it; neither is looked for inside a fenced block (a fence
// opens on a line starting ``` or ~~~ and closes on a line of only that character). Compared in order with the
// alphanumeric words of plainOf(parseBody(source)): a set or a count compare would not catch a reorder.
const WORD = /[\p{L}\p{N}]+/gu
const words = (text: string) => text.match(WORD) ?? []
function oracle(source: string): string[] {
  const out: string[] = []
  let fence: string | null = null
  for (const raw of source.replace(/<br\s*\/?>/gi, '\n').split(/\r\n|\r|\n/)) {
    const t = raw.trim()
    let line = raw
    if (fence !== null) {
      if (t.length >= 3 && t.split(fence).join('') === '') fence = null
    } else if (t.startsWith('```') || t.startsWith('~~~')) {
      fence = t[0]
    } else if (/^\s*\[rec\](\s|$)/.test(raw)) {
      line = raw.replace('[rec]', ' ')
    } else {
      line = raw.replace(/^(\s*)\d{1,9}\.(\s+\S)/, '$1 $2')
    }
    out.push(...words(line))
  }
  return out
}

const wordsKept = (text: string) => {
  expect(words(plainOf(parseBody(text)))).toEqual(oracle(text))
}

describe('never drop a word', () => {
  for (const [name, text] of Object.entries(VISUAL)) {
    test(`fixture ${name}`, () => wordsKept(text))
  }

  test('the oracle is not vacuous: it sees words of a known body', () => {
    expect(oracle('1. one<br>[rec] two\n```\n[rec] 3. three\n```')).toEqual(['one', 'two', 'rec', '3', 'three'])
  })

  test('200 seeded random strings', () => {
    let seed = 20261016
    const rnd = (n: number) => {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
      return seed % n
    }
    const pieces = ['#', '##', '-', '*', '1.', '**', '`', '```', '~~~', '|', '|---|', '[rec]', '<br>', ' ', '\t', ' '.repeat(20), '\r\n', '\n', '\n', 'alpha', 'beta', '日本語', '状態', '🚀', 'x']
    for (let k = 0; k < 200; k++) {
      let text = ''
      const n = 1 + rnd(30)
      for (let j = 0; j < n; j++) text += pieces[rnd(pieces.length)] + (rnd(3) === 0 ? '' : ' ')
      wordsKept(text)
    }
  })
})

describe('totality edges', () => {
  test('empty, newline-only and space-only bodies give blanks and plain text ""', () => {
    expect(parseBody('')).toEqual([{ type: 'blank' }])
    expect(parseBody('\n')).toEqual([{ type: 'blank' }, { type: 'blank' }])
    expect(parseBody('   ')).toEqual([{ type: 'blank' }])
    for (const t of ['', '\n', '   ']) expect(plainOf(parseBody(t)).trim()).toBe('')
  })
})

describe('table edges', () => {
  const cells = (b: Block) => (b.type === 'table' ? [b.header.length, ...b.rows.map((r) => r.length)] : [])

  test('ragged rows keep every cell', () => {
    const b = first('| A | B |\n|---|---|\n| 1 |\n| 1 | 2 | 3 |')
    expect(cells(b)).toEqual([2, 1, 3])
    wordsKept('| A | B |\n|---|---|\n| 1 |\n| 1 | 2 | 3 |')
  })

  test('one column, empty cells, no trailing pipe, alignment colons', () => {
    expect(cells(first('| A |\n|---|\n| 1 |'))).toEqual([1, 1])
    expect(cells(first('| A | B |\n|---|---|\n|  | x |'))).toEqual([2, 2])
    expect(cells(first('A | B\n--|--\n1 | 2'))).toEqual([2, 2])
    expect(cells(first('| A | B | C |\n|:---|:---:|---:|\n| 1 | 2 | 3 |'))).toEqual([3, 3])
  })

  test('a table right after a paragraph, with no blank line', () => {
    expect(types('intro\n| A |\n|---|\n| 1 |')).toEqual(['para', 'table'])
  })

  test('an escaped pipe splits the cell (decision: no escape handling); no word is lost', () => {
    const text = '| A | B |\n|---|---|\n| a\\|b | c |'
    expect(cells(first(text))).toEqual([2, 3])
    wordsKept(text)
  })

  test('a table ends at the first line without a pipe', () => {
    expect(types('| A |\n|---|\n| 1 |\nafter')).toEqual(['table', 'para'])
  })
})

describe('fence edges', () => {
  test('info string is kept as lang; ~~~ fences; an indented fence', () => {
    expect(first('```ts\nx\n```')).toEqual({ type: 'code', lang: 'ts', lines: ['x'] })
    expect(first('~~~\nx\n~~~')).toEqual({ type: 'code', lang: '', lines: ['x'] })
    expect(first('   ```\nx\n   ```')).toEqual({ type: 'code', lang: '', lines: ['x'] })
  })

  test('a ~~~ fence is not closed by ```', () => {
    expect(first('~~~\na\n```\nb\n~~~')).toEqual({ type: 'code', lang: '', lines: ['a', '```', 'b'] })
  })

  test('a fence inside a bullet is not a fence (decision: a bullet whose text starts with backticks); no word lost', () => {
    const text = '- ```ts\nx\n```'
    expect(types(text)[0]).toBe('bullet')
    wordsKept(text)
  })

  test('[rec], # and ** inside a fence stay literal', () => {
    const b = first('```\n[rec] yes\n# not a heading\n**not bold**\n```')
    expect(b).toEqual({ type: 'code', lang: '', lines: ['[rec] yes', '# not a heading', '**not bold**'] })
  })

  test('text after a would-be closing fence is code, not dropped', () => {
    expect(first('```\na\n``` tail\nb\n```')).toEqual({ type: 'code', lang: '', lines: ['a', '``` tail', 'b'] })
  })
})

describe('bodyBlocks (T2: sanitize, <br>, drop the title line, parse)', () => {
  test('<br> in the E2 shape and <BR/> are line breaks', () => {
    expect(bodyBlocks('a<br>b<BR/>c<br />d', 'zzz').length).toBe(4)
    const b = bodyBlocks(VISUAL.e2, 'unrelated')
    expect(b.filter((x) => x.type === 'rec').length).toBe(7)
  })

  test('the first line equal to the title is dropped', () => {
    expect(plainOf(bodyBlocks('My title<br>rest', 'My title'))).toBe('rest')
    expect(plainOf(bodyBlocks('  My title  \nrest', 'My title'))).toBe('rest')
  })

  test('only the first of two title lines is dropped', () => {
    expect(plainOf(bodyBlocks('T\nT\nrest', 'T'))).toBe('T\nrest')
  })

  test('a body equal to the title gives no blocks and does not crash', () => {
    expect(bodyBlocks(E1_TITLE, E1_TITLE)).toEqual([])
    expect(bodyBlocks('', '')).toEqual([])
    expect(() => bodyBlocks('', 'title')).not.toThrow()
  })

  test('real E1: its first line is its title', () => {
    expect(plainOf(bodyBlocks(VISUAL.e1, E1_TITLE)).startsWith('Brief:')).toBe(true)
  })

  test('\\r\\n is one line break, and ESC, OSC and U+202E never reach the blocks', () => {
    expect(types('a\r\nb')).toEqual(['para', 'para'])
    expect(bodyBlocks('T\r\nx\r\ny', 'T').length).toBe(2)
    for (const name of ['esc', 'osc', 'rlo']) {
      const out = plainOf(bodyBlocks(VISUAL[name], 'zzz'))
      expect(out).not.toContain('\u001b')
      expect(out).not.toContain('\u0007')
    }
  })
})

// --- never throws, linear (V-28) -----------------------------------------------------------------------------
const timed = (text: string) => {
  const t0 = Date.now()
  const blocks = parseBody(text)
  const plain = plainOf(blocks)
  return { ms: Date.now() - t0, blocks, plain }
}

describe('linear', () => {
  const killers: Record<string, string> = {
    'one 10,000-character line': 'word '.repeat(2000),
    'one 10,000-character word': 'a'.repeat(10000),
    '5,000 **': '**'.repeat(5000),
    '5,000 unclosed **a openers': '**a '.repeat(5000),
    '5,000 **a**b pairs': '**a**b'.repeat(5000),
    '5,000 backticks': '`'.repeat(5000),
    '5,000 spaced backticks': 'a ` '.repeat(2500),
    'alternating ` and *': '`*'.repeat(5000),
    '10,000 pipes on one line': '|'.repeat(10000),
    '2,000 table rows': '| a | b |\n|---|---|\n' + '| 1 | 2 |\n'.repeat(2000),
    '2,000 rows x 20 cells': `${Array(20).fill('h').join(' | ')}\n${Array(20).fill('---').join('|')}\n` + `${Array(20).fill('c').join(' | ')}\n`.repeat(2000),
    'unclosed fence of 5,000 lines': '```\n' + 'line\n'.repeat(5000),
    'bullets nested to depth 2,500': Array.from({ length: 500 }, (_, i) => ' '.repeat(i * 10) + '- x').join('\n'),
    '10,000 <br>': '<br>'.repeat(10000),
    '2,000 headings and bullets': '# h\n- b\n'.repeat(1000),
  }
  for (const [name, text] of Object.entries(killers)) {
    test(`${name}: under 200 ms, words kept`, () => {
      const r = timed(text)
      expect(r.ms).toBeLessThan(200)
      expect(words(r.plain)).toEqual(oracle(text))
    })
  }

  test('4x the input takes under 12x the time (+20 ms) for bold, code and pipe cases', () => {
    for (const unit of ['**a ', '**a**b', '`a ', 'a ` ', '`*', '| a ']) {
      const small = timed(unit.repeat(20000)).ms
      const big = timed(unit.repeat(80000)).ms
      expect(big).toBeLessThan(12 * small + 20)
    }
  })

  test('a far-away opener of the other kind is not searched for again at every span', () => {
    const build = (n: number) => '**a**b'.repeat(n) + ' `x`'
    const small = timed(build(40000)).ms
    const big = timed(build(160000)).ms
    expect(big).toBeLessThan(12 * small + 20)
    const rev = (n: number) => '`a`b'.repeat(n) + ' **x**'
    expect(timed(rev(160000)).ms).toBeLessThan(12 * timed(rev(40000)).ms + 20)
  })

  test('hostile fixtures all parse', () => {
    for (const text of Object.values(VISUAL)) expect(() => parseBody(text)).not.toThrow()
    expect(types('|')).toEqual(['para'])
  })
})

describe('real samples', () => {
  test('E1 and E2 are byte copies: known substrings', () => {
    expect(E1_REC).toContain('(c), built (a) first')
    expect(E1_OPTIONS.startsWith('(a) Attached page')).toBe(true)
    expect(VISUAL.e1).toContain('1. Size M (BA, Tech Lead, both QAs')
    expect(VISUAL.e1.startsWith(E1_TITLE + '<br>Brief: ')).toBe(true)
    expect(VISUAL.e2).toContain('<br>   [rec] ')
    expect(VISUAL.e2).toContain('<br>1. Which screens change?<br>   [rec] the item screen')
  })

  test('E1: numbered items, three of them stay numbers, no raw syntax left on them', () => {
    const b = parseBody(VISUAL.e1)
    expect(b.filter((x) => x.type === 'number').map((x) => (x.type === 'number' ? x.n : 0))).toEqual([1, 2, 3])
  })

  test('E2: E2 has seven [rec] lines, tags removed from the text', () => {
    const b = parseBody(VISUAL.e2)
    expect(b.filter((x) => x.type === 'rec').length).toBe(7)
    expect(plainOf(b).split('\n').some((l) => l.trim().startsWith('[rec]'))).toBe(false)
  })

  test('the real escalations table parses to a table', () => {
    expect(types(VISUAL.escalationsTable)).toContain('table')
  })

  test('a body equal to the title is one paragraph with the title', () => {
    expect(plainOf(parseBody(VISUAL.titleOnly))).toBe(E1_TITLE)
  })

  test('the structured fixture holds every element', () => {
    const seen = new Set(types(VISUAL.structured))
    for (const t of ['heading', 'bullet', 'number', 'code', 'table', 'rec', 'para', 'blank']) expect(seen.has(t as Block['type'])).toBe(true)
  })
})

describe('fence close and number width', () => {
  for (const ch of ['`', '~']) {
    test(`a 1- or 2-char line of ${ch} inside a ${ch.repeat(3)} fence stays code`, () => {
      const b = parseBody([ch.repeat(3), 'a', ch, 'b', ch.repeat(2), 'c', ch.repeat(3), 'after'].join('\n'))
      expect(b[0]).toEqual({ type: 'code', lang: '', lines: ['a', ch, 'b', ch.repeat(2), 'c'] })
      expect(b[1].type).toBe('para')
    })
  }

  test('multi-digit numbers keep n as written; ten digits is plain text', () => {
    expect(first('10. x')).toMatchObject({ type: 'number', n: 10 })
    expect(first('123456789. x')).toMatchObject({ type: 'number', n: 123456789 })
    const b = parseBody('1234567890. x')
    expect(b.length).toBe(1)
    expect(b[0].type).toBe('para')
    expect(plainOf(b)).toBe('1234567890. x')
  })
})

describe('title rule P6: an 80-character stored title is the cut of the first body line', () => {
  const full = 'Which branch merges first for BRD-02 through BRD-06 after BRD-01 passes both QAs and the PO review today?'
  const cut = full.slice(0, 80)
  test('the first body line becomes the title and leaves the body', () => {
    expect(cut.length).toBe(80)
    expect(itemTitle(`${full}\nrest`, cut)).toBe(full)
    expect(plainOf(bodyBlocks(`${full}\nrest`, cut))).toBe('rest')
  })
  test('a shorter title equal to the first line keeps the old behaviour', () => {
    expect(itemTitle('My title\nrest', 'My title')).toBe('My title')
    expect(plainOf(bodyBlocks('My title\nrest', 'My title'))).toBe('rest')
  })
  test('an 80-char title whose body line does not start with it is untouched', () => {
    expect(itemTitle(`other ${full}\nrest`, cut)).toBe(cut)
    expect(plainOf(bodyBlocks(`other ${full}\nrest`, cut)).startsWith('other')).toBe(true)
  })
  test('a body that is only that line gives no body', () => {
    expect(itemTitle(full, cut)).toBe(full)
    expect(bodyBlocks(full, cut)).toEqual([])
  })
  test('a CRLF body works; a leading blank line does not match', () => {
    expect(itemTitle(`${full}\r\nrest`, cut)).toBe(full)
    expect(plainOf(bodyBlocks(`${full}\r\nrest`, cut))).toBe('rest')
    expect(itemTitle(`\n${full}\nrest`, cut)).toBe(cut)
  })
})

describe('P6 title cut at 80 characters', () => {
  const q = 'Shall we ship the new inbox pane to every manager before Friday at noon, or wait for QA first?'
  const lines = (b: string, t: string) => plainOf(bodyBlocks(b, t))
  test('a cut mid-word: the full first line is the title and leaves the body', () => {
    const t = q.slice(0, 80)
    expect(itemTitle(`${q}\nMore detail.`, t)).toBe(q)
    expect(lines(`${q}\nMore detail.`, t)).toBe('More detail.')
  })
  test('a cut that ends in a space (79 chars once trimmed) still matches', () => {
    const sp = 'Shall we ship the new inbox pane to every manager before Friday at noon, or '
    const full = `${sp}${'x'.repeat(1)} wait for QA first, please answer today`
    const t = `${sp}x `.padEnd(80, ' ').slice(0, 80)
    expect(t.length).toBe(80)
    expect(t.endsWith(' ')).toBe(true)
    expect(itemTitle(`${full}\nMore detail.`, t)).toBe(full)
    expect(lines(`${full}\nMore detail.`, t)).toBe('More detail.')
  })
  test('a short title that only starts the first line is left alone', () => {
    expect(itemTitle('Deploy note for you\nx', 'Deploy')).toBe('Deploy')
    expect(lines('Deploy note for you\nx', 'Deploy')).toBe('Deploy note for you\nx')
  })
})
