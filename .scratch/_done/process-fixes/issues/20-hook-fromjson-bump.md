# Task 20: hook dedupe survives a corrupt line; version 0.8.1

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Also run tests/test_windows_safe.py, tests/test_utf8_helpers.py, tests/test_instructions.py (SQ-10) and quote the result in `## Behaviour`. Source: `.claude/squads/plugin/goals/process-fixes/answers/respawn-rules-review.md`. The version bump rides this last ticket (SQ-5): its AC has the grep for the old version.

Status: handed in
Source: finding 9a (Chieu E17 a).
Files: bin/squad-usage-hook, .claude-plugin/plugin.json, tests/ (hook test; any test that hard-codes 0.8.0: grep).
Ticket: commit this file's content as `.scratch/process-fixes/issues/20-hook-fromjson-bump.md` in your first commit.
Base: the task 19 sha (same branch). No merge into main.

## AC
- AC1 Dedupe: the `jq` check of `usage-events.jsonl` in `bin/squad-usage-hook` (line ~24) reads the log with `-R` and `fromjson?`, so a corrupt line is skipped and a real earlier event of the same session and rule still stops the hook from firing again.
- AC2 Test: a log with one corrupt line plus one valid event for the session: the hook does not fire again.
- AC3 Version: `.claude-plugin/plugin.json` says 0.8.1. `grep -rn '0\.8\.0' .claude-plugin/ bin/ templates/ README.md` shows no live reference to the old version (a changelog entry or a test fixture for an old version is fine; list what is left in `## Behaviour`). A CHANGELOG line for 0.8.1 if the project keeps one.

## Design notes
Touched files: bin/squad-usage-hook, .claude-plugin/plugin.json, skills/squad-process-update/changelog.md (v13 entry, TA4), tests/test_squad_usage_hook.py.
- Dedupe: `jq -R -e ... 'fromjson? | objects | select(...)'`. `-R` reads each line as text, `fromjson?` drops a corrupt or blank line, `objects` drops `5`, `[]`, `null`, `"x"`. Checked by hand: the old filter exits 5 on such a log, the new one exits 0.
- One test with the mixed log (corrupt, blank, valid event, four non-objects) plus a control with the valid event for another session; no fourth test.
- Version 0.8.1 in plugin.json (marketplace.json has no version).
- I agree with TA1-TA5 as written.

## Technical AC (QA whitebox, coarse on purpose; Developer may propose changes in the design notes, 2 exchanges max)
- TA1 Dedupe: the `jq` call reads `$log` with `-R` and `fromjson?` and keeps `-e`. It must skip, not die on: a torn or corrupt line, a blank line, and a valid JSON line that is not an object (`5`, `[]`, `null`, `"x"`). Use `objects` (or equivalent) after `fromjson?`, because `.session` on a number raises an error and the hook would fire again. jq 1.7 here; the `-e` exit stays 0 only on a match.
- TA2 Test (extend tests/test_squad_usage_hook.py): log = corrupt line + valid event for the session and rule + a non-object line, in that mixed order: hook exits 0, no new line appended. Control: the same log with the valid event for another session: the hook fires (exit 2, one new line). Do not add a fourth test.
- TA3 Version: `.claude-plugin/plugin.json` says 0.8.1; `grep -rn '0\.8\.0' .claude-plugin bin templates README.md` is empty; the whole-repo `grep -rn '0\.8\.0' . --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=.claude --exclude-dir=.scratch` leaves only `skills/squad-process-update/changelog.md` (v12 history) and the `--new-pin` fixture in tests/test_squadscaffold.py:78 (not a plugin version); list them in `## Behaviour`.
- TA4 Changelog: `skills/squad-process-update/changelog.md` gets a v13 entry for this scope on top (Plugin 0.8.1): `removed:` COST-9, COST-1; `changed:` COST-3, COST-8b, the Developer text of the hook; each with a `why:` as the v12 entry does. Same shape as v12; the lint/tests that read it pass.
- TA5 Run: the hook test file, tests/test_squadscaffold.py, tests/test_processlint.py, the three SQ-10 files, and any test the `0.8.0` grep or the changelog edit hits. Quote results in `## Behaviour`.

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 dedupe reads the log with `-R` and `fromjson?` (and `objects`, TA1) | `bin/squad-usage-hook` line 24; hand check below | `cd tests && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_usage_hook` |
| AC2 corrupt line + valid event: the hook does not fire again (control: other session fires) | `test_the_dedupe_skips_corrupt_blank_and_non_object_lines` | same |
| AC3 version 0.8.1, no live 0.8.0 | `.claude-plugin/plugin.json`; the greps in Behaviour; v13 changelog entry (TA4) | `grep -rn '0\.8\.0' .claude-plugin bin templates README.md` |

