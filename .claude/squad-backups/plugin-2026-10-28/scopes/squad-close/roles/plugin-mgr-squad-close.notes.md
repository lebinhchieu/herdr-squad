# Notes: plugin-mgr-squad-close
## Now
Closing now (PO accepted E3 = close). Branch squad/plugin/squad-close/plugin-dev-squad-close-2 (5adfc45..fb2091c) unmerged; PO may say "merge fb2091c" in chat. Folder moved to _done after close; chat-only.
## Update 2026-10-23
PO chose (b): fix the 55 failures here. Task 03 (tasks/03.md) running: Dev plugin-dev-squad-close-2 (branch squad/plugin/squad-close/plugin-dev-squad-close-2, base edf5d87). qa-b: no set (PO ok). Next: Dev ASK with root causes -> HANDIN -> spawn only QAW `squad-spawn qa-whitebox plugin-qaw-squad-close` -> PASS -> Coach, close. E2 answered; roster cleaned (old pod gone). The (a) bullet below is superseded.
## Open threads
- PO answer: (a) waive + close, or (b) fix suite here. If (a): spawn Token Coach (ITER-6b; `squad-spawn token-coach plugin-coach-squad-close --scope squad-close`), accept <=3 proposals, then ITER-15 drafts in tasks/, tell PO unmerged branch squad/plugin/squad-close/plugin-dev-squad-close-1 (5adfc45..edf5d87), resolve/withdraw open inbox items, then `squad-close plugin --scope squad-close` last. NOTE: the new squad-close keeps my Manager alive after close (chat-only).
- Merge only when PO says so in chat (MRG-1): check git merge-base --is-ancestor, git merge --no-ff edf5d87 in project root, no untracked files outside .claude/squads (MRG-5).
- Follow-up draft: tasks/03-suite-baseline-failures.md (PO waiver needed).
## Decisions that bind
Design from .scratch/squad-close-keeps-manager/grill.md; sizes/models default.
## Pointers
iterations/1.md, iterations/1.summary.md, evidence/suite/base-vs-final.md, tasks/01.md 02.md
