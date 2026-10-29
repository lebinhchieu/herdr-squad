// The markdown subset of an item body (inbox-visual V-05..V-07), as data. Pure: no drawing; imports only the sanitiser.
// Total and linear: every line is looked at a bounded number of times, an unmatched opener is searched for once,
// and a line that matches nothing is a plain paragraph. Each element drops only its own syntax characters.

import { oneLine, sanitize } from './core'

export type Span = { kind: 'text' | 'bold' | 'code'; text: string }

export type Block =
  | { type: 'heading'; level: 1 | 2 | 3; spans: Span[] }
  | { type: 'bullet'; depth: number; spans: Span[] }
  | { type: 'number'; n: number; depth: number; spans: Span[] }
  | { type: 'code'; lang: string; lines: string[] }
  | { type: 'table'; header: Span[][]; rows: Span[][][] }
  | { type: 'rec'; spans: Span[]; indent?: number }
  | { type: 'para'; spans: Span[] }
  | { type: 'blank' }

const BR = /<br\s*\/?>/gi

// `**x**` and `x` spans of one line. Anything unmatched stays text.
export function parseInline(line: string): Span[] {
  const out: Span[] = []
  let text = ''
  const flush = () => {
    if (text !== '') out.push({ kind: 'text', text })
    text = ''
  }
  let i = 0
  let nextBold = -2 // -2: not searched yet, -1: none left in the line
  let nextCode = -2
  while (i < line.length) {
    if (nextBold !== -1 && nextBold < i) nextBold = line.indexOf('**', i)
    if (nextCode !== -1 && nextCode < i) nextCode = line.indexOf('`', i)
    const hit = nextBold === -1 ? nextCode : nextCode === -1 ? nextBold : Math.min(nextBold, nextCode)
    if (hit === -1) break
    text += line.slice(i, hit)
    i = hit
    if (hit === nextCode) {
      const end = line.indexOf('`', i + 1)
      if (end === -1) {
        nextCode = -1
        text += '`'
        i += 1
      } else if (end === i + 1) {
        text += '`'
        i += 1
      } else {
        flush()
        out.push({ kind: 'code', text: line.slice(i + 1, end) })
        i = end + 1
      }
    } else {
      const end = line.indexOf('**', i + 2)
      const body = end === -1 ? '' : line.slice(i + 2, end)
      if (end === -1) {
        nextBold = -1
        text += '**'
        i += 2
      } else if (body === '' || body.trim() !== body) {
        text += '**'
        i += 2
      } else {
        flush()
        out.push({ kind: 'bold', text: body })
        i = end + 2
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
    if (trimmed.startsWith('[rec]') && (trimmed.length === 5 || isSpace(trimmed[5]))) {
      const indent = line.length - line.trimStart().length
      blocks.push({ type: 'rec', spans: parseInline(trimmed.slice(5).trim()), ...(indent > 0 ? { indent } : {}) })
    } else {
      blocks.push(headingLine(line) ?? listLine(line) ?? { type: 'para', spans: parseInline(line.trimEnd()) })
    }
    i++
  }
  return blocks
}

// A space at an emphasis boundary, so `a**b**c` reads as three words, as its source does.
const spansText = (spans: Span[]) =>
  spans.reduce((acc, s, i) => acc + (i > 0 && (s.kind !== 'text' || spans[i - 1].kind !== 'text') ? ' ' : '') + s.text, '')

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
  const t = oneLine(sanitize(title)).trim()
  const lines = sanitize(body).replace(BR, '\n').split('\n')
  const first = lines[0].trim()
  if (first === t) {
    lines.shift()
    return { title: t, lines }
  }
  if (Array.from(t).length >= TITLE_MAX && first.startsWith(t)) {
    lines.shift()
    return { title: oneLine(first), lines }
  }
  return { title: t, lines }
}

// The title the pane shows: the stored title, or the first body line when the stored one is its 80-character cut.
export const itemTitle = (body: string, title: string): string => split(body, title).title

// A body that is only its title gives no blocks.
export function bodyBlocks(body: string, title: string): Block[] {
  const { lines } = split(body, title)
  return lines.length === 0 ? [] : parseBody(lines.join('\n'))
}
