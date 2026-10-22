# T7 · integration
Status: ready-for-agent
Type: task
Blocked by: T1 to T6, T8, T9 (all passed)
Repo: /home/chieule/workspace/squad (branch from main c1be501 unless the briefing names a base)
Spec: ../spec.md (B-ids) · Design: ../design.md (decision numbers) · Technical AC: `$SCOPE_DIR/evidence/qa-w-tech-ac.md` (AC ids)

## Files this task touches
None of its own: branch from the **T9 passed sha** (it already contains T1, T3, T4, T8 and T9: `git log c1be501..<sha>` and `git merge-base --is-ancestor` to confirm) and merge the other passed branches T2 `3aa8f8d`, T5 `4e37832`, T6 `6382aa7` (the Manager's briefing gives the final shas). Resolve nothing by guessing, `BLOCKED` on a conflict.

## Do
Do **not** run the full suite (PO rule, design decision 14): run the targeted tests for the merged files (`tests/test_process_*`, `tests/test_suite_rules_process.py`, `tests/test_team_lead_perms.py`, `tests/test_pod_*`, `tests/test_manager_m_l.py`, `tests/test_squadprocess*`, `tests/test_instructions.py`, `tests/test_squad_spawn.py`, `tests/test_squad_respawn.py`, `tests/test_model_effort_settings.py`, `tests/test_team_lead_role.py`) and hand in. The **Tech Lead** then runs `python3 tests/run_suite.py --tz --receipt $SCOPE_DIR/evidence/T7` once, in the background, on your final sha (in your worktree), and saves the receipt there. Also run `python3 bin/processlint.py templates/squad/process.md`. `dev-evidence.md` lists a **deploy note**: after the PO's yes the Manager must copy the new allow entries into the live `.claude/squads/plugin/settings/team-lead.json` (a squad's copy overrides the template; T9's model/effort keys need no live edit: they fall back per key to the template) and apply the v4 `process.md` to the live squad. Check every `process.md →` citation resolves (`tests/test_process_citations.py`) and the full-text grep of AC-1.3 against the merged tree.

## Technical AC
AC-8. Business AC: B14.

## QA blackbox findings to fix on the integration branch (added 2026-10-17)
QA blackbox FAILed T1 to T4 on small wording defects (`$SCOPE_DIR/evidence/T1..T4/qa-b.md`). The branches are chained (T9 builds on T8, T3, T4, T1), so they are fixed once, here, as **separate commits after the merges**, one commit per finding group, each with a test line pinning the wording. Edit only the lines named. A QA re-checks each fix as a diff.
| Finding | File | Fix |
|---|---|---|
| T1 F1 | `templates/squad/process.md` ~178 (Team Lead to Manager bullet) | Replace "a dispute it cannot settle" with "a plan or assignment dispute it is itself a party to (the parties send every other dispute to the Manager themselves)". Keep the two-round rule line. Re-copy to `history/process-v4.md`; update the changelog item if it quotes the old words. |
| T2 F1 | `agents/team-lead.md` Disputes | One line: when the Team Lead is itself a party to a plan, order or assignment dispute it does not settle it; after the two-round rule it goes to the Manager. |
| T2 F2 | `agents/team-lead.md` summary line | Add each task's final passed sha and the checkers that passed it. Keep the 40-line cap. |
| T3 F1 | `agents/manager.md` Merging bullet | The Manager takes each task's passed sha and checkers from `iterations/<n>.summary.md` or the task files, never from messages. |
| T3 F2, F3 | `agents/manager.md` | Remove the literal "(B15)" from the Spawning text. Add to the check-in text that the Manager also receives the Team Lead's one line at 3 returns on a task (M, L). |
| T4 F1 | `agents/qa-blackbox.md` | PASS/FAIL copies the Team Lead (M, L) only; delete "and the BA". Check `qa-whitebox.md` says the same. |
| T4 F2 | `agents/dev.md` | One line: `BLOCKED <task>` and answers to `STATUS?` go to the Team Lead (S: the Tech Lead); a permission prompt is not sent anywhere. |
Tests go in the existing `tests/test_pod_contact_routes.py`, `tests/test_team_lead_role.py`, `tests/test_manager_m_l.py`, `tests/test_pod_rules_process.py`. Keep processlint at exit 0; `tests/test_process_history.py` stays green. Then re-run the targeted list and hand in; the Tech Lead's suite run comes after the QAs pass these fixes.
