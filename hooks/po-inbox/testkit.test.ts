import { expect, test } from 'claude-code/testing'

import { lines, rowsOfTree, styleOf } from './testkit'

const tree = {
  type: 'Box', props: { flexDirection: 'column' }, children: [
    { type: 'Text', props: { bold: true }, children: ['Title'] },
    { type: 'Text', props: { dimColor: true }, children: ['meta'] },
    { type: 'Text', props: { color: 'error', italic: true }, children: ['blocks ', 'X'] },
    { type: 'Text', props: {}, children: ['aaaa bbbb'] },
  ],
}

test('styleOf finds a bold, a dim and a coloured Text', () => {
  expect(styleOf(tree, 'Title')).toEqual({ bold: true })
  expect(styleOf(tree, 'meta')).toEqual({ dimColor: true })
  expect(styleOf(tree, 'blocks X')).toEqual({ color: 'error', italic: true })
  expect(styleOf(tree, 'absent')).toBeNull()
})

test('rowsOfTree counts rendered rows by width', () => {
  expect(lines(tree)).toHaveLength(4)
  expect(rowsOfTree(tree, 80)).toBe(4)
  expect(rowsOfTree(tree, 4)).toBe(7)
})

test('styleOf returns the innermost Text of a nested tree (the band shape)', () => {
  const band = {
    type: 'Text', props: { wrap: 'truncate' }, children: [
      { type: 'Text', props: { bold: true }, children: ['Inbox'] }, ' · ',
      { type: 'Text', props: { color: 'warning' }, children: ['2 to answer'] },
    ],
  }
  expect(styleOf(band, '2 to answer')).toEqual({ color: 'warning' })
  expect(styleOf(band, 'Inbox')).toEqual({ bold: true })
  expect(styleOf(band, ' · ')).toEqual({})
})

test('rowsOfTree counts a row Box (the band shape) as one row, a wrapped one by its joined width', () => {
  const row = {
    type: 'Box', props: {}, children: [
      { type: 'Text', props: {}, children: ['Inbox  2 to answer   '] },
      { type: 'Button', props: { label: 'Open (i)' }, children: [] },
    ],
  }
  expect(rowsOfTree(row, 80)).toBe(1)
  expect(rowsOfTree(row, 20)).toBe(2)
  expect(rowsOfTree({ type: 'Box', props: { flexDirection: 'column' }, children: [row, row] }, 80)).toBe(2)
})
