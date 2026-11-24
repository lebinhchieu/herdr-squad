# Evidence 10
sha: 82827f8
## Behaviour

On the board, a branch whose tip is the passed sha plus commits that touch only the ticket's evidence folder (`<ticket>/` or `<ticket>.evidence/`) now counts as matching: the stage stays `passed` instead of `sha changed after PASS`. Git is read only when tip and sha differ (`merge-base --is-ancestor`, then `diff --name-only`). Any other path, a non-ancestor sha or a git error keeps `sha changed after PASS`. The row's `tip` is still the real tip. No event and no change to `squadtask.py` logic (two docstrings only).

## Review

| AC | Test | How run |
|---|---|---|
| T25 | `EvidenceTip.test_T25_evidence_only_commit_passes_other_path_and_git_error_do_not` (real temp git repo: evidence commit and old `.evidence` folder give `passed`; `bin/x` and an unknown sha give `sha changed after PASS`) | `python3 -m unittest tests.test_squadboard_tasks.EvidenceTip` |
| T26 | `EvidenceTip.test_T26_no_git_call_when_tip_matches` (no git call when tip equals sha; calls when it differs) | same |
| Docstrings | `squadboard_inbox.py` ("Passed branches come"), `squadtask.py` `word` (no `ready for review`) | `git diff` |

Targeted run: `test_squadboard_tasks` 26 ok; `test_squadboard_inbox`, `test_squadtask` ok; `test_squadboard_panels` has the 2 known clock failures (T12, T14), not from this change.

## QA blackbox 10 (sha 82827f8)

### QA blackbox 10 (sha 82827f8)

Method: `live`. Dev evidence has no shots. I ran the board (`bin/squad-board`, worktree of the branch, port 0) on two temp git repos (QA scope s1, no-QA scope s2). Real branches, real commits, events from the hook (`squad-log-message`). I read each row from `/api/tasks`. Real store untouched. Judged on states.md AC12, AC20 and the ticket's behaviour: evidence-only commits keep `passed`, other paths show `sha changed after PASS`.

| Case | Mode | What I did | What I saw | Result |
|---|---|---|---|---|
| Baseline | live | QA team: HANDIN + both QA PASS on commit X | `passed`, waits PO | pass |
| Evidence-only | live | commit `<ticket>/evidence.md` + an image file in `img/` on top of X | still `passed`, tip is the new tip | pass |
| Two evidence commits | live | one more evidence commit | still `passed` | pass |
| Code commit | live | commit `bin/b` on top | `sha changed after PASS`, waits QA, note `PASS on 17ab87bf25, branch tip 8847c6ecd0` | pass |
| Mixed commit | live | one commit with evidence + `bin/c` | `sha changed after PASS` | pass |
| Other ticket's evidence | live | commit evidence folder of ANOTHER ticket | `sha changed after PASS` | pass |
| No-QA (AC20) | live | hook HANDIN with valid evidence -> `passed`; evidence-only commit | still `passed` | pass |
| No-QA code commit | live | commit `bin/y` | `sha changed after PASS`, waits `evidence check` | pass |

#### Follow-ups
None new. Old ones still open (silent unknown `--slot`, no W4 via `pass --slot manager`, unwritable store silent, W3 repeats on a 2nd HANDIN).

Verdict: PASS.

## QA whitebox 10 (sha 82827f8)

### QA whitebox 10 (82827f8): PASS
Diff read (squadboard_tasks.py `_evidence_only` + `stage`, 2 docstrings, EvidenceTip tests) against design.md s6.1, T25, T26.
- Git runs only when tip and sha differ (prefix test first); `merge-base --is-ancestor` then `diff --name-only`; `_git` gives None on failure -> False, no raise; every path must start with `<stem>/` or `<stem>.evidence/`; plan-table tickets (no .md `where`) -> False; cached per request in `cache`.
- squadtask.py: docstring only; store format untouched.
Ran in worktree tcg-6: test_squadboard_tasks + test_squadtask 41 OK; test_squadboard_inbox OK 4 times (12 tests). Panels T12/T14 clock failures: known, not in diff.
Follow-up (not FAIL): test_squadboard_inbox hung once in my first run (after 5 tests, killed at 300 s) and passed in 4 later runs; tcg-3 saw the same hang on a branch that does not touch it. Looks like an existing flake, not this diff. Not run live on the real scope (the `sel` shape for read() needs the board's squad object); temp git repo only.

## Tech Lead review 10

### Tech Lead review, ticket 10 (evidence-only tip)

Final sha for QA verdicts: 82827f8 (branch squad/plugin/task-claim-gates/plugin-dev-tcg-6, on top of 04's 2545cab).

- Code read (bin/squadboard_tasks.py, `_evidence_only` + one fact read by `stage`): git runs only when tip and sha differ and sha is an ancestor of tip; every changed path must sit in `<ticket stem>/` or `<stem>.evidence/`. Any git failure gives False (no raise). Row `tip` stays the real tip. Read side only: no store or event change (D1 holds).
- Docstrings: squadboard_inbox.py:12 and squadtask.py:178 are comment-only edits.
- Tests: `python3 -m unittest test_squadboard_tasks test_squadtask` -> 41 run, OK. T25 and T26 (class EvidenceTip) both ok.
- Open: HANDIN has code and evidence in one commit, so `squad-evidence check` is not run yet. After both QAs PASS, the Developer sends `evidence sha` and I run the check (EVID-2c).

Verdict on code: PASS.
