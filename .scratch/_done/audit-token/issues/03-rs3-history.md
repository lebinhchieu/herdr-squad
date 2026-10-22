# 03 RS-3 evidence from history (AT-01b)

Status: wontfix (history too small: Sonnet arm 1 scope; see Comments)
Blocked by: 01 (passed, def08da)
Owner: a new Developer (dev-1 is retired), if the Manager accepts; start from `audit.py` at the AT-01 passed commit ad3b4c7
Output: `.scratch/audit-token/rs3-history.md`, `.scratch/audit-token/scripts/rs3.py`

AT-01 found no real fix: two are above 2% but have no RS-3 evidence (driver 5 manager Opus to Sonnet, driver 2 QA `effort: medium`). **Scope after QAW's check:** driver 2 (QA `effort: medium`) has no history contrast (tech-lead, qa-whitebox, qa-blackbox and ba ran `high` on every message, audit.md [D5]; dev medium vs high is not QA), so it is dropped from this ticket and ends "no history, unproven by construction" (H6; QAB's H6b stays as the rule for any future measure). Driver 5 (manager model) is the only driver compared, and its only Sonnet scopes are partly Sonnet ([D4b]), so "unproven (n too small)" is the likely outcome. Compare QA returns per task in past scopes under each manager model, name the confounds and the sample size. No new model runs. Reads `scopes/**/messages.jsonl` and the AT-01 data, read-only.

**"Unproven" is an expected outcome.** The Developer must not stretch the rule to get a verdict.

## Business AC
BA's rule: business-ac.md, "RS-3 evidence from history". Weak evidence is "unproven", not "real". The PO decides role-model changes either way.

## Technical AC
- **H1 Rule first.** Before any number is computed, commit `rs3-rule.md`: what counts as a QA return (the message type and format in `messages.jsonl`, e.g. lines starting `FAIL <task>:`), the unit (returns per HANDIN, per task) and which confounds must be balanced. Tech Lead's numbers, which the Developer may only tighten: a scope is **Opus-manager** at 0% Sonnet manager messages, **Sonnet-manager** at 50% or more, and **mixed** in between (not counted); minimum **3 scopes and 10 HANDINs per arm**. If an arm has n=0 the report says "cannot compare" and the verdict is "unproven". A partly-Sonnet scope is never reassigned to fill an arm. Git order shows the rule before the result.
- **H1b Minimum n.** `rs3-rule.md` states the minimum number of scopes and tasks per arm as numbers, before any result. The report states n per arm after dropping mixed scopes. If either arm is below the minimum the verdict is "unproven (n too small)" with the n. The rule is never edited after the numbers; a change is a new commit with its reason.
- **H2 Real samples first, with field shape.** Parse `messages.jsonl` of two scopes by hand before trusting a pattern (one with FAILs, one with none: the constant case). Count the HANDIN and FAIL lines in each; the report states the format of the lines and the counts, no message text. It also states the field shape: the `type`, `from`, `to`, `task` fields used, whether lines are deduped by `msg_id`, whether a HANDIN resent after a FAIL is a new HANDIN, and that a message to a non-QA role (e.g. a Manager ASK to a QA) is not a return. These choices are fixed in `rs3-rule.md` (H1), not discovered afterwards.
- **H3 Setting per scope.** Manager model share per scope comes from AT-01's role-and-model data (D4b), not from `agents/*.md` today. Arms and the mixed label follow the H1 rule.
- **H4 Per-task table.** For each scope: size (S/M/L from `scope.md`), tasks, HANDINs, FAILs, returns per HANDIN, total $ (from AT-01), manager model, QA effort. Arms are compared with counts and the spread, no p-value theatre. The QA effort column is constant `high` in every scope: context only, not an arm. State n per arm.
- **H4b Cost side (driver 5).** The table adds respawns per scope and manager messages per task (RS-2 cost side), not only FAILs and $.
- **H4c FAIL counting.** QA whitebox and QA blackbox FAILs are counted separately. `rs3-rule.md` says whether a task returned twice counts once or twice (per return).
- **H5 Confounds.** Name them: scope size, task type, date (rules changed over time: Token Coach 2026-10-12, absolute limits 2026-10-14), who managed, test flakiness (board-flakes). Say which the data lets you separate and which not.
- **H6b Driver 2 metric validity.** QA returns per HANDIN is not a quality measure when QA is the thing changed (a weaker QA returns fewer FAILs). Driver 2 can reach "real" only with a downstream measure too: defects found after a QA PASS (later fix commits on the same task, PO findings, a next-scope return). If no such measure exists in the data, driver 2 ends "unproven" and the report says why.
- **H6 Verdict per driver.** Driver 5 ends "real" only if H1's rule passes (n per arm at or above the minimum), else "unproven" with the reason in one line. Driver 2 is "no history, unproven by construction" with D5's one line as the reason. Net cost of any extra returns is added to RS-2 as in AT-01 T7.
- **H7 Re-run.** `rs3.py` is read-only, `python3 -I`, takes `--until` like `audit.py`, and gives the same numbers on a re-run. Numbers in `rs3-history.md` equal `rs3.py` output on re-run, and each FAIL and HANDIN count is cross-checked with an independent grep. Per-scope total $ is read from AT-01's data at ad3b4c7, not recomputed with another price table. Evidence as in AT-01 T9 (base sha, command, `git diff --stat` only under `.scratch/audit-token/`, five numbers with their source lines).
- **H8 Privacy.** Ids, counts and paths only.

## Comments

- 2026-10-16 Tech Lead: QAB OK on the fairness rule with four additions (H1b, H4b, H4c, H6b), added above.
- 2026-10-16 Tech Lead: QAW's four points added: driver 2 dropped (no history contrast), partly-Sonnet rule and numeric minimum n in H1, field-shape check in H2, cross-check and AT-01 $ source in H7. H6b kept for the dropped driver as the rule for a future measure.
- 2026-10-16 Tech Lead: dropped on the Manager's FINAL; counted read-only before spending a Dev. Manager Sonnet share from audit-tables.md D4b at ad3b4c7: po-inbox 58/107 = 54% (Sonnet arm, 50 HANDINs, 30 FAILs), add-ui-ux-design 32/78 = 41% (mixed, 3 HANDINs), 0% Sonnet: board-flakes 16 HANDINs, refine-process 19, squad-tabs 29 (Opus arm, 3 scopes, 64 HANDINs; board, generic-rules, guide have no manager messages). HANDIN and FAIL counts: `type` field over `scopes/**/messages.jsonl`, deduped by msg_id, no text read. Sonnet arm is 1 scope, under the 3-scope minimum.
