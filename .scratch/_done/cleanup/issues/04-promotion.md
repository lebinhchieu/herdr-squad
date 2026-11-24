# Task 04: Promotion: ADR 0019 + CONTEXT.md/README cleanup

Status: ready
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Team: tech-lead, qa-white, qa-black. Suite: `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` (CLAUDE.md Running tests); full suite by Tech Lead on final sha. Branch from repo HEAD (main) unless noted. Hand in to both QAs. A risk flag or user-visible change found: `BLOCKED <task>`.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`.

Last task. Cite [PROMO-5] (`squad-process rule PROMO-5`): commit `promote.md` into the project docs.

## Touches
`docs/adr/0019-*.md` (new: process history and old-layout migration dropped, repo pruned), `CONTEXT.md`, `README.md`; via `/domain-modeling` per `project.md`. Remove glossary/README text about dropped commands. Branch from the integration of 01-03 passed shas (integration task, [GOAL-6b]: `squad-process rule GOAL-6b`).

## AC
Tech Lead writes promote.md content and AC; QA whitebox checks it ([PROMO-8]).

## Design notes
(Tech Lead, 2026-10-28)

Integration + promotion in one Developer task: merge the passed branches of 02, 03, 01 (that order; 01 is already stacked on 02) into the Developer's own branch, run the targeted tests, hand in; the Tech Lead runs the full suite `--tz` after ([GOAL-6b], [SUITE-3]). 01 and 02 already removed the README/CONTEXT lines naming dropped commands (their notes), so 04 adds the lasting records and sweeps.

### Touches (confirmed)
New `docs/adr/0019-drop-process-history-and-old-layout-migration.md`; `CONTEXT.md` and `README.md` (glossary/README fixes only where the sweep below finds stale text, via `/domain-modeling`); `$SCOPE_DIR/promote.md` (Tech Lead writes it; Developer commits its content, [PROMO-4]). No code.

### promote.md content (Tech Lead writes it before the Developer starts; one section per target)
1. **ADR 0019** (decision, date 2026-10-28, status accepted): the plugin no longer ships (a) process.md version history v1-v9 and the `squad-process version|check|plan|compose --out|apply --legacy` machinery, `templates/squad/process.md`, snapshots; (b) `squad-migrate` (flat→per-scope, `--scope-to-goal`) and `squad-process adopt`; (c) the tracked `.claude/squad-backups/*`, `.scratch/_done/`, `SETTINGS-NOTES.md`, `handover/`. Why: 0.6.0 left them with no live caller; git history keeps them (cite the merge sha). Consequences: a squad older than 0.6.0 cannot be converted by the plugin (hand-edit `scope.md` to a `team:` line, or start a composed squad with `squad-process scaffold`); legacy `process.md`-only squads keep spawning with plugin rules; `squad-start` JSON has no `process_update`; `--scope-to-goal` is gone. States what it supersedes: ADR 0005 (process versioning) is already superseded by 0016: say 0019 retires the leftover tooling of 0005 without changing 0016; ADR 0004 (layout detection) unchanged. Notes dead pointers (`docs/adr/0011` → `.scratch/squad-plugin-windows/design.md`, bin comments → `.scratch/composed-process/...`) are history now.
2. **CONTEXT.md**: remove/reword terms that describe dropped things (legacy-mode sentence at ~125 mentioning `adopt`; the Process-update/skill entry at ~137 mentioning `adopt`; "Frozen copies ... `history/`" at ~133; `_Avoid_: migration (that word is squad-migrate ...)` at ~138). Keep the **Changelog** term (still read by `upgrade`). No new term unless the sweep finds an undefined one; then note it for `/domain-modeling`, never invent.
3. **README.md**: 0.6.0 paragraph (~27) rewritten to the manual `team:` step; `squad-migrate`, `adopt`, `apply --legacy` rows (~48-49) gone; "Flat squads" bullet (~76) says `squad-start` refuses and nothing converts; file table counts of `bin/` entries correct.

### Technical AC
Common C1-C4 as in task 02 Design notes (C4: edits only the three docs + new ADR).
- D1 `promote.md` ⇄ ADR 0019, CONTEXT.md and README edits match line for line (QA whitebox PROMO-8 compares); nothing in the docs that promote.md does not list; nothing added that this scope did not decide.
- D2 Sweep: `git grep -n "squad-migrate\|squad-process adopt\|squadadopt\|apply --legacy\|process-v[0-9]\|process_update\|templates/squad/process\.md\|history/"` over README.md CONTEXT.md docs/ skills/ agents/ bin/ hooks/ templates/ tests/ CLAUDE.md returns hits only in ADR 0019 (as history), older ADRs (immutable; not edited) and `skills/*/changelog.md` prose.
- D3 ADR numbering: file is 0019, previous is 0018 (`ls docs/adr`); front matter/heading style matches 0018; it names what it overrides (QA: same shape as `test_promotion_0_6_0` ADR check; extend only if a test enumerates ADRs).
- D4 Links in README/CONTEXT/ADR 0019 resolve (path exists or is a git-history reference with a sha); `CONTEXT.md` terms still match `squad-process` real output (`mode` names `composed | legacy | none`).
- D5 Integration: branch contains each passed sha (`git merge-base --is-ancestor` x3 in evidence); `git diff <integration base>..HEAD` shows no change outside the three docs and the ADR beyond what 01-03 delivered; targeted tests for changed files green.
- D6 Tech Lead runs the full suite `--tz` on the final sha; this receipt is the one that goes to the PO ([SUITE-3]).
- Deploy: the PO merges once (02, 03, 01, 04 together). Rollback: git revert of the merge. No data migration.
