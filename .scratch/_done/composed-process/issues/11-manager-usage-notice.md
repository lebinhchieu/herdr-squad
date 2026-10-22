Status: ready-for-agent
Type: task
Task ID: 11
Touches: `bin/squad-manager-guard` (new), `hooks/hooks.json` (PreToolUse entry for Bash), `templates/squad/process/cost.md` (Manager COST rules), `tests/test_squad_manager_guard.py` (new), `tests/test_hooks_json.py`
Does not touch: `bin/squad-usage-hook` (the Stop-hook exemption for the Manager stays), `agents/*`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_manager_guard test_hooks_json test_squad_usage test_windows_safe`
Blocked by: 06, 10

# 11: The Manager hears its own context size at quiet moments

**Done when a Manager over the threshold gets one notice in the tool result of its next `squad-spawn` or `squad-inbox add`, never in the middle of the PO's conversation, and the cost rules say what it does then.**

## Why
Review finding 5: the Manager ran to 144k (audit-token), 132k (remove-board), 168k (inbox-visual) and 108k (win-compat it.2) although the rule was reworded twice. `squad-usage-hook` exempts the Manager on purpose: a Stop-hook nudge would cut into the PO's conversation. A spawn or an inbox write is a quiet moment by definition.

## What
- **`squad-manager-guard`** (PreToolUse, matcher `Bash`):
  - only acts when `SQUAD_ROLE=manager` and the command starts with `squad-spawn` or `squad-inbox add`;
  - reads the Manager's row with `squad-usage`; when context is over 100k, or the cache expired since the last turn, it adds one notice ("context <n>k: after this step write your notes and run squad-respawn <name> [COST-n]");
  - gives the notice at most once per session per threshold crossing, logged to `usage-events.jsonl` like the Stop hook;
  - never blocks the tool call.
- **How the notice reaches the model is not verified.** First test whether a PreToolUse hook's `hookSpecificOutput.additionalContext` reaches the model; if not, use `systemMessage`. Record which works in the evidence.
- **Rules:** the Manager's COST rules lose "the cost hook never nudges you" and gain the reaction above.
- **Optional, if the PO says so at the goal check:** add the effort-before-model step-up rule ("Later" in spec).

## Technical AC
1. Decision table: role ≠ manager → no output; a non-matching command → no output; under the threshold → none; over it → one notice, a second call in the same session → none.
2. A missing `squad-usage` or `jq` makes it exit 0 silently.
3. A live probe in a temp squad shows the notice reaching a Haiku Manager session (command and answer recorded).
