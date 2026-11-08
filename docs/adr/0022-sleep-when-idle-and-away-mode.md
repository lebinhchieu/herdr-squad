# 0022: With sleep on, idle for any reason means sleep; "I am away" turns on sleep and away mode

Status: accepted

## Context
Sleep-when-done suspended the PC only when every ticket was done and nobody worked. A merge needs the PO (MRG-1), so "all merged" never came, and a team stalled by a network or usage-limit problem, or waiting for the PO, never let the PC sleep. The PO also had to remember `squad-watchdog sleep on` before leaving, and the watchdog ran as a hidden detached process the PO could not see or stop.

## Decision
- With `sleep on`, the PC suspends once when no agent on the machine works for N minutes, whatever the tickets say. The log names the reason (`all tickets passed`, `team idle with open tickets`, `team idle`). The switch is `sleep-when-idle` everywhere; an old `watchdog.sleep` file stays valid.
- A `UserPromptSubmit` hook, `bin/squad-away-hook`, reads "I am away" / "I am back" in a Manager session. Away: `sleep on` plus the file `<home>/away`. Back: both off. The hook only switches; the behaviour is rule ITER-17.
- Away mode (ITER-17): key decisions wait for the PO (the "Always goes to PO" items, and any merge, push or deploy, which never go to the inbox); everything else the owner or Manager decides, advisor first; an unclear question is parked and other work continues.
- The watchdog runs in its own herdr tab labelled `watchdog` (no focus, only the watchdog), one per home, with the detached process as the fallback outside herdr or when the tab fails.

## Consequences
- The PC can sleep while the team waits for the PO's answer. That is what the PO asked for; the log line says why.
- "I am away" is matched at the start of a prompt in a Manager session only; other sessions and sentences are ignored.
- The tab depends on herdr: `tab create` takes no command, so `squad-start` creates the tab and then types the command with `herdr pane run` (`exec ...` on POSIX, PowerShell `& ...; exit` on Windows).
- Reversible: `sleep off`, delete `<home>/away`, or `SQUAD_WATCHDOG=off`.
