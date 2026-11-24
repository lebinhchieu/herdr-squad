# Architect role: recommended design (draft for PO confirmation)

Status: confirmed by PO

## What it is
Optional role, `architecture: yes|no` in `scope.md`, default `no`. Only the PO turns it on; the Manager never proposes it. Any size. `squad-spawn architect` refuses without `architecture: yes`. Role-short `arch`.

## Deliverable (Q1)
One `$SCOPE_DIR/architecture.md` per scope, `Status: draft|final`, mirroring the Designer's `ui-design/`. Holds:
- components and modules the scope touches
- boundaries and seams
- contracts and data shapes
- constraints the plan and the technical design must follow
- list of irreversible choices (data model, new dependency, vendor), each with options and a recommendation
ADR text is drafted in `$SCOPE_DIR/tasks/` ([FILE-11]); the promotion task commits it to `docs/adr/` via `/domain-modeling`.
Open for PO: in a goal, per scope (recommended) or one goal-level `shared/architecture.md`?

## Timing and feedback (Q2)
- Spawned after the goal check, before the plan: before the Manager's task split (S, M), before the Team Lead plans (L). The plan waits for `architecture.md` `Status: final` (same gate as a UI ticket waiting for its design).
- Retired once final; respawned for a question on it (as the Designer).
- It checks no built code. The team follows it, or sends `ASK` to the Architect; after 2 rounds the Manager decides ([CORE-4]).
- Enforcement (so "follow" has teeth, without the Architect checking): conformance to `architecture.md` joins the technical AC and is checked by the existing code checker: S the Developer's review subagent, M QA whitebox, L Tech Lead + QA whitebox.

## Versus Tech Lead: "sits above" (Q3)
- L: Architect owns the architecture; Tech Lead keeps per-task design, quality, security and suites inside it.
- S and M (no Tech Lead): Architect sits above the Developer's design notes.
- Irreversible choices: the Architect lists and recommends; the decision stays with the PO as today (WHO-2), escalated by the Manager. The Architect takes the "irreversible design choice" owner slot only for the proposal, not the decision. This changes SIZE-22 / ADR 0016's table rows "Irreversible design choice" and adds an architecture row; CONTEXT.md "Tech Lead _Avoid_: architect" is rewritten.
- Disputes: Manager settles, unchanged.

## Model
Default sonnet high like other roles; PO may choose opus for this high-leverage role.

## Touchpoints
Role card `agents/architect.md`, `templates/squad/settings/architect.json`; rules: CORE-3, WHO-2, WHO-2d, SIZE-3 (flag), new SIZE rule (role), SIZE-22, START-4 (`arch`), START-5, SPAWN-2a/b/c, new SPAWN rule, LC gate (S/M and L), technical-AC rules; `bin/squadcompose.py` (`_FACT_*`, goal-home default loop, facts header), `bin/squad-spawn` (all role lists + guard), `templates/scope/scope.md`, `squadrules_cli`; tests (grep `tests/` for each touched string, goldens included); CONTEXT.md, README, ADR, process version bump + history snapshot (ADR 0005).
