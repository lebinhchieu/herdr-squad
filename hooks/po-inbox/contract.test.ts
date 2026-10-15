import { describe, expect, test } from 'claude-code/testing'

import { parseSnapshot } from './core'
import { FIXTURES } from './fixtures'

// PI-07 (iii): the full-home fixture is the CLI's real output for every kind of item.
const home = () => JSON.parse(FIXTURES['contract-home'])
const parse = (v: unknown) => parseSnapshot(JSON.stringify(v))

describe('contract-home fixture', () => {
  test('parses, with every item kept', () => {
    const p = parseSnapshot(FIXTURES['contract-home'])
    expect(p.ok).toBe(true)
    expect(home().items.length).toBeGreaterThan(10)
  })

  test('an extra key anywhere is ignored', () => {
    const h = home()
    h.future = 1
    for (const it of h.items) {
      it.extra = 1
      if (it.answer) it.answer.extra = 1
      if (it.done) it.done.extra = 1
    }
    expect(parse(h).ok).toBe(true)
  })

  test('a missing key on an item, a missing top-level key and version 2 are errors', () => {
    for (const key of ['id', 'kind', 'state', 'title', 'body', 'flags']) {
      const h = home()
      delete h.items[0][key]
      expect(parse(h).ok).toBe(false)
    }
    for (const key of ['version', 'counts', 'items']) {
      const h = home()
      delete h[key]
      expect(parse(h).ok).toBe(false)
    }
    const h = home()
    h.version = 2
    expect(parse(h).ok).toBe(false)
  })
})
