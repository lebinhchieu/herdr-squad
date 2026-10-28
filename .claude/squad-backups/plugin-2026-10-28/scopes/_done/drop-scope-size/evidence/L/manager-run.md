# Step L: Manager side (live run, scratch squad)

Build: clone of main at 59e2741 (12 final, `tree` at /tmp/dsz-live/tree; evidence-only 17b88b9 not needed). Scratch squad: /tmp/dsz-live/sq (scopes open-q, screen, fix; stub: `squad-spawn --dry-run`, real `squad-inbox`, `squad-team`, `squad-process`). Manager rules composed from the build: /tmp/dsz-live/mgr.md (SIZE-1 table, SIZE-13, SIZE-16). Run with `--plugin-root /tmp/dsz-live/tree` (its plugin.json still says 0.5.2 until task 13).

| Brief | Scope | Proposal (inbox item, escalations.md) | PO reply (scripted) | Recorded |
|---|---|---|---|---|
| open question + risk flag + data model | open-q | all 7 roles, BA/TL/Team Lead/QAW/QAB/Architect yes, Designer no; models; no "size" | "drop tech-lead and architect" | `team: ba, team-lead, qa-white, qa-black`; iterations/1.md Log has "Team override: PO removed tech-lead despite breaking-contract flag"; `squad-spawn architect`, `tech-lead` exit 1 "not on the team"; `qa-whitebox`, `ba` pass (AC 1, 5, 6) |
| new screen | screen | Designer yes, signal "new screen: report filter"; QAB yes (Designer on team); BA/Tech/Team Lead/Architect no | "add architect, drop qa-white" | `team: qa-black, designer, architect`; `qa-whitebox` exit 1, `architect`, `designer` pass (AC 2, 31) |
| one-line fix | fix | all six optional roles no with reasons ("no observable change" for QAB; QAW no because the five out conditions hold) | "keep" | `team: none`; dev passes, `qa-blackbox` exit 1 (AC 4) |

Mid-scope (fix): `squad-team add designer` exit 2 without `--po-ok` (AC 17); `add ba` (doubt-owner manager -> ba; spawn ba; respawn manager), `add qa-black` (behaviour-check, ui-check, handin-target change; respawn manager, ba, dev), `add designer --po-ok`, `remove designer` exit 2 without `--at-boundary`, then removed with it (AC 16a, 19). Handover (decided/built/open), Log lines, check-in note and the BA briefing are in `scopes/fix/iterations/1.md` and `scopes/fix/messages.jsonl` (AC 16 b, c, e, f). AC 18: Handover Open names evidence/01/qa-b.md (QAB writes the review file; not simulated by the Manager).

Findings for the Tech Lead:
- F1 The spawn refusal for a non-design role ends "only the PO adds the designer or architect" (tech-lead, qa-whitebox, qa-blackbox): misleading.
- F2 `squad-team` and the gate read `plugin.json` 0.5.2 against pin 0.6.0 until task 13; harmless here.
- F3 The Manager proposal rules say nothing about how a Manager records an inbox reply into `team:` beyond "edit `scope.md`" (worked, no command).
