# Plugin follow-ups from add-architecture retro (draft)
Source: iterations/1.coach.md `## Plugin proposals`.
1. `usage-events.jsonl` events carry no `ctx` / turn count: add them to the line `squad-usage --check` writes.
2. `squad-usage` shows only the current session after a respawn, hiding sessions that went over the line: one row per session, or the max peak across sessions.
3. The `fresh` event does not record the path taken (`respawned` or `retired`): record it.
