# 02 evidence

## Review

AC trace (tech-ac.md T1.x, S1-S4, G1-G3; spec AC1-AC4 data side). Run: `cd tests && python3 -m unittest test_squadtree test_squadcommands`.

| AC | Test | How run |
|---|---|---|
| T1.1 golden | `test_squadtree.TreeTests.test_T1_1_golden_herdr_readable_and_down` (tree.json herdr up, tree-herdr-down.json herdr down; Tech Lead DECISION 02) | unittest; regen: `python3 tests/test_squadtree.py --regen` |
| T1.2 / S1 read-only | `test_T1_2_read_only_run_changes_nothing` | unittest |
| T1.3 discovery | `test_T1_3_discovery` (SQUAD_DIR, worktree, none, flat, bad --repo, bad flag exit 2) | unittest |
| T1.4 / T1.4b | `test_T1_4b_field_shape_and_facts_equal_the_board` | unittest |
| T1.5 | `test_T1_5_light_rows_...`, `test_T1_5b_...` | unittest |
| T1.6 | `test_T1_6_herdr_runs_once_...` | unittest |
| T1.7 perf | measured below | `time python3 bin/squad-tree --repo .` |
| T1.8 | `NextStepTests.test_T1_8_*` | unittest |
| T1.9 a-j | `test_squadcommands.CommandTests.test_T1_9*` | unittest |
| T1.10 / T1.11 | `test_T1_10_T1_11_broken_files_and_hostile_text_do_not_crash` | unittest |
| T1.12 | `test_T1_12_the_copied_texts_run_for_real` | unittest |
| G1 / G2 / S2-S3 | stdlib only; `encoding="utf-8"`; `squadio.utf8_stdio()`; names go through NAME_RE | SQ-10 run below |

## Behaviour

- Real run on this repo (3 squads, 25 scopes, herdr absent): 0.10 s.
- Defect found by T1.12: `squad-report ... --squad NAME` refuses (`no such squad`) without `$SQUAD_DIR`, i.e. in Chieu's plain shell. So `report` and `report-status` texts carry the squad folder path: `squad-report api --squad /abs/.claude/squads/plugin`.
- `report-status` answers by exit code (0 fresh, 3 stale, 4 missing); the test accepts those.
- SQ-10: `python3 -m unittest test_windows_safe test_utf8_helpers test_instructions` plus the new files: 64 tests OK.
- `test_squadboard_list` has one failure at the base commit too (`last_active` from real branch times); `test_squadboard_demo` browser tests fail on `1 d ago` (clock). Neither touched by this diff.

## QA blackbox review

### QA blackbox: ticket 02 (squad-tree data CLI), sha 9fe68b9

Method: `git archive 9fe68b9` into a temp dir; ran `bin/squad-tree` on this repo (real) and on a scratch repo built by the ticket's helper; compared with the running `squad-board` (served on 127.0.0.1, read in playwright-cli); pasted the offered commands. No code read.

| What | live/shot | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1.4 numbers equal the board (real repo) | live | `squad-tree --repo . --json`, then board picker for squad plugin | update-not-deny: pane 2/2, needs 0; board "0 open of 2 tasks", nothing. process-fixes: pane 20 of 200; board "10 scopes . 180 open tasks". squads-mod: pane 0/6; board "6 open of 6 tasks". Board header "0 need you across the squad"; pane squad needs_you 0 | pass |
| Next step on real data | live | read `next_step` | process-fixes "All scopes closed: close goal"; squads-mod "Working. Nothing for you."; update-not-deny "All tasks done: close" | pass |
| Speed | live | `time` | 0.27 s real repo (3 squads, 25 scopes); 0.08 s scratch; AC8.4 asks under 3 s | pass |
| AC7.1 read only | live | hash (path,size,mtime) of scratch repo before/after a run | no change | pass |
| AC6.1 no squads | live | git repo with no squads | exit 0, `squads: []` | pass |
| bad `--repo` | live | `--repo /nonexistent/x` | "--repo is not a directory", exit 2 | pass |
| AC6.2 flat squad | live | scratch `old-flat` | "flat squad: not supported"; New work wait "flat layout: squad-start refuses it"; Close squad ready | pass |
| AC6.7 two squads, filter | live | scratch + `--squad plugin` | both listed; filter gives one | pass |
| AC6.8 worktree and subfolder | live | ran with no `--repo` from a git worktree and from `.scratch/` | main repo's squads listed both times | pass |
| AC5.5 unsafe names | live | scope folders `bad name`, `x;rm` | row lists, `name_safe: false`, `commands: []` | pass |
| ANSI in text | live | brief with ESC and BEL | valid JSON, raw text kept (the mod must strip it; ticket 03) | pass |
| AC1.3 herdr unreadable | live | run with herdr off PATH | agents null; "Cannot read herdr: open board"; scopes `unknown: [herdr]` | pass |
| AC3.2/3.3/3.6/3.7 command lists (scratch and real) | live | read commands | goal-name Resume; closed scope: Board, Report, Report status; Retire only on done goal and lone done scope; Resume "agents are working", Inbox "no open questions"; Board says keeps running | pass |
| AC5.3 paste: Report status, Inbox list, Watchdog status, `--help` entries | live | pasted on the real squad with the archived bin on PATH | "missing"; "0 to answer, 0 to read, 0 waiting"; watchdog status line; usage text | pass |
| AC5.3 paste: Close scope `--dry-run` (scratch) | live | pasted | dry run printed, nothing moved | pass |
| Close squad warning is true | live | compared with what `squad-close <squad>` does (CLOSE-5) | retires every agent and archives | pass |
| AC5.3 Close goal text | live | read the text on a ready goal (real `process-fixes`) | `squad-close plugin --goal process-fixes` with NO `--dry-run` | FAIL (Manager ruling FINAL: a FAIL, spec rule 8 and AC5.3) |

Not run: Resume, Board (opens a browser tab or Manager tab; board I ran separately with --no-open), Sleep when idle (writes).

Follow-ups:
1. Report/Report status text uses the squad folder path (`--squad /abs/.../plugin`); the spec table says `--squad S`. It runs, so I accept it.
2. Real goal `process-fixes` shows "20 of 200" tasks: each of its 10 scopes repeats the goal's 20 tickets. The board shows the same ("180 open tasks"), so AC1.4 holds, but it looks wrong to a user.
3. With herdr unreadable, goal g1 has `unknown: []` while its scopes have `unknown: [herdr]`.

#### Re-check, sha b5018d8 (LC-3b: Close goal text only)

| What | live/shot | What I did | What I saw | Result |
|---|---|---|---|---|
| AC5.3 Close goal text | live | `squad-tree --repo . --json` from the archive of b5018d8, read `close-goal` on real goal process-fixes | `squad-close plugin --goal process-fixes --dry-run` | pass |
| AC5.3 paste Close goal | live | pasted that text on the real squad | dry run: "would retire plugin-coach-process-fixes", "would move .../goals/process-fixes to goals/_done/process-fixes", Manager kept; nothing moved | pass |
| Fixtures | live | read `hooks/squads/fixtures/tree.json` and `tree-herdr-down.json` | Close goal and Close scope texts carry `--dry-run` (4 hits each) | pass |
| Close squad text | live | read `close-squad`; pasted `squad-close plugin --dry-run` | text is `squad-close <squad>` with the warning "retires every agent and archives the squad", as the spec table says; the CLI also accepts `--dry-run` on a squad | Follow-up (Manager FINAL: spec table wins over AC5.3 wording) |

Verdict on b5018d8: PASS. Follow-up: Close squad copy has no `--dry-run`; a paste archives the squad. BA to decide at promotion whether it should.

## Tech Lead review

### Tech Lead review: ticket 02 (data CLI), sha 9fe68b9

Verdict: FAIL on 9fe68b9 (F1, one line); **PASS on b5018d8** (F1 fixed, see Re-review). Everything else meets the technical AC. Checked by reading the code at 9fe68b9 and by running it on a git-initialised copy of that commit (`git archive`), 2026-11-12.

#### Findings
- **F1 (required): Close goal has no `--dry-run`.** `bin/squadcommands.py` `close-goal` text is `squad-close S --goal G`. Spec AC5.3 says Close is copied with `--dry-run`; spec rule 8 offers "close goal `--dry-run`" first; `close-scope` already has it. Fix: `squad-close %s --goal %s --dry-run`. Update the fixtures and the T1.12 run (the dry-run form must exit 0 or refuse as the CLI does).
- **F2 (note, not required): Resume for a scope whose `goal:` names a goal that does not exist.** `_resume_name` falls back to the scope name, and `squad-start --resume` refuses a scope that has any `goal:` line (bin/squad-start:259-261). Rare (a broken goal reference). Optional: in that case give Resume `state: wait` with reason `goal G not found`. Put it in the backlog if not done.

#### AC check (tasks/tech-ac.md)
| AC | Result | How |
|---|---|---|
| T1.1 golden | ok | tests pass; two goldens (herdr readable, herdr down) per the 2026-11-12 ruling |
| T1.2 read-only | ok | real run on this repo: `git status --porcelain` unchanged; CLI writes only stdout |
| T1.3 discovery | ok | `find_repo`: `--repo`, `SQUAD_DIR` parents[2], `git --git-common-dir` parent (worktree safe), cwd |
| T1.4/T1.4b | ok | facts come from `scope_row` / `goal_row`; `_facts` has the six keys; no `new` |
| T1.5 light rows | ok | `_light` used for lone done scopes, done goals and their scopes; done scope of an OPEN goal has full facts |
| T1.6 herdr once | ok | memo in `sel` (`_herdr_working`); `test_squadboard_list` passes except the pre-existing T04_AC1 |
| T1.7 performance | ok | this repo (3 squads): 0.091 s wall |
| T1.8 next_step | ok | rules read in order 8 (goal, no open scope), 1 (null fact), 2, 3, 6, 4, 5, 7, 9; goal's rule 2 names the first open scope with questions (sorted by questions) |
| T1.9 commands | ok except F1 | `name_safe`, quoting by `os.name`, retire only for lone or goal, Close scope/goal `wait` reasons, inbox text `squad-inbox --home DIR list --open --no-write` |
| T1.10 broken file | ok | `scope_row` already tolerant; light rows read `scope.md` via `_text` |
| SQ-10 files | ok | `test_windows_safe`, `test_utf8_helpers`, `test_instructions` pass on the copy |

Targeted run on the copy: `test_squadtree test_squadcommands test_squadboard_list test_windows_safe test_utf8_helpers test_instructions`: 77 tests, 1 failure = `test_squadboard_list.test_T04_AC1`, pre-existing (fails the same on 76dd43a and a6520db: file mtimes of the copied fixture). The demo browser tests (2 of 13) also fail on the base; not run again here.

#### Safety and style
- No `run_ok` or `argv`; `KEYS` holds exactly the ten Command keys; no `--force` in any text.
- Python text uses `encoding`; the CLI calls `squadio.utf8_stdio()` first; no `fcntl`.
- `squadboard.py`/`squadboard_list.py` edits are additive (alias `goal_row`, memo, `squads_of`); the board is unchanged.

Final sha: not named yet (REV-3): after the F1 fix and both QA verdicts.

#### Re-review: b5018d8 (2026-11-12)
- Diff 9fe68b9..b5018d8 is 4 files, 4 lines: `bin/squadcommands.py` close-goal text now `squad-close S --goal G --dry-run`; both fixtures carry that one changed `text`; `tests/test_squadcommands.py` expects it. Nothing else changed.
- Targeted run on a git copy of b5018d8: `test_squadtree test_squadcommands test_windows_safe test_utf8_helpers test_instructions`: 64 tests OK. (`test_squadboard_list` T04_AC1 is the pre-existing failure, unchanged by this fix.)
- T1.12: close-goal is in the "every flag is in the tool's usage" group (not run: it can refuse or move folders); close-scope's dry-run runs for real. Accepted.
- F2 goes to the backlog (Team Lead's ruling).
Final sha: named after both QA verdicts (REV-3).

## QA whitebox review

### QA whitebox: ticket 02 (data CLI)

#### Return 2: sha ffbb7b3 — PASS
Re-check (LC-3b): only tests/test_squadtree.py changed (+29 lines). Read-only clone, `python3 -m unittest test_squadtree`: 13 tests OK.
- Finding 1 fixed: `test_T1_4b...` now compares each open goal's `facts` with `L.goal_row` over the same scope rows.
- Finding 2 fixed: `test_T1_8_AC1_5_AC1_6_sort_order_and_squad_total` asserts order [q1, fix, new1, old1] (needs you, stuck, recency) and squad needs_you = 3. `squadtree._sorted_goals` and scope order both use the board's `_sort_open`, so the test exercises the real sort.
- Follow-ups from return 1 stay as Follow-ups (not AC).

### Return 1: sha b5018d8 (base a6520db; 9fe68b9 + Close goal --dry-run)

Verdict: FAIL (return 1): two written AC have no test. Everything else passes.
Read-only: clone of the branch checked out detached in a mktemp dir; the Developer's worktree untouched.

#### Ran
- `cd tests && python3 -m unittest test_squadtree test_squadcommands test_windows_safe test_utf8_helpers test_instructions test_squadboard_list`: 77 tests, 1 failure = `test_squadboard_list` T04_AC1 `last_active`. Same failure on main 76dd43a (run by me), so not from this diff (T1.6 "unchanged": 12 of 13 pass, same as base).
- Live run, REV-5b: `squad-tree --repo <this repo> --json` with real herdr and real git: 0.086 s (T1.7, limit 2 s). 3 squads, 31 scopes; parses; rules 3, 4, 8, 9 all seen on real rows (squads-mod "1 task stuck", update-not-deny "All tasks done: close", goal process-fixes "All scopes closed: close goal"); working tree clean afterwards.
- Live copied texts: `squad-report status cleanup --squad <path>` = fresh, rc 0; `squad-close plugin --goal process-fixes --dry-run` rc 0 "would move ... Manager stays". `git status` clean after.
- Diff read: `squadtree.py`, `squadcommands.py`, `squad-tree`, `squadboard.py` (+`squads_of`), `squadboard_list.py` (memo `_herdr`, `goal_row` rename; the only caller of `_goal_row` was in this file, updated).

#### Findings (break a written AC: tests missing)
1. **T1.4 goal rows are not compared.** AC: "the six facts of a scope row AND of a goal row equal `scope_row` / `goal_row`". `test_T1_4b_field_shape_and_facts_equal_the_board` (tests/test_squadtree.py ~line 110-120) skips everything but `kind == "scope"`. Would pass: also compare each open goal's `facts` with `L.goal_row(squad, home, "open", scope_rows)` built from the same scope rows (a few lines in that test).
2. **T1.8 "sort case AC1.6" has no test (and AC1.5 total has none).** No test in test_squadtree.py checks the order of rows. AC1.6: equal needs you, more stuck first; equal stuck, more recent first. Would pass: one test on `_sorted_goals` or `build` output with three rows (equal needs you; different stuck; equal stuck, different `last_active`) asserting the order, and the squad `needs_you` = 2 + 1 = 3 (AC1.5; the golden holds one value only).

#### Follow-ups (not AC, no return)
- `squadcommands.py:19` has its own `NAME_RE`; design-notes s3 says use `squadboard.NAME_RE`. Two copies can drift.
- A scope whose `goal:` line names a goal that does not exist is treated as lone, so Resume prints `squad-start --resume <scope>`, which `squad-start` refuses ("belongs to goal X", bin/squad-start:261 checks only the scope.md line). Rare; Tech Lead to decide.
- A goal with zero scopes shows rule 8 "All scopes closed: close goal" (a goal just started). Spec rule 8 says "no open scope left", so it follows the text; BA may want "no scopes yet".
- Goal totals multiply a shared ticket folder (process-fixes: 20 of 200, each of 10 scopes counts the same 20 tickets). Equal to the board's number (AC1.4), so not a defect of this ticket; a board issue.
- T1.7 evidence quotes only herdr absent (0.10 s); the herdr-present number is 0.086 s (mine).
