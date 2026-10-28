# QA blackbox, task 01 (sha d5a4b9c; branch head d2c2d00 = evidence-only)

Ticket 01 is engine vocabulary: no new user-visible command or output. My check = no behaviour change for users, and lint clean. No UI, no screenshots.

| What | What I did | What I saw | Result |
|---|---|---|---|
| Lint | `python3 bin/squad-process lint` on the branch | prints `ok`, exit 0 | PASS |
| Composed rules unchanged, this scope (size L, qa-b yes) | `squad-process compose <role> --home <scope>` for manager, dev, qa-blackbox, qa-whitebox, tech-lead, team-lead, ba on base 2949573 and on the branch; diff ignoring the plugin/composed header lines | all 7 identical, exit 0 | PASS |
| Composed rules unchanged, other shapes | scratch `scope.md` copies: S; M+design; M+architecture; L with qa-b no; M+design+architecture; compose manager, dev, qa-whitebox on base and branch | all 15 identical, exit 0 | PASS |
| `squad-process who SIZE-22` | ran on branch | still prints S/M/L acts/aware lines as before | PASS |

Not observable yet (later tickets, not 01): AC 1-8, 9 (`duties:` line absent from composed Manager rules, as expected before ticket 02/04), 11 overlay rejection, 12-15, 16-31. AC 10 and 24 come from the suite receipt.
