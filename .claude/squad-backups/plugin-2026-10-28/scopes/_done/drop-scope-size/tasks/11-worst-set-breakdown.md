# Ticket 11: worst Developer set breakdown

Worst: team tech-lead,qa-black,designer,architect; goal yes; qa light = 5423 B (limit 5120, cut >= 303).

| part | bytes |
|---|---|
| header | 496 |
| LC-25 Advisor when stuck | 283 |
| START-6 Session start | 278 |
| LC-18 Developer work | 257 |
| EVID-2b Assemble evidence | 256 |
| REV-22 Review | 246 |
| START-10 Developer start | 242 |
| COST-5a Developer retires, Manager | 237 |
| REV-14a Diff check | 207 |
| MSG-11a Gaps, Manager | 195 |
| LC-19 Design | 187 |
| CORE-2 Message types | 184 |
| SAFE-11 Scratch directories | 180 |
| SAFE-1a No push, Developer | 169 |
| CORE-6 Rules not attached | 163 |
| SAFE-3 Close what you open | 154 |
| REV-13d Hand in, QA blackbox alone | 152 |
| EVID-2a Behaviour | 151 |
| LC-19c Architecture | 150 |
| MSG-3 Task ID | 135 |
| CORE-1 Task states | 132 |
| SUITE-2a Suites, Developer | 132 |
| REV-22a Review against the architecture | 128 |
| CORE-4 Two rounds | 124 |
| CORE-3 Owners | 109 |
| LC-3a Returned task | 104 |
| LC-20b Done, QAs | 104 |
| CORE-5 Files first | 92 |
| SAFE-4 Stay in your lane | 91 |
| MSG-4a Ask the owner, Manager | 85 |

## Comments
- LC-25 note (3rd FAIL, before HANDIN): Q: how to close QAW F1 (4 missing changelog rows) and F2 (REV-22a duty) within 5120 B. Advice: name the diff in REV-22a, audit every "same duty" row against 90be196, rerun base-vs-branch script after commit, justify START-10 git status drop, evidence-only commit last. Done: REV-22a "to check the diff conforms" (+EVID-2b "After all `PASS`:" for bytes, worst 5117), 7 + 4 changelog rows incl. LC-25/MSG-3/START-10 reasons.
