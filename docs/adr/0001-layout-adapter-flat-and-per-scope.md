# Layout adapter: one list of homes for flat and per-scope squads

Status: superseded by 0008 (was: accepted (BRD-19, design L1-L14))

The board reads a squad as a list of **homes**, so one code path serves both layouts.

- `scopes/` is a directory → per-scope layout, else flat.
- Homes are `goals/<g>/` then `scopes/<s>/`: real directories, names `^[a-z][a-z0-9-]*$`, so `_done/` is never read.
- A Manager row is pod `all`; any other row's pod is its home's folder name.
- Logs of all homes are concatenated and `msg_id` is deduped globally. Iterations are the union of numbers; the highest is current, the filter is per home.
- Escalation and manager-idle ids carry the home; an activity record goes into the agent's own home.
- The `/state` key list did not change.

**Why hard to reverse:** ids, pods and the iteration filter all depend on it; a change breaks saved tabs and fixtures.
