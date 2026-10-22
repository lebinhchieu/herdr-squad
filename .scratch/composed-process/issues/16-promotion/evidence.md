# 16 Promotion: evidence

Wording applied from the goal's `promote.md` (rows 1-7, Blocks A-E); not copied here. Commits: ticket copy, ADRs (row 1-5), README (row 6), CONTEXT.md (row 7), this file.

## Technical AC

**AC1 terms.** `python3 -I`, count of `^\*\*<term>\*\*` in CONTEXT.md: Rule 1, Rule ID 1, Overlay 1, Composed rules 1, Plugin pin 1, Tombstone 1, Composed mode 1, Failing sha 1 (Process changelog 1, Process update 1). **Legacy mode** is in the line `**Composed mode** / **Legacy mode**:` as Block C writes it, so it is not at a line start (1 occurrence in the file). `Process version` / `Section view`: 0 hits in CONTEXT.md, README.md, ADR 0016 (case-sensitive). **Flag:** Block C's Plugin pin `_Avoid_` line reads "version lock, process version" (lowercase, CONTEXT.md:107), kept as the block gives it; a case-insensitive grep finds it. ADR 0005 keeps its own history words.

**AC2** `grep -n "S (Tech Lead\|(S: Tech Lead\|process-version\|M (+ BA" README.md CONTEXT.md` prints nothing. Block D entries (Size, Risk flag, Done, Manager, BA, Team Lead, Tech Lead, Single point of contact, Manager traffic, QA whitebox/blackbox, Integration task, Token Coach, Promotion, Process changelog, Process update; lines 3 and Squad) applied; Process version and Section view deleted.

**AC3** Statuses: 0016 `accepted (composed-process, PO answers D1–D16 2026-10-21/22)`; 0005 `superseded by 0016 (composed-process)`. 0006, 0008, 0010 carry their amendment lines. "once accepted" wording: gone. Body lines removed: 0005 the "Superseded by 0016 once accepted" line (row 2); 0006 the "Amended by 0016 once accepted" line (row 3); 0008 the last Decision sentence and the first Consequences bullet (row 4); 0010 none.

**AC4** README: `## The process` is 1 paragraph line, before `## The layers`; changed lines: sizes sentence, protocol sentence, `bin/squad-process` row, `bin/processlint.py` row, `templates/squad/` row, Squad row. No other line changed.

**AC5** `grep -n "Opus" CONTEXT.md README.md docs/adr/0016-*.md`: one line, ADR 0016 S Done bullet, advisor on Opus; the review subagent is Sonnet at high effort.

**AC6** `git diff --stat 17fc41f HEAD`: only ticket file, CONTEXT.md, README.md, ADRs 0005/0006/0008/0010/0016 (+ this file). `bin/squad-process lint` exit 0, no findings. `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_templates test_sizes test_process_writing test_instructions`: Ran 81 tests, OK. No full suite.

## AC7: ADR 0016 bullet → source (`decisions.md` line = goal `shared/decisions.md`)

| Bullet | Source |
|---|---|
| Composed mode / legacy / pin refuses / legacy compose / adopt / deploy order | decisions 6, 16, 18, 31 |
| Rule hash, tags, prefix table, pin format | decisions 5 |
| Pinned runtime, `squad-close` prune | decisions 10, 22 (tickets 05, 25) |
| `plugin.pin`, adopt adds `plugin:` | decisions 10, 18 (ticket 09) |
| Upgrade compares hashes; adopt writes only verbatim matches | ticket 07 (`07-upgrade-by-rule-id.md`), promote.md row 22 only; **not independently sourced** (no decisions line says "verbatim") |
| Settings, QA blackbox fails closed | decisions 17 (ticket 08) |
| Rule on demand, S Developer < 5120 B | decisions 15, 30 (ticket 22) |
| Lint pointers, `lint --cards` | decisions 8, 12, 17 |
| Sizes | decisions 24 (ticket 17) |
| Duty owner table | decisions 25, 30, 28; Sonnet review: ticket 32 (decisions 25 still says Opus, superseded by PO 2026-10-22 per promote.md) |
| S Done, advisor, LC-25/26 | decisions 25, 27, 28; tickets 18, 32 |
| Role defaults | decisions 26 (tickets 19, 20) |
| Evidence location, `--base` | decisions 14, 20 (ticket 21) |
| Return = failing sha | decisions 20 |
| Developer retirement, drafts, retro, `qa: light` | decisions 21, 23; `qa: light` proposal: Coach C1 #1 accepted (Manager notes, `scopes/_done/sizes-and-models/iterations/1.coach.md`), **not in decisions.md** |
| Hashes may change; alternatives rejected | decisions 15 (hashes), 21 (size clause forbidden), 9 (cap raise trimmed instead) |

Unsourced items flagged above: the "verbatim matches" clause and the `qa: light` clause (both taken as Block A gives them).

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
