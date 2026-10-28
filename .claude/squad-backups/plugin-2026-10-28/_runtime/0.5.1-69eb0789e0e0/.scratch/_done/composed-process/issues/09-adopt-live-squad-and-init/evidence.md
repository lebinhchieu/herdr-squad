# Evidence: 09 adopt existing squads; new squads start composed

**`squad-process adopt` turns a v6 squad into overlay + pin + local settings and pins its open scopes; `scaffold` (called by `squad-init`) starts new squads composed. Harness green (102 tests); the live folder is byte-identical after a dry run and a real run on copies.**

Harness: `cd tests; python3 -m unittest test_squadadopt test_squadupgrade test_squad_start test_windows_safe` → 102 OK. Also run (touched files): test_instructions, test_dev_rules_size, test_squadprocess, test_squadprocess_apply, test_model_effort_settings, test_squadsettings, test_process_history, test_squad_spawn, test_squad_respawn, test_squadruntime, test_squadcompose, test_squadrules, test_processlint.
sha: a5bf6fb
## Behaviour

**B09-1 dry run on a copy of the live squad** (`adopt-dry-run.txt`, exit 3 = PO items open, nothing written).
- Overlay: **0 operations**. Three v6 edits are already in the plugin's rules (START-5 twice, LC-7a/7b/EVID-1) and need none.
- Four leftovers listed as PO items, none guessed: `L210` (LC-3a/3b/4 text), `L244` (COST respawn bullets), `L246+` (COST "Before a PO wait"), `L276+` ("No commits on the PO's branch"). Each is reworded in the final rules, checked by grep: LC-3b `re-checks only the changed files`, review.md "one final sha", lifecycle.md `defect class`, cost.md COST-3/COST-7/COST-10b `before every spawn` / `Before a PO wait`, SAFE-5 `No squad role commits on the PO's branch`. So the produced overlay answers all four `drop` (`adopt-real-on-copy.txt`).
- Result: `process.local.md` = title only → copied to `tests/fixtures/upgrade/live-squad.local.md` (built from the final rules at 22's sha plus 06/07/08/24; `cmp` equal). `CiDryRun.test_every_overlay_is_placeable` now globs it and `test_the_live_squad_overlay_fixture_lints_and_classifies` checks it.
- Live folder: `sha256sum` of every non-jsonl file under `.claude/squads/plugin/` before and after = identical; the dry run left the copy identical to the live folder too (B09-6).

**B09-8 permissions**: the dry run lists "permissions regained": every role gets `rule`/`who`; **team-lead regains `Bash(squad-spawn dev:*)`**, `squad-retire`, `herdr agent list|get|read` (the v4 gap). Also listed: model/effort keys the old files lacked. A retired `Bash(squad-process show:*)` is not carried into the local files. `adopt` refuses (exit 2) if any old allow/deny entry would be lost.

**B09-2 / AC2** `test_squadadopt.TwoOpsOneItem`: fixture with one edit (`When unsure, size up.`), one deleted bullet (SIZE-16), one paragraph no rule covers → dry run "overlay with 2 operation(s)", "PO items (1 open of 1)"; `--yes` alone or `--resolve` alone exit 3 `NOT APPLIED` and the tree hash is unchanged; with both: exit 0, `SIZE-4` and `SIZE-16` ops (`upstream: proposed`), `squad-process lint` 0. An edit whose old text is not found once in a mapped rule is an item, never an operation. Answers: `drop`, `add:<roles>` (SQ-n, topic `squad`), `replace:<ID>:<file>`; bad answers exit 2, nothing written.

**B09-3 / AC3** `ArchiveAndSettings`: after a real run `process.md` is gone, `process.v6-archived.md` is byte-equal to the original, `plugin.pin` holds the pin, a log row is written; each `settings/<role>.json` → `<role>.v6-archived.json` (equal to the original JSON) and `<role>.local.json` holds only the squad's difference (its own allow entries, a changed scalar, `codePaths` extracted from the Read denies; `.worktrees` entry regenerated). Effective settings (squadsettings.effective) contain every old allow/deny entry (QA blackbox code-path denies are rewritten `Read(///..)` -> `Read(//..)`, same effect).

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

## QA whitebox

### QA whitebox 09: adopt existing squads; new squads start composed

Verdict: **PASS** at a5bf6fb (branch squad/plugin/role-cards-upgrade/plugin-dev-rcu-6, on 22's 4118516 + 07, 08, 24). Read-only on the Developer's worktree; all runs on copies in /tmp (removed by literal path). `git status` clean after every run.

#### Checked
1. **Tests.** Own harness: 28 (test_squadadopt) and the 102-test list OK; my wider list (adopt, upgrade, start, spawn/respawn, runtime, settings, compose, rules, processlint, instructions, size, process_history, model_effort) 483 OK. `squad-process lint` 0.
2. **Dry run on a copy of the live squad** (B09-1): exit 3, 0 overlay operations, 3 "already in the plugin" notes, 4 PO items (L210, L244, L246+, L276+) each with old/new text and candidate IDs, none guessed. Hash of every non-jsonl file in the copy identical before/after; the live folder was only ever read.
3. **Write gates:** no flag, `--yes` only, `--resolve` only (all four), unknown `--resolve L999` all leave the tree hash unchanged (exit 3; bad key rejected with the open keys listed).
4. **Real run on the copy** (all four `drop` + `--yes`): exit 0. `process.v6-archived.md` byte-equal to the live `process.md`; all nine `<role>.v6-archived.json` byte-equal to the live files; `process.local.md` = title only; `plugin.pin` written; one log row; `scopes/role-cards-upgrade` and `goals/composed-process` got a `plugin:` line (only that line added, rest unchanged). `squad-process lint --squad-dir` 0. A second run: "already adopted", exit 0, tree hash unchanged.
5. **After adopt:** `squad-spawn dev ... --scope role-cards-upgrade --dry-run` and `squad-spawn tech-lead ... --goal composed-process --dry-run` exit 0 with the pinned runtime and `--append-system-prompt-file`; `compose dev --home <scope>` exits 0.
6. **Order of writes** (`execute`, squadadopt.py:475-498): overlay, local settings, pin (only if absent), log row, scope/goal pins, then process.md and settings renames last; a cut-short run is finished by the next one (test).
7. **Permissions** (B09-8): effective settings (own merge via `squadsettings.effective`) contain every old allow/deny entry for all nine roles except the four QA blackbox code-path denies, which are normalised (see note); dry run lists the regained entries (team-lead regains `squad-spawn dev`, `squad-retire`, `herdr agent list|get|read`).
8. **Settings templates:** all nine have `rule` and `who` and none has `show`. The size test's four-template check moved to a nine-template test in test_instructions (covers the TL's amendment).
9. **`show` retired:** no caller left in agents, skills, bin, templates, hooks; the remaining hits are tests asserting absence and the `RETIRED` list in squadadopt.py:35. Legacy `apply --legacy` path kept (tests).
10. **v6 map data** (`MapData`): every target ID is a template rule or tombstone, map lines are within the archived v6.
11. **Scaffold:** tests build a squad with no `process.md`, nine local settings, `project.md`, and lint 0; refuses a legacy squad. squad-init SKILL.md steps 1, 3, 5 call it.

#### Non-blocking notes
- QA blackbox `Read(///home/.../bin/**)` (old, from squad-init's `Read(//<abs path>/**)`) becomes `Read(//home/.../bin/**)` in the effective file. That is the canonical form and codePaths are not lost, but evidence.md's "contain every old allow/deny entry" is not literally true for these four denies, and the dry run does not mention the rewrite. Add a line to the PO's check-in; QAB should confirm the deny still blocks a code read after adopt.
- Adopt pins a scope by inserting the `plugin:` line before the first blank line (not appended at the end); harmless.
- The cut-short-run branch and `--resolve` exit code for a bad key come from the Developer's tests (read, not re-run by hand).

## QA blackbox

### QA blackbox: ticket 09 (adopt + scaffold), sha a5bf6fb

Bed: a COPY of `.claude/squads/plugin` (13,509 files, 95 MB) plus fixtures in a scratch dir (deleted after); tools from rcu-6's worktree; stub `herdr`. Real live folder never touched (branch diff has 0 files under `.claude/squads`; repo `git status` clean).

| AC | What I did | What I saw | Result |
|---|---|---|---|
| B09-1 | `adopt --squad-dir <copy> --dry-run` | exit 3, nothing written (hash of all files equal before/after); overlay 0 operations; 4 PO items (L210, L244, L246+, L276+) with old/new text and candidate rules; 3 "already in the plugin" notes. I grepped every new text: all already in plugin rules (LC-3b, COST-3/5/8/9/11, SAFE-5), so `drop` loses nothing | PASS |
| B09-2 | Fixture: edit `When unsure, size up, and say so in the briefing.`, deleted SIZE-16 bullet, new paragraph "Squad ritual". Dry run; `--yes` alone; `--resolve` alone; both | 2 ops (replace SIZE-4, replace SIZE-16, `upstream: proposed`) + 1 PO item; `--yes` alone and `--resolve` alone exit 3, tree hash unchanged; both: exit 0, overlay holds both ops, composed Manager has the edit, composed Tech Lead lacks the deleted bullet; `squad-process upstream` lists both with why + body; `lint --squad-dir` exit 0. (A bold-prefixed bullet edit does not map and goes to the PO instead: safe) | PASS |
| B09-3 | Real run on the live copy with the 4 `drop` resolves + `--yes` | exit 0; `process.v6-archived.md` kept (25.1 KB), `process.local.md`, `plugin.pin` `0.4.1 a5bf6fb...`, `process-log.md` row added; each `settings/<role>.json` became `<role>.local.json` (dev: 2 allow; qa-blackbox: allow + codePaths) plus `<role>.v6-archived.json`. Effective qa-blackbox settings vs old: no allow lost, +rule/who, deny code paths kept (`///` typo now `//`), +`.worktrees` deny | PASS |
| B09-4 | `squad-process scaffold --squad-dir <empty> --code-path X`; lint; re-run; skill text | no `process.md`; `process.local.md`, `plugin.pin`, `project.md`, 9 `settings/*.local.json` (qa-blackbox with `codePaths`), `scopes/`, `goals/`; `lint --squad-dir` exit 0; re-run "nothing to create", codePaths unchanged. `/squad:squad-init` text calls scaffold | PASS |
| B09-5 | `squad-process show dev`; `apply` w/o and with `--legacy`; spawn in a rolled-back (legacy) copy | `show` is an unknown command; `apply` exits 2 naming `--legacy`; `apply --legacy` works; legacy spawn attaches rules (24); `grep 'squad-process show'` in agents/skills/bin/templates/hooks: only the RETIRED constant | PASS |
| B09-6 | branch diff names; repo status | no file under `.claude/squads/`; live folder untouched | PASS |
| B09-7 | After the real run: `plugin:` lines; stub `squad-spawn qa-blackbox` in the open scope; `squad-spawn manager --goal`; `squad-respawn --dry-run`; 2nd `adopt` | `scope.md` and `goal.md` both got `plugin: 0.4.1 a5bf6fb...` (dry run named them); spawn exit 0 builds `_runtime/0.4.1-a5bf6fbb49f3`, rules header shows the pin; goal manager spawn exit 0; respawn would call spawn with notes prompt; 2nd adopt "already adopted ... nothing to do", tree hash unchanged | PASS |
| B09-8 | dry-run "regained" list; template settings of all nine roles | lists rule/who for all 9 roles, plus team-lead `squad-spawn dev`, `squad-retire`, `herdr agent list/get/read`; new `model`/`effortLevel` keys listed separately ("keys the template sets that the old file lacked") | PASS |
| B09-9 | Rollback by file copy on a copy of the adopted squad: remove local files and pin, restore archives | `process.md` and 4 checked `settings/*.json` byte-identical to the original; legacy spawn works (one "legacy squad" line). Left over, harmless: `plugin:` lines in scope.md/goal.md | PASS |
| Nine-role allows (moved from 22) | grep `squad-process rule/who` in all nine templates | present in all nine | PASS |

Notes (not failures):
1. Adopt adds `model: sonnet` / `effortLevel` to roles whose old file set none (listed in the dry run); the PO sees it before confirming.
2. Deploy-step resolve keys (L210, L244, L246+, L276+) must be re-read on the live files at that time (dev says so).

Verdict: PASS a5bf6fb.
