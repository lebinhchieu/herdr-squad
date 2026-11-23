## Review

AC trace
- AC1 | tests/test_squad_respawn.py::test_lazy_respawn_spawns_with_lazy_no_prompt_and_marks_the_event | python3 -m unittest test_squad_respawn
- AC2 | tests/test_squad_spawn.py::test_lazy_writes_the_marker_and_sends_nothing_not_even_a_wait, test_lazy_with_prompt_or_task_exits_2_and_starts_nothing | python3 -m unittest test_squad_spawn
- AC3 | tests/test_squad_spawn.py::test_a_plain_spawn_removes_a_stale_lazy_marker | same
- AC4 | test_lazy_respawn_... (default half: prompt sent, no marker, no `lazy` key; usage text) | same
- AC5 | test_lazy_respawn_... (`"lazy": true` only when lazy) + readers below | same
- AC6 | test_lazy_writes_the_marker... (dry run says "would write", writes nothing) | same
- AC7 | test_windows_safe, test_utf8_helpers green; marker asserted byte-exact `<sid>\n` | python3 -m unittest

## Behaviour

Readers of `usage-events.jsonl` in `bin/`, each ignores an unknown key:
- `bin/squad-usage:115` `orphan_fresh`: reads only `o.get("agent")` and `o.get("rule")` (`respawn` still clears a fresh).
- `bin/squad-usage-hook:25`: `jq select(.session == $s and .rule == $r)`; no other field read.
- `bin/squad-manager-guard:119`: writer (claim_lock append); `seen_keys` (line 88) reads only `session`, `role`, `rule`.
- `bin/squad-event`, `bin/squad-retire`, `bin/squad-spawn`: writers.

Tests run: test_squad_respawn (34 ok), test_squad_spawn (119 ok), grep hits + SQ-10 files (test_windows_safe, test_utf8_helpers, test_instructions, test_crlf_squad_files, test_winlaunch, test_team_lead_perms, test_squad_start, test_squad_usage_hook, test_squad_manager_guard, test_squad_usage, test_templates): 198 run, 1 fail: test_templates::test_designer_may_write_only_ui_design_files (Write(//tmp/**) in the designer settings; `templates/` untouched by this ticket; zero hits in `scopes/_done/*/iterations/*.md`).
