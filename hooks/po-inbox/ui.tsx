// The band above the prompt, the inbox pane and the collapsed `squad-inbox add` tool row (PI-04).
// Everything drawn is plain Text/Button/Input/Box; every string goes through the sanitiser.
import type { On } from 'claude-code'

import type { InboxItem, InboxSnapshot } from '../../types'
import { goTo, markRead, openPane, patchUi, pickOption, readView, setDraft, submitAnswer } from './actions'
import type { Tone } from './core'
import {
  ageOf, bandCounts, blocksTone, bodyBudget, capGroup, cellWidth, clipCells, DEFAULT_BODY_ROWS, doneItems, fit, kindTone, listGroups, oneLine, outcomeTone, parseAdd,
  heightTier, recommendedKey, rowsFor, sanitize, stamp, wrapRows,
} from './core'
import { clipRows, drawBody, optionRows, toneProps } from './draw'
import type { Opt } from './draw'
import { bodyBlocks, itemTitle } from './markup'

const BODY_COLUMNS_FULL = 60

// tool_use_ids of Bash rows drawn collapsed; their success result draws nothing.
const collapsed = new Set<string>()

const line = (text: string): string => oneLine(sanitize(text))

function itemLine(it: InboxItem, cols: number): string {
  return fit(line(it.title), cols)
}

function when(iso: string, precision?: string): string {
  return stamp(iso, precision)
}

// --- the band ---------------------------------------------------------------------------------

type Seg = { text: string; tone: Tone }
type Words = { answer: string; read: string; waiting: string; waitingOnly: string }
const LONG: Words = { answer: 'to answer', read: 'to read', waiting: 'waiting', waitingOnly: 'answered, waiting for the Manager' }
const SHORT: Words = { answer: 'answer', read: 'read', waiting: 'waiting', waitingOnly: 'waiting' }
const TINY: Words = { answer: 'answer', read: 'read', waiting: 'wait', waitingOnly: 'wait' }
// IV-04 ladder: the first rung whose whole line (the button as `[ label ]`) fits; the last one wraps.
const RUNGS = [
  { head: 'Inbox  ', words: LONG, sep: ' · ', label: 'Open inbox (i)', gap: '   ' },
  { head: 'Inbox  ', words: LONG, sep: ' · ', label: 'Open (i)', gap: '   ' },
  { head: 'Inbox ', words: SHORT, sep: ' · ', label: 'Open (i)', gap: ' ' },
  { head: '', words: SHORT, sep: ' · ', label: 'Open (i)', gap: ' ' },
  { head: '', words: TINY, sep: ' ', label: 'Open (i)', gap: ' ' },
  { head: '', words: TINY, sep: ' ', label: 'Open (i)', gap: ' ' },
]

function bandSegs(c: { answers: number; reads: number; waiting: number; problems: number }, w: Words): Seg[] {
  const out: Seg[] = []
  if (c.answers > 0) out.push({ text: `${c.answers} ${w.answer}`, tone: 'warn' })
  if (c.reads > 0) out.push({ text: `${c.reads} ${w.read}`, tone: 'none' })
  if (c.waiting > 0) out.push({ text: `${c.waiting} ${c.answers + c.reads === 0 ? w.waitingOnly : w.waiting}`, tone: 'warn' })
  if (c.problems > 0) out.push({ text: `${c.problems} ${c.problems === 1 ? 'problem' : 'problems'}`, tone: 'bad' })
  return out
}

async function renderBand($: any, e: any, next: any) {
  if (e.props.hasSurvey) return next(e)
  const { snap, error } = await readView($)
  const c = bandCounts(snap, error)
  if (!c) return next(e)
  const { Box, Text, Button } = $.ui.resolve(e) as any
  const cols = e.props.bodyColumns
  let at = RUNGS.length - 1
  for (let i = 0; i < RUNGS.length - 1; i++) {
    const r = RUNGS[i]
    const segs = bandSegs(c, r.words)
    const width = cellWidth(r.head + segs.map((x) => x.text).join(r.sep) + r.gap) + cellWidth(`[ ${r.label} ]`)
    if (width <= cols) {
      at = i
      break
    }
  }
  const r = RUNGS[at]
  const parts: any[] = []
  bandSegs(c, r.words).forEach((s, i) => {
    if (i > 0) parts.push(<Text key={`s${i}`}>{r.sep}</Text>)
    parts.push(<Text key={`c${i}`} {...toneProps(s.tone)}>{s.text}</Text>)
  })
  const button = <Button key="open" hotkey="i" label={r.label} onPress={() => openPane($)} />
  if (at === RUNGS.length - 1) {
    return (
      <Box key="inbox-band" flexDirection="column">
        <Text wrap="wrap">{parts}</Text>
        {button}
      </Box>
    )
  }
  return (
    <Box key="inbox-band">
      <Text wrap="truncate">
        {r.head ? <Text bold>Inbox</Text> : null}
        {r.head.slice(5)}
        {parts}
        {r.gap}
      </Text>
      {button}
    </Box>
  )
}

// --- the pane ---------------------------------------------------------------------------------

function notice(ui: any, T: any) {
  const { Text } = T
  if (!ui.notice) return null
  return ui.notice.tone === 'ok' ? <Text color="success">{`✓ ${line(ui.notice.text)}`}</Text> : <Text color="error">{`⚠ ${line(ui.notice.text)}`}</Text>
}

function problemTexts(snap: any, error: any): string[] {
  const rows: string[] = snap ? snap.errors.map((er: any) => `⚠ ${line(er.file)} row ${er.row}: ${line(er.message)}`) : []
  if (error) rows.push(`⚠ ${line(error)}`)
  return rows
}

function problems(snap: any, error: any, T: any) {
  const { Text } = T
  return problemTexts(snap, error).map((t, i) => <Text key={`pe${i}`} color="error" wrap="wrap">{t}</Text>)
}

// The amber count is the waiting one (V-15); under 60 columns the words are the short ones.
type Part = { key: string; text: string; tone: Tone }
function headingParts(snap: InboxSnapshot, compact: boolean): Part[] {
  const c = snap.counts
  const parts: Part[] = []
  if (c.answer_open) parts.push({ key: 'a', text: `${c.answer_open} ${compact ? 'answer' : 'to answer'}`, tone: 'none' })
  if (c.read_open) parts.push({ key: 'r', text: `${c.read_open} ${compact ? 'read' : 'to read'}`, tone: 'none' })
  if (c.waiting) parts.push({ key: 'w', text: `${c.waiting} waiting`, tone: 'warn' })
  return parts
}

const headingWidth = (parts: Part[]): number => cellWidth('Inbox') + parts.reduce((n, p) => n + 3 + cellWidth(p.text), 0)

function headingNode(parts: Part[], T: any) {
  const { Text } = T
  const nodes: any[] = []
  parts.forEach((p) => {
    nodes.push(<Text key={`hs${p.key}`}>{' · '}</Text>)
    nodes.push(<Text key={`h${p.key}`} {...toneProps(p.tone)}>{p.text}</Text>)
  })
  return <Text key="heading" bold wrap="wrap">{'Inbox'}{nodes}</Text>
}

const BUTTON_PAD = 4 // `[ ` and ` ]` around a button label
const buttonWidth = (label: string): number => cellWidth(label) + BUTTON_PAD
const HEAD_GAP = 3

// Row 1 of the list (list.md sections 2 and 7). Drop order when it does not fit: the `↓ N more` hint, the long words,
// then the Done button moves to its own row. The hint `h` is drawn only on the first layout, which holds it.
function headingRow(snap: InboxSnapshot, cols: number, empty: boolean, doneLabel: string | null, hint: string | null, onDone: () => void, T: any) {
  const { Box, Text, Button } = T
  const btn = doneLabel === null ? null : <Button key="done" hotkey="d" label={doneLabel} onPress={onDone} />
  const bw = doneLabel === null ? 0 : HEAD_GAP + buttonWidth(doneLabel)
  const longOk = cols >= BODY_COLUMNS_FULL
  const long = empty ? [] : headingParts(snap, false)
  const short = empty ? [] : headingParts(snap, true)
  const hw = hint === null ? 0 : 2 + cellWidth(hint)
  const layout = (parts: Part[], withHint: boolean) => {
    const used = headingWidth(parts) + bw
    const node = headingNode(parts, T)
    const gap = withHint && hint !== null ? Math.max(2, cols - used - cellWidth(hint)) : 0
    return {
      rows: 1,
      node: (
        <Box key="top">
          {node}
          {btn ? <Text key="gap">{' '.repeat(HEAD_GAP)}</Text> : null}
          {btn}
          {withHint && hint !== null ? <Text key="hint" dimColor>{`${' '.repeat(gap)}${hint}`}</Text> : null}
        </Box>
      ),
    }
  }
  if (longOk && hint !== null && headingWidth(long) + bw + hw <= cols) return layout(long, true)
  if (longOk && headingWidth(long) + bw <= cols) return layout(long, false)
  // under 60 columns the long words are not offered, so the hint may sit beside the short ones
  if (!longOk && hint !== null && headingWidth(short) + bw + hw <= cols) return layout(short, true)
  if (headingWidth(short) + bw <= cols) return layout(short, false)
  // the button on its own row; the heading wraps as it always did
  const parts = longOk ? long : short
  return {
    rows: rowsFor(`Inbox${parts.map((p) => ` · ${p.text}`).join('')}`, cols) + (btn ? 1 : 0),
    node: (
      <Box key="top" flexDirection="column">
        {headingNode(parts, T)}
        {btn}
      </Box>
    ),
  }
}

const INDENT = '    '

// The short age at the right end of a row: `left` cells are used, the age ends at the last of `cols` cells.
const agePad = (left: number, age: string, cols: number): string => ' '.repeat(Math.max(2, cols - left - cellWidth(age)))

function listScreen($: any, e: any, ui: any, snap: InboxSnapshot, error: any, T: any) {
  const { Box, Text, Button } = T
  const cols = e.props.bodyColumns
  const bodyRows = typeof e.props.scroll?.bodyRows === 'number' ? e.props.scroll.bodyRows : DEFAULT_BODY_ROWS
  const short = heightTier(bodyRows) === 'short'
  const compact = cols < BODY_COLUMNS_FULL
  const opened: string[] = ui.more ?? []
  const g = listGroups(snap)
  const empty = g.blocks.length + g.nothing.length + g.waiting.length === 0
  const doneCount = snap.items.filter((it: InboxItem) => it.state === 'done').length
  let n = 0
  // rows used so far, and the items (with the `+N more` they stand for) whose first row lies below the viewport
  let used = 0
  const starts: { at: number; items: number }[] = []
  const subLines = (it: InboxItem, waiting: boolean): { nodes: any[]; rows: number } => {
    if (waiting) {
      if (!it.answer) return { nodes: [], rows: 0 }
      return { nodes: [<Text key="sub" dimColor>{clipCells(`${INDENT}(your answer sent ${when(it.answer.ts)})`, cols)}</Text>], rows: 1 }
    }
    if (short) return { nodes: [], rows: 0 }
    const label = `blocks ${line(it.blocks) || 'nothing'}`
    const tone = toneProps(blocksTone(it.blocks))
    const a = ageOf(it.created, snap.now)
    const age = compact || a === 'now' ? a : `created ${a} ago`
    const withAge = a !== '' && cellWidth(`${INDENT}${label} · ${age}`) <= cols
    if (withAge) {
      return {
        nodes: [
          <Text key="sub">
            {INDENT}
            <Text {...tone}>{label}</Text>
            <Text dimColor>{` · ${age}`}</Text>
          </Text>,
        ],
        rows: 1,
      }
    }
    const rows = wrapRows(label, Math.max(1, cols - INDENT.length), 2)
    return {
      nodes: rows.map((r, i) => (
        <Text key={`sub${i}`}>
          {INDENT}
          <Text {...tone}>{r}</Text>
        </Text>
      )),
      rows: rows.length,
    }
  }
  const row = (it: InboxItem, waiting: boolean) => {
    n += 1
    const id = line(it.id)
    const kind = waiting ? 'answered' : it.kind
    const kindProps = toneProps(waiting ? 'warn' : kindTone(it))
    // short tier: the short age ends the row (the waiting rows carry their status in the sub-row instead)
    const age = short && !waiting ? ageOf(it.created, snap.now) : ''
    const prefix = 3 + cellWidth(id) + 2 + cellWidth(kind) + 2
    const title = clipCells(line(it.title), Math.max(10, cols - prefix - (age === '' ? 0 : 2 + cellWidth(age))))
    const hot = n <= 9 ? { hotkey: String(n) } : {}
    const sub = subLines(it, waiting)
    starts.push({ at: used + 1, items: 1 })
    used += 1 + sub.rows
    return (
      <Box key={`row-${it.id}`} flexDirection="column">
        <Button key={it.id} plain {...hot} onPress={() => goTo($, 'item', it.id)}>
          {n > 9 ? '   ' : ''}
          <Text dimColor>{id}</Text>
          {'  '}
          <Text {...kindProps}>{kind}</Text>
          {'  '}
          {title}
          {age === '' ? null : agePad(prefix + cellWidth(title), age, cols)}
          {age === '' ? null : <Text dimColor>{age}</Text>}
        </Button>
        {sub.nodes}
      </Box>
    )
  }
  const group = (key: string, title: string, items: InboxItem[], waiting = false) => {
    if (!items.length) return null
    const { shown, hidden } = capGroup(items, opened.includes(key))
    used += rowsFor(`${title} (${items.length})`, cols)
    const rows = shown.map((it) => row(it, waiting))
    if (hidden > 0) starts.push({ at: used + 1, items: hidden })
    if (hidden > 0) used += 1
    return (
      <Box key={key} flexDirection="column">
        <Text bold wrap="wrap" {...(waiting ? { color: 'warning' } : {})}>
          {title}
          <Text bold={false} dimColor>{` (${items.length})`}</Text>
        </Text>
        {rows}
        {hidden > 0 ? (
          <Button key={`more-${key}`} plain onPress={() => patchUi($, { more: [...opened, key] })}>
            <Text dimColor>{`   +${hidden} more`}</Text>
          </Button>
        ) : null}
      </Box>
    )
  }
  // The rows are built first (they count what lies below); the heading row is drawn last but goes on top.
  const doneLabel = doneCount ? `Done (${doneCount}) (d)` : null
  const onDone = () => goTo($, 'done', null)
  used = headingRow(snap, cols, empty, doneLabel, null, onDone, T).rows
  const noticeNode = notice(ui, T)
  if (ui.notice) used += rowsFor(`${ui.notice.tone === 'ok' ? '✓' : '⚠'} ${line(ui.notice.text)}`, cols)
  const problemNodes = problems(snap, error, T)
  used += problemTexts(snap, error).reduce((a, t) => a + rowsFor(t, cols), 0)
  if (empty) used += 1
  const groups = [group('blocks', 'Blocks work', g.blocks), group('nothing', 'Blocks nothing', g.nothing), group('waiting', 'Answered, waiting for the Manager', g.waiting, true)]
  const below = starts.filter((s) => s.at > bodyRows).reduce((a, s) => a + s.items, 0)
  const top = headingRow(snap, cols, empty, doneLabel, below > 0 ? `↓ ${below} more` : null, onDone, T)
  return (
    <Box flexDirection="column">
      {top.node}
      {noticeNode}
      {problemNodes}
      {empty ? <Text>Nothing waits on you.</Text> : null}
      {groups}
    </Box>
  )
}

// --- the item screen (IV-03, redesign 01) -----------------------------------------------------
// Decision first (item.md): Back + header + hint on row 1, title, options, Note, Send, then Context folded with a
// Details button. The Details page (`ui.detail`) is the reading page. Rows are estimated with `rowsFor`.

const FLOOR_ANSWER = 3
const FLOOR_FREE = 4
const FLOOR_READ = 12
const TITLE_ROWS = 2

type Sized = { node: any; rows: number }
type Row = Sized & { tag?: 'note' | 'send' | 'ctx' }
type Piece = { text: string; props: Record<string, unknown> }

function itemNotice(ui: any, cols: number, T: any): Sized | null {
  const { Text } = T
  if (!ui.notice) return null
  const ok = ui.notice.tone === 'ok'
  const text = clipRows(`${ok ? '✓' : '⚠'} ${line(ui.notice.text)}`, cols, 2)
  return { node: <Text key="notice" color={ok ? 'success' : 'error'} wrap="wrap">{text}</Text>, rows: rowsFor(text, cols) }
}

// `created Y`: under a day `5h ago`; from a day the date and the age when wide, the age alone when compact.
function createdText(it: InboxItem, now: string, cols: number): string {
  const age = ageOf(it.created, now)
  if (age === '') return when(it.created, it.created_precision)
  if (age === 'now') return 'now'
  if (!age.endsWith('d')) return `${age} ago`
  return cols >= BODY_COLUMNS_FULL ? `${when(it.created, it.created_precision).slice(0, 10)} (${age} ago)` : `${age} ago`
}

function handledLines(it: InboxItem): { text: string; tone: string }[] {
  const a = it.answer
  const d = it.done
  const tone = outcomeTone(it)
  const out: { text: string; tone: string }[] = []
  if (it.state === 'answered-waiting' && a) {
    out.push({ text: `Answered ${when(a.ts)}, waiting for the Manager.`, tone })
  } else if (d) {
    if (d.kind === 'read') out.push({ text: `Read ${when(d.ts)}.`, tone })
    else if (d.kind === 'answered' && a && a.source === 'chat') out.push({ text: `Answered in chat ${when(d.ts)}.`, tone })
    else if (d.kind === 'answered') {
      out.push({
        text: a && a.delivered_ts ? `Answered ${when(d.ts)}, delivered ${when(a.delivered_ts)}.` : `Answered ${when(d.ts)}.`,
        tone,
      })
    } else if (d.kind === 'answered-file') out.push({ text: 'Answered in the file (not through the inbox).', tone })
    else if (d.kind === 'withdrawn') out.push({ text: `Withdrawn by the Manager ${when(d.ts)}${d.reason ? `: ${line(d.reason)}` : ''}.`, tone })
    else out.push({ text: 'Removed from escalations.md before an answer.', tone })
  }
  return out
}

// The state a handled item is opened for: its lines, the PO's answer as typed (never parsed), an unsent note.
// `outcomeRows`: the most rows the outcome line may take (done.md section 3), past that it ends with `…`; null = whole.
function handledBlock(it: InboxItem, ui: any, error: any, cols: number, outcomeRows: number | null, T: any): { parts: any[]; rows: number; cut: boolean } {
  const { Text } = T
  const draft = ui.draft[it.id] ?? ''
  const parts: any[] = []
  let rows = 0
  let cut = false
  const add = (node: any, text: string) => {
    parts.push(node)
    rows += rowsFor(text, cols)
  }
  const changed = 'This item changed while you were reading it.'
  if (draft !== '') add(<Text key="changed" color="warning" wrap="wrap">{changed}</Text>, changed)
  handledLines(it).forEach((hl, i) => {
    const text = outcomeRows === null ? hl.text : clipRows(hl.text, cols, outcomeRows)
    if (text !== hl.text) cut = true
    add(<Text key={`h${i}`} {...toneProps(hl.tone)} wrap="wrap">{text}</Text>, text)
  })
  if (it.answer && it.flags.includes('cell-not-written')) {
    const t = 'Answer kept. escalations.md was not updated.'
    add(<Text key="kept" dimColor wrap="wrap">{t}</Text>, t)
  }
  if (it.state === 'answered-waiting' && error) {
    const t = `answered, delivery not confirmed: ${line(error)}`
    add(<Text key="unconfirmed" color="error" wrap="wrap">{t}</Text>, t)
  }
  if (it.answer) {
    add(<Text key="yours" bold>Your answer</Text>, 'Your answer')
    sanitize(it.answer.text)
      .split('\n')
      .forEach((l: string, i: number) => add(<Text key={`a${i}`} wrap="wrap">{l === '' ? ' ' : l}</Text>, l === '' ? ' ' : l))
  }
  if (draft !== '') {
    add(<Text key="unsent" dimColor>Your unsent note (not sent):</Text>, 'Your unsent note (not sent):')
    const d = sanitize(draft)
    add(<Text key="draft" wrap="wrap">{d}</Text>, d)
  }
  return { parts, rows, cut }
}

// Switches between Decide and Details, then puts the focus ring on Back (the first row): the host keeps the scroll it
// needed to show the focused button, so without this the new page opens scrolled to where the old button was.
async function setDetail($: any, detail: boolean): Promise<void> {
  await patchUi($, { detail })
  try {
    await $.ui.focus({ requestId: 'inbox', key: 'back' })
  } catch {
    // the host may refuse (the pane lost the keys); the page is still right
  }
}

// Row 1 of the item: the buttons, then the header and the hint. Drop order when it does not fit (item.md section 13):
// the hint, the `blocks` text (clipped), the age, then the header moves to its own row.
function topLayout(btnWidth: number, make: (blocks: string, age: string) => Piece[], blocksFull: string, age: string, hint: string | null, cols: number, canClip = true) {
  const avail = Math.max(0, cols - btnWidth - 2)
  const w = (p: Piece[]) => cellWidth(p.map((x) => x.text).join(''))
  const full = make(blocksFull, age)
  if (hint && w(full) + 2 + cellWidth(hint) <= avail) return { pieces: full, hint: true, extra: false, avail }
  if (w(full) <= avail) return { pieces: full, hint: false, extra: false, avail }
  for (const a of !canClip ? [] : age === '' ? [''] : [age, '']) {
    for (let k = cellWidth(blocksFull) - 1; k >= 8; k--) {
      const p = make(clipCells(blocksFull, k), a)
      if (w(p) <= avail) return { pieces: p, hint: false, extra: false, avail }
    }
  }
  // "blocks nothing" says nothing the header needs: last, it goes whole so the header stays on row 1 (design: `R1 · read · 3m`)
  if (canClip && blocksFull === 'nothing') {
    for (const a of age === '' ? [''] : [age, '']) {
      const p = make('', a)
      if (w(p) <= avail) return { pieces: p, hint: false, extra: false, avail }
    }
  }
  return { pieces: full, hint: false, extra: true, avail }
}

const DOT: Piece = { text: ' · ', props: { dimColor: true } }

function pieceNodes(ps: Piece[], Text: any): any[] {
  return ps.map((p, i) => (
    <Text key={`hp${i}`} {...p.props}>{p.text}</Text>
  ))
}

function itemScreen($: any, e: any, ui: any, snap: InboxSnapshot, it: InboxItem, error: any, T: any) {
  const { Box, Text, Button, Input } = T
  const cols = e.props.bodyColumns
  const bodyRows = typeof e.props.scroll?.bodyRows === 'number' ? e.props.scroll.bodyRows : DEFAULT_BODY_ROWS
  const tall = heightTier(bodyRows) === 'tall'
  const fromDone = ui.screen === 'doneItem'
  const back = fromDone ? 'done' : 'list'
  const open = it.state === 'open'
  const isForm = open && it.kind === 'answer'
  const isRead = open && it.kind === 'read'
  const detail = !!ui.detail
  const id = it.id
  const pending = ui.pending === id
  const rec = it.recommendation && line(it.recommendation) !== '' ? line(it.recommendation) : null
  const opts: Opt[] = (it.options ?? []).map((o: any) => ({ key: line(o.key), text: line(o.text) }))
  const recKey = recommendedKey(rec, opts)
  const notice = itemNotice(ui, cols, T)
  const titleFull = itemTitle(it.body, it.title)
  const blocks = bodyBlocks(it.body, it.title)
  const hasBody = blocks.some((b) => b.type !== 'blank')

  // row 1: buttons
  const markReadBtn = <Button key="mark-read" label="Mark read (m)" hotkey="m" onPress={() => markRead($, id)} />
  const backLabel = detail ? (isForm ? '← Decide (b)' : '← Back (b)') : isForm ? '← Back' : '← Back (b)'
  const backBtn = (
    <Button
      key="back"
      label={backLabel}
      {...(isForm && !detail ? {} : { hotkey: 'b' })}
      onPress={() => (detail ? setDetail($, false) : goTo($, back, null))}
    />
  )
  const buttons = [backBtn, ...(isRead ? [markReadBtn] : [])]
  const btnWidth = buttons.reduce((n, _b, i) => n + (i === 0 ? cellWidth(backLabel) : cellWidth('Mark read (m)')) + 4, 0) + (buttons.length - 1)

  // row 1: header pieces
  const age = ageOf(it.created, snap.now)
  const blocksFull = line(it.blocks) || 'nothing'
  const bt = it.state === 'done' ? 'dim' : blocksTone(it.blocks)
  const make = (b: string, a: string): Piece[] => {
    const ps: Piece[] = [{ text: line(it.id), props: { dimColor: true } }]
    const kind = line(it.kind)
    if (detail || kind !== 'answer') ps.push(DOT, { text: kind, props: toneProps(kindTone(it)) })
    if (b !== '') ps.push(DOT, { text: `blocks ${b}`, props: toneProps(bt) })
    if (detail) ps.push(DOT, { text: `created ${createdText(it, snap.now, cols)}`, props: { dimColor: true } })
    else if (a !== '') ps.push(DOT, { text: a, props: { dimColor: true } })
    return ps
  }
  const headAge = detail ? '' : age
  const extra = topLayout(btnWidth, make, blocksFull, headAge, null, cols, !detail).extra
  const row1Rows = 1 + (extra ? rowsFor(make(blocksFull, headAge).map((x) => x.text).join(''), cols) : 0)

  const segs: Row[] = []
  const add = (node: any, rows: number, tag?: Row['tag']) => segs.push({ node, rows, ...(tag ? { tag } : {}) })
  if (notice) add(notice.node, notice.rows)

  // title
  const titleShown = detail ? titleFull : clipRows(titleFull, cols, TITLE_ROWS)
  const titleCut = titleShown !== titleFull
  add(<Text key="title" bold wrap="wrap">{titleShown}</Text>, rowsFor(titleShown, cols))

  const optionBlock = (picked: string | null, pick: ((k: string) => void) | null) => {
    const d = optionRows(opts, rec, recKey, picked, cols, tall, pick, T)
    add(<Box key="opts" flexDirection="column">{d.nodes}</Box>, d.rows)
  }
  const mgrRow = () => {
    if (rec === null || recKey !== null) return
    const prefix = '✓ Manager recommends: '
    const full = `${prefix}${rec}`
    const text = tall ? full : clipRows(full, cols, 1)
    add(
      <Text key="mgr" wrap="wrap">
        <Text color="success" bold>{text.startsWith(prefix) ? prefix : ''}</Text>
        {text.startsWith(prefix) ? text.slice(prefix.length) : text}
      </Text>,
      rowsFor(text, cols),
    )
  }
  const field = (key: string, label: string) => (
    <Input
      key={ui.rev ? `${key}-${ui.rev}` : key}
      label={label}
      value={ui.draft[id] ?? ''}
      submitLabel="send"
      onInput={(v: string) => setDraft($, id, v)}
      onSubmit={(v: string) => {
        submitAnswer($, id, v)
      }}
    />
  )

  let floor = FLOOR_ANSWER
  let outcomeCut = false
  let plan: { expanded: boolean; fitRows: number; budget: number; tall: boolean } | null = null
  const markEnd = <Button key="mark-read-end" label="Mark read" onPress={() => markRead($, id)} />
  if (detail) {
    if (!isForm && !isRead) {
      // the reading page holds the whole outcome and the PO's answer (Decide may have cut the outcome line)
      const hb = handledBlock(it, ui, error, cols, null, T)
      add(<Box key="state" flexDirection="column">{hb.parts}</Box>, hb.rows)
    }
    if (isForm) {
      if (rec !== null) {
        const text = `✓ recommends: ${rec}`
        add(
          <Text key="rec" wrap="wrap">
            <Text color="success">✓ recommends: </Text>
            {rec}
          </Text>,
          rowsFor(text, cols),
        )
      }
      add(<Text key="gap">{' '}</Text>, 1)
    }
  } else if (isForm) {
    if (opts.length > 0) {
      optionBlock(ui.picked[id] ?? null, (k) => (pending ? undefined : void pickOption($, id, k)))
    } else if (it.options_raw) {
      add(<Text key="rawlabel" bold>Options, as the Manager wrote them</Text>, 1)
      const raw0 = sanitize(it.options_raw)
      const raw = tall ? raw0 : clipRows(raw0, cols, 3)
      add(<Text key="raw" wrap="wrap">{raw}</Text>, rowsFor(raw, cols))
    }
    mgrRow()
    add(field(opts.length > 0 ? 'note' : 'reply', opts.length > 0 ? 'Note (optional)' : 'Your reply'), 1, 'note')
    add(<Button key="send" label={pending ? 'Sending…' : 'Send answer'} onPress={() => submitAnswer($, id)} />, 1, 'send')
    if (opts.length === 0) floor = FLOOR_FREE
  } else if (!isRead) {
    // the outcome line takes up to 4 rows, fewer when the title already took the window (done.md section 3)
    const outcomeRows = Math.min(4, Math.max(2, bodyRows - row1Rows - rowsFor(titleShown, cols)))
    const hb = handledBlock(it, ui, error, cols, outcomeRows, T)
    outcomeCut = hb.cut
    add(<Box key="state" flexDirection="column">{hb.parts}</Box>, hb.rows)
    if (opts.length > 0) optionBlock(it.answer ? it.answer.option : null, null)
    mgrRow()
  }
  const before = () => row1Rows + segs.reduce((n, x) => n + x.rows, 0)

  // the body
  const ctxLabel = hasBody && !isRead
  if (ctxLabel) add(<Text key="ctx" bold>Context</Text>, 1, 'ctx')
  const chrome = before()
  if (detail) plan = { expanded: true, fitRows: 0, budget: 0, tall }
  else if (isRead) plan = tall ? { expanded: true, fitRows: 0, budget: 0, tall } : { expanded: false, fitRows: bodyRows - chrome, budget: bodyBudget(bodyRows, chrome + 1, FLOOR_READ), tall }
  else plan = { expanded: false, fitRows: bodyRows - chrome, budget: bodyBudget(bodyRows, chrome + 1, floor), tall }
  const bd = drawBody(blocks, cols, T, plan)
  let bodyNode: any = null
  if (bd.nodes.length > 0) {
    bodyNode = <Box key="body" flexDirection="column">{bd.nodes}</Box>
    add(bodyNode, bd.rows)
  }
  const detailsRow = (text: string) => (
    <Box key="more">
      <Box marginRight={1}><Text dimColor>{text}</Text></Box>
      <Button key="details" label="Details" onPress={() => setDetail($, true)} />
    </Box>
  )
  if (!detail && bd.cut) add(detailsRow(`… ${bd.hiddenRows} more ${bd.hiddenRows === 1 ? 'row' : 'rows'}`), 1)
  else if (!detail && titleCut) add(detailsRow('… full title'), 1)
  else if (!detail && outcomeCut) add(detailsRow('… full text'), 1)
  if (isRead) add(markEnd, 1)
  if (detail) add(<Button key="back-end" label={backLabel} onPress={() => setDetail($, false)} />, 1)

  // the hint: what lies outside the first viewport
  let at = row1Rows
  let noteBelow = false
  let sendBelow = false
  let ctxBelow = false
  for (const x of segs) {
    at += x.rows
    if (at > bodyRows) {
      if (x.tag === 'note') noteBelow = true
      if (x.tag === 'send') sendBelow = true
      if (x.tag === 'ctx' && !detail) ctxBelow = true
    }
  }
  const total = at
  const hintText = noteBelow && sendBelow ? '↓ note, send' : sendBelow ? '↓ send' : ctxBelow ? '↓ context' : total > bodyRows ? '↓ more below' : null
  const lay = topLayout(btnWidth, make, blocksFull, headAge, hintText, cols, !detail)
  const headW = lay.extra ? 0 : cellWidth(lay.pieces.map((x) => x.text).join(''))
  const showHint = !!hintText && (lay.hint || (lay.extra && cellWidth(hintText) + 2 <= lay.avail + 2))
  const gap = showHint && hintText ? Math.max(2, lay.avail - headW - cellWidth(hintText) - 1) : 0

  return (
    <Box key={detail ? 'page-detail' : 'page-decide'} flexDirection="column">
      <Box key="top">
        {buttons.flatMap((b, i) => (i === 0 ? [b] : [<Text key={`sp${i}`}>{' '}</Text>, b]))}
        {lay.extra ? null : (
          <Text key="head" wrap="wrap">
            {'  '}
            {pieceNodes(lay.pieces, Text)}
            {showHint && hintText ? <Text dimColor>{`${' '.repeat(gap)}${hintText}`}</Text> : null}
          </Text>
        )}
        {lay.extra && showHint && hintText ? <Text key="hint" dimColor>{`  ${hintText}`}</Text> : null}
      </Box>
      {lay.extra ? <Text key="head2" wrap="wrap">{pieceNodes(lay.pieces, Text)}</Text> : null}
      {segs.map((x) => x.node)}
    </Box>
  )
}

function doneScreen($: any, e: any, ui: any, snap: InboxSnapshot, T: any) {
  const { Box, Text, Button } = T
  const all = doneItems(snap)
  const cols = e.props.bodyColumns
  const bodyRows = typeof e.props.scroll?.bodyRows === 'number' ? e.props.scroll.bodyRows : DEFAULT_BODY_ROWS
  const tall = heightTier(bodyRows) === 'tall'
  const { shown, hidden } = capGroup(all, (ui.more ?? []).includes('done'))
  const word = (it: InboxItem): string => {
    const d = it.done
    if (!d) return 'done'
    if (d.kind === 'answered' && it.answer && it.answer.source === 'chat') return 'answered in chat'
    if (d.kind === 'answered-file') return 'answered in the file'
    return d.kind
  }
  // done.md section 2: the short age ends the title row in both tiers; the tall tier keeps a one-row sub-row for a withdrawn reason
  const row = (it: InboxItem, i: number) => {
    const id = line(it.id)
    const w = word(it)
    const d = it.done
    const lead = i < 9 ? '' : '   '
    const age = d ? ageOf(d.ts, snap.now) : ''
    const prefix = 3 + cellWidth(id) + 2 + cellWidth(w) + 2
    const title = clipCells(line(it.title), Math.max(10, cols - prefix - (age === '' ? 0 : 2 + cellWidth(age))))
    const reason = tall && d && d.kind === 'withdrawn' && d.reason ? clipCells(`${INDENT}withdrawn: ${line(d.reason)}`, cols) : ''
    return (
      <Box key={`row-${it.id}`} flexDirection="column">
        <Button key={`d-${it.id}`} plain {...(i < 9 ? { hotkey: String(i + 1) } : {})} onPress={() => goTo($, 'doneItem', it.id)}>
          {lead}
          <Text dimColor>{id}</Text>
          {'  '}
          <Text {...toneProps(outcomeTone(it))}>{w}</Text>
          {'  '}
          {title}
          {age === '' ? null : agePad(prefix + cellWidth(title), age, cols)}
          {age === '' ? null : <Text dimColor>{age}</Text>}
        </Button>
        {reason === '' ? null : <Text key="reason" dimColor>{reason}</Text>}
      </Box>
    )
  }
  // Back and the heading share row 1; narrow: the count goes, then the heading moves under Back
  const count = ` (${all.length})`
  const backW = buttonWidth('← Back (b)') + HEAD_GAP
  const withCount = backW + cellWidth('Done · newest first') + cellWidth(count) <= cols
  const oneRow = withCount || backW + cellWidth('Done · newest first') <= cols
  const heading = (
    <Text key="heading" bold>
      {'Done · newest first'}
      {withCount ? <Text bold={false} dimColor>{count}</Text> : null}
    </Text>
  )
  const back = <Button key="back" label="← Back (b)" hotkey="b" onPress={() => goTo($, 'list', null)} />
  return (
    <Box flexDirection="column">
      {oneRow ? (
        <Box key="top">
          {back}
          <Text key="gap">{' '.repeat(HEAD_GAP)}</Text>
          {heading}
        </Box>
      ) : (
        <Box key="top" flexDirection="column">
          {back}
          {heading}
        </Box>
      )}
      {all.length === 0 ? <Text>Nothing handled yet.</Text> : null}
      {shown.map(row)}
      {hidden > 0 ? (
        <Button key="more-done" plain onPress={() => patchUi($, { more: [...(ui.more ?? []), 'done'] })}>
          <Text dimColor>{`   +${hidden} more`}</Text>
        </Button>
      ) : null}
    </Box>
  )
}

async function renderPane($: any, e: any) {
  const T = $.ui.resolve(e) as any
  const { Box, Text } = T
  const { ui, snap, error } = await readView($)
  if (!snap) {
    return (
      <Box flexDirection="column">
        <Text bold>Inbox</Text>
        {error ? <Text color="error" wrap="wrap">{`⚠ ${line(error)}`}</Text> : <Text>Nothing waits on you.</Text>}
      </Box>
    )
  }
  if (ui.screen === 'done') return doneScreen($, e, ui, snap, T)
  if (ui.screen === 'item' || ui.screen === 'doneItem') {
    const it = snap.items.find((x) => x.id === ui.id)
    if (it) return itemScreen($, e, ui, snap, it, error, T)
    const gone = { ...ui, notice: { tone: 'error' as const, text: `${ui.id} is no longer in the inbox.` } }
    return listScreen($, e, gone, snap, error, T)
  }
  return listScreen($, e, ui, snap, error, T)
}

// --- the collapsed `squad-inbox add` row ------------------------------------------------------

function commandOf(input: unknown): string | null {
  if (typeof input !== 'object' || input === null) return null
  const c = (input as { command?: unknown }).command
  return typeof c === 'string' ? c : null
}

function renderToolUse($: any, e: any, next: any) {
  if (e.props.tool !== 'Bash') return next(e)
  const command = commandOf(e.props.input)
  const add = command === null ? null : parseAdd(command)
  if (!add) return next(e)
  const { Text } = $.ui.resolve(e) as any
  const title = fit(add.title ?? 'new item', Math.max(10, (e.viewport?.columns ?? 80) - 12))
  if (e.props.isErrored) {
    const said = typeof e.props.output === 'string' ? e.props.output : ''
    const first = line(said.split('\n')[0] ?? '')
    return <Text color="error" wrap="truncate">{`→ inbox: not added${first ? `: ${fit(first, 120)}` : ''}`}</Text>
  }
  collapsed.add(e.props.tool_use_id)
  return <Text dimColor wrap="truncate">{`→ inbox: ${title === '' ? 'new item' : title}`}</Text>
}

// A failed add (a non-zero exit shows as isErrored, or as a code on the result) keeps its normal result.
function exitedNonZero(output: unknown): boolean {
  if (typeof output !== 'object' || output === null) return false
  const o = output as { exitCode?: unknown; code?: unknown; interrupted?: unknown }
  const code = typeof o.exitCode === 'number' ? o.exitCode : typeof o.code === 'number' ? o.code : 0
  return code !== 0 || o.interrupted === true
}

function renderToolResult($: any, e: any, next: any) {
  if (e.props.tool !== 'Bash' || e.props.isErrored || exitedNonZero(e.props.output) || !collapsed.has(e.props.tool_use_id)) return next(e)
  const { Box } = $.ui.resolve(e) as any
  return <Box key="inbox-result" />
}

// The normal transcript folds Bash calls into one count line ("Ran 1 shell command"); when every
// call in the group is a collapsed `squad-inbox add`, draw the pointer lines instead of the count.
function renderToolGroup($: any, e: any, next: any) {
  const calls: any[] = e.props.calls
  if (!Array.isArray(calls) || calls.length === 0) return next(e)
  const adds = calls.map((c) => {
    const command = c.tool === 'Bash' ? commandOf(c.input) : null
    return command === null || c.isErrored ? null : parseAdd(command)
  })
  if (adds.some((a) => a === null)) return next(e)
  calls.forEach((c) => c.tool_use_id && collapsed.add(c.tool_use_id))
  const { Box, Text } = $.ui.resolve(e) as any
  return (
    <Box flexDirection="column">
      {adds.map((a: any, i: number) => (
        <Text key={`g${i}`} dimColor wrap="truncate">{`→ inbox: ${fit(a.title ?? 'new item', 100)}`}</Text>
      ))}
    </Box>
  )
}

export function registerUi(on: On): void {
  on('ui.render', { component: 'ToolGroup' }, renderToolGroup).catch(($: any, e: any, next: any) => next(e))
  on('ui.render', { component: 'AbovePrompt' }, renderBand).catch(($: any, e: any, next: any) => next(e))
  on('ui.render', { component: 'Pane', requestId: 'inbox' }, renderPane).catch(($: any, e: any, next: any) => next(e))
  on('ui.render', { component: 'ToolUse' }, renderToolUse).catch(($: any, e: any, next: any) => next(e))
  on('ui.render', { component: 'ToolResult' }, renderToolResult).catch(($: any, e: any, next: any) => next(e))
}
