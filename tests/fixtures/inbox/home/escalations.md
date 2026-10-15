# Escalations

**Questions waiting on the PO, newest first. The Manager writes each one before telling the PO.**

| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |
|---|---|---|---|---|---|---|
| 15 | 2026-10-14 | Withdrawn by the Manager | (a) x; (b) y | | | withdrawn: no longer needed |
| 14 | 2026-10-14 | Answered in chat | (a) x; (b) y | | | (a) x |
| 13 | 2026-10-14 | Answered and delivered | (a) x; (b) y | | | (b) y<br>with a note |
| 11 | 2026-10-14 | Answered, waiting for the Manager | (a) x; (b) y | | PI-02 | (a) x |
| 8 | 2026-10-14 | Ship the badge?<br>It touches CART-04. | (a) yes; (b) no; (c) later | a | CART-04 | |
| 7 | 2026-10-13 | Already settled by hand? | (a) x; (b) y | a | | settled by hand: x |
| | | | | | | |
| 6 | 2026-10-13 | Use a \| b or c? | see (a) above | | | |
|  | 2026-10-12 | A row with no number | | | | |
| 8 | 2026-10-12 | Same number as the badge row | (b) x; (a) y | | | |
| 9 | 2026-10-12 |
| 1 | 2026-10-12 | goal.md sets size S but also says done = QA whitebox PASS. S has no QA whitebox, allows 1–2 tasks, and no risk flag; this scope has about 10 tasks and a security flag (localhost bind, token-guarded jump). Which size? | A) S + QA whitebox: Tech Lead plans, QA whitebox signs off, Developer evidence replaces QA blackbox. Logged as a process exception. B) Full M: add a BA and a QA blackbox (testing via replay mode). C) S exactly as in process.md: Tech Lead review only. | **A.** The spec is complete, so a BA adds little. QA whitebox matches goal.md's done rule and covers the security flag. Revisit QA blackbox in iteration 2 when the page exists. | Spawning anyone | 2026-10-12: A |
| 2 | 2026-10-12 | BRD-02..06 must branch from code that has BRD-01, and only the PO merges. When BRD-01 passes QA whitebox, will you merge `squad/dev-board-1` into `squad-board-spec`? Please also commit the tickets, `design.md` and the `--effort` change first, so new worktrees have them. | A) PO merges BRD-01 as soon as it passes, and the Manager pings you. B) Developers stack on `squad/dev-board-1`, branching from it by hand; this needs a base-ref option in squad-spawn, which is outside the goal. | **A.** One merge unblocks 5 tickets. | BRD-02..06 | 2026-10-12: PO delegated decisions to the Manager. Manager chose **stacking**: the Manager creates each worktree from the passed BRD-01 commit before `squad-spawn`, which reuses it. A final integration ticket combines the passed branches on one Developer branch. The PO merges once at the end. |
| 3 | 2026-10-12 | The Developer permission settings deny `git merge`, so dev-board-8 can't merge the passed branches into its own BRD-09 branch. The Manager's stacked-branches plan missed this; neither the Manager nor an agent may work around it. | A) Allow merge for this run: remove `Bash(git merge:*)` from the project copy `squad/settings/dev.json` only (the plugin template stays). `git push`, `rebase`, `reset --hard` and `checkout main` stay denied. B) The PO runs the merges into `squad/dev-board-8` by hand (5 now, 1 more for BRD-06, ~7 in iteration 2). C) The PO merges each passed branch into `squad-board-spec` as it passes, as in the original process. | **A.** It's one change, and it ends the blocks for both integrations. The process already limits merges to a Developer's own branch. | BRD-09, then BRD-08 and all of iteration 2 | 2026-10-12: A (PO). Done: merge allowed in squad/settings/dev.json. |
