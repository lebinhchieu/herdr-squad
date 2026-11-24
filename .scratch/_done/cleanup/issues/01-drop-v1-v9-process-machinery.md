# Task 01: Drop v1-v9 process.md version machinery

Status: ready
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Team: tech-lead, qa-white, qa-black. Suite: `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` (CLAUDE.md Running tests); full suite by Tech Lead on final sha. Branch from repo HEAD (main) unless noted. Hand in to both QAs. A risk flag or user-visible change found: `BLOCKED <task>`.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`.

Order changed (FINAL): runs after 02 and 03; branch from 02's passed sha (`--base`), then merge 03's passed sha.

First commit (FILE-11): copy `$SCOPE_DIR/tasks/01.md`, `02.md`, `04.md` as tickets to `.scratch/cleanup/issues/` (`01-drop-v1-v9-process-machinery.md`, `02-drop-old-layout-migration.md` (not yet on 02's branch), `04-promotion.md`). Do NOT create the 03 stub (on 03's branch: add/add conflict).
Base: 02's passed sha 5274494 (`--base`). Then merge 03's range 09ab86f..6ab2bf7 (branch squad/plugin/cleanup/plugin-dev-cleanup-2); this is an integration step, cite `squad-process rule GOAL-6b`. Targeted tests, HANDIN; Tech Lead runs the full suite --tz after.
Extra for 01 (Tech Lead): `squadupgrade.py:28`, `squad-process:42`, `squad-start:34/172` import `squadprocess`: move `_atomic_write`/`_insert_log` to `squadupgrade` before deleting it.
Scratch dirs: `.worktrees/scratch` per the squad's SAFE-11 (not /tmp).

## Touches (Tech Lead confirms before AC, LC-9b)
`skills/squad-process-update/history/`, `skills/squad-process-update/changelog.md`, `bin/squadprocess.py` legacy paths (`plan/compose/apply --legacy`), `skills/squad-process-update/SKILL.md`, tests `test_process_history`, `test_process_conversion`, `test_squadprocess*`; `templates/squad/process.md` (24K) only if nothing composed reads it.

## Cautions
- Keep what `squadupgrade._changelog_why` reads from `skills/squad-process-update/changelog.md`.
- Check every reader of `templates/squad/process.md` before deleting; `bin/squadrules.py:530` mentions the changelog.
- List files first; delete only what no code, test or doc references.
- Removes CLI paths = contract change (risk flag; Tech Lead owns).

## AC
Tech Lead writes technical AC in `## Design notes` below. Business AC: PO brief in scope.md (dead process-version history gone, suite green).

## Design notes
(Tech Lead, 2026-10-28)

**Runs AFTER 02** (see task 02 notes: `adopt` reads `history/process-v6*` and `squad_version`). Branch from 02's passed sha (`--base`); 03 is independent but 01 deletes the one `.scratch/_done/composed-process/issues/03-convert-process-to-rules/mapping.md` that 03 leaves for it.

### Touches (confirmed; LC-9) and readers found
Delete:
- `skills/squad-process-update/history/` whole (v1-v6 `.md`, `process-v6.map.md`, `process-v7/ v8/ v9/`). Readers: `squadadopt` (gone in 02), `squadprocess._snapshot`/`plan` (deleted here), `test_squadprocess`, `test_process_history`, `test_process_conversion`, `test_promotion_0_6_0::snapshot_v9`.
- `templates/squad/process.md` (24K, "process-version: 6", retired template). Readers: `squadprocess.plugin_version` (deleted here), `test_process_conversion`, `test_process_history`, `test_process_writing` (lint of TEMPLATE), `test_instructions` (INSTRUCTIONS list `:10`, `:65`, `:91`), `test_promotion_0_6_0:89`. No agent, skill, hook or composed path reads it (composed rules are `templates/squad/process/`; verified: `squadrules.py:413`). Delete it.
- `.scratch/_done/composed-process/issues/03-convert-process-to-rules/mapping.md` (03 leaves it for this task).
- Tests: `test_process_history.py`, `test_process_conversion.py`, `test_squadprocess.py`, `test_squadprocess_apply.py`; `tests/fixtures/process/` (5 files, only `test_squadprocess` reads them: verify).
Edit:
- `bin/squadprocess.py`: delete everything (`parse_version`, `squad_version`, `plugin_version`, `check`, `sections`, `read_changelog`, `plan`, `compose`, `apply`, `format_plan`, snapshot/diff/log/backup code, the `processlint` import at :467). KEEP only what `squadupgrade.py:465,524` calls: `_atomic_write` and `_insert_log` (+ `LOG_HEADER` if `_insert_log` needs it). Move them into `bin/squadupgrade.py` and delete `squadprocess.py` (preferred; dead module otherwise). `ProcessError` has no other user after 02: confirm by grep.
- `bin/squad-process`: remove `version`, `check`, `plan`, `compose --out FILE` (no-role v6 merge), `apply [--legacy]` from usage/docstring/parser/dispatch; route every `compose` to `squadrules_cli`; drop the legacy-squad docstring block and the `import squadprocess`/`squadio` use that goes with it (keep `squadio.utf8_stdio`).
- `bin/squad-start`: delete `process_update()` and its call; JSON loses the `process_update` key (keys: kind, name, dir, manager, tab) at `:272` and `:414`; `skills/squad-start/SKILL.md:27` loses the `process_update` sentence.
- `bin/squad-spawn` ~`:213-222`: delete the `squad-process check --quiet` notice and the process-update sentence in the Manager's first prompt.
- `skills/squad-process-update/SKILL.md`: keep only "Composed squads (rule by rule)"; rewrite front matter `description` and H1 (no "process.md up to version", no "migrate the process"); remove "Three paths", "Steps" (v6 merge). `disable-model-invocation: true` stays.
- `skills/squad-process-update/changelog.md`: delete the `## v6` ... `## v1` blocks and the `- snapshot: history/...` lines of v7-v9 (dangling). KEEP v9, v8, v7 blocks exactly (`_changelog_why` reads `^- <ID>: why` for `cur >= 7`, and tests read the v7+ text). `bin/squadrules.py:530` skips `changelog.md` and stays unchanged.
- `README.md:49` and `CONTEXT.md:133,137` and the "Frozen copies ... `history/`" text: delete/reword what names `apply --legacy`, `history/`, version/check (no new prose; 04 adds ADR/glossary).
- Tests (edit, never skip): `test_squad_start.py` (process_update tests ~355-420, key set `:56`, SKILL assert `:550`), `test_squad_spawn.py` (`SpawnProcessUpdateTest` ~650-704 and `toy_plugin` process-version helper), `test_win_utf8_process.py` (drop the `ap.Base`/apply cases; KEEP the processlint, squadlabel and composed `squad-process` cp1252 cases), `test_process_writing.py` (drop only the TEMPLATE lint test; KEEP tests on `processlint.lint` strings), `test_instructions.py` (remove the template from INSTRUCTIONS; the two tests that read it must keep their value: re-point `process_documents_every_variable...` and `designer_is_wired...` tokens to the composed rules (`composed(...)`) or to `templates/squad/process/*.md` if the tokens exist there; a token that exists nowhere is reported to Tech Lead as `ASK`, not dropped), `test_promotion_0_6_0.py` (drop `process-version: 6`, `snapshot_v9`, the `- snapshot:` assert; keep version equality test), `test_old_language_inventory.py` allow-list counts if they move, `test_windows_safe.py` if it lists `squadprocess`.
Do NOT touch: `bin/processlint.py` (used by `squadrules`), `templates/squad/process/` (rule folder), `squadruntime` legacy-mode detection (`process.md` only squads keep spawning), `bin/squad-close` legacy wording, plugin version (stays 0.6.0; the PO releases).

### Decisions (compatibility, LC-12)
1. Removed subcommands (`version`, `check`, `plan`, `apply`, `compose --out` without a role) fail with argparse/`squadrules_cli` usage error: exit 2, one line, no traceback. `--legacy` likewise (unknown option). No stub that prints "removed".
2. Consumers of removed output: `squad-start` JSON `process_update` (only reader: `skills/squad-start/SKILL.md:27`, updated here; grep shows no hook/mod reads it) and the Manager's first-prompt sentence (spawn) go. A legacy (process.md-only) squad therefore gets no "behind" nag; accepted: nothing can update it any more (02 + this).
3. Nothing in a composed squad changes: `version`/`check` already printed "composed squad: nothing to check".
4. PO-level? No: Q1 covers it; the key removal is an internal contract between two plugin files.

### Technical AC
Common C1-C4 as in task 02 Design notes.
- H1 `skills/squad-process-update/history/`, `templates/squad/process.md`, `bin/squadprocess.py` (or its dead remainder) gone; `git grep -n "squadprocess\|process-v[0-9]\|history/\|--legacy\|process_update\|process-version\|templates/squad/process.md"` outside `docs/adr/`, `.scratch/`, v7+ changelog text and ticket text returns nothing (changelog: only prose mentions allowed, no `snapshot:` lines).
- H2 `_changelog_why` works: unit or live call `squad-process upgrade --check` on a scratch composed squad prints the "why" lines for a v7+ ID (same output as main on the same scratch squad; QA diffs).
- H3 `squad-process plan`, `apply --legacy`, `version`, `check`, `compose --out F` each exit 2 with a usage error, no `Traceback`; `compose <role> --home D`, `rule`, `who`, `lint`, `team`, `upgrade`, `upstream`, `runtime`, `prune`, `mode`, `scaffold` behave exactly as on 02's sha (existing tests green, unchanged).
- H4 `squad-start` on a composed scratch squad (existing test harness): JSON keys exactly `kind,name,dir,manager,tab`; `squad-spawn manager ...` first prompt has no process-update sentence; neither prints a process-version message for a legacy squad.
- H5 `squad-process lint` on the plugin root passes (no rule or card broken by README/CONTEXT edits); `python3 bin/processlint.py` unchanged.
- H6 Reader check on `templates/squad/process.md` recorded in evidence before delete (the grep above); coverage move for `test_instructions` tokens listed (old assertion → new location).
- H7 Changelog: v9/v8/v7 blocks byte-identical except removed `snapshot:` lines (`git diff` shows only deletions there); `test_sizes`, `test_team_duties` changelog tests green.
- H8 SKILL.md has no `process-version`, `plan`, `apply`, `--legacy`, `adopt`, `squad-migrate` text; front matter `description` names the composed upgrade only.
- H3b `bin/squad-process` lines ~30 (docstring "Legacy squads"), ~76 (apply error text), ~132 (`--legacy` flag) removed.
- H9 `squad-process --help` (usage block in docstring) matches the real subcommands: every name in the docstring is a real parser entry and vice versa (QA blackbox compares each listed command's exit code).
- H10 Full suite `--tz` on the final sha (Tech Lead, receipt in `$SCOPE_DIR/evidence/`). Deploy: ship with 02 in one merge (the two together remove the legacy path); no data written, rollback = git revert.
