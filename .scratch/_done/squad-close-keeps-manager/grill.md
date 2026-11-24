# Grill: squad-close keeps the Manager session

:::info{title="Today"}
`squad-close` retires every agent, **the Manager last** (`bin/squad-close:340-342`, `closing.md` CLOSE-1/2/4). It calls `squad-retire`, which closes the Manager's herdr pane. When the Manager is the caller, its own tab ends the script and the Manager is gone mid-close.
:::

| Close mode | Manager retired today | Notes |
|---|---|---|
| `--scope` (lone task) | yes, scope's own Manager | CLOSE-1: "After it the Manager is gone, so it says everything first" |
| `--scope` (inside a goal) | no, goal Manager is not in the scope roster | goal Manager then `squad-respawn`s itself |
| `--goal` | yes, the goal Manager | CLOSE-4 |
| whole squad | yes, all | CLOSE-5 |

## Round 1

:::question{id="r1-q1" title="Which closes spare the Manager"}
Which modes stop retiring the Manager? (yes = recommendation: lone-task scope and goal close spare it; whole-squad close still retires everyone)
:::option{title="Scope + goal close spare it; squad close still retires all" rec}
The Manager stays for the PO to talk to after the close. Closing the whole squad means the squad is archived, so nothing is left to talk to.
:::
:::option{title="All three modes spare it"}
Squad close archives the folder but leaves Managers running with a dead `$SQUAD_DIR`.
:::
:::option{title="Scope close only"}
Goal close keeps retiring its Manager.
:::
:::

:::question{id="r1-q2" title="Opt-out flag"}
Add `--retire-manager` so a close can still end the Manager (and use it in the Manager scripts when a PO says "close it all")? Without it, the PO closes the pane by hand or runs `squad-retire <mgr>`.
:::option{title="No flag; PO runs squad-retire when wanted" rec}
Smallest change; `squad-retire` already exists.
:::
:::option{title="Add --retire-manager"}
Old behaviour one flag away.
:::
:::

:::question{id="r1-q3" title="Folder move under a live Manager"}
The folder still moves to `scopes/_done/` (or `goals/_done/`), so the live Manager's `$SCOPE_DIR`/`$GOAL_DIR` goes stale. OK to keep that and treat the Manager as chat-only after the close (no more squad tooling; CLOSE-1 tells it to report everything *before* closing as now)?
:::option{title="Yes, chat-only after close" rec}
No change to the move. Manager may answer PO questions from what it knows.
:::
:::option{title="Delay the move until the Manager is retired"}
Folder stays open until the PO retires the Manager. More moving parts: `_done` listing, overlap checks and `squad-start` all see a half-closed scope.
:::
:::

:::question{id="r1-q4" title="Pinned runtime of the kept Manager"}
`squad-close` prunes pinned runtimes no open scope/goal holds, except the one the script runs from. A kept Manager runs from its scope's pin, which is now unheld. Keep that runtime while a live Manager uses it?
:::option{title="Skip pruning the closing scope's own pin; a later close prunes it" rec}
The kept session keeps its plugin dir; the next scope or squad close removes it.
:::
:::option{title="Prune as today"}
Fine if the Manager is the caller (protected); breaks the live session's plugin dir if the PO runs the close from elsewhere.
:::
:::

:::qa-copy
:::
