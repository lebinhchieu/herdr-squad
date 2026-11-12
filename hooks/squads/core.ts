// The /squads pane, pure part: parse the squad-tree JSON, build the rows, fit them to the host's width and height.
// No `$` here. Python owns every fact and command text; this file only orders and shortens what it is given.
import type { GoalNode, ScopeNode, SquadCommand, SquadFacts, SquadNode, SquadsTree, SquadsUi } from '../../types'
import { cellWidth, clipCells, oneLine, sanitize } from '../po-inbox/core'

// A whole escape sequence goes (CSI colour codes, OSC titles ended by BEL or ESC \\, any other ESC pair), not only the ESC byte.
const ESCAPES = /\u001b\[[0-?]*[ -/]*[@-~]|\u001b\][^\u0007\u001b]*(?:\u0007|\u001b\\)?|\u001b[^[\]]?/g
export const line = (text: unknown): string =>
  oneLine(sanitize((typeof text === 'string' ? text : text === null || text === undefined ? '' : String(text)).replace(ESCAPES, '')))

// --- parse ------------------------------------------------------------------------------------

export type ParsedTree = { ok: true; tree: SquadsTree } | { ok: false; error: string }

const isObj = (v: unknown): v is Record<string, any> => typeof v === 'object' && v !== null && !Array.isArray(v)

function badNode(n: any, kind: string): string | null {
  if (!isObj(n) || typeof n.name !== 'string') return `a ${kind} has no name`
  if (!Array.isArray(n.commands)) return `${kind} ${line(n.name)} has no commands list`
  if (kind !== 'squad' && !isObj(n.next_step)) return `${kind} ${line(n.name)} has no next step`
  return null
}

export function parseTree(text: string): ParsedTree {
  let doc: any
  try {
    doc = JSON.parse(text)
  } catch {
    return { ok: false, error: 'squad-tree printed text that is not JSON' }
  }
  if (!isObj(doc)) return { ok: false, error: 'squad-tree printed no object' }
  if (doc.version !== 1) return { ok: false, error: `squad-tree version ${line(doc.version)} is not supported (this pane reads version 1)` }
  if (!Array.isArray(doc.squads)) return { ok: false, error: 'squad-tree output has no squads list' }
  for (const s of doc.squads) {
    let bad = badNode(s, 'squad')
    if (!bad && (!Array.isArray(s.goals) || !Array.isArray(s.scopes) || !isObj(s.done) || !Array.isArray(s.done.goals) || !Array.isArray(s.done.scopes))) bad = `squad ${line(s.name)} has no goals, scopes or done lists`
    const nodes: [any, string][] = [...s.goals, ...(s.done?.goals ?? [])].map((g: any) => [g, 'goal'])
    for (const [g] of nodes.slice()) if (Array.isArray(g?.scopes)) for (const x of g.scopes) nodes.push([x, 'scope'])
    for (const x of [...(s.scopes ?? []), ...(s.done?.scopes ?? [])]) nodes.push([x, 'scope'])
    for (const [n, kind] of nodes) bad = bad ?? badNode(n, kind)
    if (bad) return { ok: false, error: `squad-tree output is not valid: ${bad}` }
  }
  return { ok: true, tree: doc as SquadsTree }
}

// --- facts and words --------------------------------------------------------------------------

export const needsTotal = (t: SquadsTree): number => t.squads.reduce((n, s) => n + (typeof s.needs_you === 'number' ? s.needs_you : 0), 0)

type Node = ScopeNode | GoalNode

// Symbol and state word come from the Python next-step rule, so the mod holds no status rule.
const BY_RULE: Record<number, [string, string]> = {
  1: ['?', 'unreadable'], 2: ['●', 'needs you'], 3: ['▲', 'stuck'], 4: ['✓', 'all done'], 5: ['○', 'nobody working'],
  6: ['·', 'no tasks'], 7: ['◐', 'working'], 8: ['·', 'waiting'], 9: ['✔', 'closed'],
}
export const symbolOf = (n: Node): string => (BY_RULE[n.next_step?.rule] ?? ['·', ''])[0]
export const stateWord = (n: Node): string => (BY_RULE[n.next_step?.rule] ?? ['·', 'unknown'])[1]

const q = (v: number | null | undefined): string => (typeof v === 'number' ? String(v) : '?')

// Relative age against the tree's own clock, so a saved tree draws the same every time.
export function ago(iso: string | null | undefined, now: string): string {
  if (!iso) return '?'
  const a = Date.parse(iso)
  const b = Date.parse(now)
  if (!Number.isFinite(a) || !Number.isFinite(b)) return '?'
  const s = Math.max(0, Math.round((b - a) / 1000))
  if (s < 60) return 'now'
  if (s < 3600) return `${Math.floor(s / 60)}m`
  if (s < 86400) return `${Math.floor(s / 3600)}h`
  return `${Math.floor(s / 86400)}d`
}

export const day = (iso: string | null | undefined): string => (iso ? line(iso).slice(0, 10) : '?')

// --- rows -------------------------------------------------------------------------------------

export type Row = {
  key: string
  path: string[]
  kind: 'squad' | 'goal' | 'scope' | 'group'
  depth: number
  squad: SquadNode
  node?: Node
  label: string
  /** Group rows and parents fold; the key is what `ui.folded` holds. */
  foldKey?: string
  isFolded?: boolean
  done?: boolean
}

// Groups that start closed (Done, Run by the team) are OPEN when `+key` is in `folded`; the others are folded when `key` is.
export const isOpenKey = (ui: SquadsUi, key: string, startsClosed: boolean): boolean => (startsClosed ? ui.folded.includes(`+${key}`) : !ui.folded.includes(key))

const has = (name: string, filter: string): boolean => name.toLowerCase().includes(filter)

export function listRows(tree: SquadsTree, ui: SquadsUi): Row[] {
  const f = ui.filter.trim().toLowerCase()
  const out: Row[] = []
  for (const s of tree.squads) {
    const sp = [s.name]
    const kids: Row[] = []
    const push = (rows: Row[]) => kids.push(...rows)
    const nodeRow = (n: Node, path: string[], depth: number, done: boolean, parent: boolean): Row => ({
      key: path.join('/'), path, kind: n.kind, depth, squad: s, node: n, label: n.name, done,
      ...(parent ? { foldKey: path.join('/'), isFolded: !isOpenKey(ui, path.join('/'), false) } : {}),
    })
    if (!s.flat) {
      for (const g of s.goals) {
        const gp = [...sp, `goal:${g.name}`]
        const sub = g.scopes.filter((x) => !f || has(x.name, f) || has(g.name, f)).map((x) => nodeRow(x, [...gp, `scope:${x.name}`], 2, x.status === 'done', false))
        if (!f || has(g.name, f) || sub.length) {
          const row = nodeRow(g, gp, 1, false, g.scopes.length > 0)
          kids.push(row)
          if (!row.isFolded || f) push(sub)
        }
      }
      const lone = s.scopes.filter((x) => !f || has(x.name, f))
      if (lone.length) {
        const key = `${s.name}/nogoal`
        kids.push({ key, path: [...sp], kind: 'group', depth: 1, squad: s, label: `no goal (${lone.length})`, foldKey: key, isFolded: !isOpenKey(ui, key, false) })
        if (isOpenKey(ui, key, false) || f) lone.forEach((x) => kids.push(nodeRow(x, [...sp, `scope:${x.name}`], 2, false, false)))
      }
      const dg = s.done.goals.filter((x) => !f || has(x.name, f))
      const ds = s.done.scopes.filter((x) => !f || has(x.name, f))
      if (dg.length + ds.length) {
        const key = `${s.name}/done`
        const open = isOpenKey(ui, key, true) || !!f
        kids.push({ key, path: [...sp], kind: 'group', depth: 1, squad: s, label: `Done (${dg.length + ds.length})`, foldKey: key, isFolded: !open })
        if (open) {
          dg.forEach((x) => kids.push(nodeRow(x, [...sp, `goal:${x.name}`], 2, true, false)))
          ds.forEach((x) => kids.push(nodeRow(x, [...sp, `scope:${x.name}`], 2, true, false)))
        }
      }
    }
    if (f && !has(s.name, f) && kids.length === 0) continue
    const head: Row = { key: s.name, path: sp, kind: 'squad', depth: 0, squad: s, label: s.name, foldKey: s.name, isFolded: !isOpenKey(ui, s.name, false) && !f }
    out.push(head)
    if (!head.isFolded && !s.flat) out.push(...kids)
  }
  return out
}

// --- one row of text --------------------------------------------------------------------------

const pad = (s: string, w: number): string => s + ' '.repeat(Math.max(0, w - cellWidth(s)))
export const fitCells = (s: string, w: number): string => (w <= 0 ? '' : clipCells(s, w))

// Columns drop in the BA's rank order as the pane narrows: agents (< 76 cells), last (< 58), tasks (< 46).
export function columnsFor(cols: number): { agents: boolean; last: boolean; tasks: boolean } {
  return { agents: cols >= 76, last: cols >= 58, tasks: cols >= 46 }
}

export function rowText(r: Row, cols: number, now: string, nameW: number, nextW: number): string {
  const ind = '  '.repeat(r.depth)
  const mark = r.foldKey ? (r.isFolded ? '▸' : '▾') : ' '
  if (r.kind === 'group') return fitCells(`${ind}${mark} ${r.label}`, cols)
  if (r.kind === 'squad') {
    const s = r.squad
    if (s.flat) return fitCells(`${mark} ${line(s.name)}  ${line(s.message ?? 'flat squad: not supported')}`, cols)
    const open = s.goals.length + s.scopes.length + s.goals.reduce((n, g) => n + g.scopes.filter((x) => x.status === 'open').length, 0)
    const tail = `needs ${s.needs_you}  ${open} open`
    const name = fitCells(line(s.name), Math.max(4, cols - 2 - tail.length - 2))
    return fitCells(`${mark} ${name}  ${tail}`, cols)
  }
  const n = r.node as Node
  const sym = symbolOf(n)
  const name = line(n.name)
  if (n.status === 'done' || !n.facts) {
    const rest = `${day(n.closed_at)}  Closed. Read the report.`
    const head = `${ind}${mark} ${sym} `
    const w = Math.max(4, cols - cellWidth(head) - 2 - cellWidth(rest))
    return fitCells(`${head}${pad(fitCells(name, w), Math.min(nameW, w))}  ${rest}`, cols)
  }
  const f = n.facts as SquadFacts
  const needs = f.needs_you === 0 ? '' : `needs ${q(f.needs_you)}`
  const stuck = f.stuck > 0 ? `stuck ${f.stuck}` : ''
  const tasks = n.unknown?.includes('tickets') || f.tasks_total === 0 ? '?' : `${f.tasks_done}/${f.tasks_total}`
  const nextText = line(n.next_step.text)
  const head = `${ind}${mark} ${sym} `
  const mk = (k: { agents: boolean; last: boolean; tasks: boolean }) =>
    [k.tasks ? pad(tasks, 5) : '', k.last ? pad(ago(f.last_active, now), 4) : '', k.agents ? `${q(f.agents_working)}w` : ''].filter(Boolean).join(' ')
  const c = columnsFor(cols)
  if (cols < 76) {
    // Narrow: name, needs you and next step keep their room; tasks, last and agents drop first (in the BA's rank order).
    const flags = [needs, stuck].filter(Boolean).join(' ')
    const flagsW = flags ? cellWidth(flags) + 2 : 0
    const wantNext = Math.min(cellWidth(nextText), 18)
    let right = mk(c)
    for (const k of ['agents', 'last', 'tasks'] as const) {
      if (cellWidth(head) + 6 + 2 + flagsW + wantNext + (right ? 2 + cellWidth(right) : 0) <= cols) break
      c[k] = false
      right = mk(c)
    }
    const avail = cols - cellWidth(head) - flagsW - (right ? 2 + cellWidth(right) : 0)
    const nextAlloc = Math.min(cellWidth(nextText), nextW, Math.max(8, avail - 2 - nameW))
    const nameAlloc = Math.max(4, Math.min(nameW, avail - 2 - nextAlloc))
    const body = `${head}${pad(fitCells(name, nameAlloc), nameAlloc)}  ${flags ? flags + '  ' : ''}${fitCells(nextText, nextAlloc)}${right ? `  ${right}` : ''}`
    return fitCells(body.trimEnd(), cols)
  }
  const right = mk(c)
  const fixed = cellWidth(head) + 2 + 8 + 2 + 8 + 2 + (right ? 2 + cellWidth(right) : 0)
  const room = Math.max(8, cols - fixed)
  const nw = Math.min(nameW, Math.max(4, Math.floor(room / 3)))
  const next = fitCells(nextText, Math.max(4, Math.min(nextW, room - nw - 2)))
  const body = `${head}${pad(fitCells(name, nw), nw)}  ${pad(needs, 8)}  ${pad(stuck, 8)}  ${pad(next, Math.min(nextW, Math.max(4, room - nw - 2)))}${right ? `  ${right}` : ''}`
  return fitCells(body.trimEnd(), cols)
}

export function widths(rows: Row[]): { nameW: number; nextW: number } {
  let nameW = 8
  let nextW = 10
  for (const r of rows) {
    if (r.kind === 'group' || r.kind === 'squad') continue
    nameW = Math.max(nameW, Math.min(24, cellWidth(line(r.node?.name))))
    nextW = Math.max(nextW, Math.min(34, cellWidth(line(r.node?.next_step.text))))
  }
  return { nameW, nextW }
}

// --- the window -------------------------------------------------------------------------------

export type Window = { from: number; count: number; above: number; below: number }

// `cap` rows in all, the `↑ N above` and `↓ N more` lines counted. Rank order is the list order, so what drops is the tail.
export function windowOf(total: number, top: number, cap: number): Window {
  cap = Math.max(1, cap)
  if (total <= cap) return { from: 0, count: total, above: 0, below: 0 }
  let from = Math.max(0, Math.min(top, total - 1))
  let count = cap - (from > 0 ? 1 : 0)
  if (from + count < total) count -= 1
  count = Math.max(1, count)
  if (from + count > total) from = Math.max(0, total - count)
  return { from, count, above: from, below: total - from - count }
}

// --- commands ---------------------------------------------------------------------------------

export const placeholderOf = (c: SquadCommand): string[] => (c.placeholder ? (c.text.match(/<[A-Za-z]+>/g) ?? []) : [])

export function noticeCopied(c: SquadCommand): string {
  const ph = placeholderOf(c)
  const text = line(c.text)
  return ph.length ? `copied: ${text} (replace ${[...new Set(ph)].join(' and ')})` : `copied: ${text}`
}

export const noticeFailed = (): string => 'copy failed: select the command text on screen'

// --- detail target ----------------------------------------------------------------------------

export type Target = { squad: SquadNode; goal: GoalNode | null; node: Node | null }

export function resolve(tree: SquadsTree, path: string[]): Target | null {
  const squad = tree.squads.find((s) => s.name === path[0])
  if (!squad) return null
  if (path.length === 1) return { squad, goal: null, node: null }
  const [kind, name] = [path[1].split(':')[0], path[1].slice(path[1].indexOf(':') + 1)]
  if (kind === 'goal') {
    const goal = [...squad.goals, ...squad.done.goals].find((g) => g.name === name)
    if (!goal) return null
    if (path.length === 2) return { squad, goal, node: goal }
    const sn = path[2].slice(path[2].indexOf(':') + 1)
    const sc = goal.scopes.find((x) => x.name === sn)
    return sc ? { squad, goal, node: sc } : null
  }
  const sc = [...squad.scopes, ...squad.done.scopes].find((x) => x.name === name)
  return sc ? { squad, goal: null, node: sc } : null
}
