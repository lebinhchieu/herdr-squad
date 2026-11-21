# 01 ADR 0030 and CONTEXT terms

## Behaviour
Docs only; no code, no tests. ADR 0030 added; one `Amended by 0030` line in each of 0010, 0018, 0022, 0028; CONTEXT.md gets **Coordinator** and **Plan owner** (retired) and its Manager, Team Lead, Single point of contact, Manager traffic, Tech Lead, Team, Token Coach and Watchdog entries match. SQ-10 not triggered (no `bin/` or printed text).

## Review
AC trace (the table is in `checks.md`, same folder):
- AC1 | docs/adr/0030-team-lead-always.md | `grep -n '^## ' docs/adr/0030-*.md`
- AC2 | docs/adr/0010, 0018, 0022, 0028 | `git diff a3a44d8 -- docs/adr`
- AC3 | tickets 02-06, promote.md | read
- AC4 | CONTEXT.md | `git diff a3a44d8 -- CONTEXT.md`
- AC5 | CONTEXT.md, ADR 0030 | `grep -n -e plan-owner -e "plan owner" CONTEXT.md docs/adr/0030-*.md`
- AC6 | tests/ | `grep -rl -e CONTEXT.md -e docs/adr tests/`: only a fixture text, no test reads the files
