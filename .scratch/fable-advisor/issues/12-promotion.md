# 12: Promotion and version bump (PROMO-4/5, SQ-5)
Status: ready-for-agent (after 11 passes)
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=tech-lead, promote-owner=tech-lead. Test economy: targeted tests only; full suite only after Chieu's yes via the Manager. Cite [PROMO-4], [SIZE-24b].
Lane: Developer plugin-dev-fable-w (own branch, tip = the passed 11 sha)
Files: `CONTEXT.md`, `docs/adr/0023-phase-rules.md`, `docs/adr/0024-check-table-lives-in-scope-evidence.md`, `docs/adr/0025-developer-rule-byte-cap.md`, `README.md` (`bin/` table), `skills/squad-process-update/changelog.md`, `.claude-plugin/plugin.json` (version only), the ticket files and evidence. No code, no tests, no rule text.
Source: `$SCOPE_DIR/promote.md` (the only promote file; the Tech Lead owns it).

## Business AC
1. Every entry of `promote.md` is committed to the file it names, with the wording given. A `<fill>` is replaced by a value read from the final tip (`git diff 9b05952..HEAD -- templates/squad/process`, `grep LIMIT tests/test_dev_rules_size.py`), never guessed. Nothing from "Follow-ups" becomes a doc.
2. ADR files follow `docs/adr/0022-*.md`: title `# NNNN: <sentence>`, `Status: accepted`, `## Context`, `## Decision`, `## Consequences`; numbers 0023-0025 (docs/adr ends at 0022 on the base).
3. Plugin version bump 0.7.7 -> 0.8.0 (new tools and rules). The base is 0.7.7 (main, commit 5febd45), not 0.7.5: 0.7.5 is only this scope's pin. The changelog block is `## v12` with the first line "Plugin 0.8.0."
4. `squad-process lint` exit 0 and the ticket evidence of 12 follows [EVID-1].

## Design notes (Tech Lead)
- Read the check table, phase rule and review-pack terms against `CONTEXT.md` first; add only what is missing ("passed" exists, add the one sentence only).
- Write the ADRs from `promote.md` items 1-3 plus the facts in `tasks/09-check-table.md` and `tasks/10-smaller-attached-rules.md` (design notes); do not invent consequences.
- The glossary uses "the PO", never "Chieu".
- The only place the plugin version is written is `.claude-plugin/plugin.json` (`grep -rIn '0\.7\.7'` over the repo, excluding `.git`, `.worktrees`, `.scratch`, finds only it). If a second place appears after the merge, change it too and say so.
- Deploy (LC-13): docs and one version string; order: merge 12 last; the Manager re-pins to 0.8.0 and then removes SQ-2 from `process.local.md` (WHO-6). Rollback: revert the merge; the pin of old squads stays valid.

## Technical AC (Tech Lead; QA whitebox checks)
- T1. `grep -c "<fill>"` over the committed docs is 0 (`grep -rn "<fill>" CONTEXT.md docs/adr README.md skills/squad-process-update/changelog.md`, quote it).
- T2. Every figure in an ADR is checked against the tip: LIMIT value, the count and IDs of the phase rules (`grep -n "^phase:" templates/squad/process/*.md`), the index lines (compose Manager and Tech Lead, count). Quote each command. A number that differs from `promote.md` is correct if the tip says so; note it in evidence.
- T3. Version: `grep -n '"version"' .claude-plugin/plugin.json` shows 0.8.0; `grep -rIn '0\.7\.7' --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=.scratch --exclude-dir=__pycache__ .` prints nothing (quote both). The changelog block says 0.8.0.
- T4. Diff scope: `git diff <11 sha>..HEAD --stat` lists only the Files above. Any `bin/`, `templates/` or `tests/` change is a FAIL.
- T5. Every README row names a tool that exists (`ls bin/<tool>`) and its usage matches `--help` (quote one `--help` per new tool).
- T6. Targeted tests: `grep -rl "CONTEXT.md\|changelog\|plugin.json\|docs/adr" tests/` hits, run them (a test may read the version or the changelog); `squad-process lint`.
- T7. ADR/CONTEXT wording follows the repo's style and the reply rules for chat do not apply; no mention of "Chieu" in `CONTEXT.md` or ADRs (the PO is "the PO").
Evidence: `## Behaviour` = the grep and test commands above with output; `## Review` = the diff stat.
