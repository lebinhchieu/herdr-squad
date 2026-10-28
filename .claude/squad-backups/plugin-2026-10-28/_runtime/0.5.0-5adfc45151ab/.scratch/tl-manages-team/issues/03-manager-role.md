# T3 · agents/manager.md for M and L
Status: ready-for-agent
Type: task
Blocked by: T1 (shares manager.md; branch from T1's passed sha)
Repo: /home/chieule/workspace/squad (branch from main c1be501 unless the briefing names a base)
Spec: ../spec.md (B-ids) · Design: ../design.md (decision numbers) · Technical AC: `$SCOPE_DIR/evidence/qa-w-tech-ac.md` (AC ids)

## Files this task touches (and no others)
`agents/manager.md`, `tests/test_manager_m_l.py` (new). Do not touch the Writing-rule block (`tests/test_process_writing.py` pins it) or the budget line (T1 did).

## Do
In M and L the Manager no longer: spawns Developers, runs the pod's health checks, routes routine questions, triages 3 returns, relabels QAs, or tells the PO about a `blocked` pane. In S every one of these stays exactly as written; mark them "S" in the text.
- **Spawning section:** Developers: S only ("M, L: the Team Lead spawns them"). Keep spawning Team Lead (M, L), Tech Lead, BA, QAs, Designer, Token Coach. **Tell each Team Lead in its first prompt the size and its Developer share of the cap** (a lone scope: the whole cap; in a goal the goal Manager divides the cap among running scopes, shares summing to at most the cap; **quote this rule in manager.md** (B15), and say a finished scope's share goes to the scopes still running at their next briefing or respawn).
- **Keeping the squad healthy:** M and L: watch the Team Lead only (alive, not stuck, context) and read `iterations/<n>.summary.md` for the retro and check-in; S unchanged. Delete "tell the PO which pane" for blocked panes (no relay: each agent's own toast reaches the PO).
- **Disputes:** the Manager settles every dispute except plan, order and assignment ones in M and L, which the Team Lead settles; the parties come straight to the Manager (no relay). `FINAL:` stays.
- **Stacked branches:** in a goal the Manager checks the base and names it in the iteration file; the Team Lead spawns with it.
- Keep: sizing, size changes, the PO and the inbox, merge on request, close, Token Coach, goal Manager duties.

## Technical AC
AC-4.1, AC-4.6, AC-2. `tests/test_manager_m_l.py` pins that S text (Manager spawns Developers in S, S health checks) is present, that M/L Developer spawning and polling are not, and that the Team Lead watch is. Existing `test_instructions.py` manager tests stay green.

## Business AC
B2 (Manager side), B8, B9, B20.
