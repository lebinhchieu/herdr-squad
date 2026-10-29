// Drawing of the item screen's structured parts (IV-03): body blocks, inline spans, tables, option blocks.
// Pure functions of props, no `$`. Colour is a theme key from TONE or weight only (V-15, V-18). Every function that
// draws rows also says how many rows it drew, by the same `rowsFor` the screen uses for its cut (T9 v3).
import { ACCENT, CHIPS, chipProps, chipText, cellWidth, diagramRuns, LEGEND_WORD, legendTags, rowsFor, tableLayout, TONE, wrapRows } from './core'
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

// What a span list draws as plain text: a code chip is its text, no padding (the plain spaces of the sentence stay);
// a link is `label <url>` (a bare url is itself); a badge is its filled chip, glyph and padding counted.
const spanDrawn = (s: Span): string =>
  s.kind === 'link' ? (s.text === '' ? s.url : `${s.text} <${s.url}>`) : s.kind === 'badge' ? chipText(s.text) : s.text
const drawnText = (spans: Span[]): string => spans.map(spanDrawn).join('')

export function drawSpans(spans: Span[], T: T, base = ''): any[] {
  const { Text } = T
  return spans.map((s, i) => {
    const key = `${base}s${i}`
    if (s.kind === 'bold') return <Text key={key} bold>{s.text}</Text>
    if (s.kind === 'code') return <Text key={key} inverse>{s.text}</Text>
    if (s.kind === 'badge') return <Text key={key} {...chipProps(CHIPS[s.text].tone)}>{chipText(s.text)}</Text>
    if (s.kind === 'link') {
      // The url is always shown: a pane cannot open it, and no escape sequence leaves the pane.
      return s.text === '' ? (
        <Text key={key} underline>{s.url}</Text>
      ) : (
        <Text key={key}>
          <Text underline>{s.text}</Text>
          {' '}
          <Text dimColor>{`<${s.url}>`}</Text>
        </Text>
      )
    }
    return s.text
  })
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
  const header = b.header.map(drawnText)
  const rows = b.rows.map((r) => r.map(drawnText))
  const lay = tableLayout({ header, rows }, cols)
  const out: any[] = []
  let n = 0
  if (lay.kind === 'aligned') {
    // One Text per row, one child per cell, so a badge cell keeps its colour; the last non-empty cell has no padding.
    const row = (k: string, cells: Span[][], props: Record<string, unknown>) => {
      let last = lay.widths.length - 1
      while (last > 0 && drawnText(cells[last] ?? []) === '') last--
      const parts: any[] = []
      for (let i = 0; i <= last; i++) {
        const sp = cells[i] ?? []
        parts.push(...drawSpans(sp, T, `${k}c${i}`))
        if (i < last) parts.push(' '.repeat(Math.max(0, lay.widths[i] - cellWidth(drawnText(sp))) + 2))
      }
      return <Text key={k} wrap="wrap" {...props}>{parts}</Text>
    }
    out.push(row('h', b.header, { bold: true }))
    out.push(<Text key="r" wrap="wrap">{lay.widths.map((w) => '─'.repeat(w)).join('  ')}</Text>)
    b.rows.forEach((r, i) => out.push(row(`t${i}`, r, {})))
    n = 2 + rows.length
  } else {
    const width = Math.max(header.length, ...rows.map((r) => r.length))
    b.rows.forEach((r, i) => {
      if (i > 0) {
        out.push(<Text key={`g${i}`}>{' '}</Text>)
        n += 1
      }
      for (let j = 0; j < width; j++) {
        const column = header[j] ?? ''
        const value = rows[i][j] ?? ''
        out.push(
          <Text key={`c${i}-${j}`} wrap="wrap">
            <Text bold>{column}</Text>
            {value === '' ? ':' : ': '}
            {drawSpans(r[j] ?? [], T, `c${i}-${j}`)}
          </Text>,
        )
        n += rowsFor(value === '' ? `${column}:` : `${column}: ${value}`, cols)
      }
    })
  }
  return { node: <Box key={key} flexDirection="column">{out}</Box>, rows: n, parts: out }
}

// A diagram (body-styles.md 3): a fence labelled `diagram`, or any fence with a box-drawing character.
const BOX = /[\u2500-\u257f]/
export const isDiagram = (b: Extract<Block, { type: 'code' }>): boolean => /^diagram(\s|$)/.test(b.lang) || b.lines.some((l) => BOX.test(l))

// The first `n` cells of `s`, a wide char that does not fit dropped whole.
function cutCells(s: string, n: number): string {
  let out = ''
  let w = 0
  for (const ch of s) {
    const cw = cellWidth(ch)
    if (w + cw > n) break
    out += ch
    w += cw
  }
  return out
}

// Aligned, never wrapped. Lines wider than `W = cols - 2` are cut to `W - 1` cells and end in `›`, with a footer row. Colour is
// decided on the drawn text: connectors `permission`, state tags filled chips in place, names plain. Every part is one row.
function drawDiagram(b: Extract<Block, { type: 'code' }>, cols: number, T: T, key: string): Drawn {
  const { Box, Text } = T
  if (b.lines.length === 0) return { node: <Box key={key} flexDirection="column" />, rows: 0, parts: [] }
  const W = Math.max(1, cols - 2)
  const lines = b.lines.map((l) => l.split('\t').join('    ').trimEnd())
  const widest = Math.max(...lines.map(cellWidth))
  const shown = lines.map((l) => (cellWidth(l) > W ? `${cutCells(l, W - 1)}›` : l))
  const out: any[] = []
  const caption = (/^diagram(\s|$)/.test(b.lang) ? b.lang.slice(7) : b.lang).trim()
  if (caption !== '') wrapRows(caption, W, 2).forEach((r, i) => out.push(<Text key={`cap${i}`} italic dimColor>{`  ${r}`}</Text>))
  shown.forEach((l, i) => {
    const runs = diagramRuns(l).map((r, j) =>
      r.kind === 'conn' ? (
        <Text key={`d${i}-${j}`} color={ACCENT}>{r.text}</Text>
      ) : r.kind === 'tag' ? (
        <Text key={`d${i}-${j}`} {...chipProps(CHIPS[r.text.slice(1, -1) as 'ok'].tone)}>{r.text}</Text>
      ) : (
        r.text
      ),
    )
    out.push(<Text key={`d${i}`}>{'  '}{runs}</Text>)
  })
  const tags = legendTags(shown)
  if (tags.length > 0) {
    const entry = (t: string) => cellWidth(`[${t}]`) + 1 + cellWidth(LEGEND_WORD[t as 'ok'])
    let row: string[] = []
    let used = 8 // two spaces and `legend`; each entry adds its separator (two spaces) and its width
    const rows: string[][] = []
    for (const t of tags) {
      if (row.length > 0 && used + 2 + entry(t) > cols) {
        rows.push(row)
        row = []
        used = 0
      }
      row.push(t)
      used += 2 + entry(t)
    }
    rows.push(row)
    rows.forEach((r, i) => {
      const kids: any[] = i === 0 ? [<Text key="lg" dimColor>legend</Text>] : []
      r.forEach((t, j) => {
        if (i === 0 || j > 0) kids.push('  ')
        kids.push(<Text key={`lt${t}`} {...chipProps(CHIPS[t as 'ok'].tone)}>{`[${t}]`}</Text>)
        kids.push(<Text key={`lw${t}`} dimColor>{` ${LEGEND_WORD[t as 'ok']}`}</Text>)
      })
      out.push(<Text key={`lg${i}`}>{'  '}{kids}</Text>)
    })
  }
  if (widest > W) wrapCells(`› ${widest} columns wide, the pane shows ${W}`, W).forEach((r, i) => out.push(<Text key={`ft${i}`} dimColor>{`  ${r}`}</Text>))
  return { node: <Box key={key} flexDirection="column">{out}</Box>, rows: out.length, parts: out }
}

function drawCode(b: Extract<Block, { type: 'code' }>, cols: number, T: T, key: string): Drawn {
  if (isDiagram(b)) return drawDiagram(b, cols, T, key)
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
    case 'callout': {
      // The label is a filled chip (9.2); the text wraps under column 0. A decision's sentence is bold.
      const rest = drawnText(b.spans)
      const words = drawSpans(b.spans, T, key)
      return {
        node: (
          <Text key={key} wrap="wrap">
            {recPad(b)}
            <Text {...chipProps(CHIPS[b.tone].tone)}>{chipText(b.tone)}</Text>
            {rest === '' ? null : ' '}
            {b.tone === 'decision' ? <Text bold>{words}</Text> : words}
          </Text>
        ),
        rows: rowsFor(`${recPad(b, NBSP)}${chipText(b.tone)}${rest === '' ? '' : ' '}${rest}`, cols),
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
  if (b.type === 'table') return [b.header, ...b.rows].map((r) => r.map(drawnText).join('  ')).join('\n')
  const t = drawnText(b.spans)
  return b.type === 'bullet' ? `• ${t}` : b.type === 'number' ? `${b.n}. ${t}` : b.type === 'rec' ? `${recPad(b, NBSP)}✓ recommended ${t}` : b.type === 'callout' ? `${recPad(b, NBSP)}${chipText(b.tone)}${t === '' ? '' : ' '}${t}` : t
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
    const lines = wrapRows(o.text, width, tall ? 2 : 1)
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
        hanging(
          `r${o.key}`,
          <Text key="p">{''}</Text>,
          pw,
          <Text key="t" wrap="wrap">
            <Text color={TONE.good} bold>✓ recommended: </Text>
            {rec}
          </Text>,
          T,
        ),
      )
      rows += rowsFor(reason, Math.max(1, cols - pw))
    }
  }
  return { nodes: [<Box key="opts" flexDirection="column">{nodes}</Box>], rows }
}
