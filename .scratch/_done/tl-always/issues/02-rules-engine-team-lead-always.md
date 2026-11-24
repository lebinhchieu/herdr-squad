# 02 Rules engine: team-lead always present
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: bin/squadrules.py, bin/squadrules_cli.py, bin/squadcompose.py, bin/squadteam.py, bin/squadupgrade.py; tests/test_squadrules.py, test_squadcompose.py, test_sizes.py, test_squad_team.py, test_squadupgrade.py, rulesview.py (docstring), test_rules_contract.py (its `plan-owner` rows only if 03/04 left any)
Depends: 03, 04 (group B: after they are merged into its base; reader before deleter, SQ-1; the plan had `-`). Goal: `../iterations/1.md`; brief `../scope.md`.
Evidence: .scratch/tl-always/issues/02-rules-engine-team-lead-always/evidence.md

## What and why
Drop the `plan-owner` key (duties and team variants); team-lead is always on the team. `squad-process upgrade` lists stale overlay ops of removed variants. Tech Lead lists SQ-1 readers/deleters of the key (grep over bin/, hooks/, templates/, tests/) in the task.

## Design notes (Tech Lead)
Not touched (grep shows no reader): bin/squad-start, bin/squad-spawn, bin/squadtaskprompt.py. `squad-process` itself needs no edit (it routes to squadrules_cli / squadupgrade).
Harness: tests build teams through `rulesview.py` (`composed`, `acts`, `who`) and tmp scope folders; `test_squad_team.py` has synthetic rules with `plan-owner =` in `RULES` (lines 17-22): rewrite them on a surviving key (`code-check = tech-lead`, `tech-lead = yes`).

Design:
- `squadrules.py`: remove `plan-owner` from `DUTIES`; `handin-target` chain becomes `("qas", "team-lead")`. Move `team-lead` from `TEAM_KEYS` to `IMPLICIT_ROLES`; remove it from `PRESENCE_KEY`, `WHEN_KEYS`, `PRIMARY_KEYS`. `resolve_duties` adds `team-lead` to the team set before walking chains. `parse_team`: a `team-lead` token is skipped (accepted, ignored), unlike `manager`/`dev` which stay errors. `OLD_WHEN_KEYS` gains `plan-owner` and `team-lead`, each with a one-line pointer (the Team Lead always plans and coordinates: drop the condition; a `= manager` / `= no` condition never holds, drop the operation).
- `squadcompose.py`: `duties:` line (`duties_line`) prints the new `DUTIES` (no `plan-owner`); `_NEW_WHO_KEYS` follows `DUTIES`; `read_home` derives facts from the reduced `TEAM_KEYS`.
- `squadteam.py`: `_token("team-lead")` refuses with "always on the team" (it is implicit now); the `spawn:`/`retire:` report never lists it.
- `squadrules_cli.py`: help text (lines 163, 184) names the new key list; `squad-process team --has team-lead` exits 0 on any decided team.
- `squadupgrade.py`: extend `_OLD_COND` and `_TRANSLATE` so `old_when_conditions` also finds `plan-owner = team-lead` (-> drop the condition), `plan-owner = manager` and `team-lead = no` (-> never holds: drop the operation), `team-lead = yes` (-> drop the condition). Same printing path as `size`: nothing is written, the list appears in `squad-process upgrade --check`; drop the line-335 alternative hint for `team-lead = yes` (that key is gone).

Technical AC:
- AC1 `parse_team("ba, team-lead")` equals `parse_team("ba")`; `team_facts` of both are equal and contain no `team-lead` and no `plan-owner` key. Test in test_squadrules.py.
- AC2 `resolve_duties([])` has no `plan-owner`; `handin-target` is `team-lead` for a team with no QA and `qas` with one. test_squadrules.py / test_squadcompose.py.
- AC3 A `when:` with `plan-owner = x` or `team-lead = yes|no` is rejected with `OldKeyError` whose text carries the pointer; `squad-process lint --squad-dir <fixture>` prints `file:line` and exits non-zero for such an overlay (fixture overlay in a tmp squad). test_squadrules.py.
- AC4 `squad-process upgrade --check` on a fixture overlay with four ops (one per old condition above) prints, for each, `<ID> (line N): <old> -> <translation>`, writes nothing, and the exit code equals the `size` case today. test_squadupgrade.py.
- AC5 `squad-team add team-lead` and `remove team-lead` exit 2 with "always on the team"; `squad-team add ba` on `team: team-lead, qa-white` rewrites the line without `team-lead` and reports no `spawn:`/`retire:` for it. test_squad_team.py.
- AC6 `grep -rn "plan-owner" bin/ templates/ agents/ hooks/ skills/` lists only the old-key pointers in squadrules.py/squadupgrade.py and the changelog (history); `grep -rn "team-lead = " templates/` is empty. `squad-process lint` over the repo templates is clean. (Needs 03 and 04 merged into the base: check at start, `BLOCKED` otherwise.)
- AC7 `squad-process who MSG-5` and `squad-process who WHO-1e` list no `plan-owner =` or `team-lead =` keys.
- AC8 Developer rules size (test_dev_rules_size.py) and composed headers (test_squadcompose.py `duties:` assertions, test_sizes.py lines 72 and 132) updated to the new duty list and passing.
- AC9 SQ-10: the diff edits `bin/`, so run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result in `## Behaviour`.
- AC10 Targeted tests: every touched test file plus `grep -rl "resolve_duties\|team_facts\|IMPLICIT_ROLES\|TEAM_KEYS\|plan-owner\|handin-target" tests/` hits; no test newly skipped; the full suite is the Tech Lead's (SUITE-1), not yours.
Compatibility (LC-12): no stored data changes; `scope.md` is only read; a `team-lead` token in any scope.md keeps working. Overlay ops on retargeted rules go stale by hash: AC4 is the listing; rollback = revert the merge.

## Evidence
`evidence.md` next to the ticket (path in Evidence: line, Tech Lead).
