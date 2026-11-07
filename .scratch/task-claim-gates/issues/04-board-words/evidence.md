# Evidence 04

## Behaviour

The Tasks panel flag and filters now use the word `passed`; `done` and `ready for review` are no longer shown on the board. Checked in the panel browser test on the `checkout` fixture (rows 06 and 09 are `passed`):

| Where | Before | Now |
|---|---|---|
| Tasks rows flagged "need" | stage `ready for review` | stage `passed` (2 rows) |
| Tasks filter buttons | `Ready for review (n)`, `Done (n)` | `Passed (2)`, `Merged (n)` |
| Inbox note | "branches ready for review: see Tasks" | "passed branches: see Tasks" |
| `squadboard_inbox` hook and `unknown` name | `ready_for_review` | `passed` |
