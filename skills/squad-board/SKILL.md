---
name: squad-board
description: Print the URL of the squad board, or start it afresh - use when the user asks to open, find, recover or restart the board, or says the board URL was lost or the page does not load.
disable-model-invocation: true
---

# Open the squad board

**Result: the board's URL, one line ending in the token, from a board running in the `board` herdr tab.** `bin/squad-board-start` does the work and never starts a second board.

1. Check `HERDR_ENV` is `1`. If not, tell the user to open herdr and run this from a pane there.
2. Pick the squad: the name the user gives, else the only folder in `.claude/squads/` (several and none named: ask).
3. Run `squad-board-start --squad <squad>`. Add `--restart` when the user says restart or the page does not load.
4. Show the URL line as printed. Say it ends in the token and that Jump needs it.
5. If the command fails, show its output as is.
