# 01 ADR 0030 and CONTEXT terms

## Behaviour
Docs only; no code, no tests. ADR 0030 added; one `Amended by 0030` line in each of 0010, 0018, 0022, 0028; CONTEXT.md gets **Coordinator** and **Plan owner** (retired) and its Manager, Team Lead, Single point of contact, Manager traffic, Tech Lead, Team, Token Coach and Watchdog entries match. SQ-10 not triggered (no `bin/` or printed text).

## Review
AC trace (the table is in `checks.md`, same folder):
- AC1 | docs/adr/0030-team-lead-always.md | `grep -n '^## ' docs/adr/0030-*.md`
- AC2 | docs/adr/0010, 0018, 0022, 0028 | `git diff a3a44d8 -- docs/adr`
- AC3 | tickets 02-06, promote.md | read
- AC4 | CONTEXT.md | `git diff a3a44d8 -- CONTEXT.md`
- AC5 | CONTEXT.md, ADR 0030 | `grep -n -e plan-owner -e "plan owner" CONTEXT.md docs/adr/0030-*.md`
- AC6 | tests/ | `grep -rl -e CONTEXT.md -e docs/adr tests/`: only a fixture text, no test reads the files

## QA blackbox

### 01 QA blackbox (sha f40fbff)
Docs only; checked by reading the ADR/CONTEXT text and `git diff a3a44d8..f40fbff -- docs CONTEXT.md`. Live: none possible (no behaviour).

| AC | how | saw | result |
|---|---|---|---|
| AC1 ADR 0030 shape | live: read file | `# 0030: ...`, `Status: accepted (tl-always; Chieu answered E1 on 2026-11-21)`, Context, Decision, Consequences, Alternatives rejected. Rejected = E1 options (b), (c) as in escalations.md row 1 | pass |
| AC2 overrides + 4 amend lines | live: diff | **Overrides** names 0010, 0016, 0018, 0022, 0028 with the sentence each; one `Amended by 0030` line in each of 0010/0018/0022/0028, nothing else changed in them | pass |
| AC3 claims vs tickets 02-06 | live: read tickets | `squad-team` refusal (02 AC5), `upgrade --check` lists old keys (02 AC4), lint file:line (02 AC3), watchdog fallback + goal watchdog (06), defaults opus medium / sonnet low (05); no claim the tickets lack | pass |
| AC4 CONTEXT.md | live: diff | Coordinator added; Plan owner (retired) added; Manager, Team Lead, Single point of contact, Manager traffic, Tech Lead, Team, Token Coach (and Watchdog) edited; none says Team Lead optional or owns the plan | pass |
| AC5 grep | live: grep | plan-owner/plan owner only in the retired entry (CONTEXT:27-28) and ADR Context/Decision history | pass |
| AC6 tests | live: grep | `grep -rl` hit only tests/fixtures/board/t28/04.md (fixture text); evidence says so | pass |

Follow-ups (not AC): CONTEXT **Duty owner** (line 92) still lists "plan" among duties; settle with 02's duty table. 

## QA whitebox

### QA whitebox 01, sha f40fbff
Docs only; read the whole diff (`git diff a3a44d8..f40fbff` for ADR 0030, the four 0010/0018/0022/0028 amendment lines, CONTEXT.md). AC1 shape and sections present; AC2 overrides sentence names 0010, 0016, 0018, 0022, 0028, one `Amended by 0030` line in each of four; AC3 claims checked against tickets 02-06 (always-on team-lead and refusal = 02 AC5, lint file:line = 02 AC3, 31 tombstones = 16 in 03 + 15 in 04, watchdog = 06, defaults = 05, SPAWN-12 = 04, squad-retire closes the pane = bin/squad-retire:26); AC4 terms Coordinator, Plan owner (retired), Manager, Team Lead, Manager traffic, Tech Lead, Team, Token Coach edited; AC5 grep shows only the retired-term entry and the ADR's own history; AC6 `grep -rl` hits only tests/fixtures/board/t28/04.md (fixture text), no test reads the touched files. No code in the diff.
PASS.
#### Follow-ups
- CONTEXT.md **Manager** entry: "The Team Lead spawns and retires the other roles" is wrong against the shipped rules (SPAWN-2b/2c in 04): the Manager spawns `team-lead` and every other role on `team:`; the Team Lead spawns Developers only. Fix wording: "The Team Lead spawns and retires the Developers"; best done in the promotion task (07).
