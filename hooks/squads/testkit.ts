// Shared by the squads tests and by the generated render test: boot the plugin with a stubbed squad-tree and mount the pane.
import { mock } from 'claude-code/testing'

export const START = { cwd: '/w', surface: 'terminal', isInteractive: true } as const
export const KEYS = { plugin: 'squad' } as const

export const pane = (surface: string, cols = 100, bodyRows = 20) =>
  ({
    plugin: 'squad', surface, component: 'Pane', requestId: 'squads',
    props: { title: 'Squads', isFocused: true, bodyColumns: cols, placement: 'inline', scroll: { bodyRows }, view: {} },
  }) as any

export type World = { runs: string[][]; copies: any[]; opened: any[]; fsCalls: number; reply: { exitCode: number; stdout: string; stderr: string }; copied: boolean; clock: any; gate: Promise<void> | null }

// `stdout` is what bin/squad-tree prints; `reply` may be changed between presses.
export async function boot($: any, on: any, stdout: string): Promise<World> {
  const w: World = {
    runs: [], copies: [], opened: [], fsCalls: 0, copied: true, clock: undefined as any, gate: null,
    reply: { exitCode: 0, stdout, stderr: '' },
  }
  mock.env(on, {})
  w.clock = mock.clock(on)
  on('session.start', (_$: any, e: any) => ({ cwd: e.cwd }))
  on('process.run', async (_$: any, e: any) => {
    w.runs.push(e.argv)
    if (w.gate) await w.gate
    return { value: { ...w.reply, isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('fs.stat', () => { w.fsCalls += 1; return { value: { kind: 'file', size: 1, mtimeMs: 1, isLink: false } } })
  on('fs.write', () => { w.fsCalls += 1; return { value: undefined } })
  on('command.register', (_$: any, e: any) => ({ value: { command: e.name } }))
  on('ui.open', (_$: any, e: any) => (w.opened.push(e), { value: { isPlaced: true } }))
  on('ui.close', () => ({ value: undefined }))
  on('ui.copy', (_$: any, e: any) => (w.copies.push(e), { value: { isCopied: w.copied } }))
  on('ui.toast', () => ({ value: undefined }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['ENGINE'] }) as any)
  await $.session.start(START)
  return w
}
