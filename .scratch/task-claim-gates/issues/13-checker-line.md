# 13 Checker line: say who decides with no checker

Status: ready-for-agent
Blocked by: 12 (passed)

PROMO-8 re-check of the diff. Docs only. One line: `CONTEXT.md` line 89 (Checker entry), last sentence becomes "With none on the team the HANDIN evidence check (squad-evidence check) decides; no role confirms."

Files: `CONTEXT.md`.

Technical AC:
1. `git diff 07c4876` changes only that line.
2. `grep -n "code-check owner" CONTEXT.md` prints nothing.
3. Test files that read CONTEXT.md pass (fixture t28/04.md: tests/test_squadboard_tasks.py).
