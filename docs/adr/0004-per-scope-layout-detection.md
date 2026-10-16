# Per-scope layout is detected from `scopes/`, not configured

Status: partly superseded by 0009 (board part); the layout rule is restated there (was: accepted (BRD-19))

A squad is per-scope when `scopes/` is a directory; otherwise it is flat. There is no setting. Legacy flat squads keep working unchanged.

- A stale root `roster.md` is ignored once `scopes/` exists. A symlinked `scopes` is not a directory for this test.
- Each home keeps its own roster, escalations, logs, `iterations/` and `roles/`.
- Two scopes can both have an escalation `#1`, so its id and text name the home (L9).
- The board's default is one board per herdr workspace.

**Why surprising:** moving a folder named `scopes` into a flat squad changes how the whole squad is read.
