// The band above the prompt, the inbox pane and the collapsed `squad-inbox add` tool row (PI-04).
// Everything drawn is plain Text/Button/Select/Input/Box; every string goes through the sanitiser.
import type { On } from 'claude-code'

import type { InboxItem, InboxSnapshot } from '../../types'
import { goTo, markRead, openPane, patchUi, pickOption, readView, setDraft, submitAnswer } from './actions'
import { ageOf, bandCounts, doneItems, fit, listGroups, oneLine, parseAdd, sanitize, stamp } from './core'

const ANSWER_FIRST_LINES = 12
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

async function renderBand($: any, e: any, next: any) {
  if (e.props.hasSurvey) return next(e)
  const { snap, error } = await readView($)
  const c = bandCounts(snap, error)
  if (!c) return next(e)
  const { Box, Text, Button } = $.ui.resolve(e) as any
  const compact = e.props.bodyColumns < BODY_COLUMNS_FULL
  const parts: any[] = []
  const sep = ' · '
  const add = (node: any) => parts.push(node)
  if (c.answers > 0) add(<Text key="a" color="warning">{compact ? `${c.answers} answer` : `${c.answers} to answer`}</Text>)
  if (c.reads > 0) {
    if (parts.length) add(<Text key="s1">{sep}</Text>)
    add(<Text key="r" color="suggestion">{compact ? `${c.reads} read` : `${c.reads} to read`}</Text>)
  }
  if (c.waiting > 0) {
    if (parts.length) add(<Text key="s2">{sep}</Text>)
    const only = c.answers + c.reads === 0
    const text = only ? (compact ? `${c.waiting} waiting` : `${c.waiting} answered, waiting for the Manager`) : `${c.waiting} waiting`
    add(<Text key="w" dimColor>{text}</Text>)
  }
  if (c.problems > 0) {
    if (parts.length) add(<Text key="s3">{sep}</Text>)
    add(<Text key="p" color="error">{`${c.problems} ${c.problems === 1 ? 'problem' : 'problems'}`}</Text>)
  }
  return (
    <Box key="inbox-band">
      <Text wrap="truncate">
        <Text bold>Inbox</Text>
        {compact ? ' ' : '  '}
        {parts}
        {'   '}
      </Text>
      <Button key="open" hotkey="i" label={compact ? 'Open (i)' : 'Open inbox (i)'} onPress={() => openPane($)} />
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

function heading(snap: InboxSnapshot): string {
  const c = snap.counts
  const parts: string[] = []
  if (c.answer_open) parts.push(`${c.answer_open} to answer`)
  if (c.read_open) parts.push(`${c.read_open} to read`)
  if (c.waiting) parts.push(`${c.waiting} waiting`)
  return parts.length ? `Inbox · ${parts.join(' · ')}` : 'Inbox'
}

function listScreen($: any, e: any, ui: any, snap: InboxSnapshot, error: any, T: any) {
  const { Box, Text, Button } = T
  const cols = e.props.bodyColumns
  const g = listGroups(snap)
  const empty = g.blocks.length + g.nothing.length + g.waiting.length === 0
  let n = 0
  const rows = (items: InboxItem[], waiting: boolean) =>
    items.map((it) => {
      n += 1
      const kind = waiting ? 'answered' : it.kind
      const sub = waiting
        ? it.answer
          ? `(your answer sent ${when(it.answer.ts)})`
          : ''
        : `blocks ${line(it.blocks) || 'nothing'} · created ${ageOf(it.created, snap.now) === 'now' ? 'now' : `${ageOf(it.created, snap.now)} ago`}`
      const hot = n <= 9 ? { hotkey: String(n) } : {}
      return (
        <Box key={`row-${it.id}`} flexDirection="column">
          <Button key={it.id} plain {...hot} onPress={() => goTo($, 'item', it.id)}>
            {`${it.id}  ${kind}  ${itemLine(it, Math.max(10, cols - 16))}`}
          </Button>
          {sub ? <Text dimColor wrap="truncate">{`    ${sub}`}</Text> : null}
        </Box>
      )
    })
  const group = (title: string, items: InboxItem[], waiting = false) =>
    items.length ? (
      <Box key={title} flexDirection="column">
        <Text bold>{title}</Text>
        {rows(items, waiting)}
      </Box>
    ) : null
  const doneCount = snap.items.filter((it: InboxItem) => it.state === 'done').length
  return (
    <Box flexDirection="column">
      <Text bold>{empty ? 'Inbox' : heading(snap)}</Text>
      {notice(ui, T)}
      {problems(snap, error, T)}
      {empty ? <Text>Nothing waits on you.</Text> : null}
      {group('Blocks work', g.blocks)}
      {group('Blocks nothing', g.nothing)}
      {group('Answered, waiting for the Manager', g.waiting, true)}
      {doneCount ? <Button key="done" hotkey="d" label={`Done (${doneCount}) (d)`} onPress={() => goTo($, 'done', null)} /> : null}
    </Box>
  )
}

function body($: any, it: InboxItem, ui: any, T: any) {
  const { Box, Text, Button } = T
  // The escalations row writes line breaks as <br>, and often starts with the title the screen already shows.
  const lines = sanitize(it.body).replace(/<br\s*\/?>/gi, '\n').split('\n')
  if (lines.length > 0 && lines[0].trim() === line(it.title).trim()) lines.shift()
  const cut = !ui.expanded && lines.length > ANSWER_FIRST_LINES
  const shown = cut ? lines.slice(0, ANSWER_FIRST_LINES) : lines
  return (
    <Box flexDirection="column">
      {shown.map((l: string, i: number) => (
        <Text key={`b${i}`} wrap="wrap">{l === '' ? ' ' : l}</Text>
      ))}
      {cut ? (
        <Box key="more">
          <Text dimColor>{`… ${lines.length - ANSWER_FIRST_LINES} more lines `}</Text>
          <Button key="show-all" label="Show all" onPress={() => patchUi($, { expanded: true })} />
        </Box>
      ) : null}
    </Box>
  )
}

function handledLines(it: InboxItem): { text: string; tone?: string }[] {
  const a = it.answer
  const d = it.done
  const out: { text: string; tone?: string }[] = []
  if (it.state === 'answered-waiting' && a) {
    out.push({ text: `Answered ${when(a.ts)}, waiting for the Manager.`, tone: 'warning' })
  } else if (d) {
    if (d.kind === 'read') out.push({ text: `Read ${when(d.ts)}.` })
    else if (d.kind === 'answered' && a && a.source === 'chat') out.push({ text: `Answered in chat ${when(d.ts)}.` })
    else if (d.kind === 'answered') {
      out.push({
        text: a && a.delivered_ts ? `Answered ${when(d.ts)}, delivered ${when(a.delivered_ts)}.` : `Answered ${when(d.ts)}.`,
        tone: 'success',
      })
    } else if (d.kind === 'answered-file') out.push({ text: 'Answered in the file (not through the inbox).', tone: 'warning' })
    else if (d.kind === 'withdrawn') out.push({ text: `Withdrawn by the Manager ${when(d.ts)}${d.reason ? `: ${line(d.reason)}` : ''}.` })
    else out.push({ text: 'Removed from escalations.md before an answer.' })
  }
  return out
}

function answerForm($: any, it: any, ui: any, T: any) {
  const { Box, Text, Button, Select, Input } = T
  const id = it.id
  const pending = ui.pending === id
  const hasOptions = !!it.options && it.options.length > 0
  const picked = ui.picked[id]
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
  const send = (
    <Button key="send" variant="primary" label={pending ? 'Sending…' : 'Send answer'} onPress={() => submitAnswer($, id)} />
  )
  return (
    <Box flexDirection="column">
      {hasOptions ? (
        <Box flexDirection="column">
          <Text bold>Options</Text>
          {it.options.map((o: any) => (
            <Text key={`o${o.key}`} wrap="wrap">{`  (${line(o.key)}) ${line(o.text)}`}</Text>
          ))}
          {it.recommendation ? <Text dimColor wrap="wrap">{`Manager recommends: ${line(it.recommendation)}`}</Text> : null}
          <Select
            key="pick"
            label="Your answer"
            options={it.options.map((o: any) => ({ value: o.key, label: `(${line(o.key)}) ${line(o.text)}` }))}
            {...(picked ? { value: picked } : {})}
            onSelect={(v: string) => pickOption($, id, v)}
          />
          <Text>{picked ? `Picked: (${line(picked)}) ${line((it.options.find((o: any) => o.key === picked) || { text: '' }).text)}` : 'Picked: none yet'}</Text>
          {field('note', 'Note (optional)')}
        </Box>
      ) : (
        <Box flexDirection="column">
          {it.options_raw ? (
            <Box flexDirection="column">
              <Text bold>Options, as the Manager wrote them</Text>
              <Text wrap="wrap">{sanitize(it.options_raw)}</Text>
            </Box>
          ) : null}
          {field('reply', 'Your reply')}
        </Box>
      )}
      {send}
    </Box>
  )
}

function itemScreen($: any, e: any, ui: any, snap: InboxSnapshot, it: InboxItem, error: any, T: any) {
  const { Box, Text, Button } = T
  const fromDone = ui.screen === 'doneItem'
  const back = fromDone ? 'done' : 'list'
  const isForm = it.state === 'open' && it.kind === 'answer'
  const hot = isForm ? {} : { hotkey: 'b' }
  const handled = it.state !== 'open'
  const draft = ui.draft[it.id] ?? ''
  return (
    <Box flexDirection="column">
      <Button key="back" label={isForm ? '← Back' : '← Back (b)'} {...hot} onPress={() => goTo($, back, null)} />
      {notice(ui, T)}
      <Text dimColor wrap="wrap">
        {`${it.id} · ${it.kind} · blocks ${line(it.blocks) || 'nothing'} · created ${when(it.created, it.created_precision)} (${ageOf(it.created, snap.now) === 'now' ? 'now' : `${ageOf(it.created, snap.now)} ago`})`}
      </Text>
      <Text bold wrap="wrap">{line(it.title)}</Text>
      {body($, it, ui, T)}
      {handled ? (
        <Box flexDirection="column">
          {draft !== '' ? <Text color="warning">This item changed while you were reading it.</Text> : null}
          {handledLines(it).map((hl, i) => (
            <Text key={`h${i}`} {...(hl.tone ? { color: hl.tone } : {})} wrap="wrap">{hl.text}</Text>
          ))}
          {it.answer && it.flags.includes('cell-not-written') ? (
            <Text dimColor wrap="wrap">Answer kept. escalations.md was not updated, so the board may still list it.</Text>
          ) : null}
          {it.state === 'answered-waiting' && error ? (
            <Text color="error" wrap="wrap">{`answered, delivery not confirmed: ${line(error)}`}</Text>
          ) : null}
          {it.answer ? <Text bold>Your answer</Text> : null}
          {it.answer
            ? sanitize(it.answer.text)
                .split('\n')
                .map((l: string, i: number) => <Text key={`a${i}`} wrap="wrap">{l === '' ? ' ' : l}</Text>)
            : null}
          {draft !== '' ? <Text dimColor>Your unsent note (not sent):</Text> : null}
          {draft !== '' ? <Text wrap="wrap">{sanitize(draft)}</Text> : null}
        </Box>
      ) : it.kind === 'read' ? (
        <Button key="mark-read" hotkey="m" label="Mark read (m)" onPress={() => markRead($, it.id)} />
      ) : (
        answerForm($, it, ui, T)
      )}
    </Box>
  )
}

function doneScreen($: any, e: any, snap: InboxSnapshot, T: any) {
  const { Box, Text, Button } = T
  const items = doneItems(snap)
  const cols = e.props.bodyColumns
  const word = (it: InboxItem): string => {
    const d = it.done
    if (!d) return 'done'
    if (d.kind === 'answered' && it.answer && it.answer.source === 'chat') return 'answered in chat'
    if (d.kind === 'answered-file') return 'answered in the file'
    return d.kind
  }
  return (
    <Box flexDirection="column">
      <Button key="back" label="← Back (b)" hotkey="b" onPress={() => goTo($, 'list', null)} />
      <Text bold>Done · newest first</Text>
      {items.length === 0 ? <Text>Nothing handled yet.</Text> : null}
      {items.map((it, i) => (
        <Button key={`d-${it.id}`} plain {...(i < 9 ? { hotkey: String(i + 1) } : {})} onPress={() => goTo($, 'doneItem', it.id)}>
          {`${it.id}  ${word(it)}  ${it.done ? when(it.done.ts) : ''}  ${itemLine(it, Math.max(10, cols - 40))}${it.done && it.done.kind === 'withdrawn' && it.done.reason ? `  (withdrawn: ${line(it.done.reason)})` : ''}`}
        </Button>
      ))}
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
  if (ui.screen === 'done') return doneScreen($, e, snap, T)
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
