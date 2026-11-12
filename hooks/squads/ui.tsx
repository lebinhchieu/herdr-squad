// The /squads pane: a list screen and a detail screen. Plain Text/Button/Input/Box; every string from the JSON goes
// through `line` (sanitize + oneLine from po-inbox/core). Nothing here runs a command: a press selects or copies.
import type { On } from 'claude-code'

import type { SquadCommand, SquadsTree, SquadsUi } from '../../types'
import { back, copyCommand, patchUi, refresh, scrollTo, select, setFilter, toggle, view } from './actions'
import type { Row, Target } from './core'
import {
  ago, day, fitCells, isOpenKey, line, listRows, needsTotal, resolve, rowText, stateWord, symbolOf, widths, windowOf,
} from './core'

const DEFAULT_ROWS = 20

function sizeOf(e: any): { rows: number; cols: number } {
  const rows = e.props?.scroll?.bodyRows ?? (typeof e.viewport?.rows === 'number' ? e.viewport.rows : DEFAULT_ROWS)
  const cols = e.props?.bodyColumns ?? e.viewport?.columns ?? 80
  return { rows: Math.max(1, Math.floor(rows)), cols: Math.max(10, Math.floor(cols)) }
}

// --- list -------------------------------------------------------------------------------------

function listScreen($: any, e: any, T: any, tree: SquadsTree | null, ui: SquadsUi, error: string | null) {
  const { Box, Text, Button, Input } = T
  const { rows: bodyRows, cols } = sizeOf(e)
  const narrow = cols < 40
  const need = tree ? needsTotal(tree) : 0
  const refreshBtn = <Button key="refresh" hotkey="r" label={narrow ? 'r' : 'Refresh (r)'} onPress={() => { void refresh($) }} />
  const title = need > 0 ? `Squads  ${need} need you` : 'Squads'
  const header = (
    <Box key="head">
      <Text bold>{fitCells(title, Math.max(6, cols - (narrow ? 5 : 16)))}</Text>
      <Text>{'  '}</Text>
      {refreshBtn}
    </Box>
  )
  // The fixed words come first so a narrow pane cuts the cause, not "nothing was changed".
  const errorRow = error ? (
    <Box key="err" flexDirection="column">
      <Text color="error" wrap="truncate">{fitCells(`⚠ Refresh failed, nothing was changed${tree ? ' (last list kept)' : ''}: ${line(error)}`, cols)}</Text>
      <Button key="retry" label="Try again" onPress={() => { void refresh($) }} />
    </Box>
  ) : null
  const filterRow = ui.isFiltering || ui.filter ? (
    <Input key="filter" label="/ " value={ui.filter} submitLabel="ok" onInput={(v: string) => { void setFilter($, v) }} onSubmit={() => { void patchUi($, { isFiltering: false }) }} />
  ) : (
    <Button key="filter-open" hotkey="f" plain label="/ filter (f)" onPress={() => { void patchUi($, { isFiltering: true }) }} />
  )

  if (!tree) {
    return (
      <Box flexDirection="column">
        {header}
        {errorRow ?? <Text dimColor>{fitCells('Reading .claude/squads …', cols)}</Text>}
      </Box>
    )
  }
  if (tree.squads.length === 0) {
    return (
      <Box flexDirection="column">
        {header}
        {errorRow}
        <Text>No squads here.</Text>
        <Text dimColor wrap="wrap">Start one with /squad:squad-init</Text>
      </Box>
    )
  }

  const rows = listRows(tree, ui)
  const keysLong = 'r refresh · f filter · Tab walks rows · Esc closes'
  const keys = cols >= keysLong.length ? keysLong : cols >= 24 ? 'r refresh · f filter' : 'r · f'
  const footer = <Text key="foot" dimColor wrap="truncate">{fitCells(ui.notice ?? keys, cols)}</Text>
  const footer2 = ui.notice && bodyRows >= 11 ? <Text key="foot2" dimColor wrap="truncate">{fitCells(keys, cols)}</Text> : null
  const chrome = 1 + (errorRow ? 2 : 0) + (filterRow && bodyRows >= 8 ? 1 : 0) + 1 + (footer2 ? 1 : 0)
  const win = windowOf(rows.length, ui.top, bodyRows - chrome)
  const shown = rows.slice(win.from, win.from + win.count)
  const { nameW, nextW } = widths(rows)
  const now = tree.generated

  const draw = (r: Row) => {
    const text = rowText(r, cols, now, nameW, nextW)
    const cut = 2 * r.depth + 1
    const lead = text.slice(0, cut)
    const rest = text.slice(cut)
    const open = () => {
      if (r.kind === 'group') void toggle($, r.foldKey as string, r.foldKey?.endsWith('/done') === true)
      else void select($, r.path)
    }
    return (
      <Box key={r.key + (r.kind === 'group' ? ':g' : '')}>
        {r.foldKey && r.kind !== 'group' ? (
          <Box>
            <Text>{lead.slice(0, -1)}</Text>
            <Button key={`${r.key}:fold`} plain label={lead.slice(-1)} onPress={() => { void toggle($, r.foldKey as string, false) }} />
          </Box>
        ) : <Text>{lead}</Text>}
        <Button key={r.key} plain label={rest} onPress={open} />
      </Box>
    )
  }

  return (
    <Box flexDirection="column">
      {header}
      {errorRow}
      {bodyRows >= 8 ? filterRow : null}
      {win.above > 0 ? <Button key="above" plain label={`↑ ${win.above} above`} onPress={() => { void scrollTo($, win.from - win.count) }} /> : null}
      {rows.length === 0 ? <Text>{`No match for "${line(ui.filter)}".`}</Text> : shown.map(draw)}
      {win.below > 0 ? <Button key="below" plain label={`↓ ${win.below} more`} onPress={() => { void scrollTo($, win.from + win.count) }} /> : null}
      {footer}
      {footer2}
    </Box>
  )
}

// --- detail -----------------------------------------------------------------------------------

const CHANGES: Record<string, string> = { read: 'read', writes: 'writes', destructive: 'destructive', starts: 'starts work', varies: 'varies' }

function commandBlock($: any, T: any, c: SquadCommand, cols: number, key: string) {
  const { Box, Text, Button } = T
  const press = (p: any) => { void copyCommand($, c, p?.surface) }
  const dim = c.state === 'wait'
  return (
    <Box key={key} flexDirection="column">
      <Button key={`${key}:head`} plain label={fitCells(`⧉ ${line(c.label)}  (${CHANGES[c.changes] ?? line(c.changes)})`, cols)} onPress={press} />
      <Text dimColor wrap="truncate">{fitCells(`  ${line(c.when)}`, cols)}</Text>
      <Button key={`${key}:text`} plain label={fitCells(`  ${line(c.text)}`, Math.max(cols, 1))} onPress={press} />
      {dim ? <Text color="warning" wrap="truncate">{fitCells(`  Not yet: ${line(c.reason ?? '')}`, cols)}</Text> : null}
    </Box>
  )
}

function detailScreen($: any, e: any, T: any, tree: SquadsTree, ui: SquadsUi, t: Target) {
  const { Box, Text, Button } = T
  const { cols } = sizeOf(e)
  const n = t.node
  const lines: any[] = []
  const kv = (k: string, v: string) => lines.push(<Text key={`kv-${k}`} wrap="truncate">{fitCells(`${k.padEnd(10)} ${line(v)}`, cols)}</Text>)
  let commands: SquadCommand[]
  let safe = true
  if (n) {
    safe = n.name_safe !== false
    commands = n.commands
    lines.push(<Text key="state" bold wrap="truncate">{fitCells(`${symbolOf(n)} ${stateWord(n)}   ${line(t.squad.name)}${t.goal && n.kind === 'scope' ? ` / ${line(t.goal.name)}` : ''}`, cols)}</Text>)
    lines.push(<Text key="name" wrap="truncate">{fitCells(line(n.name), cols)}</Text>)
    if (n.brief) lines.push(<Text key="brief" dimColor wrap="wrap">{line(n.brief)}</Text>)
    if (n.status === 'done' || !n.facts) {
      lines.push(<Text key="closed">{`Closed ${day(n.closed_at)}. Read the report.`}</Text>)
    } else {
      const f = n.facts
      kv('Next', n.next_step.text)
      kv('Needs you', f.needs_you === null ? '?' : String(f.needs_you))
      kv('Stuck', String(f.stuck))
      kv('Tasks', n.unknown.includes('tickets') || f.tasks_total === 0 ? '?' : `${f.tasks_done}/${f.tasks_total}`)
      kv('Last', ago(f.last_active, tree.generated))
      kv('Agents', f.agents_working === null ? '?' : String(f.agents_working))
      if (n.unknown.length) kv('Unknown', n.unknown.join(', '))
    }
  } else {
    commands = t.squad.commands
    lines.push(<Text key="state" bold wrap="truncate">{fitCells(`squad   ${line(t.squad.name)}`, cols)}</Text>)
    if (t.squad.flat) lines.push(<Text key="flat">{line(t.squad.message ?? 'flat squad: not supported')}</Text>)
    else kv('Needs you', String(t.squad.needs_you))
  }

  const children: any[] = []
  if (n && n.kind === 'goal' && n.scopes.length) {
    const sub = n.scopes.map((x): Row => ({ key: `${t.squad.name}/goal:${n.name}/scope:${x.name}`, path: [t.squad.name, `goal:${n.name}`, `scope:${x.name}`], kind: 'scope', depth: 0, squad: t.squad, node: x, label: x.name, done: x.status === 'done' }))
    const { nameW, nextW } = widths(sub)
    children.push(<Text key="scopes-h" bold>Scopes</Text>)
    for (const r of sub) children.push(<Button key={r.key} plain label={rowText(r, cols, tree.generated, nameW, nextW)} onPress={() => { void select($, r.path) }} />)
  }

  const mine = commands.filter((c) => c.group !== 'team')
  const team = commands.filter((c) => c.group === 'team')
  const body: any[] = []
  if (!safe) body.push(<Text key="unsafe" color="warning" wrap="wrap">Name not safe for a command: rename the folder</Text>)
  else {
    body.push(<Text key="cmds-h" bold>Commands</Text>)
    mine.forEach((c, i) => body.push(commandBlock($, T, c, cols, `c${i}:${c.id}`)))
    if (team.length) {
      const key = `team:${[...(ui.path)].join('/')}`
      const open = isOpenKey(ui, key, true)
      body.push(<Button key="team" plain label={`${open ? '▾' : '▸'} Run by the team (${team.length})`} onPress={() => { void toggle($, key, true) }} />)
      if (open) team.forEach((c, i) => body.push(commandBlock($, T, c, cols, `t${i}:${c.id}`)))
    }
  }

  const footer = ui.notice ? <Text key="foot" dimColor wrap="wrap">{line(ui.notice)}</Text> : <Text key="foot" dimColor>Press a command to copy it. Esc or b goes back.</Text>
  return (
    <Box flexDirection="column">
      <Button key="back" hotkey="b" label="← Back (b)" onPress={() => { void back($) }} />
      {lines}
      {children}
      {body}
      {footer}
    </Box>
  )
}

// --- the pane ---------------------------------------------------------------------------------

async function renderPane($: any, e: any) {
  const T = $.ui.resolve(e) as any
  const { ui, tree, error } = await view($)
  if (tree && ui.path.length) {
    const t = resolve(tree, ui.path)
    if (t) return detailScreen($, e, T, tree, ui, t)
  }
  return listScreen($, e, T, tree, ui, error)
}

export function registerUi(on: On): void {
  on('ui.render', { component: 'Pane', requestId: 'squads' }, renderPane).catch(($: any, e: any, next: any) => next(e))
}
