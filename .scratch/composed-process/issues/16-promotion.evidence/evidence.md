# Evidence: 16 Promotion

## Tech Lead review

### Tech Lead review 16: FAIL on 89ba7eb, PASS on 0b8f1e4 (1 finding, my wording error)

Sha 89ba7eb on squad/plugin/integrate-promote/plugin-dev-ip-3 (base 17fc41f). Diff read line by line against goals/composed-process/promote.md.

#### Finding (README.md line 47, `bin/squad-process` row)
1. `upstream` does not write: `bin/squadupgrade.py` `cmd_upstream` (l.482-505) only prints the overlay's `upstream: proposed` operations. promote.md row 6 said "read-only except ... `adopt` and `upstream`"; that was my mistake, the Developer applied it as written. Required text: "(read-only except `upgrade --apply --yes` and `adopt`; `upstream` prints the proposed operations; `apply --legacy` is the old v6 merge)".
2. `upgrade --check|--apply` inside a table cell: the `|` splits the cell even in a code span. Write `upgrade --check\|--apply`.

#### Checked and OK
- ADR 0016 Status + Block A bullets and table, 0005, 0006, 0008, 0010: verbatim to rows 1-5; no other body line removed (0008: only the named Decision sentence and first Consequences bullet).
- README: other changed lines 21, 28/ layers row, 32, 44, 50 and `## The process` (1 paragraph) as Block B; no other line changed.
- CONTEXT.md: all Block C terms once at line start (count 1 each; `Legacy mode` shares the Composed mode line as Block C wrote it); Process version/Section view absent from CONTEXT, README, ADR 0016; Block D entries and Block E lines as written; `grep` for old S/M wording prints nothing; Opus appears in ADR 0016 only on the advisor line.
- Flag 1 (lowercase "process version" in Plugin pin `_Avoid_`) accepted: it is the avoided word. Flag 3 accepted: `adopt` verbatim-only and `qa: light` proposal are both in the plugin (LC-21 / squadupgrade). Flag 4: Block A (Sonnet) is right; I fix decisions.md line 25.
- Diff touches only the Touches files. Lint rc 0 and the Dev's tests are doc-only relevant.

Fix: only README.md line 47 (plus the Dev's evidence if it quotes the line). Then re-HANDIN; I re-check just that line.

#### Re-check 0b8f1e4
Diff 89ba7eb..0b8f1e4 = README.md line 47 only: `upstream` removed from the read-only exceptions and described as printing; pipe escaped. Lint rc 0. PASS.
