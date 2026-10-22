# 04 Threshold check hook

Status: resolved
Blocked by: 01, 03

Add a Stop hook to the squad settings file. It runs `squad-usage --check` on the session's own id. When a rule fires, it tells the agent the rule and the action, and appends an event to `usage-events.jsonl`.

## AC
- Fires only for squad sessions.
- Costs no LLM call.
- A fixture over 60% produces a 'fresh' message and an event line.

## Comments

- Added `bin/squad-usage-hook` (bash + jq, like `squad-log-message`) and a `Stop` entry in `hooks/hooks.json`. It reads `session_id` (and `transcript_path`, `stop_hook_active`) from stdin, runs `squad-usage --check`, and on a hit appends `{ts, agent, role, session, rule, action}` to `$SQUAD_DIR/usage-events.jsonl` and exits 2 with the message on stderr. No LLM call.
- Checked from the hooks docs: Stop gets `session_id`, `transcript_path`, `hook_event_name`, `last_assistant_message`; exit 2 + stderr continues the turn with that text. `stop_hook_active` could not be confirmed from the page I could read, so the hook guards on it (exit 0 if true) and also fires each rule only once per session via `usage-events.jsonl`.
- **Deviation from the spec:** the hook lives in the plugin's `hooks/hooks.json`, not in the per-role `settings/*.json`. Those files are passed with `--settings`, have no way to point at the plugin dir, and are project-tuned copies that old squads would not get. "Squad sessions only" is the same env guard (`SQUAD_NAME`, `SQUAD_DIR`) `squad-log-message` uses.
- **Assumption:** the Manager is exempt (`SQUAD_ROLE=manager`): it is the PO's session and cannot be respawned the same way.
- Limit: `idle` can only fire when a turn starts after a long gap and the next Stop sees the old last-turn time; at Stop the just-finished turn is "now", so in practice `idle` is seen by `--check` run outside the hook (Manager, `squad-respawn`).
- Test: `python3 -B -m unittest tests.test_squad_usage_hook` → 8 tests OK (60% fixture → 'fresh' message + event line; non-squad, manager, under threshold, repeat, `stop_hook_active` all silent).
