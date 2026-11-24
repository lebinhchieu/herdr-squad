# 06 Skill: a refused home no longer blocks the move; `upgrade --apply` log row stops saying scopes keep their pin
Duties: Developer builds and writes design notes (this file is the design) and the evidence; technical AC are in this file (Tech Lead, agreed with QA whitebox); business AC = this ticket as written; QA whitebox code check; QA blackbox behaviour check (walks the refused-home dialog and reads the log row in a scratch squad); hand in to both QAs
Files: skills/squad-process-update/SKILL.md, skills/squad-process-update/changelog.md, bin/squadupgrade.py, tests/test_squadupgrade.py
Evidence: .scratch/fix-update/issues/06-refused-home-and-log-row/evidence.md
Status: ready
After: 03 (build on 03's branch, tip 117c442; the sha both QAs passed for 03 is e728bb8). No file overlap with 04 (docs/adr, CONTEXT.md): the Team Lead may give both to one Developer, 06 first.

Ticket path: `.scratch/fix-update/issues/06-refused-home-and-log-row.md`. Touched files are an estimate (LC-9b); a change re-issues this file.
Origin: QA follow-ups 1 and 2 of ticket 03, turned into this ticket by the Manager's DECISION 03, 06 (both show up the first time Chieu uses 0.10.2). It stays plugin 0.10.2: no version bump (SQ-5 was spent in 03); the changelog v21 block gets one line.
Harness: the `run(...)` helper and `Base` of `tests/test_squadupgrade.py`; for the refused-home walk use the scratch-squad setup 01 and 02 used for `homes` (a home whose compose is refused: an old-pinned scope under an overlay with a re-hashed replace op, see `tasks/plan-notes.md` Risk check; or the read-refused case `tests/test_squadupgrade.py` already builds for `homes`). Run tests from `tests/` with `python3 -m unittest <files>`.

## Problem
1. **Refused home.** `squad-process homes --check` exits 2 when any offered home is refused (compose or read), though other homes still move (`bin/squadhomes.py` run(): the table prints, then exit 2). `homes --apply --yes` without `--only` then raises `refused <home>: ... (deselect it with --only)` and writes nothing (`bad` list). SKILL.md step 4 says for exit 2 "show its words, offer only the homes that compose", but it has no inbox item for that case (the item is defined for exit 3 only) and its option (a) `homes --apply --yes` carries no `--only`, so the skill's own command refuses. Safe (nothing written), but the skill fails on a real path.
2. **Stale log row.** `bin/squadupgrade.py:561` writes into `process-log.md` the row `Upgraded plugin <old> -> <new>; running scopes keep their scope.md pin`. With the Home step of 03 that is the opposite of what happens next, and it stays in the log for good. Only this one line prints the claim: `grep -rn 'keep their scope.md pin' bin skills README.md docs tests` hits `bin/squadupgrade.py:561` alone (checked by the Tech Lead; the v20 changelog line 37 says "pinned scopes keep their runtime", a different true statement: leave it).

## Design
1. **SKILL.md step 4, exit 2 (a refused home).** Replace the sentence "Exit 2 (a refused home): show its words, offer only the homes that compose." by a short flow, same style, under 8 added lines:
   - Show the refused home's own words (the table row and note) and put it in the report; never route around it.
   - Read the table of `homes --check`: the homes whose state is `moves` are the composing ones. None: say "no home can move now" and go to step 5; no item.
   - Else ONE inbox item as in the exit 3 case, the body also naming each refused home and why it stays, with options `(a) move <names of the composing homes> and respawn now; (b) move only <goal home> (only when the goal is a composing mover); (c) leave them`. The yes: (a) `squad-process homes --apply --yes --only <every composing home name> --squad-dir <squad>`; (b) `--only <goal home name>`; (c) stop. Say plainly that without `--only` the apply refuses and writes nothing.
   - The exit 3 flow stays as written: its (a) has no `--only` because nothing is refused there. Keep both flows consistent (same body fields, same respawn text).
2. **bin/squadupgrade.py:561** the row text becomes `Upgraded plugin <old> -> <new>; open scopes and goals keep their own pin until squad-process homes moves them`. True whether or not Chieu runs the Home step. Nothing else in `cmd_apply` changes: the row's second cell, `rows`, the order of writes (`plugin.pin` last) and the printed `backup:` / `log rows:` / `applied:` lines stay. Past rows already in a squad's `process-log.md` are history and are never rewritten.
3. **changelog.md v21 block**, under `changed:`, one line: `- `upgrade --apply --yes` logs "open scopes and goals keep their own pin until squad-process homes moves them" instead of "running scopes keep their scope.md pin"; the skill's refused-home case moves the homes that compose with `--only`. why: both read wrong next to the new Home step.` Not a new version.
4. No other file changes: not `bin/squadhomes.py` (its refusal and `--only` are right as built), not `plugin.json`, not README.

## Compatibility (LC-12)
Only a log row's wording and skill text change. A reader of the old row: `grep -rn 'keep their scope.md pin\|running scopes keep' bin skills tests docs README.md templates` (the Developer runs it, quotes it, and runs every hit). Tests, `squad-report` or `process-log` parsers that match the `Upgraded plugin` prefix keep working: the prefix and the first cell shape do not change. No deploy step beyond 03's; rollback = revert this commit.

## AC
- AC1 `grep -rn 'keep their scope.md pin\|running scopes keep' bin skills README.md docs tests templates` prints nothing; `grep -n '\-\-only' skills/squad-process-update/SKILL.md` shows the composing-homes `--only` in the exit 2 flow as well as the goal-only one.
- AC2 Test (extend one existing test in `tests/test_squadupgrade.py`, no new file): after `upgrade --apply --yes` the new log row in `process-log.md` contains `until squad-process homes moves them` and not `keep their scope.md pin`; the `Upgraded plugin` prefix, `applied:` line and `plugin.pin` write are unchanged (the existing assertions stay and pass).
- AC3 QA blackbox walks the refused-home case in a scratch squad (a goal or a lone scope plus a refused home): `homes --check` exit 2 with the table; the skill's (a) command `homes --apply --yes --only <composing names>` exits 0, moves only those homes (their pin files and log rows change), leaves the refused home's pin file and log untouched; the same apply without `--only` still exits with the `refused ... (deselect it with --only)` text and writes nothing. The evidence quotes the `squad-inbox add` line for the new item with its body file text and the printed output of all three commands. A case with no composing home: the text says "no home can move now", no item.
- AC4 Technical (SQ-10, bin text changes): run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`, `tests/test_squadupgrade.py`, `tests/test_promotion_0_6_0.py` (version stays 0.10.2, changelog test) and `tests/test_squad_spawn.py` (it has legacy `squad-process-update` cases); quote the result in `## Behaviour`. `plugin.json` stays 0.10.2: `git diff 117c442 -- .claude-plugin/` is empty.
- AC5 No change to `bin/squadhomes.py`: `git diff 117c442 -- bin/squadhomes.py` is empty.

## SQ-1 (deletes and moves)
Deletes or moves no file. Readers of the removed text: none outside `bin/squadupgrade.py` (the grep in AC1 is the check).

## Comments
