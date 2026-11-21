# 05 `upgrade` and `homes` find the newest plugin from a pinned session: evidence

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
