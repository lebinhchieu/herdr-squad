# 05 Add the touched-text test rule to CLAUDE.md (coach proposal 1)
Status: ready-for-agent
Type: task

Duties: cite [PROMO-5] promotion, [REV-13b] hand-in, [EVID-2d] evidence. Docs-only; change nothing else. Commit this file as `.scratch/coachwait-closelocal/issues/05-claude-md-touched-tests.md`, evidence next to it. Base: `b19c37c` (`--base`).

Edit `CLAUDE.md` -> "Running tests" (repo root): add ONE bullet, same style as its neighbours (must / never / at most; no history, dates or incidents):
"- A Developer whose diff touches `templates/` or text a `bin/` tool prints must, before HANDIN, run `grep -rl '<touched path or changed string>' tests/` and run every hit (goldens included), even test files it did not edit."
Place it after the first bullet. No other line changes. Evidence: `git diff` of CLAUDE.md in evidence.md; run `python3 tests/test_instructions.py`-style tests if one reads CLAUDE.md (`grep -l CLAUDE.md tests/*.py`, run those hits).
Business AC: the bullet is in CLAUDE.md exactly once, one-line diff otherwise empty, tests that read CLAUDE.md pass.
