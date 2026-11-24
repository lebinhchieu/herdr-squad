# 01 adr and glossary
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: -
Feature: record (`tasks/features.md`)

## What the PO gets
Record the decisions before code: a dashboard replaces the board removed by ADR 0009, and the new files and terms.

## Rules
- New ADR: a dashboard replaces the removed board. It shows one goal or one scope, never all (so ADR 0007 "no cross-home view" still holds), is read-only except `board-ui.json`, and `squad-start` only prints its command (ADR 0009 "Manager tab only" stays).
- ADR 0007 amended in one line: parked questions live in `open-questions.md`.
- The ADR names the new squad files: `board-ui.json`, `open-questions.md`, the optional `tickets: <feature-slug>` line in `scope.md`.
- `CONTEXT.md` gets the terms: dashboard, choice (goal or scope), needs you, parked question, ready for review, work time.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T01.AC1** Given the repo after this task, when a reader opens `docs/adr/`, then one new ADR says the dashboard replaces the removed board and names `board-ui.json`, `open-questions.md` and the `tickets:` line.
- **T01.AC2** Given the new ADR, when read, then it says it supersedes only ADR 0009's loss line (or says plainly where it contradicts it).
- **T01.AC3** Given `CONTEXT.md`, when a reader looks up "needs you", "parked question", "ready for review", "work time", then each has one line matching `tasks/features.md`.
- **T01.AC4** Given ADR 0007, when read, then one line points to `open-questions.md` for parked questions.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M15 (`architecture.md` section 6). No code, no tests.
- New: `docs/adr/0020-dashboard-replaces-removed-board.md` (draft: `tasks/adr-draft-0020-dashboard.md`).
- Edit: `docs/adr/0009-board-removed.md` (status line), `docs/adr/0007-inbox-sits-on-escalations.md` (one line), `CONTEXT.md` (draft: `tasks/context-glossary-delta.md`).
- Also (FILE-11, first Developer task): commit the scope drafts under `.scratch/dashboard/`: `spec.md` (from `tasks/features.md`), `architecture.md`, `issues/01..17`, `ui-design/` (design, final prototype). Nothing else.
- Test harness: none.

## Comments
