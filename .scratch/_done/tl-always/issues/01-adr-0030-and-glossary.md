# 01 ADR 0030 and CONTEXT terms
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: docs/adr/0030-team-lead-always.md (new), docs/adr/0010-team-lead-runs-the-pod.md, docs/adr/0018-team-replaces-size.md, docs/adr/0022-sleep-when-idle-and-away-mode.md, docs/adr/0028-watchdog-follows-goals-file.md (one amendment line each), CONTEXT.md
Depends: - (group A, parallel with 03, 04, 05, 06; plan order: `tech-lead-plan.md`). Goal: `../iterations/1.md`; brief `../scope.md`.
Evidence: .scratch/tl-always/issues/01-adr-0030-and-glossary/evidence.md

## What and why
ADR 0030 amends 0010 and 0018: Team Lead always on the team; Manager owns the plan and settles disputes; Team Lead coordinates (spawn, assign per plan, track STATUS/ledger, health checks), escalates only on fixed triggers, never reorders the plan; watchdog wakes the Team Lead (goal option a); Manager subagents default sonnet high, model/effort per task, forks allowed. CONTEXT.md: add terms plan owner (retired as a variant) and coordinator. Use /domain-modeling. First commit: copy tasks/01..07.md to .scratch/tl-always/issues/ as NN-<slug>.md.

## Design notes (Tech Lead)
Docs only; no code, no tests to write. SQ-1: deletes and moves nothing (it only adds a file and note lines).
Read first: `docs/adr/0010`, `0018`, `0022`, `0028`, `$SCOPE_DIR/tasks/tech-lead-plan.md` (risks, decisions to record), `../scope.md`. Use `/domain-modeling` for the glossary and the ADR.

Decisions the ADR records (all bound by Chieu or the Tech Lead's plan input):
1. The Team Lead is always on the team; `plan-owner` is no longer a duty or a `when:` key, and neither is `team-lead` as a presence key. The Manager owns the plan (which tasks, their order, the iteration goal) and settles disputes; the Team Lead coordinates (spawns and retires Developers, assigns per the plan, tracks STATUS and the ledger, health checks), escalates only on fixed triggers and never reorders the plan.
2. `team:` may still list `team-lead` (the engine accepts and ignores it). Tech Lead's choice, flagged for the Manager (reversible).
3. Watchdog (Chieu E1, option a): a scope's watchdog wakes its own Team Lead (falls back to the Manager while no Team Lead is up or when it is blocked); a scope inside a goal gets its own watchdog; the goal's watchdog wakes the goal Manager only on `goals.md` events. Detail in `06.md`.
4. Defaults: Manager `opus medium`, Team Lead `sonnet low` (settings JSON, ADR 0010 point on where defaults live stands). Subagents the Manager spawns default to `sonnet high` (Agent `model: sonnet`, `effort: high`), the Manager picks model and effort per task (gather and explore stay sonnet high, a judgment call may use opus or a higher effort), forks are allowed (a fork runs on the Manager's model).
5. Plugin 0.10.0, breaking for rule retargets: 31 Manager-twin rules get tombstones; overlay ops on them go stale and `squad-process upgrade --check` lists them.

AC (technical):
- AC1 `docs/adr/0030-team-lead-always.md` exists, first lines follow 0028's shape (`# 0030: ...`, `Status: accepted (tl-always; Chieu answered E1 on 2026-11-21)`), has Context, Decision, Consequences, Alternatives rejected (the E1 options Chieu did not pick are in `../iterations/1.md` and `../escalations.md`; do not invent others).
- AC2 It names what it overrides, sentence by sentence, as 0018 does: 0010 (Team Lead only in M and L; "Manager plans" at S), 0016's size-L-only Team Lead (already amended by 0018), 0018 (the `team:` token list includes `team-lead`; "every subset of the seven roles is valid" becomes six optional roles), 0022 and 0028 (watchdog and blocked-pane wake target the Manager). Each of 0010, 0018, 0022, 0028 gets one line `Amended by 0030 (team-lead-always): <what>` in the style 0010 uses for 0016. No other edit to those files.
- AC3 Every sentence of the ADR is checked against the code of tasks 02-06 as planned in their tickets (no claim the tickets do not make).
- AC4 CONTEXT.md: add **Coordinator** (the Team Lead's role: spawns, assigns per the plan, tracks, health-checks, escalates on fixed triggers, never reorders) and **Plan owner** as a retired term pointing to 0030 (Manager owns the plan, Team Lead coordinates); edit **Manager**, **Team Lead**, **Manager traffic**, **Tech Lead** ("The Team Lead owns the plan"), **Team** (drop `team-lead` from the optional list) and the **Token Coach** line ("with a QA or Team Lead") to match. No term left saying the Team Lead is optional or owns the plan.
- AC5 `grep -n "plan-owner\|plan owner" CONTEXT.md docs/adr/0030-*.md` shows only the retired-term entry and the ADR's own history of the key.
- AC6 Run `grep -rl "CONTEXT.md\|docs/adr" tests/` hits (none expected; say so) and any test that reads the touched files.
Verification: read the files; no suite.

## Evidence
`evidence.md` next to the ticket (path in Evidence: line, Tech Lead).
