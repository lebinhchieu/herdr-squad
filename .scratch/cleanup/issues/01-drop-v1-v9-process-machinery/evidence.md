# Evidence 01: drop v1-v9 process.md machinery

## Behaviour

Base 5274494 (02), merged 03 (09ab86f..6ab2bf7, no conflict; GOAL-6b integration step). Scratch dirs under `.worktrees/scratch`.

**Removed** (`git rm`): `skills/squad-process-update/history/` (whole), `templates/squad/process.md`, `bin/squadprocess.py`, `tests/test_process_history.py`, `test_process_conversion.py`, `test_squadprocess.py`, `test_squadprocess_apply.py`, `tests/fixtures/process/` (only `test_squadprocess` read it), `.scratch/_done/composed-process/issues/03-convert-process-to-rules/mapping.md`.

**squadprocess remainder:** `_atomic_write`, `_insert_log`, `LOG_HEADER` moved into `bin/squadupgrade.py` (used by `upgrade --apply` log/overlay/pin writes); `ProcessError` had no user left. `squad-process`, `squad-start`, `squad-spawn` no longer import it.

**H6 reader check on `templates/squad/process.md`** (before delete): readers were `squadprocess.plugin_version` (deleted), the two deleted tests, `test_process_writing` (TEMPLATE lint, dropped), `test_instructions` (list + 2 tests), `test_promotion_0_6_0` (`process-version: 6` test, dropped). No agent/skill/hook/composed path reads it.
Coverage move (`test_instructions`, tokens checked against the rule folder `templates/squad/process/*.md` as `RULES`):
- `process_documents_every_variable_and_every_squad_command`: all 13 tokens (SQUAD_DIR … scopes/_done) found in rules and in composed manager text; unchanged list, now asserted on `RULES`.
- `designer_is_wired...`: `design: yes` exists nowhere now (the rules say `when: design = yes`), so the token became `design = yes`; `ui-design/` and `` `ux` `` found in rules. Old assertion → new: `design: yes` → `design = yes`. Nothing dropped.
- `test_process_writing`: only the TEMPLATE lint test and the version-line test dropped; `processlint.lint` string tests kept.

**H3 removed subcommands**, all exit 2, usage line, no `Traceback` (`bin/squad-process <cmd>`): `plan`, `apply --legacy --file x --yes`, `version`, `check`, `compose --out F` (`required: role, --home`), `bogus`. `lint` 0, `rule CORE-1` prints the rule, `mode --squad-dir /nonexistent` prints `none` 0. Covered by `test_squadscaffold.Retirement`.
`squad-process compose <role> --home D`, `team`, `who`, `upgrade`, `upstream`, `runtime`, `prune`, `mode`, `scaffold`: existing tests unchanged and green.

**H2 `_changelog_why`:** called on this tree and on a `git archive 5274494` copy for versions 7, 8, 9, 6: 317 / 31 / 267 / 0 entries, identical JSON sha1 `8c560a01…` both sides. (`upgrade --check` with an old pin needs the old runtime; 0.5.2 rule files use `size`, which the current lint refuses, so the live run is covered by the unit call above and `test_squadupgrade`.)

**H4 squad-start / spawn:** JSON keys exactly `kind,name,dir,manager,tab` (test_squad_start `LegacyStartTest`: 4 process.md texts, dry-run, `--resume`; none print "process update"/"process version"). `skills/squad-start/SKILL.md` loses the `process_update` sentence (test asserts absent). Manager first prompt on a legacy squad: only the "rules are attached" sentence (test_squad_spawn `SpawnLegacyPromptTest`). Spawn also lost the `squad-process check` call.

**H7 changelog:** `git diff` of `skills/squad-process-update/changelog.md`: 158 deletions, 0 additions; `## v6`…`## v1` blocks and the three `- snapshot: history/…` lines (v9, v8, v7) gone; v9/v8/v7 text otherwise untouched. `test_sizes`, `test_team_duties` green.

**H8 SKILL.md:** front matter `description` now names the composed upgrade only; H1 "Upgrade a squad's rules"; sections "Three paths", "Steps", "Rules" removed; only the composed steps remain. `disable-model-invocation: true` kept. Mentions of `process-version`, `plan`, `apply`, `--legacy`, `adopt`, `squad-migrate`: 0.

**H3b:** `bin/squad-process` docstring/parser/dispatch rewritten: "Legacy squads" block, the apply error text and the `--legacy` flag are gone; `version/check/plan/apply` and the no-role `compose --out` merge are gone. Every non-delegated form routes to `squadrules_cli`.

**H9:** docstring lists lint, compose <role>, team, upgrade, upstream, mode, runtime, prune, scaffold: every one is dispatched (mode/runtime/prune → squadruntime, scaffold, upgrade/upstream, rest → squadrules_cli). `squad-process --help` (squadrules_cli) lists only its own five, as before for the delegated ones.

**H5:** `squad-process lint` on the plugin root exit 0; `bin/processlint.py` untouched.

**H1 grep** `git grep -n "squadprocess\|process-v[0-9]\|history/\|--legacy\|process_update\|process-version\|templates/squad/process.md"` outside `docs/adr/`, `.scratch/`, changelog: only new tests that assert the removal or use a legacy squad's text (`test_squad_start`, `test_squad_spawn`: `process-version: N` fixture text for a process.md-only squad; `test_squadscaffold`: `--legacy` passed to prove exit 2; `test_squad_start:355,514` name `process_update` to assert it is gone). No code or doc hit. Changelog: no `snapshot:` lines or `history/` text.

**Docs:** README squad-process row loses "`apply --legacy` is the old v6 merge"; CONTEXT "Process changelog" loses "Frozen copies … `history/`". No new prose.

**Also fixed (not in the ticket, found by the touched-path `grep -rl` runs):**
- `test_squadsettings` expected "09" in the spawn warning that 02 reworded ("not an overlay"): assertion updated.
- `test_templates` required `templates/squad/process.md`: now `project.md`, `process-log.md`.
- `test_squadruntime`: two tests drove `squad-process check/version` (gone) in a composed squad: removed (covered by the exit-2 tests).
- `test_squadrules.test_routing`: `compose --out F` / `version` now route to `squadrules_cli`; the `_mutating` stub dropped.
- `squadupgrade` "not composed" message: no longer points to `squad-process plan` / `apply`; now "new squads: squad-process scaffold (or /squad:squad-init)".
- `test_win_utf8_process`: apply/check/version cases dropped; processlint and squadlabel cases kept; added a composed `squad-process rule`/`who` cp1252 case.

**Tests run** (touched + `grep -rl` hits: every test file naming squad-process, squad-start, squad-spawn, squadupgrade, process-update, changelog, templates/squad, CONTEXT.md, README.md, process.md, history): 934 tests, OK (2 skipped). Full suite `--tz`: Tech Lead on the final sha.

**Feature loss for the PO:** `squad-process version|check|plan|apply|compose --out`, the squad-start "process behind" nag and the Manager's first-prompt sentence are gone. A process.md-only squad can no longer be updated by the plugin.
