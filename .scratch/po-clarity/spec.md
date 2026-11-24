# PO clarity: fewer stops, readable items, one plan view

Status: needs-triage

Raised by Chieu, 2026-11-24.

## Problem

Chieu feels out of control while a squad runs. There are four causes, each seen on a live squad:

| Cause | Seen in | Effect on Chieu |
|---|---|---|
| Routine gates | guardian `clarify`: 24 items in 2 days, about half "confirm close" or "start now?" | Stopped often for a yes he always gives |
| Bare IDs | E23: "D74 closes O10/O11/O13/O15/O16", "plan14 still open on your word" | Has to look up each code |
| No plan view | Plan split over `goal.md`, `decisions.md`, `summaries/`, inbox | Can't see where the work stands |
| Missing tickets | `upstream-proposals`: board shows 01-06; 07-11 exist only on Developer branches | Board is out of date |

A fifth cause, about every ticket: tickets are walls of text. They have no picture of the screen, flow or data they change.

## Goal

```diagram What Chieu does after this change
Chieu opens the board
▼
Plan panel: order, blockers, estimate, aim
▼
Inbox item: one plan row, no bare IDs
▼
Ticket: a picture first, then the AC
```

## Tickets

| # | Ticket | Size | Depends on |
|---|---|---|---|
| 01 | Board shows every ticket of a scope | S | none |
| 02 | Standing yes for routine gates | S | none |
| 03 | Inbox refuses bare IDs | S | none |
| 04 | Plan panel (goal and scope): order, blockers, estimate, aim | M | 01 |
| 05 | Inbox item shows its plan row | S | 04 |
| 06 | Tickets carry a picture when it helps | S | none |

## Out of scope

- Rewriting the live `upstream-proposals` tickets. Their agents are mid-build, and an edit would race them.
- A cross-home plan view (ADR 0007 and 0026 keep the board to one home).
