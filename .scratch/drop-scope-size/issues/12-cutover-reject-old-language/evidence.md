# Evidence: 12 Cutover: engine rejects the old language

## Behaviour
- Old `size:`/`design:`/`architecture:`/`qa-b:` in an unpinned `scope.md`: compose/team errors name the file and `squad-process adopt`, exit 2. A pinned old home keeps the pin path (source "old"). Non-Manager compose on an undecided home exits 2. D1 scaffold, `legacy_scaffold` parameter and `who_lines` size lines deleted (permanent test in test_squadcompose CutoverTest).
- `WHEN_KEYS` drops `size`, `qa-b`; a plugin rule or overlay `when:` using them (or `qa-whitebox`) is a lint and compose error naming the rule and the new key; a `when:` with two role/duty keys is a lint error. `who`/`lint` help names the new key.
- `squad-process upgrade`: overlay op with `when: size = L` / `qa-b = yes` listed with suggested translation, exit 3, `--apply` refuses, writes nothing (AC 21, test_squadupgrade OldWhenLanguage).
- Size-keyed fixtures converted (`tests/fixtures/rules/*`), hashes remapped; `tests/rulesview.py` keeps S/M/L only as a test shorthand over `legacy_team`.
- S4 reader inventory: permanent `tests/test_old_language_inventory.py` fails on any hit of `size:|'size'|"size"|qa-b` in bin/ hooks/ agents/ skills/ outside the allow-list below (per-file count). Hits are converter mapping, migrate input, pinned-runtime D7 text, report display, old-format errors, upgrade table, or false positives (`st_size`, `fs.stat` size).
- AC29: `grep -iw size` over `squad-start`, `templates/scope`, `templates/goal`, `agents/`, `squad-process who --help`: no hit (same test). Only remaining hit in `templates/` is a tombstone `why:` in `_removed.md:44` ("not per size"), not PO-visible output.
- Lint baseline (G2b): `squad-process lint` on base 2175bd2 empty, exit 0; branch empty, exit 0.
- Changelog v9: this ticket changes no rule block (fixtures and code only); `git diff 2175bd2 -- templates` is empty for ticket 12, so no ID rows added.
- Tests green: every grep-hit file for squadrules/squadcompose/squadupgrade/squadteam/squadrules_cli/rulesview/fixtures/rules (41 files), run per file; test_process_conversion; test_old_language_inventory. test_squadinbox `test_no_pyc` fails only when other test files share the process (pycache), passes alone.

## Inventory allow-list (file: count, reason)
bin/squad-log-message:44 comment; bin/squad-migrate:83 migrate input; bin/squad-respawn:29,37 and bin/squad-spawn:112,124 pinned-runtime D7; bin/squadadopt.py:364,428,440-443,485 converter mapping; bin/squadcompose.py:57,78,307,308 old-format rejection; bin/squadinbox.py:201 st_size (false positive); bin/squadreport.py:81,435,495 and squadreport_rollup.py:88,200,206 report display; bin/squadrules.py:50-52,135,252-268 OLD_WHEN_KEYS/legacy_team/lint msgs; bin/squadruntime.py:368 converter pointer; bin/squadteam.py:82,88 converter pointer; bin/squadupgrade.py:60-67 overlay translation table; hooks/po-inbox/* fs.stat size and evidence file name (false positives).
