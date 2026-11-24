# Evidence: 17 Promotion: ADR 0036 and what must outlive the scope

## Behaviour

Base `08095ba` (09-16 merged). Code commits: `c1cd47e` (ADR 0036), `72cbfad` (ADR text corrected after review). Only file changed outside this folder: `docs/adr/0036-task-ids-evidence-folder-no-qa-checkers.md`.

**AC1 ADR 0036 exists, three decisions with Why, number unused**
```
$ for b in $(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes); do git ls-tree --name-only $b docs/adr/ | grep -c '/0036'; done
refs checked: 366, refs with a 0036 file: 0   (before the commit)
$ git ls-tree --name-only main docs/adr/ | tail -2
docs/adr/0034-handin-evidence-gate-blocks.md
docs/adr/0035-routine-gates-go-ahead.md
```
The ADR has `# 0036: ...`, `Status:`, `## Context`, `## Decision` (task-id grammar; evidence-only rule; no-QA checkers by `team:` tokens; rejected options), `## Consequences`, the form of 0034/0035.

**AC2 each item of promote.md and the file it went to**
| promote.md item | File |
|---|---|
| Rules ITER-19, LC-9c, START-19c (check only) | `templates/squad/process/iterations.md:151`, `lifecycle.md:106`, `starting.md:195`: present |
| ADR 0020: 01 line and 07 amendment (check only) | `docs/adr/0020-*.md`: "main beats a draft; a branch already merged into main is ignored", `origin`, "Amendment (ticket 07, Preview)" `img=1&base=` present |
| `docs/inbox-body-guide.md` bare-ID refusal (check only) | `docs/inbox-body-guide.md:61` present |
| Changelog v31, plugin 0.11.0 (check only) | `skills/squad-process-update/changelog.md:16` `## v31`; plugin.json now 0.11.1 (0.11.0 shipped, then 15 bumped) |
| CONTEXT.md terms Origin tag, Plan fields, Plan line, Bare ID, Routine gate (iteration 2) | `CONTEXT.md:264-280`: present, nothing to add |
| ADR 0035 (iteration 2) | `docs/adr/0035-routine-gates-go-ahead.md`: present on main |
| ADR 0036 (iteration 3 target) | `docs/adr/0036-task-ids-evidence-folder-no-qa-checkers.md`: new, this ticket |
| Follow-ups (not tickets now) | Included in ADR 0036 `## Consequences`, last bullet |

**AC3 no glossary term in iteration 3**: `promote.md` says "No `CONTEXT.md` term from this iteration"; `git diff --name-only 08095ba HEAD -- CONTEXT.md` prints nothing.

**AC4 whole-repo files** (foreground, `< /dev/null`, `python3 -m unittest discover -s tests -p <file>`):
```
test_instructions   Ran 16 tests  OK  (re-run after the 72cbfad edit: OK)
test_windows_safe   Ran 14 tests  OK
test_utf8_helpers   Ran 14 tests  OK
```
`grep -rl --exclude-dir=__pycache__ 'docs/adr' tests/` has no hit: no other test reads the ADR directory.

## Review

Fresh-context reviewer (sonnet, high) on `c1cd47e`, Standards and Spec. Standards: form matches 0034/0035; number and file name right; no non-ASCII, tabs or links. Spec: grammar, `from_message`, bash copy, table test (`tests/test_squad_spawn.py:984`), no-QA `checkers`/`slots`, `[evidence=PASS]` and the NUM_FILE/_draft_text/squadreport_tasks/ticket_text follow-ups verified. Findings fixed in `72cbfad`: (1) the jq filter in `squad-log-message` accepts rule ids too (superset, not a copy), (2) the evidence-only rule: the `.md` check holds for `<stem>/` only, `.evidence/` is accepted without it, and the board's `_evidence_only` is narrower, (3) the unsupported "no byte headroom" clause was dropped. Not checked by the reviewer: `squadboard_files` and the spawn-event fallback claims (taken from the Tech Lead's promote.md).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `git ls-tree` over 366 refs: 0 hits for `0036`; ADR file has the 0034 form | - | - |
| AC2 | table in `## Behaviour`: every promote.md item mapped to a file | - | - |
| AC3 | `git diff --name-only 08095ba HEAD -- CONTEXT.md` empty | - | - |
| AC4 | test_instructions 16, test_windows_safe 14, test_utf8_helpers 14: OK | - | - |

## Changelog line

None: ticket 17 adds a project doc only. why: the ADR records decisions that later work builds on; no plugin file changed.
