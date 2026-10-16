// Shared by the visual tickets' tests: mount the pane, read text, colour and weight from the drawn tree.
// `boot`, `item`, `snap`, `band`, `pane`, `lines`, `dump` are copies of the helpers in ui.test.ts (which is not edited).
import { mock } from 'claude-code/testing'

import { rowsFor } from './core'

export const START = { cwd: '/w', surface: null, isInteractive: true } as const
export const NOW = '2026-10-15T12:00:00'

export const item = (o: Record<string, unknown>) => ({
  id: 'E3', kind: 'answer', state: 'open', title: 'Which branch merges first?', body: 'Body line',
  options: null, options_raw: null, recommendation: null, blocks: 'PI-04', created: '2026-10-13T09:10:00',
  created_precision: 'second', answer: null, done: null, flags: [], ...o,
})

export const snap = (items: any[], errors: any[] = []) => ({
  version: 1, home: '/h', now: NOW,
  counts: {
    answer_open: items.filter((i) => i.state === 'open' && i.kind === 'answer').length,
    read_open: items.filter((i) => i.state === 'open' && i.kind === 'read').length,
    waiting: items.filter((i) => i.state === 'answered-waiting').length,
  },
  items, errors,
})

export async function boot($: any, on: any, s: unknown, cli?: (argv: string[], stdin?: string) => any) {
  const w = { runs: [] as { argv: string[]; stdin?: string }[], submits: [] as string[], opened: [] as any[], order: [] as string[], current: s }
  mock.env(on, { SQUAD_ROLE: 'manager', SCOPE_DIR: '/h' })
  mock.clock(on)
  on('session.start', (_$: any, e: any) => ({ cwd: e.cwd }))
  on('process.run', (_$: any, e: any) => {
    w.runs.push({ argv: [...e.argv], stdin: e.init?.stdin })
    const r = cli ? cli(e.argv.slice(1), e.init?.stdin) : undefined
    const out = r ?? { exitCode: 0, stdout: JSON.stringify(w.current), stderr: '' }
    return { value: { ...out, isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('fs.stat', () => ({ value: { kind: 'file', size: 1, mtimeMs: 1, isLink: false } }))
  on('command.register', (_$: any, e: any) => ({ value: { command: e.name } }))
  on('ui.open', (_$: any, e: any) => (w.opened.push(e), w.order.push('open'), { value: { isPlaced: true } }))
  on('ui.close', () => (w.order.push('close'), { value: undefined }))
  on('prompt.submit', (_$: any, e: any) => (w.submits.push(e.text), { text: e.text }))
  on('session.id', () => ({ value: 'sess-1' }))
  on('ui.toast', () => ({ value: undefined }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['ENGINE'] }) as any)
  await $.session.start(START)
  return w
}

export const band = (surface: string, cols = 100, extra: Record<string, unknown> = {}) =>
  ({
    plugin: 'squad', surface, component: 'AbovePrompt',
    props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: cols, scroll: { bodyRows: 5 }, ...extra },
  }) as any

// `bodyRows` is a parameter: a UI ticket passes the number the engine really delivers, not a guess.
export const pane = (surface: string, cols = 100, bodyRows = 20) =>
  ({
    plugin: 'squad', surface, component: 'Pane', requestId: 'inbox',
    props: { title: 'Inbox', isFocused: true, bodyColumns: cols, placement: 'inline', scroll: { bodyRows }, view: {} },
  }) as any

export function textOf(node: any): string {
  if (node === null || node === undefined) return ''
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(textOf).join('')
  return textOf(node.children ?? [])
}

// The drawn tree as text lines: a Text block or a Button is one line.
export function lines(node: any, out: string[] = []): string[] {
  if (node === null || node === undefined || typeof node === 'string') return out
  if (Array.isArray(node)) {
    node.forEach((n) => lines(n, out))
    return out
  }
  if (node.type === 'Text') out.push(textOf(node))
  else if (node.type === 'Button') out.push(`[${node.props?.label ?? textOf(node)}]`)
  else if (node.type === 'Input') out.push(`<${node.props?.label ?? ''}${node.props?.value ?? ''}>`)
  else if (node.type === 'Select') out.push(`{${node.props?.label ?? ''}${node.props?.value ?? ''}}`)
  else lines(node.children ?? [], out)
  return out
}
export const dump = async (ui: any) => lines(await ui.drawn()).join('\n')

const STYLE_PROPS = ['color', 'dimColor', 'bold', 'weight', 'italic', 'underline', 'inverse', 'strikethrough', 'backgroundColor']

// Style props of the first Text whose own text contains `text`; null when none does.
export function styleOf(tree: any, text: string): Record<string, unknown> | null {
  if (tree === null || tree === undefined || typeof tree === 'string') return null
  if (Array.isArray(tree)) {
    for (const n of tree) {
      const r = styleOf(n, text)
      if (r) return r
    }
    return null
  }
  if (tree.type === 'Text' && textOf(tree).includes(text)) {
    const out: Record<string, unknown> = {}
    for (const k of STYLE_PROPS) if (tree.props && tree.props[k] !== undefined) out[k] = tree.props[k]
    return out
  }
  return styleOf(tree.children ?? [], text)
}

// Rendered rows of the whole tree at `cols`, by the same estimate the screens use (`rowsFor`);
// a ticket that must not share that estimate counts with its own reference wrap instead.
export const rowsOfTree = (tree: any, cols: number): number => lines(tree).reduce((n, l) => n + rowsFor(l, cols), 0)
