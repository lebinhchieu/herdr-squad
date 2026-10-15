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

// C0 and C1 controls incl. ESC and DEL; \n and \t survive when `keepLayout`.
function isControl(code: number, keepLayout: boolean): boolean {
  if (keepLayout && (code === 10 || code === 9)) return false
  return code <= 0x1f || (code >= 0x7f && code <= 0x9f)
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
  return `Inbox ${item.id}: ${oneLine(sanitize(item.title))}`
}
