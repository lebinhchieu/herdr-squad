# Notes: plugin-arch-drop-scope-size (architect)

## Now
RETIRED on Manager's order. architecture.md amended for PO E4 (I3, I4), still `Status: final`; ADR draft updated; DECISION sent to Manager, ASK answers sent to Tech Lead. Nothing left to do ([COST-13b]).

## Decisions that bind later work
- Keys: presence `ba, team-lead, tech-lead, qa-white, qa-black, design, architecture`; `team:` tokens and duty values `ba, team-lead, tech-lead, qa-white, qa-black, designer, architect`; role/agent names `qa-whitebox`/`qa-blackbox` stay (`ROLE_KEY` maps).
- No released shim: converter (`squad-process adopt`) is the only reader of `size:`; engine rejects old lines/keys with pointer. No `--from-size`, no brief size hint.
- Pinned scopes (<0.6.0): converter skips; squad-spawn/respawn hand off to `$runtime/bin/...` (Tech Lead D7); my I4 reading: pinned not part of I4 (flagged to Manager).
- Branch-internal scaffold (Tech Lead D1, Manager FINAL) allowed until cutover task; permanent test proves it gone.
- I8 (128 shapes) is the only open PO choice.

## Pointers
- architecture.md (sections 2, 3, 5, 6 constraint 1/5/11, 7, 8), tasks/adr-0018-team-replaces-size.md, tasks/spec.md, tasks/tech-design.md rev 2

## Open threads
- Sent: DECISION to Manager (amendment, conflicts in spec.md lines 50/94/113, tech-design.md lines 10/14/43/AC 65); ANSWER to Tech Lead (4 points). No replies read yet.
- If the PO flips a reading (pinned scopes converted too; `team:` tokens as role names): edit architecture.md §2, §7, §8 and the ADR only; keep section numbers.
