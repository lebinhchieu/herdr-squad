# QA blackbox, task 04 (HANDIN 0763658, code c97299a, branch squad/plugin/drop-scope-size/plugin-dev-dsz-04)

Method: scratch squad (mktemp dir, git repo, `team:` scope.md, `plugin: 0.6.0 abc1234` pin), the branch's `bin/squad-spawn --dry-run`, `squad-respawn --dry-run`, `squad-start --dry-run`, `squad-log-message` fed a SendMessage JSON. CLI only, no code read. Judged: AC 6, 12, 15, 20, 26, 27, 29, 30.

| AC | Did | Saw | Result |
|---|---|---|---|
| 6 | `team: ba, qa-white`: spawn ba, qa-whitebox, manager, dev | all would run (exit 0) | PASS |
| 6 | same team: spawn qa-blackbox, architect | exit 1: `role qa-blackbox is not on the team in .../scope.md (team: ba, qa-white); only the PO adds the designer or architect` | PASS |
| 15 | `team:` blank: manager / ba | manager ok; ba exit 1 `the team is undecided in .../scope.md; only the Manager can be spawned until a team: line decides it` | PASS |
| 15 | `team: none`: manager, dev | both ok | PASS |
| 30 | `ba, ba` / `ba, wizard` | exit 2 `scope.md:3: team token 'ba' listed twice` / `unknown team token 'wizard' (allowed: ...)` | PASS |
| 27 | `qa-whitebox` / `qa-b` in `team:` | exit 2 `team token 'qa-whitebox' is a role name; write 'qa-white'` / `unknown team token 'qa-b'` | PASS |
| 30 / G7 | hostile `team: ba; touch X` and `$(touch X2)` | exit 2 unknown token, X and X2 not created | PASS |
| 26 | legacy-mode squad (process.md, no pin), scope.md `size: M`: manager and ba | exit 2 `scope.md:2: old format size:; run squad-process adopt (dry run first) ...`, nothing started | PASS |
| 26 | `size: M` beside `team:` | exit 2 `old line size: beside team:; the team line decides, delete the old line by hand` | PASS |
| 26 | composed-mode scope with no `plugin:` line | exit 2 `composed mode needs a pin ...` (old message, does not name `size:` or adopt); this is the pre-existing no-pin refusal, not a legacy squad | FAIL, F1 |
| 20 | pin `0.5.2` + `size: L`: spawn dev dry run | `would hand off to the pinned runtime: .../_runtime/0.5.2-294957333ee4/bin/squad-spawn ...`, exit 0 | PASS |
| 20 | `squad-respawn dev-1 --dry-run` on pin 0.5.2, from PO shell and with SQUAD_NAME set | plan printed (rename, squad-spawn, close old pane), scope.md byte-identical (cmp) | PASS |
| 20 | pin `0.6.0` + `size: L` spawn | exit 2 `old format size:` pointer to adopt (no hand off) | PASS |
| 20 | malformed pin `plugin: bogus line` | exit 2 `plugin pin: expected plugin: <version> <sha> ..., got 'bogus' 'line'` | PASS |
| 29 | `squad-start "SEC-04 ..." --dry-run` output; templates/scope/scope.md | no word "size" (only inside worktree path `drop-scope-size`); scope template has `team:` | PASS |
| 12 | Dev's recipe: HANDIN aaaaaa1, FAIL, HANDIN bbbbbb2, FAIL, HANDIN cccccc3, FAIL piped into `squad-log-message`; teams `team-lead, qa-white` / `qa-white` / `none` / blank / `size: L` | only the 3rd FAIL printed the notice: `BLOCKED 05: 3 returns` to Team Lead [LC-7b] with team-lead on team; to Manager [LC-7c] for the other four | PASS |

Not covered by me (CLI dry-run cannot show it): non-dry respawn on a team missing the role (the `--dry-run` plan does not run the gate); pinned runtime missing `bin/squad-spawn` (I will not delete files of a real runtime).

## Findings
- F1 (FAIL, Tech Lead ruled it a finding): composed scope with no `plugin:` line and `size:` (no `team:`) is refused with the old "composed mode needs a pin" text. AC 26 needs the message to name file and the `size:` line and point at `squad-process adopt`. Repro: scratch squad (git repo, process.local.md, `_runtime/`), scope.md `name: s` + `size: M`, `squad-spawn manager m1 --scope s --dry-run --prompt x` -> exit 2, wrong text. A scope with neither `size:` nor pin may keep the pin message.
- F2: closed. Dev answered how to trigger; AC 12 hook half PASS (row above).

## Re-check on b2dcc52 (diff c97299a..b2dcc52; Tech Lead final)

| AC | Did | Saw | Result |
|---|---|---|---|
| 26 (F1) | composed squad (process.local.md, `_runtime/`), scope.md `name: s` + `size: M`, no `plugin:` line: `squad-spawn manager` / `dev` `--dry-run` | exit 2 `scope.md:2: old format \`size:\`; run \`squad-process adopt\` (dry run first) to convert the scope to a \`team:\` line` (names file, line, adopt) | PASS |
| 26 | neither `size:` nor pin / `team:` without pin | old "composed mode needs a pin" text kept (allowed) | PASS |
| 26 | `size: M` + `team: ba` no pin | exit 2 `old line size: beside team:; ... delete the old line by hand` | PASS |
| 20 | pin 0.5.2 + `size: L`, `_runtime/` empty, dry run dev | exit 1 `pinned runtime .../0.5.2-... has no bin/squad-spawn; refusing, nothing created`; `_runtime` still empty | PASS |
| 6/15/30 | regression: `team: team-lead, qa-white` spawn ba / qa-blackbox / manager; hostile `team: ba; touch HOSTILE` | ba, qa-blackbox exit 1 "not on the team"; manager ok; hostile exit 2 unknown token, file not created | PASS |
| 12 | 3x (HANDIN `commit <7-hex sha>`, FAIL) into `squad-log-message`, fresh log, 5 teams | only the 3rd FAIL prints stdout JSON `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"task 05 has 3 returns: also send BLOCKED 05: 3 returns to Team Lead [LC-7b] ..."}}`; Manager [LC-7c] for `qa-white`, `none`, blank, `ba, tech-lead`, `size: L`; 1st/2nd FAIL and 4th/5th silent | PASS |

Notes: notice counts HANDIN-FAIL pairs with 7+ hex shas; 3 FAILs of one sha with no new HANDIN print nothing. Short shas (`c1`) print nothing. Tech Lead's wording "3rd FAIL of the same sha" read as the Dev recipe; no AC text pins it.

Verdict: PASS on b2dcc52.
