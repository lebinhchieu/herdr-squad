// The /squads pane, pure part: parse the squad-tree JSON, build the rows, fit them to the host's width and height.
// No `$` here. Python owns every fact and command text; this file only orders and shortens what it is given.
import type { GoalNode, ScopeNode, SquadCommand, SquadFacts, SquadNode, SquadsTree, SquadsUi } from '../../types'
import { cellWidth, clipCells, oneLine, sanitize, TONE } from '../po-inbox/core'

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

// Style of one run: a theme key (never hex), bold, dim. The same state draws the same style in the list and the detail.
export type Style = { color?: string; bold?: boolean; dim?: boolean }
export type Seg = { text: string; style?: Style }
const S = (text: string, style?: Style): Seg => (style ? { text, style } : { text })

const NEEDS: Style = { color: TONE.warn, bold: true }
const STUCK: Style = { color: TONE.bad, bold: true }
const DIM: Style = { dim: true }
// By next-step rule: 1 unreadable, 2 needs you, 3 stuck, 4 all done, 5 nobody working, 6 no tasks, 7 working, 8 waiting, 9 closed.
const TONE_BY_RULE: Record<number, Style> = {
  1: { color: TONE.warn }, 2: NEEDS, 3: STUCK, 4: { color: TONE.good }, 5: DIM, 6: DIM, 7: { color: 'suggestion' }, 8: DIM, 9: { color: TONE.good },
}
export const toneOf = (n: Node): Style => TONE_BY_RULE[n.next_step?.rule] ?? DIM
export const COMMAND_STYLE: Style = { color: 'ide' }
export const NOT_YET_STYLE: Style = { color: TONE.warn }
export const CHANGE_STYLE: Record<string, Style> = {
  read: { color: TONE.good }, writes: { color: TONE.warn }, destructive: STUCK, starts: { color: TONE.warn }, varies: DIM,
}
export const NEEDS_STYLE = NEEDS
export const STUCK_STYLE = STUCK
export const DIM_STYLE = DIM

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

const joinSegs = (segs: Seg[]): string => segs.map((x) => x.text).join('')

// The row text is cut to the width as one string (as before); the styled runs are cut to the same prefix.
function clipSegs(segs: Seg[], cols: number): Seg[] {
  const full = joinSegs(segs).trimEnd()
  const cut = fitCells(full, cols)
  let common = 0
  while (common < cut.length && common < full.length && cut[common] === full[common]) common++
  const out: Seg[] = []
  let at = 0
  for (const x of segs) {
    if (at >= common) break
    const t = x.text.slice(0, common - at)
    at += x.text.length
    if (t !== '') out.push(S(t, x.style))
  }
  if (cut.length > common) {
    if (out.length) out[out.length - 1] = S(out[out.length - 1].text + cut.slice(common), out[out.length - 1].style)
    else out.push(S(cut.slice(common)))
  }
  return out
}

const padSeg = (text: string, w: number, style?: Style): Seg[] => (text === '' ? [S(' '.repeat(w))] : [S(text, style), S(' '.repeat(Math.max(0, w - cellWidth(text))))])

export const sliceSegs = (segs: Seg[], from: number): Seg[] => {
  const out: Seg[] = []
  let at = 0
  for (const x of segs) {
    const start = Math.max(0, from - at)
    at += x.text.length
    if (start < x.text.length) out.push(S(x.text.slice(start), x.style))
  }
  return out
}

export const rowText = (r: Row, cols: number, now: string, nameW: number, nextW: number): string => joinSegs(rowSegs(r, cols, now, nameW, nextW))

export function rowSegs(r: Row, cols: number, now: string, nameW: number, nextW: number): Seg[] {
  const ind = '  '.repeat(r.depth)
  const mark = r.foldKey ? (r.isFolded ? '▸' : '▾') : ' '
  if (r.kind === 'group') return clipSegs([S(`${ind}${mark} ${r.label}`, DIM)], cols)
  if (r.kind === 'squad') {
    const s = r.squad
    if (s.flat) return clipSegs([S(`${mark} ${line(s.name)}  `), S(line(s.message ?? 'flat squad: not supported'), DIM)], cols)
    const open = s.goals.length + s.scopes.length + s.goals.reduce((n, g) => n + g.scopes.filter((x) => x.status === 'open').length, 0)
    const tail = `needs ${s.needs_you}  ${open} open`
    const name = fitCells(line(s.name), Math.max(4, cols - 2 - tail.length - 2))
    return clipSegs([S(`${mark} `), S(name, { bold: true }), S('  '), S(`needs ${s.needs_you}`, s.needs_you > 0 ? NEEDS : DIM), S(`  ${open} open`, DIM)], cols)
  }
  const n = r.node as Node
  const sym = symbolOf(n)
  const tone = toneOf(n)
  const nextStyle: Style = { color: tone.color, dim: tone.dim }
  const name = line(n.name)
  const headSegs = (): Seg[] => [S(`${ind}${mark} `), S(sym, tone), S(' ')]
  if (n.status === 'done' || !n.facts) {
    const rest = `${day(n.closed_at)}  Closed. Read the report.`
    const head = `${ind}${mark} ${sym} `
    const w = Math.max(4, cols - cellWidth(head) - 2 - cellWidth(rest))
    return clipSegs([...headSegs(), S(`${pad(fitCells(name, w), Math.min(nameW, w))}  `), S(rest, DIM)], cols)
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
    const flagSegs: Seg[] = flags ? [...(needs ? [S(needs, NEEDS)] : []), ...(needs && stuck ? [S(' ')] : []), ...(stuck ? [S(stuck, STUCK)] : []), S('  ')] : []
    return clipSegs([...headSegs(), S(pad(fitCells(name, nameAlloc), nameAlloc) + '  '), ...flagSegs, S(fitCells(nextText, nextAlloc), nextStyle), ...(right ? [S(`  ${right}`, DIM)] : [])], cols)
  }
  const right = mk(c)
  const fixed = cellWidth(head) + 2 + 8 + 2 + 8 + 2 + (right ? 2 + cellWidth(right) : 0)
  const room = Math.max(8, cols - fixed)
  const nw = Math.min(nameW, Math.max(4, Math.floor(room / 3)))
  const next = fitCells(nextText, Math.max(4, Math.min(nextW, room - nw - 2)))
  return clipSegs([
    ...headSegs(), S(pad(fitCells(name, nw), nw) + '  '), ...padSeg(needs, 8, NEEDS), S('  '), ...padSeg(stuck, 8, STUCK), S('  '),
    ...padSeg(next, Math.min(nextW, Math.max(4, room - nw - 2)), nextStyle), ...(right ? [S(`  ${right}`, DIM)] : []),
  ], cols)
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
