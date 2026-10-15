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
