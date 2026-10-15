// Everything of the po-inbox mod that touches `$`. The only file access is `$.fs.stat`; the only
// process is the plugin's own bin/squad-inbox, run by argv (no shell). PI-04's pane calls answerItem.
import { atom, read, update } from 'claude-code'

import type { InboxItem } from '../../types'
import { describePrompt, newOpenIds, parseSnapshot, sanitize, toastText, waitingItems } from './core'

export const inboxAtom = atom({ plugin: 'squad', key: 'inbox' } as const, null)
export const errorAtom = atom({ plugin: 'squad', key: 'inboxError' } as const, null)
export const uiAtom = atom({ plugin: 'squad', key: 'ui' } as const, { selected: null, isOpen: false })

const POLL_MS = 2000
const CLI_TIMEOUT_MS = 20000
const WATCHED = ['inbox.jsonl', 'escalations.md']

// Module state: one load of the mod, one session. A reload starts it over (the atoms stay).
const run = {
  home: '',
  isPending: false,
  sig: '',
  timer: undefined as { cancel: () => void } | undefined,
  isCommandRegistered: false,
  inflight: new Set<string>(),
  failed: new Set<string>(),
  sent: new Set<string>(),
  tries: new Map<string, number>(),
}

// T2: a Manager (SQUAD_ROLE=manager) with a home. Anything else loads the mod and does nothing.
export async function homeOf($: any): Promise<string | null> {
  const role = await $.env.get('SQUAD_ROLE')
  if (role !== 'manager') return null
  const scope = await $.env.get('SCOPE_DIR')
  if (scope) return scope
  const goal = await $.env.get('GOAL_DIR')
  return goal ? goal : null
}

export function isActive(): boolean {
  return run.home !== ''
}

function failure(r: { exitCode: number; stdout: string; stderr: string }): string {
  const said = sanitize((r.stderr || r.stdout).trim()).split('\n')[0].slice(0, 300)
  return said || `squad-inbox exited ${r.exitCode}`
}

async function setError($: any, message: string | null): Promise<void> {
  await update($, errorAtom, () => message)
}

// Runs `list --json`. A crash, a non-zero exit or a snapshot that fails the contract keeps the last
// good snapshot and sets the error state; it never throws.
export async function refresh($: any): Promise<boolean> {
  try {
    const r = await $.process.run([`${$.plugin.root}/bin/squad-inbox`, 'list', '--json'], { timeoutMs: CLI_TIMEOUT_MS })
    if (r.exitCode !== 0) throw new Error(`squad-inbox list failed: ${failure(r)}`)
    const parsed = parseSnapshot(r.stdout)
    if (!parsed.ok) throw new Error(parsed.error)
    const prev = await read($, inboxAtom)
    await update($, inboxAtom, () => parsed.snapshot)
    await setError($, null)
    const fresh = newOpenIds(prev, parsed.snapshot)
    const added = parsed.snapshot.items.filter((i) => fresh.includes(i.id))
    if (added.length === 1) await $.ui.toast(toastText(added[0]))
    else if (added.length > 1) await $.ui.toast(`${added.length} new items in the inbox`)
    return true
  } catch (e) {
    try {
      await setError($, e instanceof Error ? e.message : String(e))
    } catch {
      // the error state is best effort; a hook must not throw
    }
    return false
  }
}

async function signature($: any): Promise<string> {
  const parts: string[] = []
  for (const name of WATCHED) {
    try {
      const st = await $.fs.stat(`${run.home}/${name}`)
      parts.push(`${st.mtimeMs}:${st.size}`)
    } catch {
      parts.push('none')
    }
  }
  return parts.join('|')
}

// One poll tick: two stats, and the CLI only when one changed. No second run while one is pending.
export async function tick($: any): Promise<void> {
  if (run.isPending) return
  run.isPending = true
  try {
    const sig = await signature($)
    if (sig === run.sig) return
    if (await refresh($)) run.sig = sig
  } finally {
    run.isPending = false
  }
}

async function sendAndMark($: any, id: string, text: string): Promise<void> {
  try {
    if (!run.sent.has(id)) {
      const sent = await $.prompt.submit({ text })
      if (sent && sent.drop !== undefined) throw new Error(`the prompt was not accepted: ${sent.drop}`)
      run.sent.add(id)
    }
    const r = await $.process.run(
      [`${$.plugin.root}/bin/squad-inbox`, 'delivered', id, '--session', String(await $.session.id())],
      { timeoutMs: CLI_TIMEOUT_MS },
    )
    if (r.exitCode !== 0) throw new Error(`squad-inbox delivered failed: ${failure(r)}`)
    run.failed.delete(id)
    run.sent.delete(id)
    run.tries.delete(id)
    await refresh($)
  } catch (e) {
    // No `delivered`: retried once at the next turn.complete (the answer is never submitted twice),
    // then dropped with the error left showing.
    run.failed.add(id)
    try {
      await setError($, e instanceof Error ? e.message : String(e))
    } catch {
      // best effort
    }
  } finally {
    run.inflight.delete(id)
  }
}

// $.prompt.submit waits for the running turn (spike S1) and awaiting it inside a hook never ran
// (spike S1b): start it unawaited. One submit per item at a time.
export function deliver($: any, item: { id: string; title: string }, answerText: string): void {
  if (run.inflight.has(item.id)) return
  const tries = run.tries.get(item.id) ?? 0
  if (tries >= 2) return
  run.tries.set(item.id, tries + 1)
  run.inflight.add(item.id)
  void sendAndMark($, item.id, describePrompt(item, answerText))
}

export async function deliverWaiting($: any): Promise<void> {
  const snap = await read($, inboxAtom)
  if (!snap) return
  for (const it of waitingItems(snap)) {
    if (it.answer) deliver($, it, it.answer.text)
  }
}

export async function retryFailed($: any): Promise<void> {
  if (run.failed.size === 0) return
  const snap = await read($, inboxAtom)
  if (!snap) return
  const again = waitingItems(snap).filter((it) => run.failed.has(it.id))
  for (const it of again) {
    if (it.answer) deliver($, it, it.answer.text)
  }
}

export type AnswerInput = { id: string; option?: string; text?: string; note?: string }
export type AnswerResult = { ok: true; message?: string } | { ok: false; message: string }

// The pane's submit (PI-04): record the answer through the CLI (text by stdin), then hand it to the model.
export async function answerItem($: any, input: AnswerInput): Promise<AnswerResult> {
  const sent = input.text ?? input.note ?? ''
  const argv = [`${$.plugin.root}/bin/squad-inbox`, 'answer', input.id]
  if (input.option) argv.push('--option', input.option)
  argv.push('--source', 'pane')
  let r
  try {
    r = await $.process.run(argv, { stdin: sent, timeoutMs: CLI_TIMEOUT_MS })
  } catch (e) {
    return { ok: false, message: e instanceof Error ? e.message : String(e) }
  }
  if (r.exitCode !== 0) {
    await refresh($)
    return { ok: false, message: failure(r) }
  }
  await refresh($)
  const snap = await read($, inboxAtom)
  const item: InboxItem | undefined = snap?.items.find((it) => it.id === input.id)
  if (!item?.answer) {
    // Recorded but not readable back: send nothing; the item stays answered-waiting and the redelivery sends the recorded text.
    return { ok: true, message: `${input.id} answered; delivery to the Manager waits for the next load` }
  }
  deliver($, { id: input.id, title: item.title }, item.answer.text)
  return { ok: true }
}

// session.start: register once, load, redeliver, and leave exactly one timer however often it fires.
export async function start($: any, home: string): Promise<void> {
  run.home = home
  if (!run.isCommandRegistered) {
    run.isCommandRegistered = true
    await $.command.register({ name: 'inbox', description: 'Open the PO inbox: items to answer or read' })
  }
  if (run.timer) run.timer.cancel()
  run.timer = undefined
  const sig = await signature($)
  run.sig = (await refresh($)) ? sig : ''
  await deliverWaiting($)
  run.timer = $.clock.every(POLL_MS, () => {
    void tick($)
  })
}

export function stop(): void {
  if (run.timer) run.timer.cancel()
  run.timer = undefined
  run.home = ''
  run.sent.clear()
  run.tries.clear()
}

export async function openPane($: any): Promise<void> {
  await update($, uiAtom, (ui) => ({ ...ui, isOpen: true }))
  await $.ui.open({ id: 'inbox', title: 'Inbox' })
}
