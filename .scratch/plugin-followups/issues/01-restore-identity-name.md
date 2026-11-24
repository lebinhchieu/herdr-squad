# The /squads resume command does not name the pane

Status: needs-triage

Source: upstream-proposals retro (iterations/1.md, 1.summary.md Friction), 2026-11-24.

## Problem
herdr restores agent panes with `c1 --resume <id>`, and the pane comes back unnamed. `squad-respawn` and `squad-retire` then fail with `agent_not_found` until someone runs `herdr agent rename <pane> <name>`. Task 11 restored the hooks' identity from the roster, but not the pane name.

## Proposed fix
Scope agreed with Chieu 2026-11-24: the `/squads` resume command (`bin/squadcommands.py` `_resume_text`) also runs `herdr agent rename`, and every role gets the command, not only the Manager. Fallback (Token Coach proposal 1): `squad-respawn` and `squad-retire` find the pane by the session id in `roster.md` when the name lookup fails, or rename it first.

## Comments
- 2026-11-24, Manager: Chieu turned herdr agent resume off (`[session] resume_agents_on_restore = false`) and resumes by hand with the `/squads` resume command. That command (`bin/squadcommands.py` `_resume_text`) restores `SQUAD_*`, role, rules and settings, but does not run `herdr agent rename`, and exists for the Manager only. Proposed scope: the resume command also names the pane, and every role gets one. Token Coach plugin proposal 1 (same root): `squad-respawn`/`squad-retire` fall back to the roster session id and rename the pane themselves. Not verified: whether herdr keeps `agent_name` on a shell-only restore.
- 2026-11-24, Manager: Chieu agreed the reframe above.
