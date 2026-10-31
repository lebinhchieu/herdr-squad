# Evidence: 10b Prune the five R1 rules-wording test files

## Behaviour

Tests only; no change in `bin/ templates/ agents/ skills/ docs/`. Code sha: `fe7c3df` (base `e24f306`).

217 tests became 113 in the five files. Each removed test has a row in `removed.tsv` (rule, reason, surviving test). Report, kept-net table and mutation proof: `prune-report.md`.

| AC | Result |
|---|---|
| 1 Linux per file | OK for the five and for processlint, process_citations, instructions, pod_rules_process (`after-linux.txt`). No new skip: `git diff e24f306 -- tests \| grep '^+.*skip'` is empty. |
| 2 Mutation | 3 roles (dev, tech-lead, designer) fail the net test; a duty change fails the duty sweep (`mutation.txt`). |
| 3 Counts | before 217, removed 103 methods, added 1: now 113. |
| 4 Files | `removed.tsv` (104 rows), `prune-report.md`, copy in `$SCOPE_DIR/evidence/10b/`. |
| 5 No product change | `git diff --name-only e24f306 -- bin templates agents skills docs` is empty. |
| 6 Windows | per-file OK, same as base (`after-windows.txt`). |
| 8 Suite | not run (PO hold). |
