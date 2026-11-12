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

// Evidence for the styles: each styled run printed next to its text as `‹style: text›`; an unstyled run is bare.
// Style words: the theme key, `bold`, `dim`. A Button shows its children's runs (or its label when it has none).
const styleOf = (p: any): string => [p?.color, p?.bold ? 'bold' : '', p?.dimColor ? 'dim' : ''].filter(Boolean).join(' ')
const runsOf = (n: any, inherit: string): string => {
  if (n === null || n === undefined || n === false) return ''
  if (typeof n === 'string') return inherit ? `‹${inherit}: ${n}›` : n
  if (Array.isArray(n)) return n.map((x) => runsOf(x, inherit)).join('')
  if (n.type === 'Button') {
    const kids = n.children ?? []
    const body = kids.length ? runsOf(kids, inherit) : runsOf(n.props?.label ?? '', inherit)
    return n.props?.plain ? body : `[ ${body} ]`
  }
  if (n.type === 'Input') return `${n.props?.label ?? ''}${n.props?.value ?? ''}▏`
  const own = styleOf(n.props)
  return runsOf(n.children ?? [], n.type === 'Text' ? own || inherit : inherit)
}

export function dumpStyled(node: any): string {
  const out: string[] = []
  const walk = (n: any): void => {
    if (n === null || n === undefined || n === false || typeof n === 'string') return
    if (Array.isArray(n)) return n.forEach(walk)
    if (n.type === 'Box' && (n.props?.flexDirection ?? 'row') !== 'row') return walk(n.children ?? [])
    const s = runsOf(n, '')
    if (s !== '') out.push(s)
  }
  walk(node)
  return out.join('\n')
}
