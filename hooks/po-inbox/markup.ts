// The markdown subset of an item body (inbox-visual V-05..V-07), as data. Pure: no drawing; imports only the sanitiser.
// Total and linear: every line is looked at a bounded number of times, an unmatched opener is searched for once,
// and a line that matches nothing is a plain paragraph. Each element drops only its own syntax characters.

import { DIAGRAM_TAGS, oneLine, sanitize } from './core'
import type { DiagramTag } from './core'

// A link is `[label](url)` or a bare url (`text` ''); a badge is `[ok]`, `[fail]`, `[warn]` or `[skip]` (`text` is the word).
export type BadgeWord = DiagramTag
export type CalloutTone = 'decision' | 'warning' | 'info'
export type Span =
  | { kind: 'text' | 'bold' | 'code'; text: string }
  | { kind: 'link'; text: string; url: string }
  | { kind: 'badge'; text: BadgeWord }

export type Block =
  | { type: 'heading'; level: 1 | 2 | 3; spans: Span[] }
  | { type: 'bullet'; depth: number; spans: Span[] }
  | { type: 'number'; n: number; depth: number; spans: Span[] }
  | { type: 'code'; lang: string; lines: string[] }
  | { type: 'table'; header: Span[][]; rows: Span[][][] }
  | { type: 'rec'; spans: Span[]; indent?: number }
  | { type: 'callout'; tone: CalloutTone; spans: Span[]; indent?: number }
  | { type: 'para'; spans: Span[] }
  | { type: 'blank' }

const BR = /<br\s*\/?>/gi

const BADGES: readonly string[] = DIAGRAM_TAGS
const CALLOUTS: CalloutTone[] = ['decision', 'warning', 'info']
const isHttp = (u: string) => u.startsWith('http://') || u.startsWith('https://')

// Next index of `ch` at or after `from`, cached: a search is repeated only once `from` has passed the last hit, so the
// searches of one line cover disjoint stretches and the whole line is read a bounded number of times. `from` must never
// go down between two calls of one finder, so each use below has its own.
function finder(line: string, ch: string) {
  let at = -2 // -2: not searched yet, -1: none left in the line
  return (from: number): number => {
    if (at !== -1 && at < from) at = line.indexOf(ch, from)
    return at
  }
}

const least = (a: number, b: number, c: number, d: number): number => {
  let m = -1
  for (const x of [a, b, c, d]) if (x !== -1 && (m === -1 || x < m)) m = x
  return m
}

// `**x**`, `x`, `[label](url)`, a bare url and `[ok]` spans of one line. Anything unmatched stays text.
export function parseInline(line: string): Span[] {
  const out: Span[] = []
  let text = ''
  const flush = () => {
    if (text !== '') out.push({ kind: 'text', text })
    text = ''
  }
  let i = 0
  const findBold = finder(line, '**')
  const findCode = finder(line, '`')
  const findOpen = finder(line, '[')
  const findNextOpen = finder(line, '[')
  const findClose = finder(line, ']')
  const findParen = finder(line, ')')
  const findLinkSpace = finder(line, ' ')
  const findUrlSpace = finder(line, ' ')
  const findHttp = finder(line, 'http')
  while (i < line.length) {
    const nextBold = findBold(i)
    const nextCode = findCode(i)
    const nextOpen = findOpen(i)
    const hit = least(nextBold, nextCode, nextOpen, findHttp(i))
    if (hit === -1) break
    text += line.slice(i, hit)
    i = hit
    if (hit === nextCode) {
      const end = line.indexOf('`', i + 1)
      if (end === -1 || end === i + 1) {
        text += '`'
        i += 1
      } else {
        flush()
        out.push({ kind: 'code', text: line.slice(i + 1, end) })
        i = end + 1
      }
    } else if (hit === nextBold) {
      const end = line.indexOf('**', i + 2)
      const body = end === -1 ? '' : line.slice(i + 2, end)
      if (end === -1 || body === '' || body.trim() !== body) {
        text += '**'
        i += 2
      } else {
        flush()
        out.push({ kind: 'bold', text: body })
        i = end + 2
      }
    } else if (hit === nextOpen) {
      // `[label](url)`: the label holds no bracket; the url starts http(s):// and holds no space. `[ok]` is a badge.
      const close = findClose(i + 1)
      const another = close === -1 ? -1 : findNextOpen(i + 1)
      const clean = close !== -1 && (another === -1 || another > close)
      if (clean && line[close + 1] === '(') {
        const paren = findParen(close + 2)
        const space = findLinkSpace(close + 2)
        const url = paren === -1 ? '' : line.slice(close + 2, paren)
        if (paren !== -1 && (space === -1 || space > paren) && isHttp(url) && url.indexOf('://') + 3 < url.length) {
          flush()
          out.push({ kind: 'link', text: line.slice(i + 1, close), url })
          i = paren + 1
          continue
        }
      } else if (clean && BADGES.includes(line.slice(i + 1, close))) {
        flush()
        out.push({ kind: 'badge', text: line.slice(i + 1, close) as BadgeWord })
        i = close + 1
        continue
      }
      text += '['
      i += 1
    } else {
      // a bare url: `http://` or `https://`, at least one more character, up to the next space; one `.,;)` at its end is text
      const head = line.startsWith('https://', i) ? 8 : line.startsWith('http://', i) ? 7 : 0
      const space = findUrlSpace(i)
      let end = space === -1 ? line.length : space
      if (end - 1 > i + head && '.,;)'.includes(line[end - 1])) end -= 1
      if (head === 0 || end <= i + head || (i > 0 && /[\p{L}\p{N}]/u.test(line[i - 1]))) {
        text += 'http'
        i += 4
      } else {
        flush()
        out.push({ kind: 'link', text: '', url: line.slice(i, end) })
        i = end
      }
    }
  }
  text += line.slice(i)
  flush()
  return out
}

const isSpace = (c: string | undefined) => c === ' ' || c === '\t'

function indentOf(line: string): number {
  let n = 0
  while (n < line.length && isSpace(line[n])) n++
  return n
}

function cellsOf(line: string): string[] {
  let t = line.trim()
  if (t.startsWith('|')) t = t.slice(1)
  if (t.endsWith('|')) t = t.slice(0, -1)
  return t.split('|').map((c) => c.trim())
}

function isSeparator(line: string, columns: number): boolean {
  if (!line.includes('|') || !line.includes('-')) return false
  const cells = cellsOf(line)
  if (cells.length !== columns) return false
  return cells.every((c) => {
    const core = c.startsWith(':') ? c.slice(1) : c
    const dashes = core.endsWith(':') ? core.slice(0, -1) : core
    return dashes !== '' && dashes.split('-').every((p) => p === '')
  })
}

// A closing fence is only fence characters: text after it is code, never dropped.
function isFenceEnd(line: string, ch: string): boolean {
  const t = line.trim()
  return t.length >= 3 && t.split(ch).join('') === ''
}

function listLine(line: string): Block | null {
  const ind = indentOf(line)
  const rest = line.slice(ind)
  const depth = Math.floor(ind / 2)
  if ((rest[0] === '-' || rest[0] === '*') && isSpace(rest[1])) {
    const body = rest.slice(2).trim()
    return body === '' ? null : { type: 'bullet', depth, spans: parseInline(body) }
  }
  let d = 0
  while (d < rest.length && rest[d] >= '0' && rest[d] <= '9') d++
  if (d > 0 && d <= 9 && rest[d] === '.' && isSpace(rest[d + 1])) {
    const body = rest.slice(d + 2).trim()
    return body === '' ? null : { type: 'number', n: Number(rest.slice(0, d)), depth, spans: parseInline(body) }
  }
  return null
}

function headingLine(line: string): Block | null {
  const rest = line.slice(Math.min(indentOf(line), 3))
  let h = 0
  while (h < rest.length && rest[h] === '#') h++
  if (h < 1 || h > 3 || !isSpace(rest[h])) return null
  const body = rest.slice(h + 1).trim()
  return body === '' ? null : { type: 'heading', level: h as 1 | 2 | 3, spans: parseInline(body) }
}

// The body as blocks, one per source line except a fenced block or a table. Never throws.
export function parseBody(text: string): Block[] {
  const lines = text.replace(BR, '\n').split('\r\n').join('\n').split('\r').join('\n').split('\n')
  const blocks: Block[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const trimmed = line.trim()
    if (trimmed === '') {
      blocks.push({ type: 'blank' })
      i++
      continue
    }
    if (trimmed.startsWith('```') || trimmed.startsWith('~~~')) {
      const fence = trimmed.slice(0, 3)
      const code: string[] = []
      i++
      while (i < lines.length && !isFenceEnd(lines[i], fence[0])) code.push(lines[i++])
      i++ // the closing fence, or past the end
      blocks.push({ type: 'code', lang: trimmed.slice(3).trim(), lines: code })
      continue
    }
    if (line.includes('|') && i + 1 < lines.length) {
      const header = cellsOf(line)
      if (isSeparator(lines[i + 1], header.length)) {
        const rows: Span[][][] = []
        i += 2
        while (i < lines.length && lines[i].includes('|')) {
          rows.push(cellsOf(lines[i]).map(parseInline))
          i++
        }
        blocks.push({ type: 'table', header: header.map(parseInline), rows })
        continue
      }
    }
    const callout = CALLOUTS.find((t) => trimmed.startsWith(`[${t}]`) && (trimmed.length === t.length + 2 || isSpace(trimmed[t.length + 2])))
    if (trimmed.startsWith('[rec]') && (trimmed.length === 5 || isSpace(trimmed[5]))) {
      const indent = line.length - line.trimStart().length
      blocks.push({ type: 'rec', spans: parseInline(trimmed.slice(5).trim()), ...(indent > 0 ? { indent } : {}) })
    } else if (callout !== undefined) {
      const indent = line.length - line.trimStart().length
      blocks.push({ type: 'callout', tone: callout, spans: parseInline(trimmed.slice(callout.length + 2).trim()), ...(indent > 0 ? { indent } : {}) })
    } else {
      blocks.push(headingLine(line) ?? listLine(line) ?? { type: 'para', spans: parseInline(line.trimEnd()) })
    }
    i++
  }
  return blocks
}

// The words of one span: a link is its label and its url, a badge its word.
const spanWords = (s: Span): string => (s.kind === 'link' ? (s.text === '' ? s.url : `${s.text} ${s.url}`) : s.text)

// A space at an emphasis boundary, so `a**b**c` reads as three words, as its source does.
export const spansText = (spans: Span[]) =>
  spans.reduce((acc, s, i) => acc + (i > 0 && (s.kind !== 'text' || spans[i - 1].kind !== 'text') ? ' ' : '') + spanWords(s), '')

// The text of the blocks without their syntax characters, one line per block; the words are the body's words.
export function plainOf(blocks: Block[]): string {
  const out: string[] = []
  for (const b of blocks) {
    if (b.type === 'blank') out.push('')
    else if (b.type === 'code') out.push(...(b.lang === '' ? [] : [b.lang]), ...b.lines)
    else if (b.type === 'table') {
      out.push(b.header.map(spansText).join(' '))
      for (const r of b.rows) out.push(r.map(spansText).join(' '))
    } else out.push(spansText(b.spans))
  }
  return out.join('\n')
}

// The stored title is cut at 80 characters (no ellipsis) by `squad-inbox add`.
const TITLE_MAX = 80

// T2's pipeline: sanitize, <br> to a line break, drop the first line when it is the title the screen already shows, parse.
// P6: a title of TITLE_MAX characters whose full text starts the body is the cut form of that first line; the line is the title.
function split(body: string, title: string): { title: string; lines: string[] } {
  const rawLen = Array.from(sanitize(title)).length
  const t = oneLine(sanitize(title)).trim()
  const lines = sanitize(body).replace(BR, '\n').split('\n')
  // A cut that ends in a space is 79 trimmed characters, so the test uses the length before the trim.
  const isCut = rawLen >= TITLE_MAX
  const longer = (line: string) => line.trim().length > t.length && line.trim().startsWith(t)
  if (lines[0].trim() === t) {
    lines.shift()
    // an answer item stores `title<br>body` and its body starts with the full question: that line is the title
    if (isCut && lines.length > 0 && longer(lines[0])) return { title: oneLine(lines.shift() as string).trim(), lines }
    return { title: t, lines }
  }
  if (isCut && t !== '' && longer(lines[0])) return { title: oneLine(lines.shift() as string).trim(), lines }
  return { title: t, lines }
}

// The title the pane shows: the stored title, or the first body line when the stored one is its 80-character cut.
export const itemTitle = (body: string, title: string): string => split(body, title).title

// A body that is only its title gives no blocks.
export function bodyBlocks(body: string, title: string): Block[] {
  const { lines } = split(body, title)
  return lines.length === 0 ? [] : parseBody(lines.join('\n'))
}
