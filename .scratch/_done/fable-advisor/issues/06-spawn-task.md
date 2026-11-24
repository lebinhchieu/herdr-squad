# 06: `squad-spawn --task NN` builds the first prompt
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: A or free slot (after 04/05, or when a slot frees)
Files: `bin/squad-spawn`, tests that cover it (`grep -rl squad-spawn tests/`)
Source: idea 1. First check what `--task` already does on main (the review noted it exists).

## Business AC
1. `--task NN` (dev and checker roles) builds the first prompt from `tasks/NN.md` / the ticket, the `duties:` line, the `team:` line and `roster.md`: scope, folder, files to read first, team, HANDIN target, owner names. `--prompt` text is appended after it.
2. With `--task` the prompt names the right HANDIN target for the team (QAs on team, else Team Lead, else Manager; SIZE-22).
3. A task file with missing fields stops the spawn with a clear message; nothing is spawned.
4. Existing `squad-spawn` tests pass; a new test covers the HANDIN target for a QA team and a no-QA team.
