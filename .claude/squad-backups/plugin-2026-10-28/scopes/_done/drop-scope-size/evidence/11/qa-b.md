# QA blackbox, task 11 (HANDIN cb8888a)

Method: script sweeps all 128 team sets x goal yes/no x qa full/light (512 composes), `squad-process compose dev --home D --plugin-root W --out F`, `wc -c F` (scope.md names `x`, version `0.6.0 abc1234`). `lint` on a sample home.

| AC | Saw | Result |
|---|---|---|
| 24: every team, goal, qa: Developer rules <= 5120 B | 512/512 compose OK; max 5344 B (tech-lead,qa-black,designer,architect); 128 composes = 32 team sets x 4 over 5120. Examples: tech-lead,architect 5126-5128; team-lead,tech-lead,qa-black,architect 5144-5146; all contain architect and/or designer with tech-lead. Dev's own evidence (line 5) says the same: 32 sets over, worst 5423 B in its naming | FAIL |
| Spec line 100: "No new pinned exception" | Task keeps pinned exceptions for those 32 sets (test renamed `..._or_a_pinned_exception`) | FAIL |
| `lint` | empty | PASS |

Findings: F1 AC 24: 32 team sets (all with tech-lead plus designer and/or architect) compose a Developer file over 5120 B. Dev evidence names the blocker (safety.md ticket 14, header in squadcompose, text pinned by tests); either trim or the Tech Lead/PO rules an exception in writing and the business AC 24 is amended (REV-7).

## Re-check, HANDIN 5da365a (after trim)

Method: same sweep script (128 team sets x goal x qa = 512 composes of `dev`, `wc -c`); rule-id lists per role on 6 teams, 90be196 vs 5da365a; `squad-process rule`/`who`; `lint`.

| AC | Saw | Result |
|---|---|---|
| 24: all 128 teams x goal x qa <= 5120 B | 512/512 compose OK, max 5031 B (team-lead,tech-lead,qa-black,designer,architect; goal yes, qa light), 0 over | PASS |
| Spec line 100: no pinned exception | none needed, all under cap | PASS |
| `squad-process rule REV-5a` | prints the rule; Dev file keeps `Parsing another tool's output: [REV-5a]` and the "not in this file" lookup line | PASS |
| Other roles | rule-id lists of manager, team-lead, QAs, ba, tech-lead, designer, architect identical to 90be196 on 6 teams | PASS |
| `lint` | empty | PASS |

Findings: none blocking. Note for Tech Lead/QAW: Developer file on teams with a designer no longer carries EVID-5 ("save one screenshot per screen and state in `img/`", present before) and has no pointer to it; REV-5a is only cited. Duty-keeping is whitebox's call.

## Re-check, HANDIN f86b26b (delta: LC-19b cites EVID-5)

Sweep again: 512/512 compose, max 5031 B, 0 over 5120 (AC 24). All 64 team sets with a designer: Developer file contains `Shots: [EVID-5]` (LC-19b line); `squad-process rule EVID-5` resolves. Rule lists of other roles unchanged from 90be196; `lint` empty. Findings: none. Verdict waits for the Tech Lead's final sha.

## Re-check, final ca53ba7 (delta: REV-22a text, EVID-2b/2a/START-10 wording, changelog rows)

Method: git archive ca53ba7 to scratch; 512-compose sweep of `dev` (128 teams x goal x qa, `wc -c`); rule-id lists f86b26b vs ca53ba7 for 9 roles on 3 team shapes; `squad-process rule REV-22a|EVID-2a|EVID-2b|START-10`; `lint`.

| AC | Saw | Result |
|---|---|---|
| 24: Developer rules <= 5120 B | 512/512 compose OK, max 5038 B (team-lead,tech-lead,qa-black,designer,architect; goal yes, qa light), 0 over | PASS |
| REV-22a text | "Give the review subagent `$SCOPE_DIR/architecture.md` to check the diff conforms."; present in the composed Tech Lead file | PASS |
| EVID-2b / EVID-2a / START-10 | EVID-2b starts "After all `PASS`:"; EVID-2a, START-10 read cleanly; composed Dev file lists EVID-2a EVID-2b START-10 | PASS |
| Designer shape | Dev file keeps `Shots: [EVID-5]` | PASS |
| Rule lists, other roles | identical f86b26b vs ca53ba7 on 3 team shapes | PASS |
| `lint` | exit 0, empty | PASS |

Findings: none.
