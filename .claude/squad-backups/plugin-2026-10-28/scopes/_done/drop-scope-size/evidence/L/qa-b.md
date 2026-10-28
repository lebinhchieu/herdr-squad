# QA blackbox, step L (live Manager run on 59e2741)

Method: read the scratch squad `/tmp/dsz-live/sq` (3 scopes: escalations.md, inbox.jsonl, scope.md, iterations/1.md, messages.jsonl) and re-ran the gates myself on a COPY (`/tmp/tmp.d3gmRCkZgw/p/.claude/squads/sq`) with the build `/tmp/dsz-live/tree` (`SQUAD_DIR`, `SQUAD_PLUGIN_DIR`; `squad-spawn --dry-run`, `squad-team --home <scope> --plugin-root tree`). The Manager's own tree/squad was not touched.

| AC | What I did / saw | Result |
|---|---|---|
| 1 | open-q: ONE inbox item (E2; E1 withdrawn "wrong model defaults, replaced"), table has a row for each of BA, Tech Lead, Team Lead, QA whitebox, QA blackbox, Designer, Architect with pick, signal, model/effort; "Developers: cap 3 ... Advisor: on (opus)"; `grep -rniw size` on the whole scratch squad: 0 hits; nothing spawned before the answer | PASS |
| 2 | screen: Designer yes, signal "new screen: report filter (date-range picker)" | PASS |
| 3 | open-q: Architect yes, "irreversible choice likely: data model change (new stored table)" | PASS |
| 4 | fix: BA, Tech Lead, Team Lead, QA whitebox, QA blackbox, Designer, Architect all no, each with a reason; QA blackbox "no observable change"; QA whitebox "all five out conditions hold: at most 2 tasks, one repo, no user-visible change, no risk flag, existing tests cover it" | PASS |
| 5 | open-q: Tech Lead yes ("risk flag: breaking contract change") and QA whitebox yes; PO reply "drop tech-lead and architect"; `team: ba, team-lead, qa-white, qa-black`; iterations/1.md Log "Team override: PO removed tech-lead despite breaking-contract flag; PO also removed architect" | PASS |
| 6 | open-q `scope.md`: `team:` = confirmed roles, no `size:`, `design:`, `architecture:`, `qa-b:` line, tokens `qa-white`/`qa-black`. My `squad-spawn architect` rc 1 "role architect is not on the team ... (team: ba, team-lead, qa-white, qa-black)"; `tech-lead` rc 1 same; `qa-whitebox`, `qa-blackbox`, `ba`, `team-lead` rc 0 | PASS |
| 31 | screen: proposal qa-white+qa-black+designer, PO "add architect, drop qa-white" -> `team: qa-black, designer, architect`; spawn: architect/designer/qa-blackbox rc 0, qa-whitebox/tech-lead/ba/team-lead rc 1. open-q equals proposal minus the two dropped roles. No duplicates | PASS |
| 16 (a) | fix: `team:` includes `ba`; my `squad-team add ba` on a team without it: `duty business-ac: ticket -> ba`, `duty doubt-owner: manager -> ba`, `spawn: ba`, `respawn: manager, qa-blackbox, designer, architect` | PASS |
| 16 (b) | iterations/1.md `## Handover` has Decided, Built, Open | PASS |
| 16 (c) | messages.jsonl STATUS to the BA: "Start from iterations/1.md ## Handover (decided, built, open)" | PASS |
| 16 (d) | `squad-team add` prints the duties that move and the roles to respawn (above); Log says manager, ba, dev respawned | PASS |
| 16 (e) | Log has a line for each change (ba, qa-black, designer add/remove) | PASS |
| 16 (f) | Round 2: scratch `fix` inbox now has item R1 "fix: iteration 1 check-in" (`add`, kind read, blocks none) whose body names the team change: ba added, qa-black added, designer added with the PO's yes and removed at the boundary, team now ba, qa-black, Handover in iterations/1.md. 0 whole-word "size" in the squad | PASS |
| 17 | `squad-team add designer` rc 2 "waits for the PO's yes; ask the PO, then add --po-ok", team unchanged; `add architect` same; `add designer --po-ok` rc 0 | PASS |
| 19 | `squad-team remove designer` rc 2 "only at an iteration boundary with the PO's OK; then add --at-boundary", team unchanged; with `--at-boundary` rc 0 "retire: designer", team drops it. Designer holds no duty, so no owner to name; `remove qa-black --at-boundary` on open-q (copy) prints `duty behaviour-check: qa-black -> qa-white`, `duty ui-check: qa-black -> manager`. The fix Handover does not name any new duty owner (no duty moved on the designer removal) | PASS (vacuous for the designer) |
| 18 | Handover Open names `evidence/01/qa-b.md` as due before close; rules attached: CLOSE-1 (close only when every checker on the team passed every task), SIZE-17d (QA blackbox tests everything already built). The review file itself does not exist and cannot be written here: scratch ticket 01 has no branch, build or app (`/tmp/dsz-live/proj-fix` absent). Not testable end to end | rules+pointer verified, build-side proven by suite (TL FINAL L: sufficient for the live step) |
| 29 | Proposal text (3 items), scope.md x3, escalations.md, iterations, messages, `squad-team`/`squad-spawn` outputs: 0 whole-word "size" | PASS |

Findings:
- F1 AC 16(f) (closed in round 2, PASS): no check-in inbox item in the run. Manager to add it with `squad-inbox add --kind read` (mentions "team changed: ba, qa-black added") and I re-check only that.
- F2 (minor, = Manager's F1) `squad-spawn` refusal for tech-lead, qa-whitebox, team-lead, ba ends "only the PO adds the designer or architect": wrong for those roles (the Manager adds them itself via `squad-team add`).
- F3 AC 18: closed by TL FINAL L (pointer plus CLOSE-1/SIZE-17d suffice; scratch has no build). F2 folded into 13 (Tech FINAL).

Verdict step L: PASS (AC 1-6, 16, 17, 18 as ruled, 19, 29, 31).
