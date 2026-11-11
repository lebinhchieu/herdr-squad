# Evidence 18 hook plan owner

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 merge: both heads are ancestors; tests of both sides pass | `git merge-base --is-ancestor 172a373 HEAD` and `... squad/plugin/respawn-guard/plugin-dev-respawn-guard-1 HEAD` both true (merge commit 5659700, ticket file after it); test_squad_usage, test_squad_respawn, test_squadruntime pass | `cd tests && python3 -m unittest test_squad_usage test_squad_respawn test_squadruntime` |
| AC2 Developer text names the plan owner (Team Lead only when `team:` lists `team-lead`, else Manager; pointer COST-5 / COST-5a) | `test_developer_text_names_the_plan_owner_from_scope_md` (team-lead line, `team-lead` only in the note, no team line, no scope.md); `test_fixture_over_the_line_gives_fresh_message_and_event` (no scope.md: Manager, also in the event `action`) | `cd tests && python3 -m unittest test_squad_usage_hook` |
| AC3 other roles unchanged | `test_other_roles_text_is_unchanged` (exact string for qa-whitebox) | same |
| AC4 one test per AC 2-3, scope.md fixture | the tests above | same |

## Behaviour

- In the `dev` branch of `bin/squad-usage-hook` the `team:` line of `$home/scope.md` is read with `sed` (the trailing `(note)` is cut off). `team-lead` as a whole comma-separated token: "tell your plan owner (the Team Lead) and stop ([COST-5], no squad-respawn)". Anything else (no file, no line, `none`): "(the Manager) ... ([COST-5a], ...)". The hook still exits 2 and the same text goes into the `action` field of the event.
- The two old asserts "tell the Team Lead" now expect the Manager: that fixture has no scope.md.
- SQ-10: `test_windows_safe`, `test_utf8_helpers`, `test_instructions`, with `test_squad_usage_hook`, `test_squad_manager_guard`, `test_squad_respawn`: 114 tests, OK. Earlier run with `test_squad_usage`, `test_squadruntime`: 171 tests, OK.
