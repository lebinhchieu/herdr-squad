"""T1 starting point (Tech Lead design). Applies the agreed process.md edits in place and prints size + lint.
The wording is the design. Run once, then tighten; delete this file in the last T1 commit."""
import sys
sys.path.insert(0, "bin")
import processlint
src = sys.argv[1] if len(sys.argv) > 1 else "templates/squad/process.md"
t = open(src).read()
E = [
("process-version: 3", "process-version: 4"),
("| **M** Feature | + BA, QA whitebox, QA blackbox; Tech Lead also owns the plan |", "| **M** Feature | + BA, QA whitebox, QA blackbox, Team Lead |"),
("| **L** Full pod | + Team Lead |", "| **L** Full pod | As M |"),
("| Plan, order, assignment | Tech Lead | Tech Lead | Team Lead |", "| Plan, order, assignment | Tech Lead | Team Lead | Team Lead |"),
("- **Down:** only at an iteration boundary, with the PO's OK.", "- **Down:** only at an iteration boundary, with the PO's OK; the Manager retires the roles that drop out."),
("(decided, built, open); the Manager's briefing", "(decided, built, open); a joining Team Lead takes the plan over from it; the Manager's briefing"),
("- **Developer cap:** 3 at once, counted across all scopes of a goal; the Manager queues the rest.",
 "- **Developer cap:** 3 at once. The Team Lead (S: the Manager) spawns up to it and queues the rest; in a goal the goal Manager divides it among running scopes in their briefings."),
("| `roster.md` | Manager |", "| `roster.md` | Manager; Team Lead for its Developers |"),
("| `tasks/<id>.md` | Plan owner (Team Lead; Tech Lead in S and M) |", "| `tasks/<id>.md` | Plan owner (Team Lead; Tech Lead in S) |"),
("| `escalations.md` | Manager | Waiting on the PO |\n", "| `escalations.md` | Manager | Waiting on the PO |\n| `iterations/<n>.summary.md` | Team Lead (M, L) | Pod summary for the retro and check-in, at most 40 lines |\n"),
("| `STATUS` | Answer the Manager's health check |", "| `STATUS` | Answer a health check |"),
("- Ask the owner from `roster.md`; ask the Manager only when the roster doesn't say.",
 "- Ask the owner from `roster.md`; when it doesn't say, ask the Team Lead (S: the Manager).\n- **Pod contact (M, L):** the Team Lead spawns and retires Developers, runs health checks and routes questions. Pod members message it, not the Manager.\n- **Team Lead to Manager (M, L):** only an \"Always goes to PO\" item, a size-change signal, a dispute it cannot settle or 3 returns on one task; plus the iteration summary."),
("**A Manager ruling starts with `FINAL:` and is sent once.** The owner never re-opens it; a new fact goes to the Manager as a new `ASK`.",
 "**A Manager or Team Lead ruling starts with `FINAL:` and is sent once.** The owner never re-opens it; a new fact goes to the ruler as a new `ASK`."),
("- The Manager never pushes `STATUS`:", "- The Team Lead (S: the Manager) never pushes `STATUS`:"),
("- Never relay a permission or approval; a message approves nothing. Permission prompts go to the PO.",
 "- Never relay a permission, approval or blocked pane; a message approves nothing. Permission prompts reach the PO through the agent's own notice."),
("| Plan, task order, assignment | Team Lead (Tech Lead in S and M) | Manager |", "| Plan, task order, assignment | Team Lead (Tech Lead in S) | Team Lead (S: Manager) |"),
("| Process, roster, spawning, scope size | Manager | n/a |", "| Process, roster, spawning, scope size | Manager; Team Lead for Developers (M, L) | n/a |"),
("- After 3 returns on one task the Manager steps in", "- After 3 returns on one task the Team Lead (S: the Manager) steps in"),
("and spawns the pod only after the PO confirms.", "and spawns the pod's non-Developer roles only after the PO confirms."),
("Every role reads the sections its row names, at start and when the Manager says one changed. A Manager edits this file only after re-reading it, in small edits, each logged in `process-log.md`.","Every role reads the sections its row names, at start and when the Manager says one changed."),
("- Point at files and lines; never paste them. `BLOCKED`","- Point at files and lines. `BLOCKED`"),
("- The Manager spawns a task that needs unmerged work with `--base <passed branch or commit>`.","- A task that needs unmerged work is spawned with `--base <passed branch or commit>`, which the Manager checked and named in the iteration file."),
]
for a, b in E:
    assert t.count(a) == 1, a
    t = t.replace(a, b)
open(src, "w").write(t)  # in place; run once from the repo root
print(len(t.encode()))
for p in processlint.lint(t): print(p)
