Status: resolved
State: done
Task ID: BRD-07
Blocked by: none
Files touched: `templates/squad/process.md` (one rule, nothing else)

# BRD-07: process rule: typed messages name their task ID

**Done when the plugin's process template says that BLOCKED, HANDIN, PASS, FAIL and STATUS messages name their task ID, in one added line.**

Read first: spec story 68 and "Squad wiring", `templates/squad/process.md` → Messages section. Independent of every other ticket; any Developer may take it.

## Build

- Add one bullet under the Messages table in `templates/squad/process.md`, next to "**Short.**" and friends. Meaning: `BLOCKED`, `HANDIN`, `PASS`, `FAIL` and `STATUS` messages name their task ID right after the type (`FAIL SET-01: …`), so the squad board can derive task state. Match the file's style: bold lead word, one sentence.
- **Do not edit** `squad/process.md` (the Manager's live copy), the examples table, or anything else. The Manager decides whether to mirror the rule into the live file.

## Technical AC (BRD-07)

1. **Diff:** the one added rule line plus the one changed STATUS example line (AC3, widened 2026-10-12) in `templates/squad/process.md`; one file, nothing else.
2. **Rule text** names all five types and says the ID follows the type.
3. **Existing examples stay consistent:** `STATUS: building SET-01, …` in the Messages table has no ID right after the type. The Developer reports this to tech-board in the HANDIN (do not change the example; tech-board decides). Nothing else in the file contradicts the new rule.
4. **Suite:** `python3 -m unittest discover -s tests` still green. No new test (a doc rule is checked by reading the diff).
5. **Evidence:** `dev-evidence.md` with the diff and the test run.

### QA whitebox additions (qaw-board)
Q1. **Exact diff:** `git diff --stat main...HEAD` (or the Developer's base) shows `templates/squad/process.md | 1 +` and nothing else; `git diff` has no whitespace-only changes and the file keeps its trailing newline and line endings.
Q2. **Rule vs the types table:** the new line must not contradict the `STATUS` row (`STATUS: building SET-01, …` has the ID after `building`, not right after the type) — the Developer reports it, tech-board decides, I pass only after tech-board's DECISION is on file (comment below).
Q3. **Does not weaken the hook contract:** the hook finds the ID anywhere with `\b[A-Z][A-Z0-9]*-[0-9]+\b`, so the rule's example ID uses that shape (`FAIL SET-01: …`), and says ASK/ANSWER/DECISION may omit it.
Q4. **Live copy:** `squad/process.md` is untouched by this branch (it is outside the worktree anyway).

## Comments
- 2026-10-12 tech-board: dev-board-2 handed in 3c39dbd. Decision: change the STATUS example to `STATUS SET-01: building, 60%, no blockers` in a second commit; AC1 widened.
- 2026-10-12 tech-board: PASS by qaw-board (c63b5ba on squad/dev-board-2, with 3c39dbd). State set to done; awaiting PO merge.
