# Evidence: 09 09 Merge main into the 08 branch (SQ-7b)

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `git diff 932420a 4e7d547 --name-only` = `CONTEXT.md`; `git diff --check` clean; `git log -1 --format=%P` = 932420a 7fc9119 | `git diff 932420a 4e7d547 --name-only`: CONTEXT.md only, 8 added lines; cited rules REV-17, LC-21, LC-22a, LC-22b exist; no test reads CONTEXT.md (qa-w.md, sha 4e7d547) | - (no QA blackbox on 09, Manager DECISION 08) |

## Developer

### Developer, ticket 09, merge sha 4e7d547

- Merged main 7fc9119 into 932420a: no conflict. `git diff 932420a 4e7d547 --name-only` = CONTEXT.md only (8 insertions); `git diff --check` clean.
- Targeted check: `grep -rl CONTEXT.md tests/` hits only `tests/fixtures/board/t28/04.md` (unrelated fixture). No full suite (CONTEXT.md only). Stray `bin/__pycache__` removed.
- QA blackbox: none on 09 (only QA whitebox checks it, Manager DECISION 08).
- Follow-up from QA whitebox (not a FAIL, text from main's 7fc9119, not this merge): the Follow-up entry reads as if LC-22b batching were general; it holds only when `qa: light`.

## qa-w

### QA whitebox, task 09, sha 4e7d547

Verdict: PASS.

#### Checked (task file tasks/09.md)
- `git log -1 --format=%P 4e7d547` = 932420a 7fc9119: a merge of main (7fc9119) into the 08 branch tip 932420a.
- `git diff 932420a 4e7d547 --name-only`: `CONTEXT.md` only (8 added lines: Finding and Follow-up glossary entries). `git diff --check` clean.
- Content: every rule the entries cite exists: REV-17 (review.md:162), LC-21, LC-22a, LC-22b (lifecycle.md:224-238); the term **Return** exists in CONTEXT.md. No plugin file, test or bin touched, so no suite applies. `grep -rl CONTEXT.md tests/` hits only `tests/fixtures/board/t28/04.md` (a fixture, unrelated).

#### Follow-up (not FAIL)
- Follow-up entry says a follow-up is "batched by the Team Lead into one last, droppable ticket (LC-22b)". LC-22b has `when: qa = light`, so the batching holds only in light mode; the sentence after it names light mode, but the first one reads as general.
