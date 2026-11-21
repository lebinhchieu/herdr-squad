# 05 `upgrade` and `homes` find the newest plugin from a pinned session: evidence
sha: bdbbe04
## Review
AC trace (from `tests/`: `python3 -m unittest test_squadruntime.NewestPluginTest test_squadupgrade.Delegation`):
- AC1 | `NewestPluginTest.test_the_checkout_wins_when_newer_and_the_cache_when_newer_than_it`, `test_a_version_tie_goes_to_the_checkout`, `test_entries_that_are_no_squad_plugin_are_skipped_without_error` (github entry without plugin.json, not-`squad` name, missing folder, malformed JSON) | unittest
- AC2 | `NewestPluginTest.test_never_moves_an_unpinnable_root_backwards_and_starts_no_child` (0.10.3 vs 0.10.2: exit 1 naming both, `_run_child` never called) | unittest
- AC3 | `Delegation.test_upgrade_check_and_apply_run_the_newer_plugin_with_its_exit_code` (exit 0 and 3, stderr line, stdout equals the newer plugin run alone, apply writes `0.5.0 <checkout HEAD>`) | unittest
- AC4 | `Delegation.test_these_run_in_place_and_print_no_using_plugin_line` (`--plugin-root`, `mode`, a pinnable root with nothing newer), `test_a_delegated_child_that_cannot_pin_refuses_and_starts_no_grandchild` | unittest
- AC5 | `Delegation.test_refusal_with_nothing_found_changes_nothing_in_the_squad` (names version, both files with counts, both ways out; file listing identical before/after) + `NewestPluginTest.test_refusal_names_what_was_searched_and_the_two_ways_out` | unittest
- AC6 | `Delegation.test_homes_delegates_the_same_way` | unittest
- AC7 | `## Behaviour`, real run below
- AC8 | `## Behaviour`, test runs below; `grep -n 'os.exec\|shell=True' bin/squadruntime.py bin/squad-process` prints nothing

`squad-evidence checks` / `check --base 420e87c`: exit codes quoted in the HANDIN.

## Behaviour
Tests (from `tests/`): `python3 -m unittest test_squadupgrade test_squadruntime test_squadscaffold test_squad_respawn test_windows_safe test_utf8_helpers test_instructions`: 201 tests, OK, none skipped (SQ-10 files included). `grep -rn 'cannot pin the running' tests bin skills docs README.md`: hits only `bin/squadruntime.py` (the unchanged `running_pin` message, still used by scaffold and squad-start, and the new refusal text) and `skills/squad-init/SKILL.md` (about scaffold's `running_pin`, unchanged); no test asserts the old words. `docs/adr/0011` does not contain the text.

Design notes: `running_pin` is unchanged. `newest_plugin` and `delegate` are new in `bin/squadruntime.py`; `bin/squad-process` calls `delegate` for `upgrade` and `homes` only. `-h/--help` and an explicit `--plugin-root` never delegate. A child started with `SQUAD_PROCESS_DELEGATED` set that cannot pin itself exits 1 with the refusal. The refusal lists a fixture/listing file that is missing as `(0 entries)`.

Real run (scratch squad from `squad-process scaffold`, runtime = `git archive` of 824ba6422c46 at `_runtime/0.10.1-824ba6422c46`, `SQUAD_KNOWN_MARKETPLACES` -> a file in the real shape whose `herdr-squad` directory entry is a clone bumped to 0.10.9, plus a `github` entry without plugin.json; `SQUAD_INSTALLED_PLUGINS` -> empty):
```
$ _runtime/0.10.1-824ba6422c46/bin/squad-process upgrade --check --squad-dir <sq>
stderr: squad-process: this session runs plugin 0.10.1; using plugin 0.10.9 from <scratch>/newer (known marketplace herdr-squad)
stdout: upgrade: plugin 0.10.1 824ba642... -> 0.10.9 59223e5b...
        plugin changes: added 0, changed 0, removed 0, retargeted 0
        overlay: 0 operations: 0 unaffected, 0 re-targeted, 0 dropped, 0 need a decision
        nothing needs a decision.
exit 0
```
Same run with the known-marketplaces file removed from the fixture (exit 1):
```
cannot pin the running plugin: it is squad 0.10.1 at <sq>/_runtime/0.10.1-824ba6422c46; no newer squad plugin was found
searched: <scratch>/known.json (0 entries); <scratch>/inst.json (0 entries)
fix: update the plugin checkout or install to a version at least 0.10.1, then run this again
or pass --plugin-root <new plugin folder> and --new-pin "<version> <sha>" by hand
```
Not verified: a real mid-session pinned Manager (Chieu's check at merge). Known limit: the resolver and skill text of a pinned session are the pinned version's; a change to either in a later plugin reaches a session only after it has moved once. Sessions pinned at 0.10.0/0.10.1 move to 0.10.2 by hand (no bootstrap).

## QA whitebox

### QA whitebox 05 (sha bdbbe04, code 824ba64): PASS

Checked: diff 420e87c..824ba64 (bin/squadruntime.py, bin/squad-process, README.md, two test files) against AC1-AC8.
- Targeted run from tests/: test_squadupgrade test_squadruntime test_squadscaffold test_squad_respawn test_windows_safe test_utf8_helpers test_instructions: 201 tests OK, no skip.
- `grep -n 'os.exec\|shell=True' bin/squadruntime.py bin/squad-process`: no hit (AC8). subprocess.run list form, os.path, utf-8-sig reads.
- Live read-only run (REV-5b): `git archive 824ba64` runtime in a mktemp dir, real ~/.claude*/plugins/known_marketplaces.json: `newest_plugin` found herdr-squad (/home/chieule/workspace/squad, 0.10.1); `upgrade --check` printed the using-plugin line, then the child's output, exit 0; `mode` ran in place with no line. Scratch dir removed.
- Each AC has a test; failure cases (never backwards, no candidate, delegated child, malformed JSON) covered.

Follow-ups (not FAIL):
- `SQUAD_PROCESS_DELEGATED` stays in the child's env, so any process the child starts (the respawn in `homes --apply --yes`) inherits it. A new agent session would only inherit it if herdr passes the caller's env on; not checked. Chieu's live check at merge can look at `env | grep DELEGATED` in a respawned tab.
- AC4 names compose/runtime/upstream; only `mode` is tested. They share the same dispatch branch, so low risk.

## QA blackbox

### 05 QA blackbox on bdbbe04 (CLI output only, no screenshots)
Setup: `squad-process scaffold` squad, runtime = `git archive bdbbe04` at `_runtime/0.10.1-bdbbe04ca437` (no .git), `SQUAD_KNOWN_MARKETPLACES` -> real shape (a `github` entry with no plugin.json + `herdr-squad` directory entry = clone bumped to 0.10.9), `SQUAD_INSTALLED_PLUGINS` -> `{"version":2,"plugins":{}}`. Env SQUAD_*/SCOPE_DIR unset for the runs. Not run: a real mid-session pinned Manager (Chieu's merge check).

| AC | How | Saw | Result |
|---|---|---|---|
| AC3 | `upgrade --check` from the runtime | stderr `this session runs plugin 0.10.1; using plugin 0.10.9 from <newer> (known marketplace herdr-squad)`, stdout `0.10.1 bdbbe04.. -> 0.10.9 e0c6eb2..`, exit 0, squad files unchanged | pass |
| AC3 | `upgrade --apply --yes` | `plugin.pin` = `0.10.9 e0c6eb21...` (the checkout HEAD, not the runtime's) | pass |
| AC3 exit 3 | `homes --check` after the apply | s1 `moves`, exit 3 | pass |
| AC6 | `homes --check --home scopes/s1` | `using plugin` line, then homes table (at-target before apply, moves after) | pass |
| AC1 | installed cache 0.10.12 vs checkout 0.10.9 (inst has also a non-squad entry) | uses `0.10.12 ... (installed cache)` | pass |
| AC1 | github entry without plugin.json, malformed JSON file | skipped, no crash (malformed -> refusal with `(0 entries)`) | pass |
| AC1 | version tie (checkout 0.10.1 vs runtime 0.10.1) | delegates to the checkout | pass |
| AC2 | runtime 0.10.20 (unpinnable), best found 0.10.12 | exit 1 `newest plugin found is 0.10.12 ..., older than the running one`, names both, no child output | pass |
| AC5 | known file missing / `{}` / malformed | exit 1, names running version+path, both files with `(0 entries)`, both ways out; squad md5 listing identical before/after | pass |
| AC4 | `--plugin-root`; `mode`; `-h`; repo checkout with nothing newer | in place, no `using plugin` line | pass |
| AC4 | `SQUAD_PROCESS_DELEGATED` set, unpinnable | exit 1 refusal, no grandchild | pass |
| AC7 | matches the Developer's evidence run, reproduced by me | same lines | pass |
| real machine | runtime with no env override | reads real `~/.claude*/plugins/known_marketplaces.json`: `using plugin 0.10.1 from /home/chieule/workspace/squad (known marketplace herdr-squad)`, exit 0 | pass |

AC8 (SQ-10 files, tests, no os.exec/shell=True) is QA whitebox's.

Follow-ups (not AC breaks):
- With `SQUAD_PROCESS_DELEGATED` set the refusal says `searched: no known_marketplaces.json or installed_plugins.json found` even when files exist (it does not search). Wording could say "not searched: already the delegated run".
- `(N entries)` counts usable squad entries, not file entries (known.json with 2 entries shows 1).
