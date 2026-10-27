# Evidence: 09 Report and scope template
sha: pending

## Behaviour
- Scope data (`squadreport.collect`/`base_data`): `scope` has both `size` (old `size:` first token, as written) and `team` (display text of the `team:` line, trailing `(note)` dropped, `""` when absent/blank/no scope.md). Nothing derives one from the other (`size: L` + `team: qa-white` shows both).
- Rollup rows (`row_from`): `size` and `team` always strings (`""` for null/missing in an old data.json). Error and no_data rows: `size: None`, `team: None` (one rule, tested on both keys).
- `report.js` header chip: `team <text>` when a team is recorded, else `size <S>` (`size ?` when both empty). `rollup.js`: drawer line and name-cell suffix show team, else size. The Size filter still filters old sizes only.
- `templates/scope/scope.md`: one `team:` line; `size:`, `qa:`, `design:`, `architecture:` removed; "Done means" no longer cites Sizes.
- Tests: `TeamSizeScope` (collect), `TeamSizeKeys` (rollup), `RollupTeamChip` (browser: rollup folder served by `python3 -m http.server` on 127.0.0.1, stopped by PID; asserts the old row shows `L` and the team row `qa-white, qa-black`), header chip test in `test_squadreport_ui.py`.
- Lint baseline (G2b), `bin/squad-process lint`: base 6ec3a75 empty, exit 0; branch empty, exit 0.
- Changelog v9: no rule ID changed in this ticket.
