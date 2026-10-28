# plugin-dev-dsz-int2 notes
- INT2 = merge 04+10+06 onto 6389642 (07 excluded, goes to INT3 with 08). Final code sha fed0c95 on branch squad/plugin/drop-scope-size/plugin-dev-dsz-int2.
- Only conflict: changelog v9 (kept 10's TEAM-7 + 06's WHO-1c/1d/1e/2f). No code edits.
- QA whitebox PASS fed0c95. QA blackbox + Tech suite (--if-changed 6389642) pending at retire time.
- Still owed after all checkers pass: `squad-evidence add INT2-integration --heading ... --from $SCOPE_DIR/evidence/INT2/<file>` per review file, `squad-evidence check`, commit, HANDIN evidence sha to plugin-tech-drop-scope-size.
- Tests run via `python3 -m unittest tests.X`; tests/test_instructions.py must be run directly (unittest import errors).
