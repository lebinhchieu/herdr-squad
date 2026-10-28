# Team Lead notes (snapshot)
## Now
- Done+PASS: 01,02,03,05,09,INT1,04,06,07,08,10,11,14; INT2 fed0c95, INT3 90be196, INT4 2175bd2 (code e265fd7, Tech full suite 1667 OK). All Devs retired except dsz-12.
- Live: plugin-dev-dsz-12b (ticket 12 successor, base 17e33cc; predecessor retired at cap). Left: S4 allow-list, AC29, changelog v9, lint baseline G2b, evidence, HANDIN.
- ALL DONE: 13 PASS cf3b5c0, summary written iterations/1.summary.md, dev 13 retired. Manager told. Nothing left; answer events from notes only (COST-13b).
## Open threads
- Tickets live at .scratch/drop-scope-size/issues/ (main copies newest; I edit them as plan owner; Tech's path guard blocks him).
- Ticket 12 AC adds: AC 21 upgrade --check lines; 'ticket 11' grep empty in tests/; legacy_scaffold removal with permanent test; fixtures size keys converted.
- Ticket 11 had 3 returns, LC-7b decided (note in ticket 11 comments), Manager told.
- Plan file iterations/1.md at 80-line cap; trim before adding.
- INT/EVID-2b: INT devs skip QA-review assembly (Tech OK).
- Pinned scopes (<0.6.0) untouched: confirm at check-in.
## Decisions that bind later work
- Dev naming plugin-dev-dsz-<ticket>; spawn: squad-spawn dev NAME --scope drop-scope-size --repo /home/chieule/workspace/squad --base SHA ...; squad-spawn auto-adds roster row (set Owns, edit status via sed/python; check no duplicate row).
- Tech names one final sha per task; QAs verdict on it. Business AC beats technical ruling (REV-7 amendment needed).
- Parallel tickets: give explicit file split in prompts.
## Pointers
iterations/1.md, tasks/tech-design.md, tasks/spec.md, roster.md, squad-ledger, evidence/<NN>/.
