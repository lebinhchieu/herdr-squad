# Team Lead manages the pod

Status: FINAL v1.2 (BA 2026-10-17). Business AC agreed with QA blackbox, including its four changes (B15 observable, B18 and B9 sha and checkers, B22, B23, O2 wording). O1 and O3 settled by the Manager (FINAL, `iterations/1.md` Log). O2, O4, O5 settled by the Tech Lead (`design.md`). Final: QA blackbox accepted the set, including B4 and B15 as a weaker check, 2026-10-17.

**In M and L scopes the Team Lead runs the pod and is its single point of contact; the Manager hears only what the PO must decide, a size change, a dispute outside the plan, and one iteration-end summary. S is unchanged.** Brief: `scopes/tl-manages-team/scope.md`; PO decisions E1 (Q1a, Q2, Q3a, Q4a) bind (`iterations/1.md`).

## The goal behind the brief

The PO talks to the Manager with Opus to decide hard things. Today every HANDIN, PASS, STATUS, spawn request and routing question can reach the Manager, so its context fills with traffic and costs more per turn. The need is **"the Manager's context holds my conversation and the decisions, not the pod's chatter."** Success is measured after the merge, not before: in the first M scope run under the new process, the Manager receives only the four kinds in B6 (count `messages.jsonl` lines addressed to the Manager, by type).

## Terms

- **Pod**: the role sessions delivering one scope.
- **Single contact**: in M and L, the role every pod member messages for routine matters. It is the Team Lead.
- **Routine matter**: task flow, assignment, spawn or retire of a Developer, status, routing ("who owns X"), a Developer's question, a `HANDIN`/`PASS`/`FAIL` copy.
- **Manager traffic**: the four things the Manager hears from a pod (B6).
- **Pod lead** (new in this spec, for the spawn split): Tech Lead, Team Lead, BA, QA whitebox, QA blackbox, Designer. The Manager spawns and retires these; the Team Lead spawns and retires Developers.

## Scope

In: `process.md` template, the role files, the Team Lead's tool permissions, promotion of terms and the decision. Out: S scopes, the Manager's PO conversation and inbox, goal Managers' duties for goals (unchanged), the Team Lead's model (stays Sonnet/medium, a process choice the PO did not contest). This scope itself runs under the current `process.md`.

## Who handles what (the rule the AC check)

| Event | S | M and L |
|---|---|---|
| Developer needed for a ready task | Manager spawns | **Team Lead spawns** |
| Developer finished, area ended | Manager retires | **Team Lead retires** |
| Pod lead needed (BA, QA, Tech Lead, Designer) | Manager | Manager |
| Health check, idle agent, looping agents, filling context | Manager | **Team Lead**, for every pod member except itself; the Manager checks only the Team Lead |
| "Who owns this?", a Developer's question | Manager | **Team Lead** |
| `HANDIN` / `PASS` / `FAIL` | between Developer, Tech Lead | **Developer, QA, Team Lead** (Team Lead tracks state); never the Manager |
| Plan or assignment dispute | Manager | **Team Lead settles** |
| Any other dispute (design, business AC, done) | Manager | Parties follow the two-round rule straight to the **Manager**; no relay through the Team Lead |
| Task returned 3 times | Manager triages | **Team Lead triages** with the owners; then **one budget line to the Manager** (open point O1) |
| Outside question (for the PO) or "Always goes to PO" item | Manager | Team Lead sends the Manager once; the Manager puts it in the inbox |
| Size change signal (business gap, risk flag, user-visible change, more tasks) | Manager sees it | Anyone tells the Team Lead; **Team Lead tells the Manager once** |
| Blocked pane or permission prompt | Nobody relays; the agent's own toast tells the PO | Same (E1 Q2) |
| Iteration end | Manager | **Team Lead writes one summary file**; the Manager reads it |
| Merge, close, push, PO conversation, size, Token Coach, roster of pod leads | Manager | Manager |

## User stories and business AC

Judged in a scratch squad (stub `claude`, herdr) and by reading `process.md` and the role files as each role would, per size. IDs `B-nn` for QA blackbox and tickets.

### US1: The Manager's context stays for me
*As the PO I want the Manager to hear only escalations, size changes, disputes the pod can't settle and an iteration summary, so that it keeps its context for my decisions.*

- **B1** Given an M scope, when the Manager sizes and starts it per `process.md` → Sizes and `manager.md`, then the pod has a Team Lead who takes the plan from the Tech Lead; the Tech Lead keeps technical design and hands over the plan (amended: the draft said the Tech Lead still owns the plan). L is the same pod. The Sizes table and the "Plan, order, assignment" duty row say the Team Lead owns the plan in M and L, the Tech Lead in S.
- **B6** Given an M or L scope, when a task passes both QAs, then the `PASS` goes to the Developer and the Team Lead (no copy to the BA or Manager). The Manager receives only: (1) an "Always goes to PO" item, (2) a size-change signal, (3) a dispute outside plan and assignment that the parties could not settle, (4) one iteration-end summary file; plus the single budget line of B21. Nothing else in `process.md` or a role file tells a pod member to message the Manager.
- **B11** Given all changed files, when grepped, then no M or L passage says the Manager spawns Developers, runs the pod's health checks or routes routine questions, and "ask the Manager" appears only for the four kinds of B6; no two files contradict on who owns an action; S-only passages say they are S-only.
- **B18** Given an iteration end in M or L, then the Team Lead's summary file names: tasks done with evidence links, returns per task, friction it saw (loops, idle waits, unclear ownership) for the Manager's retro, each task's final passed sha and which checkers passed it, and open items for the PO. The Manager writes its retro and check-in from this file, not from messages.

### US2: One voice in the pod
*As a pod member I know who to message, in every size, in one read.*

- **B3** Given an M or L scope, when a Developer, QA, BA or Tech Lead needs a routine matter, then its role file and `process.md` → Messages name the Team Lead as the contact, and `roster.md` lists the Team Lead as owner of routing. The Manager is named only for B6's kinds.
- **B12** Given a Developer reading the role set in S, M and L, then one pass tells it whom to message for `ASK`, `HANDIN`, `BLOCKED` and `STATUS` in each size, with no "ask the Manager" left for M or L routine matters.
- **B2** Given an S scope, when `process.md`, `manager.md`, `dev.md`, `tech-lead.md` and both QA files are read end to end, then S behaves as today: no Team Lead, the Manager spawns Developers, runs health checks and routes.
- **B19** Given a scope that moves S to M, then the Manager spawns the Team Lead, which takes over the Tech Lead's plan file from its `## Handover` section (same format, same file); from then on the M rules apply to Developers already running. Moving M to L changes no role.

### US3: The pod manages its Developers without asking me or the Manager
*As the PO I want Developers spawned, retired and watched inside the pod, within my cap.*

- **B4** Given an M or L Team Lead session in a scratch squad, when it runs `squad-spawn dev ...`, `squad-retire` of a Developer, `herdr agent list` or `herdr agent read`, then each runs without a permission prompt and the Developer comes up in its own worktree. Its settings still deny push, merge into main, rebase, `reset --hard`, and it has no permission for `squad-close` or `squad-start`. A Team Lead spawning a non-dev role (QA, BA, Tech Lead) or retiring a non-Developer is refused by `squad-spawn`/`squad-retire` themselves (enforced, two layers: its settings allow only `squad-spawn dev`, and the commands refuse when the caller's role is team-lead), with a message QA can quote. No `squad-label` permission is needed: QAs are not relabelled in M and L. QA blackbox tests it by running `squad-spawn` and `squad-retire` as team-lead against a QA, BA and Tech Lead target (the quoted refusal) and by reading that the settings allow only `squad-spawn dev`.
- **B5** Given a ready task, when a Developer is needed or has finished, then the Team Lead spawns or retires it and edits that agent's roster row (status, owns). The Manager is not asked and sends no spawn message; the Manager still owns the rows of the pod leads.
- **B15** Given a goal with two parallel M or L scopes, when the goal Manager starts each Team Lead, then its briefing names that scope's share of the Developer cap, the shares of the scopes running at that time sum to at most the cap (3, or the brief's), and a lone scope gets the whole cap. A Team Lead spawns no more Developers than its share; a task beyond it waits as ready. Observable, and how QA blackbox tests it: it starts a scratch goal with two M scopes running together and shows the two Team Lead briefings (first prompt, `messages.jsonl` or the pane); the shares must sum to at most the cap, a lone scope's briefing gives the whole cap, and a briefing without its share FAILs B15. `manager.md` and `team-lead.md` each quote the rule, and `team-lead.md` says that when its share is used up the task waits as ready. **Residual risk, accepted on the Tech Lead's design (decision 3):** `squad-spawn` does not count, so a Team Lead that ignores its share is not refused; QA blackbox's request for a refusal was declined because the cap lives in prose and is overridable per brief. When a scope ends, its share goes to the scopes still running at the next briefing or respawn. The residual risk is named in the iteration summary of the first goal that runs this, so the PO knows the cap is a rule, not a lock.
- **B16** Given a stacked-branch task in a goal (`--base`), when the Team Lead spawns its Developer, then the base is a branch or commit the Manager named in the iteration file after the merge-base check (`process.md` → Inside a goal); the Team Lead never picks an unchecked base.
- **B17** Given a Team Lead near its cost limit (Cost rules), then it writes notes and respawns itself; the plan, roster and tasks in files let the new session continue without the Manager.

### US4: Blocked panes are mine to answer, nobody relays
*As the PO I go to a blocked pane myself, and each agent's own toast tells me.*

- **B8** Given a pane blocked on a permission prompt or an approval, then no role file tells any agent, the Team Lead or the Manager to relay it; the Manager's health-check text about telling the PO of a `blocked` pane is removed. A `BLOCKED <task>` message about work (a missing decision, a missing file) is not a permission prompt: it goes to the Team Lead in M and L.
- **B23** Given an M or L Team Lead that has died or is stuck, then the Manager's B20 check notices and respawns it from its notes; Developers keep running; no pod member messages the Manager about it except through B20.
- **B20** Given the Manager's Keeping the squad healthy section, then in M and L it checks only the Team Lead (alive, not stuck) and reads the iteration summary; it does not poll the Developers.

### US5: Disputes and returns end at the lowest role that can settle them
*As the PO I want plan arguments and repeated returns settled in the pod.*

- **B7** Given a dispute on plan, order or assignment (Tech Lead vs QA about task order, a Developer vs the plan), then the Team Lead settles it and writes it where the plan lives, unless it is itself a party (**B22**). Given any other dispute (BA vs Tech Lead on a rule, QA vs Developer on done), then after 2 exchanges the parties send it to the Manager, who settles it with `FINAL:`; the Team Lead is not a relay. The two-round rule and `FINAL:` still read coherently.
- **B21** Given a task returned 3 times, then the Team Lead reads the findings, decides with the owners whether the task, the AC or the Developer is the problem, and sends the Manager one line so the Manager can run the PO check-in the brief's Budget asks for. The Manager no longer triages it. (Open point O1.)

- **B22** Given the Team Lead is itself a party to a plan or assignment dispute (for example against the Tech Lead on the handed-over plan), then it does not settle it; it goes to the Manager under the two-round rule.

### US6: The Team Lead role is complete
*As a reader of the Team Lead role file I know what it does and what it sends upward.*

- **B9** Given `manager.md` in M and L, then it no longer lists Developer spawning, health checks of the pod or task routing; it still sizes, spawns the pod leads, settles non-plan disputes, talks to the PO, merges on the PO's request, closes and runs the Token Coach. Its merge step reads each task's passed sha and checkers from the summary or task files, not from messages. Its cost rules (read summaries, not transcripts) stay true.
- **B10** Given the Team Lead role file, then it states: Sonnet/medium; duties (spawn and retire Developers, health checks, routing, plan and assignment disputes, 3-returns triage, roster rows for its agents); and what it sends the Manager and when (B6, B21), each as one line with a pointer to a file.

### US7: The decision lasts
- **B13** Given this scope, then `CONTEXT.md` has the new terms (single contact; Team Lead redefined for M and L; Manager traffic) and an ADR records the decision; each E1 decision (Q1a, Q2 no relay, Q3a, Q4a) traces to a rule above.
- **B14** Given the merged result, then the full suite (`--tz`) passes, `process.md` passes `processlint` and fits its byte budget (23,500 B, raised by the PO), `process-version` is bumped with a snapshot and changelog item (ADR 0005), and the live squad's `process.md` is changed only by the Manager after the PO merges, logged in `process-log.md`.

## Rules to promote (for the Tech Lead's `promote.md`)

- In M and L the Team Lead is the pod's single contact and spawns and retires Developers; S is unchanged.
- The Manager hears only an "Always goes to PO" item, a size-change signal, a non-plan dispute and the iteration-end summary (plus one budget line at 3 returns).
- Nobody relays a blocked pane or permission prompt; each agent's own toast informs the PO.
- The Team Lead settles plan and assignment disputes; the Manager settles the rest.
- The Developer cap holds across a goal even with several Team Leads spawning.

## Open points

| # | Question | Proposed answer | Owner |
|---|---|---|---|
| O1 (settled: Manager FINAL, counts as the budget-overrun escalation in E1 Q3a) | The brief's Budget says the Manager checks in with the PO after 3 returns on a task, but E1 Q3a lists four things only. | The Team Lead triages, then sends one budget line (Plan's "Always goes to PO": budget overrun); the PO's Budget rule stays. Without it the PO would never hear. | Manager (not a goal change; PO sees it in the plan) |
| O2 (settled: Tech Lead decision 4) | Can the Team Lead's settings or `squad-spawn` limit it to the `dev` role? | Yes, enforced in two layers (B4). | Tech Lead |
| O3 (settled: Manager FINAL) | With the Team Lead in M, M and L have the same roles and the same Done rule. Does L remain a size? | Keep L as a signal label ("unclear requirements, many tasks, cross-repo") so goals and `scope.md` stay valid; the Sizes table says roles are the same. If the PO wants L dropped, that is a later scope. | Manager (PO sees it in the plan) |
| O4 (settled: Tech Lead decision 3) | How the cap holds across Team Leads in one goal (B15). | The goal Manager divides the cap in each Team Lead's briefing; the sum of the shares stays at or under the cap; no counter in `squad-spawn`. | Tech Lead |
| O5 (settled: Tech Lead decision 8) | Where the iteration-end summary lives (B18). | `iterations/<n>.summary.md` in the scope folder, at most 40 lines, owner the Team Lead, a row in the Files table of `process.md`. | Tech Lead |
