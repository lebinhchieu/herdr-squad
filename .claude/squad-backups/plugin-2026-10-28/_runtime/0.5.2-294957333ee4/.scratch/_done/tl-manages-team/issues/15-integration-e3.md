# T15 · integration of E3 (T10-T14)
Status: ready-for-agent
Type: task
Blocked by: T10-T14 all passed by both QAs
Repo: /home/chieule/workspace/squad
Design: ../design.md E3

## Do
A Developer branches from main 507f86e (the Manager gives `--base` and quotes `git merge-base --is-ancestor`), merges the passed branches of T10, T11, T12, T13, T14 into its own, resolves nothing silently (a conflict goes to the Tech Lead), runs the **targeted** tests of every file the five tasks touched (not the full suite; the Tech Lead runs it), and hands in.

Then the Tech Lead runs `python3 tests/run_suite.py --tz --receipt <evidence/T15>` once on the final sha and the two QAs read the receipt.

## Technical AC (AC-16)
- AC-16.1 End to end on a **copy** of the live plugin squad in a temp project (script in `dev-evidence.md`): `squad-migrate --dry-run` then real; `squad-spawn dev --show-settings` equals the pre-migration permissions; `squad-process auto` on a v3 copy applies v4 with the local edits kept (or reports the conflicting headings); a `squad-spawn --dry-run` of every role prints the generated path and no `remove` appears in any generated file (`grep -c '"remove"'` is 0).
- AC-16.2 The live test (`SQUAD_LIVE_CLAUDE=1`, T12) is run once on the final sha by QA-W, output saved.
- AC-16.3 Receipt first line `sha <HEAD> clean=yes`, OK line, 0 FAIL, run with `PYTHONDONTWRITEBYTECODE=1` and no stray `.pyc`.
- AC-16.4 README flag rows match the real `--help` output: the integration Developer pastes each new flag's `--help` line from the merged tools (`squad-settings`, `squad-process auto`, `squad-migrate --to layered-settings`, `squad-spawn`/`squad-respawn` flags) next to its README row in `dev-evidence.md`, and fixes any README row that differs (README only).
- AC-16.5 The one skip in `tests/test_docs_layered_settings.py` ("squadsettings is not on this branch yet") is removed at integration: the MIN_PLUGIN check runs unconditionally, and the targeted run of that file shows 0 skipped.

## Amendments (Tech Lead, 2026-10-17)
- AC-16.6 T14 passed (6407e9d); its three carry-overs are T15's, as one docs/test fix commit: (a) a test line for the numeric version compare (`"0.10.0"` above `"0.4.0"`, A19); (b) the A16 decision (a missing template deny is **adopted by default**; `--keep-template-denies-off` keeps it off; a missing allow still goes to `remove.allow` unless `--adopt-template-rules`) written into ADR 0011's trim bullet, the README `squad-migrate` row and the CONTEXT.md glossary line for the trim, and the A18 decision (`remove` and the stamp stay top-level; ADR names the collision risk with a future Claude key); (c) AC-16.4 and AC-16.5 on the merged tree.
- AC-16.7 `squad-start` on a v3 temp squad end to end: Manager prompt carries the applied notice once, stderr line once (T11 A13 plus T12 A13 together).
- Not done by Developers: the live test is run by QA-W from a temp clone (A20); the integration Developer does not run it.
