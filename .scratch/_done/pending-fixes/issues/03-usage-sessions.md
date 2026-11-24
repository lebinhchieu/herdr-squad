# squad-usage: show sessions and per-session peak for an agent with several sessions
Status: needs-triage
Type: task
Source: tl-always Token Coach plugin proposal (ITER-15).

## Problem
An agent row (Tech Lead, QAs, Manager) shows only the latest session's peak; earlier sessions' peaks (93-114k at `fresh`) are lost. Third scope in which the Token Coach cannot read pre-respawn peaks (tl-always iterations/1.coach.md, plugin proposal 1).

## AC (draft)
- AC1 `bin/squad-usage` adds a `sessions` column.
- AC2 A per-session peak and turns list is available for an agent with 2+ sessions.

## Base dry run (SQ-15, main 432b8ea, Manager)
tests/test_squad_usage.py: OK, 26 tests ($SCOPE_DIR/evidence/base/test_squad_usage.txt).

## Comments
