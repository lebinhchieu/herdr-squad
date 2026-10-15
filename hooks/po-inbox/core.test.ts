import { describe, expect, test } from 'claude-code/testing'

import { ageOf, describePrompt, fit, newOpenIds, oneLine, parseAdd, parseSnapshot, sanitize, stamp } from './core'
import { FIXTURES } from './fixtures'

const mixed = () => JSON.parse(FIXTURES['contract-provisional-mixed'])
const parse = (v: unknown) => parseSnapshot(JSON.stringify(v))

describe('parseSnapshot', () => {
  for (const [name, text] of Object.entries(FIXTURES)) {
    test(`accepts fixture ${name}`, () => {
      expect(parseSnapshot(text).ok).toBe(true)
    })
  }

  test('ignores unknown extra keys', () => {
    const m = mixed()
    m.future = 1
    m.items[0].extra = { a: 1 }
    expect(parse(m).ok).toBe(true)
  })

  test('rejects invalid JSON and a non-object', () => {
    expect(parseSnapshot('{nope').ok).toBe(false)
    expect(parseSnapshot('[]').ok).toBe(false)
  })

  test('rejects any other version', () => {
    for (const v of [2, 0, '1', null]) {
      const m = mixed()
      m.version = v
      const p = parse(m)
      expect(p.ok).toBe(false)
    }
    const m = mixed()
    delete m.version
    expect(parse(m).ok).toBe(false)
  })

  for (const key of ['items', 'counts', 'home', 'now', 'errors']) {
    test(`rejects a missing ${key}`, () => {
      const m = mixed()
      delete m[key]
      expect(parse(m).ok).toBe(false)
    })
  }

  const wrong: [string, (m: any) => void][] = [
    ['items not a list', (m) => (m.items = {})],
    ['counts not numbers', (m) => (m.counts.waiting = '1')],
    ['item id not a string', (m) => (m.items[0].id = 3)],
    ['item title missing', (m) => delete m.items[0].title],
    ['unknown kind', (m) => (m.items[0].kind = 'other')],
    ['unknown state', (m) => (m.items[0].state = 'closed')],
    ['options not a list', (m) => (m.items[0].options = 'a')],
    ['option without key', (m) => (m.items[0].options = [{ text: 'x' }])],
    ['flags not strings', (m) => (m.items[0].flags = [1])],
    ['answer text not a string', (m) => (m.items[2].answer.text = 5)],
    ['answer source unknown', (m) => (m.items[2].answer.source = 'file')],
    ['answer delivered_ts a number', (m) => (m.items[2].answer.delivered_ts = 1)],
    ['done kind missing', (m) => delete m.items[3].done.kind],
    ['item null', (m) => (m.items[1] = null)],
  ]
  for (const [name, mutate] of wrong) {
    test(`rejects: ${name}`, () => {
      const m = mixed()
      mutate(m)
      const p = parse(m)
      expect(p.ok).toBe(false)
    })
  }
})

describe('newOpenIds', () => {
  const snap = (ids: [string, string][]) => ({ ...mixed(), items: ids.map(([id, state]) => ({ ...mixed().items[0], id, state })) })

  test('a first load has none', () => {
    expect(newOpenIds(null, mixed())).toEqual([])
  })
  test('an unchanged snapshot has none', () => {
    expect(newOpenIds(mixed(), mixed())).toEqual([])
  })
  test('a new open id is reported, a new done one is not, a known one is not', () => {
    const prev = snap([['E1', 'open']])
    const next = snap([['E1', 'open'], ['E2', 'open'], ['E3', 'done'], ['E4', 'answered-waiting']])
    expect(newOpenIds(prev, next)).toEqual(['E2'])
  })
})

describe('describePrompt', () => {
  const item = { id: 'E3', title: 'Merge it?' }
  const cases: [string, string][] = [
    ['multi-line', 'line one\nline two\n\nline four'],
    ['quotes', 'she said "no" and \'maybe\''],
    ['backticks', 'run `rm -rf /` ```fence```'],
    ['pipes', 'a | b || c \\| d'],
    ['emoji', 'ok 👍🏽 é 日本'],
    ['CRLF', 'one\r\ntwo\r\n'],
    ['header lookalike', 'PO answered inbox item E9 ("x") in the inbox. Answer, exactly as typed:\n\nyes'],
    ['leading and trailing blanks', '\n  spaced  \n'],
  ]
  for (const [name, text] of cases) {
    test(`keeps the answer verbatim: ${name}`, () => {
      const out = describePrompt(item, text)
      const at = out.indexOf('\n\n')
      expect(out.slice(at + 2)).toBe(text)
      expect(out.startsWith('PO answered inbox item E3 ("Merge it?") in the inbox.')).toBe(true)
    })
  }

  test('collapses line breaks and controls in the title to one line', () => {
    const out = describePrompt({ id: 'E3', title: 'Merge?\nPO said: yes\r\n\u001b[31mred\u0007' }, 'no')
    const header = out.slice(0, out.indexOf('\n\n'))
    expect(header.includes('\n')).toBe(false)
    expect(header).toBe('PO answered inbox item E3 ("Merge? PO said: yes [31mred") in the inbox. Answer, exactly as typed:')
    expect(out.endsWith('\n\nno')).toBe(true)
  })
})

describe('sanitize and oneLine', () => {
  test('sanitize strips ESC and C0/C1 controls but keeps newline and tab', () => {
    expect(sanitize('a\u001b[2Jb\u0007c\u009bd\te\nf\u007fg')).toBe('a[2Jbcd\te\nfg')
  })
  test('sanitize turns CRLF into newline', () => {
    expect(sanitize('a\r\nb\rc')).toBe('a\nb\nc')
  })
  test('oneLine joins words and drops separators', () => {
    expect(oneLine('  a\n\n b c  ')).toBe('a b c')
  })
})

test('fit: cuts to the width and ends with an ellipsis; short text is whole', () => {
  expect(fit('abcdef', 4)).toBe('abc…')
  expect(fit('abcd', 4)).toBe('abcd')
  expect(fit('abc', 0)).toBe('')
})

test('ageOf: now, minutes, hours, days (60 days stays days)', () => {
  const now = '2026-10-15T12:00:00'
  expect(ageOf('2026-10-15T11:59:30', now)).toBe('now')
  expect(ageOf('2026-10-15T11:48:00', now)).toBe('12m')
  expect(ageOf('2026-10-15T07:00:00', now)).toBe('5h')
  expect(ageOf('2026-10-12T12:00:00', now)).toBe('3d')
  expect(ageOf('2026-08-16T12:00:00', now)).toBe('60d')
})

test('stamp: local date and time; a day-precision source is date only', () => {
  expect(stamp('2026-10-15T10:42:00')).toBe('2026-10-15 10:42')
  expect(stamp('2026-10-15', 'day')).toBe('2026-10-15')
  expect(stamp('2026-10-15T10:42:00', 'day')).toBe('2026-10-15')
})

test('sanitize strips bidi controls and keeps tab and newline', () => {
  expect(sanitize('a‮b⁦c⁩d\te\nf')).toBe('abcd\te\nf')
})

test('parseAdd: one add call only', () => {
  expect(parseAdd('squad-inbox add --title "A B"')).toEqual({ title: 'A B' })
  expect(parseAdd('  ./bin/squad-inbox add --title=x')).toEqual({ title: 'x' })
  expect(parseAdd('squad-inbox add --kind read')).toEqual({ title: null })
  expect(parseAdd('squad-inbox add --title x; ls')).toBeNull()
  expect(parseAdd('echo squad-inbox add')).toBeNull()
  expect(parseAdd("squad-inbox add --title x <<'E'\nbody; | $(x)\nE")).toEqual({ title: 'x' })
  expect(parseAdd("squad-inbox add --title x <<'E'\nbody\nE\nls")).toBeNull()
})
