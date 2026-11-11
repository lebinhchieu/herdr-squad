# Task 21: squad-start without touches

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"; templates/ changes include goldens). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Also run tests/test_windows_safe.py, tests/test_utf8_helpers.py, tests/test_instructions.py (SQ-10) and quote the result in `## Behaviour`. Chieu wants `touches` gone: "I do not need it". No version bump in this task (SQ-5).

Status: ready
Files: bin/squad-start, templates/scope/scope.md, templates/goal/goal.md, tests/test_squad_start.py (extend; grep `tests/` for `touches` and run every hit; old board fixtures that carry a `touches:` line stay as they are, they prove old files load)
Ticket: commit this file's content as `.scratch/process-fixes/issues/21-squad-start-no-touches.md` in your first commit.
Base: main. No merge into main.

## AC
- AC1 New briefs: a scope or goal made by `squad-start` has no `touches:` line (both templates).
- AC2 Option: `--touches` is gone from `squad-start` (usage text, parser). Passing it fails like any unknown option (exit 2). No overlap check and no `--yes` stop for overlap; `--yes` stays only if another check still uses it (design notes say which, else remove it too).
- AC3 Old files: existing `scope.md` / `goal.md` with a `touches:` line still load and never matter (no error, no stop). Any reader of `touches:` in `bin/` is removed (grep `bin/`), only `squad-start` is expected to have one.
- AC4 One test per AC (extend the existing file); a removed overlap test is deleted, not skipped.

## Design notes
Touched files: bin/squad-start, templates/scope/scope.md, templates/goal/goal.md, tests/test_squad_start.py, tests/test_templates.py (placeholder asserts), tests/test_squadruntime.py (drop the `open_scope_touches` call), tests/test_team_models.py (drop the `{{touches}}` replace; QA whitebox did not list it).
- Agree with QA whitebox technical AC T1-T7 and its points 1-3.
- Removed from `squad-start`: `tokens`, `overlaps`, `open_scope_touches`, `--touches`, the overlap stop (exit 3), the `touches` render value, docstring text.
- `--yes` removed with the stop: its only use was the overlap stop. `--yes` now fails as an unknown option (exit 2). No caller in bin/ templates/ hooks/ passes it to squad-start; the SKILL.md line that mentions it is task 22.
- No other reader of `touches:` in `bin/` (grep). Old files keep the line; nothing reads it.
- T2: the unknown-option test uses `--touches` only. The `--yes` removal is covered by T1's grep.
- T5: `test_overlap_...` and `test_disjoint_touches_...` replaced by `test_touches_is_an_unknown_option...` and `test_old_files_with_a_touches_line...` (T4: `--in-goal`, lone start, `--resume` of a scope and of a goal, files untouched). Nothing skipped.
- Known failure on main, unrelated: `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` fails the same on a clean `git archive HEAD` copy.


## Technical AC (QA whitebox; Developer: reply in Design notes if you disagree, 2 rounds, LC-4/CORE-4)
Facts from my grep of main 7d4b71d: in `bin/` only `squad-start` reads `touches` (`tokens`, `overlaps`, `open_scope_touches`, the `--touches` option, the `render` value); `--yes` is used only by the overlap stop (squad-start:387); `tests/test_squadruntime.py:645-647` calls `smod.open_scope_touches`; `tests/test_templates.py:21-22` asserts a `touches` placeholder; ~45 calls in `tests/test_squad_start.py` pass `--touches` (some with `--yes`).
- T1 `bin/squad-start` has no `touches`, `overlap`, `--yes`, exit-3 text left (`grep -n -i 'touches\|overlap\|--yes\|a\.yes' bin/squad-start` is empty), and no dead helper: `tokens`/`overlaps`/`open_scope_touches` deleted; `tokens` stays only if still used. Docstring usage and the `render` values no longer name touches. Design notes confirm `--yes` is removed (its only use was the overlap stop).
- T2 `--touches` and `--yes` fail as unknown options: exit 2, nothing created (one test, `--touches` is enough).
- T3 Both templates lose the `touches:` line and `{{touches}}`; `grep -rn touches templates/scope templates/goal` is empty. `tests/test_templates.py` placeholder asserts are updated IN THIS TASK (otherwise it fails at the 21 sha). New-brief test reads the made `scope.md` and `goal.md` and asserts no `^touches:` line.
- T4 Old files load: one test puts a `touches: x` line in an existing `scope.md` and `goal.md`, then runs `squad-start --in-goal` and `--resume`: exit 0, no `touches`/`overlap` in stderr, line left in the file untouched.
- T5 Every test call of `--touches` / `--yes` is edited out (grep of `tests/test_squad_start.py` empty). The two overlap tests (`test_overlap_...`, `test_disjoint_touches_...`) are deleted, not skipped; no new `skip`.
- T6 `tests/test_squadruntime.py:645-647` no longer calls the deleted function (drop those 3 lines; the rest of that test stays). Fixtures that carry `touches:` (board, inbox, test_squad_team:175, test_squad_spawn, test_team_models:133) stay as they are.
- T7 Run and quote: `tests/test_squad_start.py`, `test_templates.py`, `test_squadruntime.py`, `test_team_models.py`, `test_squad_team.py`, `test_squad_spawn.py` (the `grep -rl` hits), plus the three SQ-10 files; all pass, none newly skipped. No full suite.

## Review
| AC | Test | How run |
|---|---|---|
| AC1 | tests/test_squad_start.py `test_lone_task_creates...` and `test_goal_prefix_creates...` (no `touches` in made scope.md and goal.md); test_templates.py placeholders | `cd tests && python3 -m unittest test_squad_start test_templates` |
| AC2 | test_squad_start.py `test_touches_is_an_unknown_option_and_creates_nothing` (exit 2); T1 grep of bin/squad-start empty | same; `grep -n -i 'touches\|overlap\|--yes\|a\.yes' bin/squad-start` |
| AC3 | test_squad_start.py `test_old_files_with_a_touches_line_still_load_and_never_stop_anything`; grep of bin/ readers | same |
| AC4 | the two overlap tests deleted, two tests above added, no skip | `git diff main -- tests/test_squad_start.py` |
