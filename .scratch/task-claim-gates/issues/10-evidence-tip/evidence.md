# Evidence 10
## Behaviour

On the board, a branch whose tip is the passed sha plus commits that touch only the ticket's evidence folder (`<ticket>/` or `<ticket>.evidence/`) now counts as matching: the stage stays `passed` instead of `sha changed after PASS`. Git is read only when tip and sha differ (`merge-base --is-ancestor`, then `diff --name-only`). Any other path, a non-ancestor sha or a git error keeps `sha changed after PASS`. The row's `tip` is still the real tip. No event and no change to `squadtask.py` logic (two docstrings only).

## Review

| AC | Test | How run |
|---|---|---|
| T25 | `EvidenceTip.test_T25_evidence_only_commit_passes_other_path_and_git_error_do_not` (real temp git repo: evidence commit and old `.evidence` folder give `passed`; `bin/x` and an unknown sha give `sha changed after PASS`) | `python3 -m unittest tests.test_squadboard_tasks.EvidenceTip` |
| T26 | `EvidenceTip.test_T26_no_git_call_when_tip_matches` (no git call when tip equals sha; calls when it differs) | same |
| Docstrings | `squadboard_inbox.py` ("Passed branches come"), `squadtask.py` `word` (no `ready for review`) | `git diff` |

Targeted run: `test_squadboard_tasks` 26 ok; `test_squadboard_inbox`, `test_squadtask` ok; `test_squadboard_panels` has the 2 known clock failures (T12, T14), not from this change.
