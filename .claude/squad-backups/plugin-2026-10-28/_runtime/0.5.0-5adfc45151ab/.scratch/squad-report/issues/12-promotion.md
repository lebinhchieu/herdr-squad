Status: ready-for-agent
Type: task
Task ID: 12
Touches: `CONTEXT.md`, `docs/adr/0012-squad-report-derives-from-transcripts.md` (new), `README.md`
Does not touch: code, tests, `project.md` (Manager's), `process.md`
Harness: doc checks (link loop, `git grep`) plus `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_templates test_instructions` if they read `README.md`/`CONTEXT.md`
Blocked by: 11 passed

# 12: Promotion: glossary, ADR 0012, README

**Done when the lasting facts of this scope are in the repo's docs with exactly the wording in `$SCOPE_DIR/promote.md`.** This is the scope's promotion task (`process.md` → Promotion): copy the wording, do not reword. Edit through `/domain-modeling` as `project.md` requires. Ride on the integration branch (11's final sha).

## What
1. `CONTEXT.md`: the glossary terms in `promote.md` (Bucket, Digest, Attribution layer, and the BA terms Elapsed, Agent-time, Parallelism, etc. listed in `spec.md` → Business → Terms) under a heading that exists or a new `squad-report` section; no existing term changes.
2. `docs/adr/0012-squad-report-derives-from-transcripts.md`: the ADR block of `promote.md` verbatim, `Status: accepted (squad-report)`, sections as the other ADRs (title, `Status:`, `**Decision:**`, `**Why:**`, `**Consequences:**`). Check the number is still free (`ls docs/adr`); take the next one otherwise and fix `promote.md`'s references.
3. `README.md`: `squad-report` command and `/squad:squad-report`, `/squad:squad-report-analyze` named once, with one example and where the output lands (`<scope>/report/`, local, git-ignored).
4. Technical rules block of `promote.md` to the file it names (CLAUDE.md or the ADR) as written.

## Technical AC
1. `git diff --stat` shows only the files above.
2. Every relative link in `CONTEXT.md`, `README.md`, `docs/adr/*.md` and every `/squad:<skill>` name resolves (loop output in `dev-evidence.md`); every `promote.md` item is found by `git grep` (listed).
3. ADR 0012 contradicts no earlier ADR; ADR 0009 (stream removed) is cited as the reason for "no new hook".
4. Primary behaviour only (qa: light).
