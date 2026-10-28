# plugin-dev-dsz-3 notes (ticket 03) — RETIRED
- Ticket 03 done: both QAs PASS on code 64871b4; evidence sha 0f4305d handed to Tech Lead. Branch squad/plugin/drop-scope-size/plugin-dev-dsz-3.
- AC 21 (upgrade --check retarget lines) moved to ticket 12 by Tech Lead; no code in 03.
- Notes: plan_scopes skips scopes/_*; converter comment lists every dropped old line when team blank or check non-empty; `team --home` non-directory exits 2.
- Tests: python3 -m unittest tests.test_team_cli tests.test_squad_migrate tests.test_squadadopt tests.test_squadcompose tests.test_squadrules.
- squad-evidence add takes the ticket .md file, not the folder.
