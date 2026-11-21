# 07 Agent files, version bump 0.10.0, promote.md
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: agents/manager.md, agents/team-lead.md, agents/tech-lead.md (one line if it says the Team Lead is optional), .claude-plugin/plugin.json (0.9.6 -> 0.10.0), skills/squad-process-update/changelog.md (v20), README.md (role lines), tests/test_rules_contract.py (CARD assertion line ~120), `$SCOPE_DIR/promote.md` (Tech Lead writes it; the Developer commits its content to the project docs)
Depends: 01, 02, 03, 04, 05, 06 (group C: integration, after all passed). Goal: `../iterations/1.md`; brief `../scope.md`.
Evidence: .scratch/tl-always/issues/07-agent-files-version-promote/evidence.md

## What and why
Agent files match the new roles. Bump to 0.10.0 (SQ-5). promote.md per PROMO-4/PROMO-5. Integration task: SQ-6 check of passed branches, runs with --tz (Chieu asked at merge).

## Design notes (Tech Lead)
Integration (GOAL-6b, SQ-6b): the Developer merges the passed branches of 01-06 into its own branch in order 03, 04, 02 (02 needs 03 and 04), then 01, 05, 06, resolving the expected overlaps (`_removed.md`, `tests/test_rules_contract.py`, `tests/test_small_files_equivalence.py` between 03 and 04; see `tech-lead-plan.md` Related siblings), runs the targeted tests for the changed files, and hands in. The Tech Lead then runs the full suite (SUITE-1) after `ASK ... full suite?` and Chieu's yes: `python3 tests/run_suite.py --receipt $SCOPE_DIR/evidence/ --tz`, plus the three SQ-10 files first.
Edits of this task's own:
- `agents/manager.md`: the Manager owns the plan and settles disputes; the Team Lead is always on the team; subagent defaults as in the new SPAWN rule (point to the rule, do not copy it). `agents/team-lead.md`: delete "You exist only when the scope's team lists `team-lead`; without you the Manager holds the plan"; it coordinates (spawns Developers, assigns per the plan, tracks, health checks, fixed escalation triggers, never reorders the plan). Keep each card's other lines; change nothing a rule file says.
- `tests/test_rules_contract.py` `test_team_lead_exists_when_the_team_lists_it_...`: the assertion `lists \`team-lead\`` in CARD is rewritten to the new wording (one assertion that the card no longer says the Team Lead is optional).
- Version (SQ-5): `.claude-plugin/plugin.json` `"version": "0.10.0"`; changelog `## v20 — 2026-11-21` above v19 with `Plugin 0.10.0`, `added:`/`changed:`/`removed:` and a `why:` per line (ADR 0030, the 31 removed rule IDs, the `plan-owner` and `team-lead` `when:` keys now rejected, `squad-process upgrade --check` lists overlay ops that name them, watchdog target, defaults); README role lines (line 3, the optional-roles list) say the Team Lead is always on the team; `plugin.json`'s description needs no edit. `tests/test_squadruntime.py` compares `0.9.2` < `0.10.0`: unaffected.
- `promote.md` (PROMO-2, PROMO-4): the Tech Lead writes it during the scope: the ADR 0030 text and CONTEXT terms are already committed by 01, so it lists only what is left (the `team-lead` token compatibility rule if not in 0030, the SQ-1 reader-before-deleter ordering as a lesson for the squad overlay, the deploy plan as the changelog v20 text). If nothing is left, it says so and the Developer commits nothing.

Technical AC:
- AC1 `grep -rn "0\.9\.6" .claude-plugin/` is empty and `plugin.json` says `0.10.0`; changelog v20 exists with all five areas.
- AC2 After the merges `squad-process lint` is clean; `grep -rn "plan-owner" bin/ templates/ agents/ hooks/ skills/` only the old-key pointers (02) and changelog history.
- AC3 `squad-process compose manager --home <scratch scope>`, `compose team-lead`, `compose dev` on a team without `team-lead` contain the Team Lead rules and no `plan-owner=` in any `duties:` line (paste the commands and the greps).
- AC4 `squad-process upgrade --check --squad-dir .claude/squads/<plugin|board|accounts>` runs; its output goes in `evidence.md` (expected: nothing to decide, or only the line-25 COST-5a citation note of the plugin squad's overlay, which the Manager edits).
- AC5 The integration branch: every passed branch is an ancestor or listed as merged; targeted tests over the changed files pass; SQ-10 files pass.
- AC6 Agent cards: `agents/team-lead.md` has no "exist only when"; `tests/test_instructions.py` and `tests/test_rules_contract.py` pass.
- AC7 Full suite (Tech Lead, after Chieu's yes): receipt in `$SCOPE_DIR/evidence/` with first line `sha <final sha> clean=yes` and the OK line; a failing run returns the named task (SUITE-5).
Deploy plan: `tech-lead-plan.md` (Chieu deploys; the changelog v20 carries the same steps). Rollback: revert the merge, plugin back to 0.9.6.

## Evidence
`evidence.md` next to the ticket (path in Evidence: line, Tech Lead).
