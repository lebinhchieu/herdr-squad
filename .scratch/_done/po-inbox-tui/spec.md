# Spec: PO inbox pane readability (po-inbox-tui)

Status: ready-for-agent

## Problem
The PO says the inbox pane (`hooks/po-inbox/`) is "not good as expected". A real-pane audit (`.claude/squads/plugin/scopes/po-inbox-tui/ui-design/`, captures in `evidence/`) found the cause: the host gives the pane only 6 body rows at 24 terminal rows (11 at 40). Chrome and a folded body use most of them, so the PO cannot see the question and the choices together; the list shows 2 items.

## Scope
Terminal (TUI) only. No desktop support.

## User stories
1. As the PO, I see the question, the choices and the way to answer in the first viewport, so I decide without scrolling.
2. As the PO, I open one page that shows the whole message body when I need to read it.
3. As the PO, the list shows more items in a small pane and tells me how many are below.
4. As the PO, a done item shows its outcome first and complete.

## Designs (final, source of truth for AC)
- `ui-design/item.md`: item view, Details page, read and handled item, body drawing.
- `ui-design/list.md`: list and band (band unchanged).
- `ui-design/done.md`: Done list and done item.
(All in `.claude/squads/plugin/scopes/po-inbox-tui/`; the Developer reads them from there.)

## Out of scope
Colours and tone meaning, the markup parser, the band, `squad-inbox` CLI, `rowsFor`, the 7-row group fold, the `list --json` contract.

## Constraints
ADR 0007: height from `scroll.bodyRows`, never a constant; amend its two consequence lines named in item.md section 12.
