// Drawing of the item screen's structured parts (IV-03): body blocks, inline spans, tables, option blocks.
// Pure functions of props, no `$`. Colour is a theme key from TONE or weight only (V-15, V-18). Every function that
// draws rows also says how many rows it drew, by the same `rowsFor` the screen uses for its cut (T9 v3).
import { cellWidth, clipCells, rowsFor, tableLayout, TONE } from './core'
import type { Block, Span } from './markup'

type T = { Box: any; Text: any; Button: any }
// `parts` are the row nodes of a code block or table, for a row clip.
export type Drawn = { node: any; rows: number; parts?: any[] }

// The longest prefix of `text` that, with a `…`, takes at most `rows` rows at `cols`. Whole text when it fits.
export function clipRows(text: string, cols: number, rows: number): string {
  if (rows < 1) return ''
  if (rowsFor(text, cols) <= rows) return text
  const chars = Array.from(text)
  const take = (n: number) => `${chars.slice(0, n).join('').trimEnd()}…`
  let lo = 0
  let hi = chars.length
  while (lo < hi) {
    const mid = Math.ceil((lo + hi) / 2)
    if (rowsFor(take(mid), cols) <= rows) lo = mid
    else hi = mid - 1
  }
  // rowsFor is not strictly monotone in the prefix; step down until the verdict holds.
  while (lo > 0 && rowsFor(take(lo), cols) > rows) lo--
  return take(lo)
}

// `text` cut into rows of at most `width` cells, by code point (a wide char that does not fit starts the next row).
export function wrapCells(text: string, width: number): string[] {
  const w = Math.max(1, width)
  const out: string[] = []
  let row = ''
  let used = 0
  for (const ch of text) {
    const cw = cellWidth(ch)
    if (used > 0 && used + cw > w) {
      out.push(row)
      row = ''
      used = 0
    }
    row += ch
    used += cw
  }
  out.push(row)
  return out
}

export const toneProps = (t: string): Record<string, unknown> =>
  t === 'good' ? { color: TONE.good } : t === 'bad' ? { color: TONE.bad } : t === 'warn' ? { color: TONE.warn } : t === 'dim' ? { dimColor: true } : {}

// Words of a span list, a space at an emphasis boundary (the words of plainOf).
const spansText = (spans: Span[]): string =>
  spans.reduce((acc, s, i) => acc + (i > 0 && (s.kind !== 'text' || spans[i - 1].kind !== 'text') ? ' ' : '') + s.text, '')

// What a span list draws as plain text: a code chip is its text, no padding (the plain spaces of the sentence stay).
const drawnText = (spans: Span[]): string => spans.map((s) => s.text).join('')

export function drawSpans(spans: Span[], T: T, base = ''): any[] {
  const { Text } = T
  return spans.map((s, i) =>
    s.kind === 'bold' ? (
      <Text key={`${base}s${i}`} bold>{s.text}</Text>
    ) : s.kind === 'code' ? (
      <Text key={`${base}s${i}`} inverse>{s.text}</Text>
    ) : (
      s.text
    ),
  )
}

const GLYPHS = ['•', '◦', '▪']

// Indent is capped so a hostile run of leading spaces cannot push the text out of the pane.
const indentFor = (depth: number, cols: number): number => Math.min(2 * depth, Math.max(0, Math.floor(cols / 2) - 4))

// A hanging row: a fixed prefix, then text that wraps under itself.
function hanging(key: string, prefix: any, prefixWidth: number, content: any, T: T) {
  const { Box, Text } = T
  return (
    <Box key={key} flexDirection="row">
      <Box key="p" width={prefixWidth} flexShrink={0}>{prefix}</Box>
      <Box key="c" flexDirection="column" flexShrink={1}>{content}</Box>
    </Box>
  )
}

function drawTable(b: Extract<Block, { type: 'table' }>, cols: number, T: T, key: string): Drawn {
  const { Box, Text } = T
  const header = b.header.map(spansText)
  const rows = b.rows.map((r) => r.map(spansText))
  const lay = tableLayout({ header, rows }, cols)
  const out: any[] = []
  let n = 0
  if (lay.kind === 'aligned') {
    const pad = (s: string, w: number) => s + ' '.repeat(Math.max(0, w - cellWidth(s)))
    const row = (cells: string[]) => lay.widths.map((w, i) => pad(cells[i] ?? '', w)).join('  ').trimEnd()
    out.push(<Text key="h" bold wrap="wrap">{row(header)}</Text>)
    out.push(<Text key="r" wrap="wrap">{lay.widths.map((w) => '─'.repeat(w)).join('  ')}</Text>)
    rows.forEach((r, i) => out.push(<Text key={`t${i}`} wrap="wrap">{row(r)}</Text>))
    n = 2 + rows.length
  } else {
    lay.rows.forEach((rec, i) => {
      if (i > 0) {
        out.push(<Text key={`g${i}`}>{' '}</Text>)
        n += 1
      }
      rec.forEach((c, j) => {
        out.push(
          <Text key={`c${i}-${j}`} wrap="wrap">
            <Text bold>{c.column}</Text>
            {c.value === '' ? ':' : `: ${c.value}`}
          </Text>,
        )
        n += rowsFor(c.value === '' ? `${c.column}:` : `${c.column}: ${c.value}`, cols)
      })
    })
  }
  return { node: <Box key={key} flexDirection="column">{out}</Box>, rows: n, parts: out }
}

function drawCode(b: Extract<Block, { type: 'code' }>, cols: number, T: T, key: string): Drawn {
  const { Box, Text } = T
  const out: any[] = []
  if (b.lang !== '') out.push(<Text key="l" italic wrap="wrap">{b.lang}</Text>)
  let n = b.lang === '' ? 0 : rowsFor(b.lang, cols)
  b.lines.forEach((l, i) => {
    wrapCells(l.split('\t').join('    '), cols - 4).forEach((r, j) => {
      out.push(<Text key={`c${i}-${j}`}>{`  │ ${r}`}</Text>)
      n += 1
    })
  })
  return { node: <Box key={key} flexDirection="column">{out}</Box>, rows: n, parts: out }
}

export function drawBlock(b: Block, cols: number, T: T, key: string): Drawn {
  const { Text } = T
  switch (b.type) {
    case 'blank':
      return { node: <Text key={key}>{' '}</Text>, rows: 1 }
    case 'heading': {
      const props = b.level === 1 ? { bold: true, underline: true } : b.level === 2 ? { bold: true } : { bold: true, italic: true }
      return { node: <Text key={key} {...props} wrap="wrap">{drawSpans(b.spans, T, key)}</Text>, rows: rowsFor(drawnText(b.spans), cols) }
    }
    case 'rec': {
      const rest = drawnText(b.spans)
      const pad = recPad(b)
      return {
        node: (
          <Text key={key} wrap="wrap">
            {pad}
            <Text color={TONE.good} bold>✓ recommended</Text>
            {rest === '' ? null : ' '}
            {drawSpans(b.spans, T, key)}
          </Text>
        ),
        rows: rowsFor(`${recPad(b, NBSP)}✓ recommended${rest === '' ? '' : ' '}${rest}`, cols),
      }
    }
    case 'bullet':
    case 'number': {
      const indent = ' '.repeat(indentFor(b.depth, cols))
      const mark = b.type === 'bullet' ? GLYPHS[Math.min(b.depth, 2)] : `${b.n}.`
      const prefix = `${indent}${mark} `
      const pw = cellWidth(prefix)
      return {
        node: hanging(key, b.type === 'bullet' ? <Text key="m">{prefix}</Text> : <Text key="m">{indent}<Text bold>{mark}</Text>{' '}</Text>, pw, <Text key="t" wrap="wrap">{drawSpans(b.spans, T, key)}</Text>, T),
        rows: rowsFor(drawnText(b.spans), Math.max(1, cols - pw)),
      }
    }
    case 'code':
      return drawCode(b, cols, T, key)
    case 'table':
      return drawTable(b, cols, T, key)
    default:
      return { node: <Text key={key} wrap="wrap">{drawSpans(b.spans, T, key)}</Text>, rows: rowsFor(drawnText(b.spans), cols) }
  }
}

// Source lines a block stands for ("N more lines"): fences and a table's separator are lines too.
export function sourceLines(b: Block): number {
  return b.type === 'code' ? b.lines.length + 2 : b.type === 'table' ? b.rows.length + 2 : 1
}

// `rowsFor` drops leading spaces, so the counted and clipped text carries the indent as no-break spaces.
const NBSP = '\u00a0'
const recPad = (b: { indent?: number }, ch = ' ') => ch.repeat(Math.min(b.indent ?? 0, 8))

// The text of a block as plain words, for a clip of a first block taller than the budget.
function plainText(b: Block): string {
  if (b.type === 'blank') return ''
  if (b.type === 'code') return [...(b.lang === '' ? [] : [b.lang]), ...b.lines].join('\n')
  if (b.type === 'table') return [b.header, ...b.rows].map((r) => r.map(spansText).join('  ')).join('\n')
  const t = drawnText(b.spans)
  return b.type === 'bullet' ? `• ${t}` : b.type === 'number' ? `${b.n}. ${t}` : b.type === 'rec' ? `${recPad(b, NBSP)}✓ recommended ${t}` : t
}

// Runs of blank lines draw one blank row; none at either end of what is drawn.
function squeeze(blocks: Block[]): Block[] {
  const out: Block[] = []
  for (const b of blocks) if (b.type !== 'blank' || (out.length > 0 && out[out.length - 1].type !== 'blank')) out.push(b)
  while (out.length > 0 && out[out.length - 1].type === 'blank') out.pop()
  return out
}

// `tall`: a blank row above every heading that is not the first block (P8).
export type BodyPlan = { expanded: boolean; fitRows: number; budget: number; tall?: boolean }
export type DrawnBody = { nodes: any[]; rows: number; cut: boolean; hidden: number; hiddenRows: number }

// T9 v3: everything when `expanded` or when it fits `fitRows`; else whole blocks while they fit `budget`, the first
// block clipped when it alone is taller. `hidden` counts source lines not drawn (a clipped block counts as left).
export function drawBody(all: Block[], cols: number, T: T, plan: BodyPlan): DrawnBody {
  const squeezed = squeeze(all)
  const blocks: Block[] = []
  squeezed.forEach((b, i) => {
    if (plan.tall && b.type === 'heading' && i > 0 && blocks[blocks.length - 1].type !== 'blank') blocks.push({ type: 'blank' })
    blocks.push(b)
  })
  if (blocks.length === 0) return { nodes: [], rows: 0, cut: false, hidden: 0, hiddenRows: 0 }
  const drawn: Drawn[] = []
  let total = 0
  const stopAt = plan.expanded ? Infinity : Math.max(plan.fitRows, plan.budget)
  let i = 0
  for (; i < blocks.length && total <= stopAt; i++) {
    const d = drawBlock(blocks[i], cols, T, `b${i}`)
    drawn.push(d)
    total += d.rows
  }
  if (i === blocks.length && (plan.expanded || total <= plan.fitRows)) return { nodes: drawn.map((d) => d.node), rows: total, cut: false, hidden: 0, hiddenRows: 0 }
  const nodes: any[] = []
  let used = 0
  let k = 0
  for (; k < drawn.length && used + drawn[k].rows <= plan.budget; k++) {
    nodes.push(drawn[k].node)
    used += drawn[k].rows
  }
  let clipped = false
  if (k === 0 && drawn.length > 0) {
    const { Text } = T
    const b = blocks[0]
    if (b.type === 'code' || b.type === 'table') {
      // A row clip of a structured block: its first rows, then `…`.
      const keep = Math.max(1, plan.budget - 1)
      nodes.push(<T.Box key="b0" flexDirection="column">{[...(drawn[0].parts ?? []).slice(0, keep), <Text key="cut">…</Text>]}</T.Box>)
      used = keep + 1
    } else {
      nodes.push(<Text key="b0" wrap="wrap">{clipRows(plainText(b), cols, plan.budget)}</Text>)
      used = plan.budget
    }
    clipped = true
    k = 1
  }
  while (nodes.length > 0 && blocks[k - 1]?.type === 'blank' && !clipped) {
    nodes.pop()
    k--
    used -= 1
  }
  let hidden = 0
  for (let j = clipped ? 0 : k; j < blocks.length; j++) hidden += sourceLines(blocks[j])
  if (clipped) hidden -= sourceLines(blocks[0]) - 1 // the clipped block counts as one line left
  let allRows = 0
  blocks.forEach((b, j) => {
    allRows += drawn[j] ? drawn[j].rows : drawBlock(b, cols, T, `x${j}`).rows
  })
  return { nodes, rows: used, cut: hidden > 0, hidden, hiddenRows: Math.max(hidden > 0 ? 1 : 0, allRows - used) }
}

export type Opt = { key: string; text: string }

const REC_TAG = '✓ rec'

// Option rows (item.md section 3). `pick` makes each a pickable `<Button plain>` (`○`/`●`); without it they are text rows
// (a handled item). Short tier: one row, the recommended option ends in `✓ rec`. Tall tier: up to 2 rows, and the full
// recommendation under the marked option. Returns the nodes and the rows they take. Texts arrive sanitised.
export function optionRows(
  options: Opt[], rec: string | null, recKey: string | null, picked: string | null, cols: number, tall: boolean,
  pick: ((key: string) => void) | null, T: T,
): { nodes: any[]; rows: number } {
  const { Box, Text, Button } = T
  const nodes: any[] = []
  let rows = 0
  for (const o of options) {
    const mark = `${picked === o.key ? '●' : '○'} (${o.key}) `
    const isRec = recKey === o.key && rec !== null
    const pw = cellWidth(mark)
    const tag = !tall && isRec
    const width = Math.max(1, cols - pw - (tag ? cellWidth(REC_TAG) + 1 : 0))
    const lines = wrapCells2(o.text, width, tall ? 2 : 1)
    const indent = ' '.repeat(pw)
    const text = lines.map((l, i) => (i === 0 ? l : `${indent}${l}`)).join('\n')
    const tagNode = tag ? <Text key="tag" color={TONE.good}>{`${' '.repeat(Math.max(1, width - cellWidth(lines[0]) + 1))}${REC_TAG}`}</Text> : null
    const children = [<Text key="m" bold={picked === o.key}>{mark}</Text>, <Text key="t">{text}</Text>, tagNode]
    const row = pick ? (
      <Button key={`opt-${o.key}`} plain onPress={() => pick(o.key)}>{children}</Button>
    ) : (
      <Text key={`opt-${o.key}`}>{children}</Text>
    )
    nodes.push(row)
    rows += lines.length
    if (tall && isRec) {
      const reason = `✓ recommended: ${rec}`
      nodes.push(
        <Text key={`r${o.key}`} wrap="wrap">
          {indent}
          <Text color={TONE.good} bold>✓ recommended: </Text>
          {rec}
        </Text>,
      )
      rows += rowsFor(`${indent}${reason}`, cols)
    }
  }
  return { nodes: [<Box key="opts" flexDirection="column">{nodes}</Box>], rows }
}

// Wraps by words to `width` cells, at most `maxRows` rows; the last row ends with `…` when text is cut.
function wrapCells2(text: string, width: number, maxRows: number): string[] {
  if (maxRows <= 1) return [clipLine(text, width)]
  const rows: string[] = []
  let rest = text
  while (rows.length < maxRows - 1 && cellWidth(rest) > width) {
    let cut = ''
    let used = 0
    let lastSpace = -1
    const chars = Array.from(rest)
    let n = 0
    for (; n < chars.length; n++) {
      const w = cellWidth(chars[n])
      if (used + w > width) break
      used += w
      cut += chars[n]
      if (chars[n] === ' ') lastSpace = n
    }
    const at = lastSpace > 0 ? lastSpace : n
    rows.push(chars.slice(0, at).join('').trimEnd())
    rest = chars.slice(at).join('').trimStart()
  }
  rows.push(clipLine(rest, width))
  return rows
}

const clipLine = (t: string, width: number): string => clipCells(t, width)
