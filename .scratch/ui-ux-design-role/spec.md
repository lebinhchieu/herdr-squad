# UI/UX Designer role

Status: ready-for-agent

**A scope with `design: yes` in its `scope.md` gets a UI/UX Designer who delivers a design (screens, states, flows, optional HTML prototype) before the UI tasks are built. Nobody checks the design after build; the built UI is checked against it by the Developer's evidence (S) or QA blackbox (M, L).** PO decisions of 2026-10-14, iteration 1 of scope `add-ui-ux-design`.

## Decisions (PO)

- **Delivers a design only**, before build. No post-build design review.
- **Opt-in:** `design: yes|no` line in `scope.md`, default `no`. Set only when the PO asks; the Manager never proposes it. It adds the Designer to a scope of any size.
- **Model:** sonnet / high. Role id `designer`, role-short `ux` (agent name `<squad>-ux-<scope>`).

## Decisions (Tech Lead)

| # | Decision | Why |
|---|---|---|
| 1 | Design lives in `$SCOPE_DIR/ui-design/<task>.md` (+ optional `<task>.html`), first line after the title `Status: draft\|final` | `design.md` already means the project's technical design in `process.md` and `project.md`; a different name avoids the clash. Developers and QA already read `$SCOPE_DIR` |
| 2 | Hand-off is a `DECISION <task>: design final, ui-design/<task>.md` message to the Tech Lead and the task's Developer. No new message type | `DECISION` already means "written to a file first, then announced" |
| 3 | The Tech Lead puts `Design: ui-design/<task>.md` in the UI ticket and an AC line "built UI matches the design: every screen and state". The Developer does not start the UI part before `Status: final` | Plan order stays with the Tech Lead (S, M) or Team Lead (L) |
| 4 | Check after build: **S** Developer saves a screenshot per screen/state in `dev-evidence.md`, Tech Lead checks them in `tl-review.md`; **M, L** QA blackbox walks the design | Matches the PO's rule; the existing "behaviour check" duty, extended |
| 5 | `squad-spawn designer` refuses unless the scope's `scope.md` has `design: yes` (per-scope squads only; flat squads have no scope.md and are left alone) | Makes "never proposed, only when the PO asks" enforceable, not just written |
| 6 | Designer settings: may write only `ui-design/**` and its own notes; denied every other squad `*.md` and `settings/**`; same git and Jira denies as the other roles. Project code is **not** protected by settings (its cwd is the project dir): role text forbids it | Same layers and the same known gap as the Token Coach |
| 7 | Business doubt: Designer sends `ASK` to the BA (M, L) or the Tech Lead (S); the Tech Lead writes it to `escalations.md`. Designer is retired by the Manager once every design is `final` and the Tech Lead has no open question; a later design question goes to the Tech Lead, who may ask the Manager to respawn it | Lean cost; no session idle for the whole build |

## Compatibility and deploy (for the PO; nothing here is run by the squad)

- **Additive:** a `scope.md` with no `design:` line means `no`; no existing role, script path or setting changes meaning. An existing squad's `settings/` folder has no `designer.json`: `squad-spawn` already falls back to the plugin's template.
- **Existing squads' `process.md` is a copy** of `templates/squad/process.md` and does not update itself. After the PO merges, the Manager of each live squad applies the same edit to its own `process.md` and logs it in `process-log.md` (for `squad-board`: the Manager of the day, once).
- **Rollback:** revert the merge. A scope that already wrote `design: yes` is harmless (an unknown line).
- **Check after deploy:** `squad-spawn designer x --scope <s> --dry-run` on a scope with `design: yes` prints the session command; on `design: no` it refuses.

## Out of scope

Post-build design review; a design system or tokens; Figma or other tools; `design:` support in `squad-start`/`squad-board`; flat-layout squads.

## Tickets

`issues/01..03` touch disjoint files and run in parallel; `04` integrates them; `05` promotes the glossary term.
