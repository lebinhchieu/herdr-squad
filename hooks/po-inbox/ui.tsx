// The band above the prompt, the inbox pane and the collapsed `squad-inbox add` tool row (PI-04).
// Everything drawn is plain Text/Button/Select/Input/Box; every string goes through the sanitiser.
import type { On } from 'claude-code'

import type { InboxItem, InboxSnapshot } from '../../types'
import { goTo, markRead, openPane, patchUi, pickOption, readView, setDraft, submitAnswer } from './actions'
import type { Tone } from './core'
import {
  TONE, ageOf, bandCounts, blocksTone, capGroup, cellWidth, clipCells, doneItems, fit, kindTone, listGroups, oneLine, outcomeTone, parseAdd, sanitize, stamp,
} from './core'

import { blocksTone, bodyBudget, cellWidth, clipCells, DEFAULT_BODY_ROWS, kindTone, outcomeTone, recommendedKey, recPointer, rowsFor } from './core'
import { clipRows, drawBody, drawOptions, toneProps } from './draw'
import type { Opt } from './draw'
import { bodyBlocks } from './markup'

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

// Theme keys only (V-15): amber is `warning`, red `error`, dim is the dimColor prop, none is no prop.
const toneProps = (t: Tone): Record<string, unknown> => (t === 'dim' ? { dimColor: true } : t === 'none' ? {} : { color: TONE[t] })

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

function problems(snap: any, error: any, T: any) {
  const { Text } = T
  const rows: any[] = []
  if (snap) {
    snap.errors.forEach((er: any, i: number) => {
      rows.push(<Text key={`pe${i}`} color="error" wrap="wrap">{`⚠ ${line(er.file)} row ${er.row}: ${line(er.message)}`}</Text>)
    })
  }
  if (error) rows.push(<Text key="pi" color="error" wrap="wrap">{`⚠ ${line(error)}`}</Text>)
  return rows
}

// The amber count is the waiting one (V-15); under 60 columns the words are the short ones.
function heading(snap: InboxSnapshot, compact: boolean, T: any) {
  const { Text } = T
  const c = snap.counts
  const parts: any[] = []
  const add = (key: string, text: string, tone: Tone = 'none') => {
    parts.push(<Text key={`hs${key}`}>{' · '}</Text>)
    parts.push(<Text key={`h${key}`} {...toneProps(tone)}>{text}</Text>)
  }
  if (c.answer_open) add('a', `${c.answer_open} ${compact ? 'answer' : 'to answer'}`)
  if (c.read_open) add('r', `${c.read_open} ${compact ? 'read' : 'to read'}`)
  if (c.waiting) add('w', `${c.waiting} waiting`, 'warn')
  return <Text bold wrap="wrap">{'Inbox'}{parts}</Text>
}

// Rows of at most `width` cells, a word longer than a row is cut across rows; past `maxRows` the last row ends with `…`.
function wrapRows(text: string, width: number, maxRows: number): string[] {
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

const INDENT = '    '

function listScreen($: any, e: any, ui: any, snap: InboxSnapshot, error: any, T: any) {
  const { Box, Text, Button } = T
  const cols = e.props.bodyColumns
  const compact = cols < BODY_COLUMNS_FULL
  const opened: string[] = ui.more ?? []
  const g = listGroups(snap)
  const empty = g.blocks.length + g.nothing.length + g.waiting.length === 0
  let n = 0
  const subLines = (it: InboxItem, waiting: boolean) => {
    if (waiting) {
      if (!it.answer) return null
      return <Text key="sub" dimColor>{clipCells(`${INDENT}(your answer sent ${when(it.answer.ts)})`, cols)}</Text>
    }
    const label = `blocks ${line(it.blocks) || 'nothing'}`
    const tone = toneProps(blocksTone(it.blocks))
    const a = ageOf(it.created, snap.now)
    const age = compact || a === 'now' ? a : `created ${a} ago`
    const withAge = a !== '' && cellWidth(`${INDENT}${label} · ${age}`) <= cols
    if (withAge) {
      return (
        <Text key="sub">
          {INDENT}
          <Text {...tone}>{label}</Text>
          <Text dimColor>{` · ${age}`}</Text>
        </Text>
      )
    }
    return wrapRows(label, Math.max(1, cols - INDENT.length), 2).map((r, i) => (
      <Text key={`sub${i}`}>
        {INDENT}
        <Text {...tone}>{r}</Text>
      </Text>
    ))
  }
  const row = (it: InboxItem, waiting: boolean) => {
    n += 1
    const id = line(it.id)
    const kind = waiting ? 'answered' : it.kind
    const kindProps = toneProps(waiting ? 'warn' : kindTone(it))
    const title = clipCells(line(it.title), Math.max(10, cols - (3 + cellWidth(id) + 2 + cellWidth(kind) + 2)))
    const hot = n <= 9 ? { hotkey: String(n) } : {}
    return (
      <Box key={`row-${it.id}`} flexDirection="column">
        <Button key={it.id} plain {...hot} onPress={() => goTo($, 'item', it.id)}>
          {n > 9 ? '   ' : ''}
          <Text dimColor>{id}</Text>
          {'  '}
          <Text {...kindProps}>{kind}</Text>
          {'  '}
          {title}
        </Button>
        {subLines(it, waiting)}
      </Box>
    )
  }
  const group = (key: string, title: string, items: InboxItem[], waiting = false) => {
    if (!items.length) return null
    const { shown, hidden } = capGroup(items, opened.includes(key))
    return (
      <Box key={key} flexDirection="column">
        <Text bold wrap="wrap" {...(waiting ? { color: 'warning' } : {})}>
          {title}
          <Text bold={false} dimColor>{` (${items.length})`}</Text>
        </Text>
        {shown.map((it) => row(it, waiting))}
        {hidden > 0 ? (
          <Button key={`more-${key}`} plain onPress={() => patchUi($, { more: [...opened, key] })}>
            <Text dimColor>{`   +${hidden} more`}</Text>
          </Button>
        ) : null}
      </Box>
    )
  }
  const doneCount = snap.items.filter((it: InboxItem) => it.state === 'done').length
  return (
    <Box flexDirection="column">
      {empty ? <Text bold>Inbox</Text> : heading(snap, compact, T)}
      {notice(ui, T)}
      {problems(snap, error, T)}
      {empty ? <Text>Nothing waits on you.</Text> : null}
      {group('blocks', 'Blocks work', g.blocks)}
      {group('nothing', 'Blocks nothing', g.nothing)}
      {group('waiting', 'Answered, waiting for the Manager', g.waiting, true)}
      {doneCount ? <Button key="done" hotkey="d" label={`Done (${doneCount}) (d)`} onPress={() => goTo($, 'done', null)} /> : null}
    </Box>
  )
}

// --- the item screen (IV-03) ------------------------------------------------------------------
// One column in V-03 order. The top block (back, header, title, rec pointer) is first; the body is cut by rows
// (T9 v3) so the options and controls follow it; Show all draws everything. Rows are estimated with `rowsFor`.

const FLOOR_ANSWER = 3
const FLOOR_READ = 12
const TITLE_ROWS = 3
const HEADER_ROWS = 2

type Sized = { node: any; rows: number }

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

function header(it: InboxItem, snap: InboxSnapshot, cols: number, expanded: boolean, T: any): Sized & { cut: boolean } {
  const { Text } = T
  const id = line(it.id)
  const kind = line(it.kind)
  const created = createdText(it, snap.now, cols)
  const blocksFull = line(it.blocks) || 'nothing'
  const plain = (b: string) => `${id} · ${kind} · blocks ${b} · created ${created}`
  let blocks = blocksFull
  if (!expanded && rowsFor(plain(blocks), cols) > HEADER_ROWS) {
    let room = Math.max(1, HEADER_ROWS * cols - cellWidth(plain('')) - 2)
    blocks = clipCells(blocksFull, room)
    while (room > 1 && rowsFor(plain(blocks), cols) > HEADER_ROWS) blocks = clipCells(blocksFull, --room)
  }
  const bt = it.state === 'done' ? 'dim' : blocksTone(it.blocks)
  const node = (
    <Text key="header" wrap="wrap">
      <Text dimColor>{id}</Text>
      <Text dimColor>{' · '}</Text>
      <Text {...toneProps(kindTone(it))}>{kind}</Text>
      <Text dimColor>{' · '}</Text>
      <Text {...toneProps(bt)}>{`blocks ${blocks}`}</Text>
      <Text dimColor>{` · created ${created}`}</Text>
    </Text>
  )
  return { node, rows: rowsFor(plain(blocks), cols), cut: blocks !== blocksFull }
}

function pointer(rec: string | null, opts: Opt[], key: string | null, cols: number, T: any): Sized | null {
  const { Text } = T
  if (rec === null) return null
  if (key !== null) {
    const text = `✓ ${recPointer(rec, opts, cols - 2)}`
    return { node: <Text key="pointer" color="success" wrap="wrap">{text}</Text>, rows: 1 }
  }
  const rest = recPointer(rec, opts, cols - 14)
  return {
    node: (
      <Text key="pointer" wrap="wrap">
        <Text color="success">✓ recommends: </Text>
        {rest}
      </Text>
    ),
    rows: 1,
  }
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

// What is left of an open answer item after the body: options, the notice, the answer fields and Send.
function answerForm($: any, it: any, ui: any, cols: number, opts: Opt[], rec: string | null, recKey: string | null, notice: Sized | null, T: any): { parts: any[]; rows: number } {
  const { Box, Text, Button, Select, Input } = T
  const id = it.id
  const pending = ui.pending === id
  const picked = ui.picked[id] ?? null
  const parts: any[] = []
  let rows = 0
  const add = (node: any, n: number) => {
    parts.push(node)
    rows += n
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
  if (opts.length > 0) {
    add(<Text key="olabel" bold>Options</Text>, 1)
    const blocks = drawOptions(opts, rec, recKey, picked, cols, T)
    add(<Box key="opts" flexDirection="column">{blocks.nodes}</Box>, blocks.rows)
  } else if (it.options_raw) {
    add(<Text key="rawlabel" bold>Options, as the Manager wrote them</Text>, 1)
    const raw = sanitize(it.options_raw)
    add(<Text key="raw" wrap="wrap">{raw}</Text>, rowsFor(raw, cols))
  }
  if (rec !== null && recKey === null) {
    add(
      <Text key="mgr" wrap="wrap">
        <Text color="success" bold>Manager recommends: </Text>
        {rec}
      </Text>,
      rowsFor(`Manager recommends: ${rec}`, cols),
    )
  }
  if (notice) add(notice.node, notice.rows)
  if (opts.length > 0) {
    add(
      <Select
        key="pick"
        label="Your answer"
        options={opts.map((o) => ({ value: o.key, label: clipCells(`(${o.key}) ${o.text}`, Math.max(8, cols - 18)) }))}
        {...(picked ? { value: picked } : {})}
        onSelect={(v: string) => pickOption($, id, v)}
      />,
      1,
    )
    add(field('note', 'Note (optional)'), 1)
  } else {
    add(field('reply', 'Your reply'), 1)
  }
  add(<Button key="send" label={pending ? 'Sending…' : 'Send answer'} onPress={() => submitAnswer($, id)} />, 1)
  return { parts, rows }
}

// The state a handled item is opened for: its lines, the PO's answer as typed (never parsed), an unsent note.
function handledBlock(it: InboxItem, ui: any, error: any, cols: number, T: any): { parts: any[]; rows: number } {
  const { Text } = T
  const draft = ui.draft[it.id] ?? ''
  const parts: any[] = []
  let rows = 0
  const add = (node: any, text: string) => {
    parts.push(node)
    rows += rowsFor(text, cols)
  }
  const changed = 'This item changed while you were reading it.'
  if (draft !== '') add(<Text key="changed" color="warning" wrap="wrap">{changed}</Text>, changed)
  handledLines(it).forEach((hl, i) => add(<Text key={`h${i}`} {...toneProps(hl.tone)} wrap="wrap">{hl.text}</Text>, hl.text))
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
  return { parts, rows }
}

function itemScreen($: any, e: any, ui: any, snap: InboxSnapshot, it: InboxItem, error: any, T: any) {
  const { Box, Text, Button } = T
  const cols = e.props.bodyColumns
  const bodyRows = typeof e.props.scroll?.bodyRows === 'number' ? e.props.scroll.bodyRows : DEFAULT_BODY_ROWS
  const fromDone = ui.screen === 'doneItem'
  const back = fromDone ? 'done' : 'list'
  const open = it.state === 'open'
  const isForm = open && it.kind === 'answer'
  const hot = isForm ? {} : { hotkey: 'b' }
  const expanded = !!ui.expanded
  const rec = it.recommendation && line(it.recommendation) !== '' ? line(it.recommendation) : null
  const opts: Opt[] = (it.options ?? []).map((o: any) => ({ key: line(o.key), text: line(o.text) }))
  const recKey = recommendedKey(rec, opts)
  const notice = itemNotice(ui, cols, T)

  // the top block
  const hd = header(it, snap, cols, expanded, T)
  const titleFull = line(it.title)
  const ptr = isForm ? pointer(rec, opts, recKey, cols, T) : null
  // the top block (back, header, title, pointer) must fit the first viewport
  const fitCap = Math.max(1, Math.min(TITLE_ROWS, bodyRows - 1 - hd.rows - (ptr ? ptr.rows : 0)))
  const titleCap = notice && !isForm ? Math.min(2, fitCap) : fitCap
  const title = expanded ? titleFull : clipRows(titleFull, cols, titleCap)
  const topRows = 1 + (notice && !isForm ? notice.rows : 0) + hd.rows + rowsFor(title, cols) + (ptr ? ptr.rows : 0)
  const topCut = title !== titleFull || hd.cut

  // the state lines of a handled item, and what follows the body
  let after: any[] = []
  let afterRows = 0
  let state: any[] = []
  let stateRows = 0
  if (isForm) {
    const f = answerForm($, it, ui, cols, opts, rec, recKey, notice, T)
    after = f.parts
    afterRows = f.rows
  } else if (open) {
    after = [<Button key="mark-read" hotkey="m" label="Mark read (m)" onPress={() => markRead($, it.id)} />]
    afterRows = 1
  } else {
    const hb = handledBlock(it, ui, error, cols, T)
    state = hb.parts
    stateRows = hb.rows
    if (opts.length > 0) {
      const blocks = drawOptions(opts, rec, recKey, it.answer ? it.answer.option : null, cols, T)
      after = [<Text key="olabel" bold>Options</Text>, <Box key="opts" flexDirection="column">{blocks.nodes}</Box>]
      afterRows = 1 + blocks.rows
      if (rec !== null && recKey === null) {
        after.push(<Text key="mgr" wrap="wrap"><Text color="success" bold>Manager recommends: </Text>{rec}</Text>)
        afterRows += rowsFor(`Manager recommends: ${rec}`, cols)
      }
    }
  }

  const floor = it.kind === 'read' && open ? FLOOR_READ : FLOOR_ANSWER
  const chrome = topRows + stateRows + afterRows
  const bd = drawBody(bodyBlocks(it.body, it.title), cols, T, { expanded, fitRows: bodyRows - chrome, budget: bodyBudget(bodyRows, chrome + 1, floor) })
  const showAll = (text: string, k = 'show-all') => (
    <Box key={`more-${k}`}>
      <Text dimColor>{`${text} `}</Text>
      <Button key={k} label="Show all" onPress={() => patchUi($, { expanded: true })} />
    </Box>
  )
  const bodyMore = bd.cut ? showAll(`… ${bd.hidden} more lines`) : null
  const topMore = !expanded && topCut ? showAll('… full title', bodyMore ? 'show-title' : 'show-all') : null
  const total = chrome + bd.rows + (bodyMore ? 1 : 0) + (topMore ? 1 : 0)
  const hint = total > bodyRows ? <Text key="hint" dimColor>{'  ↓ more below'}</Text> : null

  return (
    <Box flexDirection="column">
      <Box key="top">
        <Button key="back" label={isForm ? '← Back' : '← Back (b)'} {...hot} onPress={() => goTo($, back, null)} />
        {hint}
      </Box>
      {notice && !isForm ? notice.node : null}
      {hd.node}
      <Text key="title" bold wrap="wrap">{title}</Text>
      {ptr ? ptr.node : null}
      {state}
      {topMore}
      {bd.nodes.length > 0 ? <Box key="body" flexDirection="column">{bd.nodes}</Box> : null}
      {bodyMore}
      {after}
    </Box>
  )
}

function doneScreen($: any, e: any, ui: any, snap: InboxSnapshot, T: any) {
  const { Box, Text, Button } = T
  const all = doneItems(snap)
  const cols = e.props.bodyColumns
  const { shown, hidden } = capGroup(all, (ui.more ?? []).includes('done'))
  const word = (it: InboxItem): string => {
    const d = it.done
    if (!d) return 'done'
    if (d.kind === 'answered' && it.answer && it.answer.source === 'chat') return 'answered in chat'
    if (d.kind === 'answered-file') return 'answered in the file'
    return d.kind
  }
  const row = (it: InboxItem, i: number) => {
    const id = line(it.id)
    const w = word(it)
    const d = it.done
    const lead = i < 9 ? '' : '   '
    const title = clipCells(line(it.title), Math.max(10, cols - (3 + cellWidth(id) + 2 + cellWidth(w) + 2)))
    const reason = d && d.kind === 'withdrawn' && d.reason ? ` · withdrawn: ${line(d.reason)}` : ''
    const sub = wrapRows(`${d ? when(d.ts) : ''}${reason}`, Math.max(1, cols - INDENT.length), Number.MAX_SAFE_INTEGER)
    return (
      <Box key={`row-${it.id}`} flexDirection="column">
        <Button key={`d-${it.id}`} plain {...(i < 9 ? { hotkey: String(i + 1) } : {})} onPress={() => goTo($, 'doneItem', it.id)}>
          {lead}
          <Text dimColor>{id}</Text>
          {'  '}
          <Text {...toneProps(outcomeTone(it))}>{w}</Text>
          {'  '}
          {title}
        </Button>
        {sub.map((r, k) => (
          <Text key={`s${k}`} dimColor>{`${INDENT}${r}`}</Text>
        ))}
      </Box>
    )
  }
  return (
    <Box flexDirection="column">
      <Button key="back" label="← Back (b)" hotkey="b" onPress={() => goTo($, 'list', null)} />
      <Text bold>
        {'Done · newest first'}
        <Text bold={false} dimColor>{` (${all.length})`}</Text>
      </Text>
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
