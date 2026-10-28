Status: ready-for-agent
Type: task
Task ID: 13
Touches: `templates/squad/process/iterations.md`, `agents/token-coach.md` (stance line only), `bin/squad-close` (empty-retro refusal), `tests/test_squad_close.py`, `tests/test_retro_rules.py` (new)
Does not touch: `bin/squad-usage`, other `agents/*`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_close test_retro_rules test_windows_safe`
Blocked by: 06, 07, 10 (10 also edits `bin/squad-close`)

# 13: The retro keeps what it learns

**Done when no scope closes with a blank retro, the Coach builds on earlier backlogs, and tool or role-card findings leave the retro as tickets or `upstream: proposed` operations.**

## Why
Review finding 8:
- about 31 Coach backlog entries that no role re-reads;
- tool bugs left as retro prose (squad-respawn's old pane, duplicate roster rows, `.pyc`, `IDLE_CTX` hard-coded, `--resume` dropping herdr names);
- 2 retros fully blank;
- the Coach may propose only process.md changes.

## What
- **Coach rules:**
  - read every `## Backlog` in the squad's earlier `*.coach.md` (`scopes/_done/**`, `goals/_done/**`);
  - promote an item seen in 2 or more scopes to a proposal, citing both;
  - write process proposals as overlay operations (`process.local.md` syntax, `upstream: proposed`), so the Manager can paste them;
  - list tool or role-card findings under `## Plugin proposals`.
- **Manager rule:** at the check-in, each `## Plugin proposals` item and each retro "Plugin follow-ups" item becomes one ticket where `project.md` names the plugin's tracker. Without such an entry, it goes in the inbox as a read item.
- **`squad-close --scope`** refuses while the last iteration file's `Went well`, `Friction` or `Process changes made` heading is empty. `--force` overrides it, and the override is logged in the iteration file.

## Technical AC
1. `squad-close` on a fixture with an empty `Friction` refuses with exit 1 and names the heading. `--force` closes and writes the log line.
2. `test_retro_rules.py`: `who` shows the Coach acting on the backlog rule and the Manager on the plugin-proposals rule.
3. A fixture squad with two coach files sharing a backlog item: the evidence shows a Coach dry run (Haiku, temp squad) that cites both. Spend at most $0.10.
