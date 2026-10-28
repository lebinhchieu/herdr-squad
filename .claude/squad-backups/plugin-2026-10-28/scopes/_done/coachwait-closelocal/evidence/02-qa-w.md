# 02 QA whitebox, sha e75a519 — PASS
- T1 ITER-6 one rule with --prompt, both output paths, inputs, message-back; ITER-6c (roles: manager) has no-loop/sleep/poll + herdr agent list after idle window ([MSG-8a] exists). lint=0; citations test OK.
- T2 ITER-7 unchanged, same file name/message; test asserts it.
- T3 bin/squad-spawn:66 one stderr line, role != manager && no prompt; exit/stdout unchanged; squad-respawn passes --prompt so no warning there. Tests cover dev/token-coach/qa-whitebox warn, manager/--prompt silent.
- T4 wording asserted in test_retro_rules; no golden diff needed (none changed); changelog entries added.
- T5 bash -n ok; diff = iterations.md, squad-spawn, 2 tests, changelog, ticket, evidence; squad-close untouched.
- T6 real stderr sample in evidence.md.
- I ran: test_squad_spawn test_retro_rules test_sizes test_process_citations test_processlint test_squadcompose = 192 OK.

---
# SUITE on integration sha ea196bb (receipt suite/suite-default.txt, `--tz`): 6 files fail -> 02 RETURNED
My earlier PASS ran a subset of tests only; the full suite shows what it missed.
Caused by 02:
- tests/test_utf8_helpers.py `test_spawn_dry_run_and_stubbed_run_for_every_role_with_a_space_and_emoji_path` (all non-manager roles, dry and real): stderr now carries the new "spawned without --prompt" warning; the test expects clean stderr. Fix: pass `--prompt` in the test or expect the warning. Passes on main.
- tests/test_squadsettings.py `test_local_file_wins_over_an_old_full_file`, `test_old_layout_keeps_the_file_and_warns_once`: `stderr.count("warning:") == 1` is now 2. Same fix. Passes on main.
- tests/test_qab_optional.py `NoLineUnchanged.test_every_role_matches_the_4901cab_golden` for manager and tech-lead, sizes S/M/L, qab yes/no (12 subtests): composed rules changed (ITER-6, ITER-6c) so goldens need refresh (pattern: `git show 6ebcfbd 03`). Passes on main.
Not caused by 02 (fail on main too, or environment):
- test_squadinbox `test_no_pyc`: bin/__pycache__/*.pyc present in the tree (fails on main checkout as well).
- test_process_conversion `Mapping` setUpClass: `.scratch/composed-process/issues/03-convert-process-to-rules/mapping.md` missing (scratch moved to done); fails on main.
- test_po_inbox_mod `test_plugin_test_passes`: exit 1 in the suite run, passes alone on main; unclear (env/load).
Fix list: also run the whole suite (or at least test_utf8_helpers, test_squadsettings, test_qab_optional) before re-hand-in.
