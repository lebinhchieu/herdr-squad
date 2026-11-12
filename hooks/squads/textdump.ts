// The drawn pane as text, for tests and for `hooks/squads/pane-text` (QA blackbox). A Box with no flexDirection or `row`
// draws its children side by side; a plain Button is its label, any other Button is `[ label ]`; a `column` Box stacks.
import { cellWidth, clipCells } from '../po-inbox/core'

const textOf = (n: any): string => (n === null || n === undefined || n === false ? '' : typeof n === 'string' ? n : Array.isArray(n) ? n.map(textOf).join('') : textOf(n.children ?? []))

function wrapText(s: string, cols: number): string[] {
  const out: string[] = []
  for (const para of s.split('\n')) {
    let cur = ''
    for (const word of para.split(' ')) {
      const next = cur === '' ? word : `${cur} ${word}`
      if (cur !== '' && cellWidth(next) > cols) {
        out.push(cur)
        cur = word
      } else cur = next
    }
    out.push(cur)
  }
  return out
}

function side(n: any): string {
  if (n === null || n === undefined || n === false) return ''
  if (typeof n === 'string') return n
  if (Array.isArray(n)) return n.map(side).join('')
  if (n.type === 'Button') {
    const label = n.props?.label ?? textOf(n)
    return n.props?.plain ? label : `[ ${label} ]`
  }
  if (n.type === 'Input') return `${n.props?.label ?? ''}${n.props?.value ?? ''}▏`
  return (n.children ?? []).map(side).join('')
}

export function dumpTree(node: any, cols: number, out: string[] = []): string[] {
  if (node === null || node === undefined || node === false || typeof node === 'string') return out
  if (Array.isArray(node)) {
    node.forEach((n) => dumpTree(n, cols, out))
    return out
  }
  if (node.type === 'Box') {
    if ((node.props?.flexDirection ?? 'row') === 'row') {
      const s = (node.children ?? []).map(side).join('')
      if (s !== '') out.push(s)
    } else dumpTree(node.children ?? [], cols, out)
    return out
  }
  if (node.type === 'Text') {
    const s = textOf(node)
    if (node.props?.wrap === 'truncate') out.push(clipCells(s, cols))
    else out.push(...wrapText(s, cols))
    return out
  }
  const s = side(node)
  if (s !== '') out.push(s)
  return out
}

export const dumpText = (node: any, cols: number): string => dumpTree(node, cols).join('\n')
