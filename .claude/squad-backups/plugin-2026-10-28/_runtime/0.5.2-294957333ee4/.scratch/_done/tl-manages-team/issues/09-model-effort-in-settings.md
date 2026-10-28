# T9 · model and effort live in the settings JSON, not in agents/*.md
Status: ready-for-agent
Type: task
Blocked by: T3 and T8 passed (both touch `agents/*.md`). Branch from the later of the two passed shas, merging the other (T3 `b9fe3bb`; T8 per the Manager's briefing). Before T7.
Repo: /home/chieule/workspace/squad
Spec: PO note 2026-10-17 in `$SCOPE_DIR/scope.md` → Notes from the PO · Design: ../design.md decision 15 · Technical AC: AC-10 below (QA-W to confirm)

## Files this task touches (and no others)
`bin/squad-spawn`, `bin/squad-respawn` (header comment only), `bin/squad-start` (help line 15 only), `templates/squad/settings/*.json` (9), the 9 `agents/*.md` (frontmatter lines only), `tests/test_squad_spawn.py`, `tests/test_squad_respawn.py`, `tests/test_model_effort_settings.py` (new), `README.md` (squad-spawn row, only if it names the frontmatter).

## Do
1. **Settings files.** Each `templates/squad/settings/<role>.json` gets top-level `"model"` and `"effortLevel"` with today's frontmatter values (ba, designer, qa-blackbox, qa-whitebox, tech-lead: sonnet/high; dev, team-lead, token-coach: sonnet/medium; manager: opus/medium). Keep every `permissions` entry exactly as is.
2. **Remove `model:` and `effort:`** from the frontmatter of all 9 `agents/*.md`. Touch no other line.
3. **`bin/squad-spawn`:** replace the `fm()` frontmatter reader with a reader of the `$settings` file chosen at line ~121 (squad's own file first, template as fallback). Precedence, **per key**: `--model/--effort` flag, then the squad's `settings/<role>.json`, then the template `<role>.json`, then nothing (Claude's default). A squad file without a key falls back to the template's value silently; there is no whole-file choice for these two keys (permissions still use the squad file when it exists, as today). Read with `jq -r '.model // empty'` and `'.effortLevel // empty'`; validate with the same regex as the flags before use (a bad value refuses with exit 2, same message style). Still pass the result as `--model`/`--effort` to `claude`: do not rely on Claude reading the keys (see design decision 15). Overrides recorded in `roles/<name>.overrides` stay flag-only: only a given flag is recorded, never the settings value. Update the `--help` text (lines 30-31) and the comment at line 143.
4. **Warning:** only when neither the squad file nor the template has the key, print `warning: no model|effortLevel for <role> in <squad file> or the template; it runs on Claude Code's default` to stderr and continue (exit 0).
5. **`bin/squad-respawn`** (header line 3) and **`bin/squad-start`** (help line 15, "default: those in agents/manager.md"): no logic change; reword the stale mention to "the model and effort in settings/<role>.json". `bin/squad-spawn` help lines 30-31 and the comment at ~143 likewise.
6. **Tests.** `test_squad_spawn.py`: `TABLE` is built from `templates/squad/settings/<role>.json`, not literals; add: squad settings override template; flag beats both; squad file lacking a key falls back to the template silently; a key in neither warns and passes no flag; invalid value refused; override file records only flags. `test_squad_respawn.py` line ~73: expect the values from the settings file. `tests/test_model_effort_settings.py` (new): every `agents/*.md` frontmatter has no `model:` or `effort:` line; every template settings file has both keys with allowed values; `permissions` unchanged (compare with `git show c1be501:<file>` parsed JSON).
7. **Run only the test files you touched**; never the full suite.

## Technical AC (AC-10)
- AC-10.1 `grep -n '^model:\|^effort:' agents/*.md` is empty; frontmatter otherwise byte-identical (`git diff` shows only those two lines per file).
- AC-10.2 A dry-run spawn of every role gives the same `--model/--effort` as before the change (table in `dev-evidence.md`, taken from c1be501 vs the branch).
- AC-10.3 Precedence and warning tests above pass; `bash -n bin/squad-spawn`; no `eval`; values validated before use.
- AC-10.4 **Real run, not memory** (read-only, one call each, saved in `dev-evidence.md`): `claude -p --settings <file with model haiku> --agent squad:dev "reply with your model id"` is made with the frontmatter keys gone, and the reply shows which wins. Tech Lead's own check on 2026-10-17: with the key present in the frontmatter (sonnet) and haiku in `--settings`, the agent ran sonnet, i.e. frontmatter beats `--settings`; a plain `-p --settings` run honoured the `model` key. This is why squad-spawn keeps passing flags.
- AC-10.6 (QA-W) The fallback is per key and the code, test, help text and deploy note agree. AC-10.7 (QA-W) No file says the defaults live in `agents/*.md`: `grep -rn 'frontmatter\|agents/manager.md' bin` is clean of that meaning.
- AC-10.5 The permissions diff of every settings file is empty (only `model` and `effortLevel` added).

## Business AC
PO note 2026-10-17: model and effort are set in the role's settings JSON so they are easy to override; the role files no longer carry them.

## Deploy note
Per-key fallback means the live `.claude/squads/plugin/settings/*.json` keep working with no edit: they fall back to the template values (same as today's frontmatter). Adding `model`/`effortLevel` to a live file is how the PO overrides one role in this squad. No ordering constraint with spawns. Rollback: `git revert`.
