// Pure part of the po-inbox mod: no `$`, no I/O. Contract: design.md "The contract".
import type { InboxItem, InboxSnapshot } from '../../types'

export type Parsed = { ok: true; snapshot: InboxSnapshot } | { ok: false; error: string }

const KINDS = ['answer', 'read']
const STATES = ['open', 'answered-waiting', 'done']

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v)
const isStr = (v: unknown): v is string => typeof v === 'string'
const isStrOrNull = (v: unknown): boolean => v === null || isStr(v)

function badItem(i: number, it: unknown): string | null {
  const at = `items[${i}]`
  if (!isObj(it)) return `${at} is not an object`
  for (const k of ['id', 'title', 'body', 'blocks', 'created']) {
    if (!isStr(it[k])) return `${at}.${k} is not a string`
  }
  if (!KINDS.includes(it.kind as string)) return `${at}.kind is not answer|read`
  if (!STATES.includes(it.state as string)) return `${at}.state is not open|answered-waiting|done`
  if (!isStrOrNull(it.recommendation)) return `${at}.recommendation is not a string or null`
  if (!Array.isArray(it.flags) || !it.flags.every(isStr)) return `${at}.flags is not a list of strings`
  const opts = it.options
  if (opts !== null) {
    if (!Array.isArray(opts) || !opts.every((o) => isObj(o) && isStr(o.key) && isStr(o.text))) {
      return `${at}.options is not null or a list of {key, text}`
    }
  }
  const a = it.answer
  if (a !== null) {
    if (!isObj(a) || !isStr(a.text) || !isStrOrNull(a.option) || !isStrOrNull(a.note) || !isStr(a.ts)
      || !isStrOrNull(a.delivered_ts) || (a.source !== 'pane' && a.source !== 'chat')) {
      return `${at}.answer is not null or {text, option, note, ts, source, delivered_ts}`
    }
  }
  const d = it.done
  if (d !== null) {
    if (!isObj(d) || !isStr(d.kind) || !isStr(d.ts) || !isStrOrNull(d.reason)) {
      return `${at}.done is not null or {kind, ts, reason}`
    }
  }
  return null
}

// The CLI is a separate program: check what the mod reads, ignore extra keys.
export function parseSnapshot(text: string): Parsed {
  let raw: unknown
  try {
    raw = JSON.parse(text)
  } catch {
    return { ok: false, error: 'squad-inbox printed invalid JSON' }
  }
  if (!isObj(raw)) return { ok: false, error: 'the snapshot is not an object' }
  if (raw.version !== 1) return { ok: false, error: `unsupported contract version ${JSON.stringify(raw.version)}` }
  if (!Array.isArray(raw.items)) return { ok: false, error: 'the snapshot has no items list' }
  const c = raw.counts
  if (!isObj(c) || ['answer_open', 'read_open', 'waiting'].some((k) => typeof c[k] !== 'number')) {
    return { ok: false, error: 'the snapshot counts are missing or not numbers' }
  }
  if (!isStr(raw.home) || !isStr(raw.now)) return { ok: false, error: 'the snapshot home or now is not a string' }
  if (!Array.isArray(raw.errors)) return { ok: false, error: 'the snapshot has no errors list' }
  for (let i = 0; i < raw.items.length; i++) {
    const bad = badItem(i, raw.items[i])
    if (bad) return { ok: false, error: bad }
  }
  return { ok: true, snapshot: raw as unknown as InboxSnapshot }
}

// C0 and C1 controls incl. ESC and DEL, and the bidi overrides; \n and \t survive when `keepLayout`.
function isControl(code: number, keepLayout: boolean): boolean {
  if (keepLayout && (code === 10 || code === 9)) return false
  const isBidi = (code >= 0x202a && code <= 0x202e) || (code >= 0x2066 && code <= 0x2069)
  return code <= 0x1f || (code >= 0x7f && code <= 0x9f) || isBidi
}

function stripControls(text: string, keepLayout: boolean, replacement: string): string {
  let out = ''
  for (const ch of text) {
    out += isControl(ch.codePointAt(0) as number, keepLayout) || (!keepLayout && (ch === '\u2028' || ch === '\u2029')) ? replacement : ch
  }
  return out
}

// An agent-written text must not drive the terminal: no ESC or other control but \n and \t.
export function sanitize(text: string): string {
  return stripControls(text.split('\r\n').join('\n').split('\r').join('\n'), true, '')
}

// One line, no controls: the title goes into a header line the Manager reads.
export function oneLine(text: string): string {
  return stripControls(text, false, ' ').split(' ').filter((w) => w !== '').join(' ')
}

// Ids open now that the previous snapshot did not hold at all. A first load (prev null) has none.
export function newOpenIds(prev: InboxSnapshot | null, next: InboxSnapshot): string[] {
  if (prev === null) return []
  const known = new Set(prev.items.map((it) => it.id))
  return next.items.filter((it) => it.state === 'open' && !known.has(it.id)).map((it) => it.id)
}

export function waitingItems(s: InboxSnapshot): InboxItem[] {
  return s.items.filter((it) => it.state === 'answered-waiting' && it.answer !== null && it.answer.delivered_ts === null)
}

// What the Manager reads: a header line, a blank line, then the PO's answer byte for byte (B-14).
export function describePrompt(item: { id: string; title: string }, answerText: string): string {
  const title = oneLine(item.title)
  return `PO answered inbox item ${item.id} ("${title}") in the inbox. Answer, exactly as typed:\n\n${answerText}`
}

export function toastText(item: { id: string; title: string }): string {
  return `New in the inbox: ${oneLine(sanitize(item.title))}`
}

// --- drawing helpers (PI-04) ------------------------------------------------------------------

// Cuts to `cols` characters and ends a cut text with an ellipsis.
export function fit(text: string, cols: number): string {
  const chars = [...text]
  if (cols <= 0) return ''
  if (chars.length <= cols) return text
  return `${chars.slice(0, cols - 1).join('')}…`
}

const pad2 = (n: number): string => (n < 10 ? `0${n}` : String(n))

// `YYYY-MM-DD HH:MM` in local time; date only when the source has no time.
export function stamp(iso: string, precision?: string): string {
  if (precision === 'day' || /^\d{4}-\d\d-\d\d$/.test(iso)) return iso.slice(0, 10)
  const t = Date.parse(iso)
  if (Number.isNaN(t)) return oneLine(sanitize(iso))
  const d = new Date(t)
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`
}

// `now`, `12m`, `5h`, `3d`.
export function ageOf(created: string, now: string): string {
  const ms = Date.parse(now) - Date.parse(created)
  if (Number.isNaN(ms)) return ''
  const min = Math.floor(ms / 60000)
  if (min < 1) return 'now'
  if (min < 60) return `${min}m`
  if (min < 1440) return `${Math.floor(min / 60)}h`
  return `${Math.floor(min / 1440)}d`
}

const NO_BLOCK = ['', 'nothing', 'none', '-', '—']
export function blocksNothing(blocks: string): boolean {
  return NO_BLOCK.includes(blocks.trim().toLowerCase())
}

export type ListGroups = { blocks: InboxItem[]; nothing: InboxItem[]; waiting: InboxItem[] }

// B-06: open items that block work, then the rest, then answered-waiting; the CLI's order inside each.
export function listGroups(s: InboxSnapshot): ListGroups {
  const open = s.items.filter((it) => it.state === 'open')
  return {
    blocks: open.filter((it) => !blocksNothing(it.blocks)),
    nothing: open.filter((it) => blocksNothing(it.blocks)),
    waiting: s.items.filter((it) => it.state === 'answered-waiting'),
  }
}

// B-27: newest handled first.
export function doneItems(s: InboxSnapshot): InboxItem[] {
  const done = s.items.filter((it) => it.state === 'done')
  return done
    .map((it, i) => ({ it, i }))
    .sort((a, b) => {
      const x = a.it.done ? a.it.done.ts : ''
      const y = b.it.done ? b.it.done.ts : ''
      return x < y ? 1 : x > y ? -1 : a.i - b.i
    })
    .map((w) => w.it)
}

export type BandCounts = { answers: number; reads: number; waiting: number; problems: number }

// null = no band: nothing open, nothing waiting, no problem.
export function bandCounts(s: InboxSnapshot | null, error: string | null): BandCounts | null {
  const problems = (s ? s.errors.length : 0) + (error ? 1 : 0)
  if (!s) return problems ? { answers: 0, reads: 0, waiting: 0, problems } : null
  const c = { answers: s.counts.answer_open, reads: s.counts.read_open, waiting: s.counts.waiting, problems }
  return c.answers + c.reads + c.waiting + c.problems === 0 ? null : c
}

// --- the collapsed `squad-inbox add` row (M7) -------------------------------------------------

// Splits a command line into words the way a shell would, or null when it holds anything that
// is not a plain word: an unquoted `;` `|` `&` `<` `>` `(` `)` or a backtick, a `$(` or backtick
// even inside double quotes, or a quote left open.
function shellWords(line: string): string[] | null {
  const words: string[] = []
  let cur = ''
  let has = false
  let quote = ''
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (quote === "'") {
      if (ch === "'") quote = ''
      else cur += ch
      continue
    }
    if (ch === '`' || (ch === '$' && line[i + 1] === '(')) return null
    if (quote === '"') {
      if (ch === '"') quote = ''
      else if (ch === '\\' && i + 1 < line.length) cur += line[++i]
      else cur += ch
      continue
    }
    if (ch === "'" || ch === '"') {
      quote = ch
      has = true
    } else if (ch === '\\' && i + 1 < line.length) {
      cur += line[++i]
      has = true
    } else if (';|&<>()'.includes(ch)) {
      return null
    } else if (ch === ' ' || ch === '\t') {
      if (has || cur) words.push(cur)
      cur = ''
      has = false
    } else {
      cur += ch
      has = true
    }
  }
  if (quote) return null
  if (has || cur) words.push(cur)
  return words
}

// The first `<<` that is outside quotes: the operator, its delimiter and whether the delimiter is quoted.
function findHeredoc(head: string): { start: number; end: number; delim: string } | null {
  let quote = ''
  for (let i = 0; i < head.length; i++) {
    const ch = head[i]
    if (quote) {
      if (ch === quote) quote = ''
      else if (quote === '"' && ch === '\\') i++
      continue
    }
    if (ch === "'" || ch === '"') quote = ch
    else if (ch === '\\') i++
    else if (ch === '<' && head[i + 1] === '<' && head[i + 2] !== '<') {
      // Only exactly <<'WORD' or <<"WORD", then whitespace or the end of the line; anything else is not inert.
      const m = /^<<(['"])([A-Za-z_][A-Za-z0-9_]*)\1(?=$|[ \t])/.exec(head.slice(i))
      if (!m) return null
      return { start: i, end: i + m[0].length, delim: m[2] }
    }
  }
  return null
}

// `{ title }` (title null when it cannot be read) for a command that is exactly one
// `squad-inbox add` invocation, optionally with a heredoc body; null for anything else.
// A heredoc body is hidden only for <<'WORD' / <<"WORD" (bash expands nothing in it) closed by a line equal to WORD.
export function parseAdd(command: string): { title: string | null } | null {
  const lines = command.replace(/^\s+/, '').split('\n')
  let head = lines[0]
  let rest = lines.slice(1)
  const m = findHeredoc(head)
  if (m) {
    head = head.slice(0, m.start) + head.slice(m.end)
    const end = rest.findIndex((l) => l === m.delim)
    if (end < 0) return null
    rest = rest.slice(end + 1)
  }
  if (rest.some((l) => l.trim() !== '')) return null
  if (/\r/.test(head)) return null
  const words = shellWords(head)
  if (!words || words.length < 2 || words[1] !== 'add') return null
  const bin = words[0]
  if (bin !== 'squad-inbox' && bin !== './bin/squad-inbox' && !(bin.startsWith('/') && bin.endsWith('/squad-inbox'))) return null
  let title: string | null = null
  for (let i = 2; i < words.length; i++) {
    if (words[i] === '--title' && i + 1 < words.length) title = words[i + 1]
    else if (words[i].startsWith('--title=')) title = words[i].slice(8)
  }
  const clean = title === null ? '' : oneLine(sanitize(title))
  return { title: clean === '' ? null : clean }
}

// --- visual helpers (IV-02): pure, no drawing ---------------------------------------------------

// V-15 / T6: theme keys, never RGB. Dim is the `dimColor` prop, not a colour.
export const TONE = { good: 'success', bad: 'error', warn: 'warning' } as const
export type Tone = 'good' | 'bad' | 'warn' | 'dim' | 'none'

// V-11 / T7: the leading `(x)` run names the option; anything that could name a second option marks none.
export function recommendedKey(rec: string | null, options: { key: string }[] | null): string | null {
  if (rec === null || options === null) return null
  const m = /^[ \t ]*\(([a-z])\)/.exec(rec)
  if (!m) return null
  const after = rec.slice(m[0].length)
  if (/^[ \t ]*(\+|\/|,[ \t ]*\([a-z]\))/.test(after)) return null
  if (/^[ \t ]*(and|or)[ \t ]*\([a-z]\)/i.test(after)) return null
  const hits = options.filter((o) => o.key === m[1])
  return hits.length === 1 ? m[1] : null
}

const inRanges = (c: number, r: number[][]): boolean => r.some(([a, b]) => c >= a && c <= b)
const ZERO = [[0x300, 0x36f], [0x200b, 0x200f], [0x20d0, 0x20ff], [0xfe00, 0xfe0f], [0xfe20, 0xfe2f], [0xe0100, 0xe01ef]]
const WIDE = [
  [0x1100, 0x115f], [0x2e80, 0x303e], [0x3041, 0x33ff], [0x3400, 0x4dbf], [0x4e00, 0x9fff], [0xa000, 0xa4cf],
  [0xac00, 0xd7a3], [0xf900, 0xfaff], [0xfe30, 0xfe6f], [0xff01, 0xff60], [0xffe0, 0xffe6],
  [0x1f300, 0x1f64f], [0x1f680, 0x1f6ff], [0x1f900, 0x1f9ff], [0x20000, 0x3fffd],
  // Emoji presentation (drawn 2 cells wide). U+2713 and U+26A0, the inbox's own glyphs, stay 1.
  [0x231a, 0x231b], [0x23e9, 0x23f3], [0x25fd, 0x25fe], [0x2614, 0x2615], [0x2648, 0x2653], [0x267f, 0x267f],
  [0x2693, 0x2693], [0x26a1, 0x26a1], [0x26aa, 0x26ab], [0x26bd, 0x26be], [0x26c4, 0x26c5], [0x26ce, 0x26ce],
  [0x26d4, 0x26d4], [0x26ea, 0x26ea], [0x26f2, 0x26f5], [0x26fa, 0x26fa], [0x26fd, 0x26fd], [0x2705, 0x2705],
  [0x270a, 0x270b], [0x2728, 0x2728], [0x274c, 0x274c], [0x274e, 0x274e], [0x2753, 0x2755], [0x2757, 0x2757],
  [0x2795, 0x2797], [0x27b0, 0x27b0], [0x27bf, 0x27bf], [0x2b1b, 0x2b1c], [0x2b50, 0x2b50], [0x2b55, 0x2b55],
  [0x1f1e6, 0x1f1ff], [0x1fa70, 0x1faff],
]

// Terminal cells of a text, by code point: wide (CJK, fullwidth, emoji) 2, combining and zero-width 0.
export function cellWidth(s: string): number {
  let w = 0
  for (const ch of s) {
    const c = ch.codePointAt(0) as number
    w += inRanges(c, ZERO) ? 0 : inRanges(c, WIDE) ? 2 : 1
  }
  return w
}

// Rows a text takes when wrapped to `cols` cells: words wrap on spaces, a longer word is hard-wrapped.
// Rounds up when unsure (the engine's real wrap is not measurable).
export function rowsFor(text: string, cols: number): number {
  const width = Math.max(1, Math.floor(cols) || 1)
  let rows = 0
  for (const line of text.split('\n')) {
    let used = 0
    let r = 1
    for (const word of line.split(' ')) {
      const w = cellWidth(word)
      if (used > 0 && used + 1 + w <= width) {
        used += 1 + w
        continue
      }
      if (w === 0 && used > 0) {
        // A run of spaces at the row end: the space starts the next row (counted, so the estimate rounds up).
        r++
        used = 1
        continue
      }
      if (used > 0) {
        r++
        // after a row filled to the full width the real renderer starts the next row one cell in
        used = used === width ? 1 : 0
      }
      // Hard-wrap one code point at a time: a wide char that does not fit starts the next row.
      for (const ch of word) {
        const cw = cellWidth(ch)
        if (used > 0 && used + cw > width) {
          r++
          used = 0
        }
        used += cw
      }
    }
    rows += r
  }
  return rows
}

export type Table = { header: string[]; rows: string[][] }
export type TableLayout =
  | { kind: 'aligned'; widths: number[] }
  | { kind: 'stacked'; rows: { column: string; value: string }[][] }

// Aligned at 60+ columns when header and rows fit as `cell  cell` (widest cell per column,
// two spaces between columns); otherwise each row stacks as `column: value`.
export function tableLayout(table: Table, cols: number): TableLayout {
  const n = Math.max(table.header.length, ...table.rows.map((r) => r.length))
  const cell = (r: string[], i: number): string => (i < r.length ? r[i] : '')
  const widths: number[] = []
  for (let i = 0; i < n; i++) {
    widths.push(Math.max(cellWidth(cell(table.header, i)), ...table.rows.map((r) => cellWidth(cell(r, i)))))
  }
  const total = widths.reduce((a, b) => a + b, 0) + 2 * Math.max(0, n - 1)
  if (cols >= 60 && total <= cols) return { kind: 'aligned', widths }
  return {
    kind: 'stacked',
    rows: table.rows.map((r) => Array.from({ length: n }, (_, i) => ({ column: cell(table.header, i), value: cell(r, i) }))),
  }
}

export const GROUP_CAP = 7

// V-20: the first 7 in input order; `hidden` is how many `+N more` stands for.
export function capGroup<T>(items: T[], expanded: boolean): { shown: T[]; hidden: number } {
  if (expanded || items.length <= GROUP_CAP) return { shown: [...items], hidden: 0 }
  return { shown: items.slice(0, GROUP_CAP), hidden: items.length - GROUP_CAP }
}

export const DEFAULT_BODY_ROWS = 20
export const DEFAULT_BODY_FLOOR = 3

// Height tier of the pane (item.md section 2): `short` up to 8 body rows (a 24-row terminal gives 6), `tall` from 9.
export type HeightTier = 'short' | 'tall'
export const heightTier = (bodyRows: number): HeightTier => (bodyRows >= 9 ? 'tall' : 'short')

// T9 v3: rows the body may use, never below `floor` (the Designer's number, default 3). A missing or NaN
// row count falls back to DEFAULT_BODY_ROWS.
export function bodyBudget(bodyRows: number | undefined, chromeRows: number, floor: number = DEFAULT_BODY_FLOOR): number {
  const rows = typeof bodyRows === 'number' && Number.isFinite(bodyRows) ? bodyRows : DEFAULT_BODY_ROWS
  const chrome = Number.isFinite(chromeRows) ? chromeRows : 0
  return Math.max(floor, rows - chrome)
}

// At most `cols` cells by cellWidth; a cut text ends with `…`; a wide char at the cut is dropped whole.
export function clipCells(s: string, cols: number): string {
  if (cols < 1) return ''
  if (cellWidth(s) <= cols) return s
  let out = ''
  let w = 0
  for (const ch of s) {
    const cw = cellWidth(ch)
    if (w + cw > cols - 1) break
    out += ch
    w += cw
  }
  return `${out}…`
}

// Rows of at most `width` cells, a word longer than a row is cut across rows; past `maxRows` the last row ends with `…`.
export function wrapRows(text: string, width: number, maxRows: number): string[] {
  const rows: string[] = []
  let cur = ''
  for (const word of text.split(' ')) {
    const pieces: string[] = []
    let piece = ''
    for (const ch of word) {
      if (piece !== '' && cellWidth(piece + ch) > width) {
        pieces.push(piece)
        piece = ''
      }
      piece += ch
    }
    pieces.push(piece)
    for (const p of pieces) {
      if (cur === '') cur = p
      else if (cellWidth(cur) + 1 + cellWidth(p) <= width) cur += ` ${p}`
      else {
        rows.push(cur)
        cur = p
      }
    }
  }
  rows.push(cur)
  if (rows.length <= maxRows) return rows
  return [...rows.slice(0, maxRows - 1), clipCells(`${rows.slice(maxRows - 1).join(' ')}…`, width)]
}

// V-15, one function per row family so a screen never invents a colour.
// Kind word: amber for an open answer item, none for a read item.
export function kindTone(it: { kind: string; state: string }): Tone {
  return it.kind === 'answer' && it.state === 'open' ? 'warn' : 'none'
}

// "blocks X": red; "blocks nothing": dim.
export function blocksTone(blocks: string): Tone {
  return blocksNothing(blocks) ? 'dim' : 'bad'
}

// Handled lines and the done list. answered-waiting: amber; answered (also in chat): green;
// answered-file: amber; read, withdrawn, removed: dim; anything unknown: none.
export function outcomeTone(it: { state: string; done: { kind: string } | null }): Tone {
  if (it.state === 'answered-waiting') return 'warn'
  if (!it.done) return 'none'
  switch (it.done.kind) {
    case 'answered': return 'good'
    case 'answered-file': return 'warn'
    case 'read':
    case 'withdrawn':
    case 'removed': return 'dim'
    default: return 'none'
  }
}
