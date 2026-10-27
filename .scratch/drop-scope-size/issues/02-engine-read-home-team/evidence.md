# Evidence: 02 Engine vocabulary (squadcompose)
sha: pending

## Behaviour
- `read_home(home, legacy_scaffold=False)` returns `{facts, team, team_source, scope, pin}`. `team:` line: decided (`team_source "team"`, every presence and duty fact set, `qa-b` mirrors `qa-black` for old rule files), `none` = `[]`, blank or hand-made (no `team:`, none of the four old lines) = undecided (`team None`, no team fact). Goal home: source `goal`, team facts missing as before.
- Bad `team:` (unknown, duplicate, `manager`/`dev`, `qa-whitebox`/`qa-blackbox`) is a `ComposeError` `scope.md:<line>: ...` naming the token (and `qa-white`/`qa-black` for role names); `squad-process compose` exits 2 with that line on stderr (spec AC 30).
- Old `size:` home: old path unchanged (source `size`, base header `(size M, ...)`); `legacy_scaffold=True` adds duty facts from `sr.legacy_team` (first token; base `\b[SML]\b` anywhere still sets `size`; test line `size: confirmed M by PO` shows both). CLI `compose` never sets it (test greps `squadrules_cli.py`). Real samples copied verbatim from the files (file:line in `REAL`): refine-process:7, extractor-role:8-9, svgdraw:7, report-ui-fix:7 (`size: M — signals:`; svgdraw has no such line), grillui:7-10.
- `qa: none (PO ...)` no longer raises: fact falls back to `full`, the line is not touched; any other bad value (`qa: maybe`) still exits 2 with `scope.md:N`.
- `load_rules(plugin_root, overlay)` and pure `choose(rules, role, facts)`; test equals the pre-split filter and the `rules:` line for 3 homes x 10 roles.
- Header (team home): Manager, Team Lead, Tech Lead get `· team: <list|none|undecided>` and a `duties:` line (13 owners, table order; `duties: undecided`); Dev and the rest print no team. Goal Manager: `team: undecided`. Golden `manager-goal.rules.md` updated for it.
- `who_lines`: size lines and `qa-b` lines unchanged; one line per value of each duty or presence key in the rule's `when:` (`business-ac = ba: acts: ...`).
- `tests/rulesview.py`: `composed(..., team=)`; size homes compose in-process with the scaffold; `who`/`acts` accept `S|M|L` and `<key> = <value>` keys.
- Lint (C6) landed in 01 (key sets, one primary key, extras); its tests are in `test_team_duties.py` and `test_squadrules.py`.
- Lint baseline (G2b), `python3 bin/squad-process lint`: base 991cab6 empty, exit 0; branch empty, exit 0 (diff identical).
- Tests run green: test_squadcompose (87, incl. byte-equal proof against base 991cab6 `compose` for 60 size-home x role pairs), test_team_duties, test_squadrules, test_sizes, test_qab_optional, test_dev_rules_size, test_crlf_squad_files, test_windows_safe, test_squad_respawn, test_squad_spawn, test_squad_start, test_squad_log_message, test_squad_migrate, test_squadadopt, test_squadruntime and the other 30 grep hits for `rulesview|squadcompose|read_home|compose|who_lines|(size`.
- Changelog v9: no rule ID changed in this ticket.
- Transitional, asked to the Tech Lead (MSG-11b): while rule files key on `size`, a team home has no `size` fact, so the fixture Manager text carries `[if size ...]` tags; a `team:` plus old lines home reads the team and ignores the old lines (not yet an error; task 12). Answer: see Comments in the ticket.
