| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `head -3 docs/adr/0030-team-lead-always.md; grep -n '^## ' docs/adr/0030-*.md` → title, Status, Context/Decision/Consequences/Alternatives rejected | | |
| AC2 | `git diff a3a44d8 -- docs/adr/0010* 0018* 0022* 0028*` → 1 added `Amended by 0030` line each, nothing else | | |
| AC3 | read of tickets 02-06: every ADR claim is in 03/04 (one-variant rules), 02 (key, token, squad-team), 05 (defaults), 06 (watchdog); promote.md limit recorded | | |
| AC4 | `git diff a3a44d8 -- CONTEXT.md`: Coordinator + Plan owner (retired) added; Manager, Team Lead, Single point of contact, Manager traffic, Tech Lead, Team, Token Coach, Watchdog edited | | |
| AC5 | `grep -n -e plan-owner -e "plan owner" CONTEXT.md docs/adr/0030-*.md` → retired entry (CONTEXT 27-28) and ADR Context/Decision history only | | |
| AC6 | `grep -rl -e CONTEXT.md -e docs/adr tests/` → only tests/fixtures/board/t28/04.md (a fixture text, not read as doc); no test reads touched files | | |
