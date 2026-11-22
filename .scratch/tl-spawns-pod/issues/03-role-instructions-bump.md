# 03 Role instructions, roster headers and the version bump
Status: ready-for-agent
Duties: design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: agents/team-lead.md (lines 3, 6, 12), agents/manager.md, templates/scope/roster.md (line 3), templates/goal/roster.md (line 3), .claude-plugin/plugin.json
Depends: 02 (final rule IDs and wording), 01 (script behaviour). The Developer merges both passed branches into its own branch first and runs the targeted tests on the result (SQ-6b). Base: main at 8d74fcb. Plan: `$SCOPE_DIR/iterations/1.md`. Design notes: `$SCOPE_DIR/tasks/design.md`.
Evidence: .scratch/tl-spawns-pod/issues/03-role-instructions-and-bump/evidence.md

## What and why
`agents/team-lead.md` still says "you spawn Developers" and "never spawn or retire a role but `dev`", and the roster headers say "Only the Manager edits this file". Make them match 01 and 02. This is the last ticket that touches plugin files before the promotion, so the version bump rides here (SQ-5). Role-instruction edits (`agents/*.md`) are covered by Chieu's brief and the confirmed plan.

## Design
- `agents/team-lead.md`: description (line 3) and the intro (line 6) say the Team Lead spawns, respawns and retires every pod role on `team:` and the Developers; Stance line 12 becomes: never spawn, respawn or retire `manager`, `token-coach` or another `team-lead`, and never relay a blocked pane or a permission prompt. Keep the rest. Cite no rule ID that does not exist after 02 (IDs are unchanged, D6).
- `agents/manager.md`: Stance gets one line: you spawn only the Team Lead and, at the close, the Token Coach; the Team Lead spawns the rest of the pod and watches its context. The Tools line keeps `squad-spawn`, `squad-retire` and `squad-respawn` (the Manager still spawns the Team Lead and acts as the fallback).
- Roster headers (both files): "Every agent of this scope (goal). `squad-spawn` adds a row; whoever spawned an agent fills its Owns and Status. The Manager keeps its own row and the Team Lead's. Look up a topic's owner here before asking the Manager." Same wording as FILE-5b from 02. The goal roster is the goal Manager's own file: it keeps the sentence "the goal Manager edits it".
- Version: `.claude-plugin/plugin.json` `0.10.3` becomes `0.10.4`, the same as the "Plugin 0.10.4" line 02 wrote in `changelog.md` v23.

## Business AC
- AC1 `agents/team-lead.md` no longer contains `a role but` nor "spawns and retires Developers"; it says the Team Lead spawns, respawns and retires every pod role and Developers and names `manager`, `token-coach` and another `team-lead` as never (base: `grep -n "role but\|spawns and retires Developers\|you spawn Developers" agents/team-lead.md` hits lines 3, 6, 12).
- AC2 `agents/manager.md` has the line that the Manager spawns only the Team Lead and the Token Coach, the Team Lead the rest.
- AC3 `grep -n "Only the Manager edits this file" templates/scope/roster.md templates/goal/roster.md` has no hit (base: 2 hits); both headers say who fills which rows as in the Design section; the table header row `| Agent | Role | Scope | Owns | Status | Session |` is unchanged (`tests/test_templates.py`).
- AC4 Version bump (SQ-5): `grep -n '"version"' .claude-plugin/plugin.json` prints `0.10.4`; `grep -c "0.10.3" .claude-plugin/plugin.json` prints `0` (base: `0.10.3`, count 1). `grep -n "^## v23" skills/squad-process-update/changelog.md` and its "Plugin 0.10.4" line agree with it. `.claude-plugin/plugin.json` is in this ticket's `Files:` line, as SQ-5 requires.

## Technical AC
- AC5 After the merge of 01 and 02 into the Developer's branch, `squad-process lint` is clean and no cited `[ID]` in the two agent files is missing from the process folder or `_removed.md`.
- AC6 Run and quote in `## Behaviour`: `tests/test_instructions.py`, `tests/test_templates.py`, `tests/test_promotion_0_6_0.py` (version identical in plugin.json, changelog, README), `tests/test_squadruntime.py`, `tests/test_old_language_inventory.py`, and every hit of `grep -rl "agents/team-lead\|agents/manager\|roster.md" tests/` that you did not edit; plus the targeted tests of 01 and 02 on the merged result (`tests/test_team_lead_perms.py`, `tests/test_rules_contract.py`).
- AC7 SQ-10: run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result.
- AC8 No test is newly skipped. Add a test only for a regression risk; the existing greps above need none. If `tests/test_instructions.py` pins the Team Lead card text, update the pin.
- AC9 Integration (SQ-6b, GOAL-6b): the handed-in sha contains both 01's and 02's branch (`git merge-base --is-ancestor <01 sha> HEAD` and the same for 02, quoted in `## Behaviour`).

## Base dry-run (SQ-15, Tech Lead, main 8d74fcb)
- From `tests/`: `test_instructions` 16 ok, `test_templates` 8 ok, `test_promotion_0_6_0` 3 ok, `test_squadruntime` 74 ok, `test_processlint` 31 ok, `test_old_language_inventory` 2 ok, `test_windows_safe` 14 ok, `test_utf8_helpers` 14 ok; `squad-process lint` prints nothing on base.
- AC1 base: 3 hits. AC3 base: 2 hits. AC4 base: version `0.10.3`, count 1 (this is the old-version grep SQ-5 asks for).
- Known failing on base: none.

## Evidence
`evidence.md` next to the committed ticket. Run `squad-evidence check <evidence folder>` (no `--base`) before HANDIN and quote the exit code (SQ-18).
