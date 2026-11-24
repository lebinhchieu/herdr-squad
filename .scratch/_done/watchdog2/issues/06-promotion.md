# Task 06: promotion of goal watchdog2, plus two small follow-ups of 05

Duties: design notes: Developer (here); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: QA whitebox writes `goals/watchdog2/promote.md` (PROMO-6), you commit it; full suite: QA whitebox, once on the final sha, only after Chieu says yes through the Manager. A risk flag, user-visible change or business doubt: `BLOCKED 06`.

Status: ready
Source: `goals/watchdog2/promote.md` (QA whitebox writes it; wait for it, do not invent content), `goals/watchdog2/shared/decisions.md`, the QA follow-ups in `scopes/wd2-pane/evidence/05/qa-w.md`. Rules to follow: PROMO-5 and CLAUDE.md "Domain docs": glossary to `CONTEXT.md` and decisions to `docs/adr/NNNN-<slug>.md` via the `/domain-modeling` skill.
Files: `README.md`, `CONTEXT.md`, `docs/adr/0022-*.md` (new), `tests/test_squad_start.py`, `bin/squad-watchdog` (docstring only).
Ticket: commit this file's content as `.scratch/watchdog2/issues/06-promotion.md` in your first commit.
Base: the task 05 passed sha 651f5c5 (branch `squad/plugin/wd2-pane/plugin-dev-wd2-pane-1`); reuse its worktree (no parallel task). Repo: /home/chieule/workspace/squad.

## AC
- AC1 The README `bin/squad-watchdog` row says the new sleep rule (sleep on: once, when nobody on this machine works for N minutes, whatever the tickets say; the log names the reason), the name `sleep-when-idle`, the watchdog tab (own herdr tab labelled `watchdog`, one per home (scope or goal), detached fallback), as `promote.md` words it. A new README row names `bin/squad-away-hook` ("I am away" / "I am back", the `away` file, rule ITER-17).
- AC2 `CONTEXT.md` gets the glossary terms `promote.md` lists, in the file's style (a term not in the glossary stays out).
- AC3 One short ADR `docs/adr/0022-<slug>.md` (Context, Decision, Consequences, like 0021) for "idle for any reason" and away mode. It states nothing the goal did not decide.
- AC4 Every claim in the new text matches the code on this branch (QA checks with `grep`); no mention of Sleep-when-done as the name.
- AC5 Follow-up 1 of 05: in `tests/test_squad_start.py` move `WatchdogTabTest` above the `if __name__ == "__main__"` guard; the file run directly runs it.
- AC6 Follow-up 2 of 05: the `bin/squad-watchdog` docstring sentence that lost an "or"/comma reads correctly. Docstring only.
- AC7 No version bump (done by wd2-bump), no other file. After the PASS the Manager adds `promoted: <date> <commit>` to `goal.md`.

## Technical AC (QA whitebox, agreed with the Developer in this file)
- T1 Run `tests/test_squad_start.py` as a file and by `unittest`; both show the same test count. Targeted: `tests/test_squad_watchdog.py` and every hit of `grep -rl 'README' tests/` and `grep -rl 'CONTEXT.md' tests/`; none skipped. No full suite without Chieu's yes.
- T2 The ADR number 0022 is free on main (`ls docs/adr`); the index file, if any, lists it.
- T3 README line lengths and table shape: each row stays one table row (no stray `|`).

## Design notes (Developer fills in)

## Rules to follow
- SQ-2: `## Review` starts with an AC trace.
- Do not bump the plugin version.
