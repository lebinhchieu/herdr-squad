# 12 Promotion: write promote.md into the project docs

Status: ready-for-agent
Blocked by: 11 (passed)

PROMO-4, PROMO-5. Docs only, on the integration branch after 11. Source: `.claude/squads/plugin/scopes/task-claim-gates/promote.md` (exact wording; read it first). Edit the docs as `project.md` says (`docs/adr/`, `CONTEXT.md`).

Files: `docs/adr/0021-task-state-events.md` (new, section 1 of promote.md), `CONTEXT.md` (section 2: **Done** becomes **Passed**, new **Merged** and **Task event**, **Ready for review** removed (entry and the relation line 384), the Task line fixed).

Technical AC:
1. ADR text equals promote.md section 1 (fenced block content).
2. `grep -n "Ready for review\|^\*\*Done\*\*" CONTEXT.md` prints nothing; `grep -n "Passed\|Merged\|Task event" CONTEXT.md` shows the new entries. No other CONTEXT.md line changes.
3. The other docs that link the removed entries are checked: `grep -rn "Ready for review" docs README.md CLAUDE.md` prints nothing.
4. Tests: run any test file that reads `CONTEXT.md` or `docs/adr/` (`grep -rl "CONTEXT.md\|docs/adr" tests/`); targeted only.
5. `squad-evidence check` on this ticket's evidence folder passes.

Reviewers: QA whitebox (PROMO-8). The Tech Lead and the BA read the wording.
