# Evidence: 09 adopt existing squads; new squads start composed

**`squad-process adopt` turns a v6 squad into overlay + pin + local settings and pins its open scopes; `scaffold` (called by `squad-init`) starts new squads composed. Harness green (102 tests); the live folder is byte-identical after a dry run and a real run on copies.**

Harness: `cd tests; python3 -m unittest test_squadadopt test_squadupgrade test_squad_start test_windows_safe` → 102 OK. Also run (touched files): test_instructions, test_dev_rules_size, test_squadprocess, test_squadprocess_apply, test_model_effort_settings, test_squadsettings, test_process_history, test_squad_spawn, test_squad_respawn, test_squadruntime, test_squadcompose, test_squadrules, test_processlint.

## Behaviour

**B09-1 dry run on a copy of the live squad** (`adopt-dry-run.txt`, exit 3 = PO items open, nothing written).
- Overlay: **0 operations**. Three v6 edits are already in the plugin's rules (START-5 twice, LC-7a/7b/EVID-1) and need none.
- Four leftovers listed as PO items, none guessed: `L210` (LC-3a/3b/4 text), `L244` (COST respawn bullets), `L246+` (COST "Before a PO wait"), `L276+` ("No commits on the PO's branch"). Each is reworded in the final rules, checked by grep: LC-3b `re-checks only the changed files`, review.md "one final sha", lifecycle.md `defect class`, cost.md COST-3/COST-7/COST-10b `before every spawn` / `Before a PO wait`, SAFE-5 `No squad role commits on the PO's branch`. So the produced overlay answers all four `drop` (`adopt-real-on-copy.txt`).
- Result: `process.local.md` = title only → copied to `tests/fixtures/upgrade/live-squad.local.md` (built from the final rules at 22's sha plus 06/07/08/24; `cmp` equal). `CiDryRun.test_every_overlay_is_placeable` now globs it and `test_the_live_squad_overlay_fixture_lints_and_classifies` checks it.
- Live folder: `sha256sum` of every non-jsonl file under `.claude/squads/plugin/` before and after = identical; the dry run left the copy identical to the live folder too (B09-6).

**B09-8 permissions**: the dry run lists "permissions regained": every role gets `rule`/`who`; **team-lead regains `Bash(squad-spawn dev:*)`**, `squad-retire`, `herdr agent list|get|read` (the v4 gap). Also listed: model/effort keys the old files lacked. A retired `Bash(squad-process show:*)` is not carried into the local files. `adopt` refuses (exit 2) if any old allow/deny entry would be lost.

**B09-2 / AC2** `test_squadadopt.TwoOpsOneItem`: fixture with one edit (`When unsure, size up.`), one deleted bullet (SIZE-16), one paragraph no rule covers → dry run "overlay with 2 operation(s)", "PO items (1 open of 1)"; `--yes` alone or `--resolve` alone exit 3 `NOT APPLIED` and the tree hash is unchanged; with both: exit 0, `SIZE-4` and `SIZE-16` ops (`upstream: proposed`), `squad-process lint` 0. An edit whose old text is not found once in a mapped rule is an item, never an operation. Answers: `drop`, `add:<roles>` (SQ-n, topic `squad`), `replace:<ID>:<file>`; bad answers exit 2, nothing written.

**B09-3 / AC3** `ArchiveAndSettings`: after a real run `process.md` is gone, `process.v6-archived.md` is byte-equal to the original, `plugin.pin` holds the pin, a log row is written; each `settings/<role>.json` → `<role>.v6-archived.json` (equal to the original JSON) and `<role>.local.json` holds only the squad's difference (its own allow entries, a changed scalar, `codePaths` extracted from the Read denies; `.worktrees` entry regenerated). Effective settings (squadsettings.effective) contain every old allow/deny entry.

**B09-7 / BA G2** `OpenWork`: an open scope and goal without `plugin:` get `plugin: <pin>` (rest of file byte-identical; `_done/` untouched); `compose` for each home exits 0 with the pin; a second run is a no-op (tree hash equal); a run cut short after the overlay is finished by the next one. On the live copy: `scopes/role-cards-upgrade` and `goals/composed-process` pinned; `squad-process compose dev --home <scope>` exit 0.

**B09-4 / AC4** `Scaffold`: `squad-process scaffold` on an empty folder → no `process.md`; `process.local.md`, `plugin.pin`, `project.md`, nine `settings/*.local.json` (qa-blackbox with `codePaths`), `scopes/`, `goals/`; `squad-process lint --squad-dir` exit 0. Without `--code-path` it prints a note and spawning QA blackbox stays fail-closed. Re-run never overwrites; a legacy squad is refused (exit 2). `skills/squad-init/SKILL.md` steps 1, 3, 5 call it.

**B09-5 show retired / legacy kept**: `grep -rn "squad-process show\|ROLE_SECTIONS" agents skills bin templates tests hooks` → only tests asserting absence. `squad-process show` is an unknown command; `apply` without `--legacy` exits 2 naming `--legacy`; `plan`/`apply --legacy` tests pass; spawn/respawn legacy path is ticket 24's (tests green).

**Settings allow (Tech Lead extra)**: `Bash(squad-process show:*)` removed from the four templates; `rule`+`who` added to manager, ba, team-lead, tech-lead, token-coach (designer, dev, QAs had them). `test_instructions.RuleDutiesTest.test_all_nine_settings_allow_rule_and_who_and_none_allows_show_or_a_wildcard` covers all nine.

**B09-9 rollback** (done on the adopted copy): `rm process.local.md plugin.pin settings/*.local.json; mv process.v6-archived.md process.md; for f in settings/*.v6-archived.json: mv to <role>.json` → `process.md` and `settings/*.json` hash equal to the live originals. Scopes keep the added `plugin:` line (harmless in legacy mode).

## Deploy step (Manager, after merge)
1. `squad-process adopt --squad-dir .claude/squads/plugin --dry-run`; show `adopt-dry-run.txt`-style output to the PO as one inbox item (4 items; recommended answer `drop` for each, with the rule IDs above).
2. On the PO's yes: `squad-process adopt --squad-dir .claude/squads/plugin --resolve L210=drop --resolve L244=drop --resolve L246+=drop --resolve L276+=drop --yes` (keys are printed by the dry run; re-check them on the live files at that time).

## Notes for QA
- Merge fallout fixed here: `test_squadsettings` (24's legacy-squad stderr line vs 08's "no stderr"), `test_squad_start` squad-init wording, `test_model_effort_settings` (retired show entry), `test_process_history` (map file in the glob).
- `adopt` treats a v6 edit as an operation only when the old text is a verbatim (whitespace-normalised) substring of exactly one mapped rule body and the generated op lints; "already in the plugin" = every new line is a verbatim substring of a rule body. Anything else is a PO item.
