# Evidence: 14 14 Evidence check accepts the whole ticket folder

## Behaviour

Code sha 7c14057 (base 46d2f4b). Files: `bin/squadevidence.py`, `bin/squadmergecheck.py`, `tests/test_squad_evidence.py`, `tests/test_squad_merge_check.py`.

**AC1 path table, both functions.** `test_squad_evidence.py::CheckBaseTest::test_path_table` and `test_squad_merge_check.py::MergeCheck::test_evidence_path_table` assert the same table. Accepted: `<stem>/evidence.md`, `<stem>/img/<file>`, `<stem>/checks.md`, `<stem>/pane-states.txt`, `<stem>/sub/x.md`, `<stem>.evidence/x`. Refused: `<stem>x/a.md`, `<stem>.md`, `<other>/checks.md`, `bin/x.py`, a stem with no ticket file. Both tests FAIL on the base `bin/` files (checked: base `squadevidence.py` and `squadmergecheck.py` copied over a copy of HEAD).

**AC2 temp repo, evidence commit adds `checks.md` and `pane-states.txt`** (real CLI run in a `/tmp` repo: ticket `03-x.md`, code commit, evidence commit with `evidence.md`, `checks.md`, `pane-states.txt`):
```
new  $ squad-evidence check .scratch/f/issues/03-x --base <code sha>
     ok: .scratch/f/issues/03-x/evidence.md        exit=0
base $ (same, base squadevidence.py)
     .scratch/f/issues/03-x/checks.md:1: changed since <sha> but outside an evidence folder (...)
     .scratch/f/issues/03-x/pane-states.txt:1: changed since <sha> but outside an evidence folder (...)   exit=1
new  squadmergecheck.evidence_only(code, tip) -> True
base squadmergecheck.evidence_only(code, tip) -> False
```
Tests: `test_any_file_under_the_ticket_folder_passes_stemless_folders_fail` (exit 0 for the two files; `bin/x` and `docs/foo/evidence.md` still exit 1, two problem lines) and `test_evidence_commit_with_checks_and_pane_states_is_evidence_only`; both FAIL on base.

**AC3 guard** `test_add_leaves_a_sibling_checks_md`: `squad-evidence add` leaves an existing `checks.md` in the folder byte-identical (passes on base too, as the ticket says).

**AC4** not here: followups 02 is already `Status: wontfix` (`superseded by 14`) on the base sha (12's commit).

**Tests run** (foreground, `< /dev/null`):
```
test_squad_evidence 51 OK · test_squad_merge_check 11 OK
grep -rl hits: test_squad_review_pack 6 OK · test_rules_wording 31 OK · test_dev_rules_size 9 OK · test_squadtask 19 OK · test_squadboard_tasks 26 OK
SQ-10 trio: test_windows_safe 14 OK · test_utf8_helpers 14 OK · test_instructions 16 OK
```
`bin/squadboard_tasks.py::_evidence_only` is unchanged (`git diff 46d2f4b HEAD --stat` lists only the four files above). The `--base` problem line now reads "any file under <stem>/ beside <stem>.md, or an old *.evidence/ folder"; no test asserts the old wording except the `outside an evidence folder.*\*\.evidence/` regex, which still matches.

Residual risk (Tech Lead's design): a script under the ticket folder now passes as evidence; the Tech Lead reads `git diff --stat <code sha> HEAD` on each evidence-only commit.

## Review

Fresh-context review subagent (sonnet, high) on `git diff 46d2f4b HEAD` (code sha 7c14057). Checks table: see `## Checks`.

**Standards:** none blocking. Small diff in the style of the neighbouring code; tests only for AC1-AC3; `bin/squadboard_tasks.py` untouched. Nit: `in_repo()` in `test_squad_merge_check.py` uses `os.chdir` with `addCleanup` because `squadmergecheck.git` has no cwd parameter; kept.

**Spec:** no bugs, no regressions. Findings, all low, none fixed:
1. Both functions accept a path under any ancestor directory `D` that has `D.md`, not only the ticket stem (spec wording "`<stem>.md` exists"). `git ls-files` shows no such pair outside `.scratch/**/issues/`: no false accept today. Kept as the spec words it.
2. The old `*.evidence/` branch never checked `<stem>.md` (unchanged from base; AC1 lists it only with the ticket present).
3. `squadmergecheck.is_evidence_path` spawns up to depth-1 `git cat-file` calls per changed path (`all()` stops at the first refused path). Fine at this size.
4. Git failure counts as "not found" (fails closed); `<stem>x/` and `<stem>.md` refused; a ticket deleted in the same diff refused. `cat-file -e` also accepts a directory named `X.md`, theoretical.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `test_squad_evidence.py::test_path_table` + `test_squad_merge_check.py::test_evidence_path_table`: OK (fail on base) | - | - |
| AC2 | CLI in temp repo: `squad-evidence check --base` exit 0 (base exit 1, two lines); `evidence_only` True (base False); tests `test_any_file_under_the_ticket_folder_passes_stemless_folders_fail`, `test_evidence_commit_with_checks_and_pane_states_is_evidence_only` | - | - |
| AC3 | `test_squad_evidence.py::test_add_leaves_a_sibling_checks_md`: OK | - | - |
| AC4 | followups 02 `Status: wontfix`, `superseded by 14` already on base 46d2f4b (12's commit) | - | - |

## Changelog line

`squad-evidence check --base` and `squad-merge-check` accept any file under a ticket's evidence folder (`checks.md`, `pane-states.txt`, subfolders), not only `evidence.md` and `img/` (why: Developers deleted `checks.md` to get past the check, and the two tools disagreed with the board's `_evidence_only`).
