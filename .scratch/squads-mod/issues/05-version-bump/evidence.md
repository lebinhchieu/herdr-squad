
sha: bcd75a6
## Review
AC trace:
- T3.1 | `.claude-plugin/plugin.json` 0.9.0, `skills/squad-process-update/changelog.md` v14 | `git diff 5d7af34 -- .claude-plugin skills`
- T3.1b | `grep -rn "0\.8\.1" .claude-plugin` | no hit (exit 1)
- T2.10 | `hooks/squads/fixtures/real.json` already present (from 03) | `ls hooks/squads/fixtures`
- SQ-6b | merge of 04 (66f78c5) into this branch, no conflict | `git log --merges -2`
- SQ-10 | the three files below | `python3 tests/<file>.py`

## Behaviour
- test_windows_safe 14 OK; test_utf8_helpers 14 OK; test_instructions 16 OK.
- Targeted: test_processlint 31 OK, test_promotion_0_6_0 3 OK, test_squadupgrade 29 OK, test_old_language_inventory 2 OK (one allow-list line added for `hooks/squads/testkit.ts`, a false positive: `fs.stat size`).
- `claude plugin test`: 644 pass, 0 fail.
- Version 0.9.0 (new feature, minor bump). Changelog block v14 has no rule changes.

## Return 1 (QA blackbox FAIL 4eaa748: squad order)
- `bin/squadtree.py` `_squad_order`: squads sort by needs you, stuck (sums over open goals and lone open scopes), then newest last active; flat/unreadable count 0.
- Test: `test_squads_sort_by_needs_you_then_stuck_then_newest` in `tests/test_squadtree.py` (equal needs: stuck, then newest).
- Goldens `tree.json`, `tree-herdr-down.json` regenerated (plugin now before old-flat); two index lines in the tests follow. `python3 tests/test_squadtree.py` 15 OK; `claude plugin test` 644 pass.

## Review: QA whitebox

### QA whitebox, ticket 05, final sha bcd75a6 (HANDIN 4eaa748, then QA blackbox return, diff bcd75a6)
Verdict: PASS. Clean clone detached at bcd75a6, run by me.

| AC | Check | Result |
|---|---|---|
| T3.1 | plugin.json 0.9.0; changelog v14; 5d7af34..4eaa748 touches no templates/ or rule text, so "no rule changes" is true | ok |
| T3.1b | `grep -rn "0\.8\.1" .claude-plugin` | no hit (exit 1) |
| SQ-6b | shas of 01, 02, 03, 04 are ancestors of 4eaa748, which is an ancestor of bcd75a6 | ok |
| SQ-10 | test_windows_safe 14, test_utf8_helpers 14, test_instructions 16 | OK |
| allow-list | hooks/squads/testkit.ts:29 `fs.stat` returns `size: 1`: real false positive | ok |
| integration | test_squadtree, test_squadcommands, test_hooks_json, test_po_inbox_mod: 30 OK; test_old_language_inventory 2 OK; `claude plugin test` 644 pass | ok |
| squad order (return from QA blackbox) | bin/squadtree.py `_squad_order` = needs you, stuck, newest (spec.md:18, ui-design line 14); new test covers 5 squads incl. flat; goldens tree.json and tree-herdr-down.json differ from 4eaa748 only by squad order (checked by JSON compare: same squads, same other keys) | ok |
| live | `squad-tree --json` on this repo: plugin, accounts, board | ok |

#### Follow-ups (SQ-4, not a FAIL)
1. `test_squadboard_list` `test_T04_AC1_rows_order_and_done_list` (line 75) fails on main and on 5d7af34 in a fresh clone (last_active is the checkout time). Not from this scope; no board code changed. Expect it in the full `--tz` run; compare with main.
2. `_squad_order` inverts the time string with `chr(0x10FFFF - ord(c))`. Works for the fixed-width ISO timestamps used here; a plain two-pass sort would read clearer.

## Review: QA blackbox

### QA blackbox: 05 (sha 4eaa748)

Setup: `git archive 4eaa748`, scratch repo from tests/fixtures/squads-tree/build.py, `bin/squad-tree --repo <scratch> --json` into `hooks/squads/pane-text` (real data, no fixture).

| Check | How | Saw | Result |
|---|---|---|---|
| T3.1 version | plugin.json | 0.9.0; changelog has v14 block | pass |
| T3.1b | `grep -rn "0\.8\.1" .claude-plugin` | no hit | pass |
| T2.10 real.json | `ls hooks/squads/fixtures` | real.json present | pass |
| Real squad-tree data drawn | pane-text on out.json | title "2 need you"; plugin needs 2, goal g1, no goal group, Done folded; flat squad "flat squad: not supported" | pass |
| Open goal row, back (live) | `--press plugin/goal:g1` then `,back` | detail with facts and commands; back returns the list; scratch repo git status unchanged (only my own copy dir) | pass |
| AC1.6 within a squad | plugin: goal g1 (needs 2) first, then lone `fix` (stuck 1) | ordered by needs, stuck | pass |
| Story 1 / AC1.1 squad rows sorted by need | scratch with squads aaa (needs 0), old-flat, plugin (needs 2) | order aaa, old-flat, plugin: alphabetical, plugin (needs 2) last | FAIL (Manager FINAL: yes, squads sort by needs you, stuck, newest; squad = sum of its scopes) |
