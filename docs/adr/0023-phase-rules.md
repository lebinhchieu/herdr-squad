# 0023: Manager-only rules print at their phase instead of being attached

Status: accepted

## Context
The Manager's composed rules were 779 lines and 57 KB, and the Tech Lead's 533 lines, on one scope's team. Most of the Manager's lines are rules that matter only at a merge, a close or a retro, and a tool the Manager must run at that moment can print them.

## Decision
- A rule may carry `phase: merge|close|coach`. Eight rules do: MRG-2, MRG-3, MRG-4, MRG-5 (merge), CLOSE-2, CLOSE-4, CLOSE-5 (close) and ITER-6c (coach). They are not attached to the Manager. The tool that starts the phase prints them: `squad-merge-check`, `squad-close`, `squad-spawn token-coach`. `squad-process phase <name> --home D` prints them by hand.
- A rule moves only when the Manager is its only acting role, a tool the Manager must run can print it, and it is not an authority gate or the rule that names the tool. So MRG-1, CLOSE-1, CLOSE-3a/b/c and ITER-6/6a/6b stay attached.
- The rule index lists IDs only. `squad-process rule <ID>` still finds every rule (CORE-6).
- A tool that prints a rule never changes its verdict or exit code.
- Measured on the same team after the change: Manager 566 lines and 47 KB, Tech Lead 277 lines; the Manager index is 20 lines and the Tech Lead index 24 lines (header included).

## Consequences
- Adding `phase:` changes the hash of each tagged rule. An overlay that replaced one goes stale; `squad-process upgrade --check` names it.
- A squad pinned to an older runtime keeps the old attached rules, so nothing is lost. On such a pin `squad-process phase` refuses and `squad-close` prints nothing.
- Overlay rules (`SQ-7`, `SQ-7b`) get no `phase:` until every squad that shares them runs this plugin.
