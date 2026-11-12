// Everything of the /squads mod that touches `$`. The only process is the plugin's own bin/squad-tree, run by argv
// (no shell) for data. A press on a row or a command never starts a process and never writes a file: it only copies.
import { atom, read, update } from 'claude-code'

import type { SquadCommand, SquadsTree, SquadsUi } from '../../types'
import { line, noticeCopied, noticeFailed, parseTree } from './core'

export const PANE = 'squads'
const REFRESH_MS = 10000
const CLI_TIMEOUT_MS = 20000

export const FRESH_UI: SquadsUi = { isOpen: false, path: [], folded: [], filter: '', top: 0, isFiltering: false, notice: null }

// `shape` declines a value an earlier version of these fields stored (it outlives a reload).
export const treeAtom = atom({ plugin: 'squad', key: 'squadsTree' } as const, null as SquadsTree | null, { shape: 'squads-tree-1' })
export const errorAtom = atom({ plugin: 'squad', key: 'squadsError' } as const, null as string | null, { shape: 'squads-error-1' })
export const uiAtom = atom({ plugin: 'squad', key: 'squadsUi' } as const, FRESH_UI, { shape: 'squads-ui-1' })

// Module state: one load of the mod. A reload starts it over (the atoms stay).
const run = { isPending: false, timer: undefined as { cancel: () => void } | undefined, isCommandRegistered: false }

export const cliArgv = (root: string): string[] => ['python3', `${root}/bin/squad-tree`, '--json']

function failure(r: { exitCode: number; stdout: string; stderr: string }): string {
  const said = line((r.stderr || r.stdout).trim().split('\n')[0] ?? '').slice(0, 300)
  return said || `squad-tree exited ${r.exitCode}`
}

// One data run. A crash, a non-zero exit, bad JSON or another version keeps the last good tree and sets the error.
export async function refresh($: any): Promise<boolean> {
  if (run.isPending) return false
  run.isPending = true
  try {
    const r = await $.process.run(cliArgv($.plugin.root), { timeoutMs: CLI_TIMEOUT_MS })
    if (r.exitCode !== 0) throw new Error(`squad-tree failed: ${failure(r)}`)
    const parsed = parseTree(r.stdout)
    if (!parsed.ok) throw new Error(parsed.error)
    await update($, treeAtom, () => parsed.tree)
    await update($, errorAtom, () => null)
    return true
  } catch (e) {
    try {
      await update($, errorAtom, () => (e instanceof Error ? e.message : String(e)))
    } catch {
      // best effort: a hook must not throw
    }
    return false
  } finally {
    run.isPending = false
  }
}

export async function start($: any): Promise<void> {
  if (!run.isCommandRegistered) {
    run.isCommandRegistered = true
    await $.command.register({ name: 'squads', description: 'List every squad, goal and scope, with the next step and commands to copy' })
  }
  if (run.timer) run.timer.cancel()
  // The tick runs the data command only while the pane is open and no run is pending.
  run.timer = $.clock.every(REFRESH_MS, async () => {
    const ui = await read($, uiAtom)
    if (ui.isOpen) void refresh($)
  })
}

export async function openPane($: any): Promise<void> {
  await update($, uiAtom, (ui) => ({ ...ui, isOpen: true, path: [], notice: null }))
  await $.ui.open({ id: PANE, title: 'Squads', focus: true, closeOnEscape: true, rows: 18 })
  void refresh($)
}

export async function view($: any): Promise<{ ui: SquadsUi; tree: SquadsTree | null; error: string | null }> {
  return { ui: await read($, uiAtom), tree: await read($, treeAtom), error: await read($, errorAtom) }
}

export async function patchUi($: any, patch: Partial<SquadsUi>): Promise<void> {
  await update($, uiAtom, (ui) => ({ ...ui, ...patch }))
}

export async function select($: any, path: string[]): Promise<void> {
  await patchUi($, { path, notice: null })
}

export async function back($: any): Promise<void> {
  await patchUi($, { path: [], notice: null })
}

export async function scrollTo($: any, top: number): Promise<void> {
  await patchUi($, { top: Math.max(0, top) })
}

export async function toggle($: any, key: string, startsClosed: boolean): Promise<void> {
  const k = startsClosed ? `+${key}` : key
  await update($, uiAtom, (ui) => ({ ...ui, folded: ui.folded.includes(k) ? ui.folded.filter((x) => x !== k) : [...ui.folded, k] }))
}

export async function setFilter($: any, filter: string): Promise<void> {
  await patchUi($, { filter: line(filter), top: 0 })
}

// The only thing a command press does: copy the text from the JSON, and say whether it worked.
export async function copyCommand($: any, c: SquadCommand, surface: unknown): Promise<void> {
  let ok = false
  try {
    ok = (await $.ui.copy({ text: c.text, surface })).isCopied === true
  } catch {
    ok = false
  }
  await patchUi($, { notice: ok ? noticeCopied(c) : noticeFailed() })
}
