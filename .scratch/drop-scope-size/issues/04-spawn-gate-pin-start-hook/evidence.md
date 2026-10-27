# Evidence: 04 spawn gate, pinned hand-off, start, hook
sha: b2dcc52

## Behaviour
- `squad-spawn` team gate (via `squad-process team --has`): role not on team exits 1 naming role and `scope.md`, nothing created; `qa-whitebox`/`qa-blackbox` gated on `qa-white`/`qa-black`; undecided team refuses all but Manager; `size:`-only or bad `team:` line exits 2 with the converter pointer / line+token; hostile `team:` values run nothing. Goal Manager has no gate.
- Pinned scope below 0.6.0: `squad-spawn` and `squad-respawn` `exec` the pin's own script with the same args (PO shell and agent session; `--dry-run` prints "would hand off"). Pin 0.6.0 -> new gate, no hand-off; no pin line -> unpinned path; malformed `plugin:` line -> refused naming the line; runtime without the script -> warning, exit 1, nothing created/renamed. One hop (runtime == this script is not re-entered). Pinned `scope.md` byte-identical after spawn and converter.
- `squad-log-message`: 3-returns notice to Team Lead iff `team-lead` on team, else Manager (also on `none`, undecided, error, `size:`); text has no size word.
- Where the 3-returns notice shows (AC 12): stdout of the hook, one JSON line `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"task N has 3 returns: ..."}}`; no file, socket or pane. Trigger: HANDIN (with `commit <sha>`) + FAIL on three distinct shas; only the 3rd FAIL prints; three FAILs on one sha count as one. Test: `test_the_notice_is_stdout_json_on_the_third_failing_sha_only`.
- Dry run with a pinned runtime lacking the script now warns and exits 1 like a real run (`test_a_dry_run_without_the_pins_*`, both scripts).
- A composed scope with `size:` and no `plugin:` line is refused with `scope.md:N: old format \`size:\`` + `squad-process adopt` (fix in `squadruntime.py` `cmd_runtime`); scopes with neither keep the pin text. Tests `test_a_composed_scope_with_size_and_no_pin_*`, both scripts.
- Pin-version / <0.6 / exec-guard block is duplicated in `squad-spawn` and `squad-respawn` on purpose: a shared sourced helper would live in the running engine and be missing from, or differ in, a pinned runtime; each script is standalone, and the two differ in the home variable, args and message.
- `squad-start:367`: Manager prompt says "propose the team".
- Lint baseline (G2b): `squad-process lint` on base 6389642 empty; branch empty; diff identical.
- Tests green: test_squad_spawn (85), test_squad_respawn (21), test_squad_log_message (22), test_squadruntime (64), test_squad_start (48), plus grep hits: crlf_squad_files, squad_ledger, squadsettings, team_lead_perms, team_models, utf8_helpers, windows_safe, team_lead_role, squad_usage_hook, squad_manager_guard, templates, instructions, architect_handoff, dev_rules_size, hooks_json, squadreport_digest.
- Changelog v9: no rule ID changed in this ticket.

## QA whitebox

### QA whitebox 04 — on code c97299a (HANDIN 0763658, evidence-only after). Verdict held until the Tech Lead names the final sha (REV-3).
Checked read-only in worktree plugin-dev-dsz-04. Passed:
- Tests OK: test_squad_spawn (85), test_squad_respawn (21), test_squad_log_message (22), test_squadruntime (64), test_squad_start (48). `squad-process lint` exit 0 empty (= base).
- Diff vs design D7/C2/C3: gate order (refusal before any worktree/label/herdr), undecided -> Manager only, `qa-whitebox` gated on `qa-white`, hand-off once (runtime == this script is not re-entered), pin >= 0.6.0 / no pin / malformed line paths, runtime missing script refused. Test names cover the pin boundary table, hostile `team:` value, byte-identical pinned scope.md, golden from base sha 2949573 (git archive, composed by the pin's own engine).
- REV-5b live (copy of this squad: pinned 0.5.2, `size: L`, stub herdr): `squad-respawn` from an agent session and PO shell: dry run prints "would hand off to the pinned runtime"; real run exec'd the pin's own squad-respawn -> pin's squad-spawn: rules recomposed with "size L", roster session id updated, old pane closed, scope.md byte-identical. `squad-spawn qa-whitebox` (dry) on the pinned copy hands off; no pin line -> refused with pin message, no herdr call; a hostile `team:` line on a mixed old/new scope.md refused (exit 2), nothing run (no PWNED files).

#### F1 (correctness) bin/squad-spawn (hand-off block, `if [[ $dry == 1 ]]`) and bin/squad-respawn (same block)
`--dry-run` exits 0 with "would hand off to the pinned runtime: .../bin/squad-spawn ..." BEFORE the `[[ -f $runtime/bin/squad-spawn ]]` check. Repro: composed squad, scope.md `size: L` + `plugin: 0.5.2 <sha>`, pin runtime folder with plugin.json but no bin/squad-spawn: `squad-spawn dev d1 --scope s1 --prompt hi --dry-run` -> rc 0 "would hand off"; without `--dry-run` -> rc 1 "has no bin/squad-spawn; refusing, nothing created". Ticket extra AC: runtime without the script -> refuse with a warning, no fallback. A dry run must predict that refusal.
Pass: move the `-f` check above the dry-run branch in both scripts (dry run then warns and exits 1) + one test per script for the dry case (the existing test_a_runtime_without_squad_spawn... covers only the real run).

#### F2 (style, REV-17 all in one return) bin/squad-spawn + bin/squad-respawn
The pin-version read (`sed` on plugin.json, basename fallback), the `0.N` < 6 test and the exec guard are the same ~10 lines in both scripts. Not a blocker alone; a single shared helper (e.g. a `squad-process runtime --pin-version` / small sourced function) would keep the boundary in one place. Pass: either dedupe, or one line in evidence.md saying why not.

### Re-check on final code sha b2dcc52 — PASS (LC-3b: changed files only)
- F1 closed: `-f` check now precedes the dry-run branch in squad-spawn and squad-respawn; live repro (pin 0.5.2 runtime without the script): `--dry-run` rc 1 with the warning, same as the real run. Tests added in test_squad_spawn (87) and test_squad_respawn (23).
- F2 accepted: no shared helper (a pinned runtime cannot share code with the running engine; evidence.md says so; Tech Lead agreed).
- squadruntime.cmd_runtime: an unpinned `size:` scope now gets the converter pointer instead of the pin text (live: `scope.md:5: old format size:; run squad-process adopt`). Tests OK: spawn, respawn, log_message (23), squadruntime (64), start (48), squadcompose (85). Lint exit 0 empty.

## QA blackbox

### QA blackbox, task 04 (HANDIN 0763658, code c97299a, branch squad/plugin/drop-scope-size/plugin-dev-dsz-04)

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

#### Findings
- F1 (FAIL, Tech Lead ruled it a finding): composed scope with no `plugin:` line and `size:` (no `team:`) is refused with the old "composed mode needs a pin" text. AC 26 needs the message to name file and the `size:` line and point at `squad-process adopt`. Repro: scratch squad (git repo, process.local.md, `_runtime/`), scope.md `name: s` + `size: M`, `squad-spawn manager m1 --scope s --dry-run --prompt x` -> exit 2, wrong text. A scope with neither `size:` nor pin may keep the pin message.
- F2: closed. Dev answered how to trigger; AC 12 hook half PASS (row above).

#### Re-check on b2dcc52 (diff c97299a..b2dcc52; Tech Lead final)

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

## Tech Lead review

sha b2dcc52 (final code, 04, return fixes): TL re-ran spawn/respawn/log_message/squadruntime/start tests OK, lint empty; read diff c97299a..b2dcc52: -f check above dry run, size-without-pin pointer, notice test. Dedup skip accepted (pinned runtime cannot share a helper).
