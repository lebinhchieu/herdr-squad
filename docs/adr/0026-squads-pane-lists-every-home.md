# A squads pane lists every home, read-only

Status: accepted (squads-mod; Chieu answered E2 (a) on 2026-11-12: the pane may list many squads as a list-only index)

Amends two lines and says so: 0007 ("no cross-home view; `squad-board` stays the cross-home view") and 0020 ("the board shows one goal or scope, and never all of them at once"; "no cross-squad view"). Both lines were about the board and the inbox. This ADR adds a list-only view of every squad, goal and scope of the repo. It does not add a cross-home board or a cross-home inbox. Every other line of 0007, 0009 and 0020 holds.

**Decision:** a `/squads` mod command opens a pane that lists the squads of the active repo, each with its goals and scopes, with the six row facts of the board list (needs you, stuck, tasks done, tasks total, agents working, last active; the same code, `squadboard_list`), one "next step" phrase per row, and for the picked row every command that applies to it. It is a list and a launcher: no task list, no time, no cost, no messages, no answering. It reads through one read-only CLI, `bin/squad-tree` (JSON version 1). It writes nothing. It runs no command at all: each command is shown with its full text and copied on a click (Chieu's choice, copy only). The only process the pane starts is `squad-tree`, for data. The commands live in one table, `bin/squadcommands.py`.

**Why:** Chieu runs several squads, goals and scopes and could not see in one place which one waits on him or what to type next. The board answers that for one home at a time and needs a command first. The inbox pane answers it for one Manager.

**Consequences:**
- The pane shows a number the board also shows, from the same code, so they agree.
- "Active repo" is the main repo of the session (a worktree resolves to the main repo); other repos are never scanned (as 0020).
- The mod loads in every session and does nothing until `/squads`; it reads no file itself (the CLI does).
- New code: `bin/squad-tree`, `bin/squadtree.py`, `bin/squadcommands.py`, `hooks/squads/`, a second path in `hooks/hooks.json` `modules`, new `$.state` keys under plugin `squad`. Two additive edits in `squadboard_list.py` and `squadboard.py` (public `goal_row`, `squads_of`, one herdr call per run).
- The JSON version 1 is additive only; the mod keeps its last good tree on any other version.
- Not built, by decision: `new since last look` (no place for a last-seen time in a terminal), running any command from the pane (Chieu chose copy only), a cross-squad inbox.

**Alternatives rejected:** extending `squad-board` with an all-squads page (a browser, a server and a token for a list; 0020 said no); a recorder of squad state (0009 removed it); the mod reading squad files itself (the facts would drift from the board); a separate commands doc (it would go stale: one code table).
