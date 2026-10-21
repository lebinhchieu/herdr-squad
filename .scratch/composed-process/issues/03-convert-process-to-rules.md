Status: ready-for-agent
Type: task
Task ID: 03
Touches: `templates/squad/process/*.md` (new: core, files, starting, sizes, goal, promotion, closing, messages, who, lifecycle, review, evidence, iterations, cost, notes, safety, suites, merge, spawning), `templates/squad/process/_removed.md` (new), `skills/squad-process-update/changelog.md` (v7 entry), `tests/test_process_conversion.py` (new), this ticket's evidence folder (`mapping.md`)
Does not touch: `templates/squad/process.md` (kept for squads not yet migrated; retired in 09), `agents/*` (06 deletes the moved text), any `bin/` file
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_process_conversion test_squadrules`
Blocked by: 02

# 03: Convert the process into ID-tagged rule files (content v7)

**Done when every rule of v6, of the live squad's Coach changes and of the process text inside role cards lives in exactly one rule block, `mapping.md` accounts for every source line, and lint passes.**

## Sources, all of them
1. `templates/squad/process.md` (v6): every bullet, table row and paragraph.
2. The live squad's accepted Coach and Manager changes not in v6: `.claude/squads/plugin/process-log.md` rows dated 2026-10-16 to 2026-10-19 that are not `v<N>` migration rows. Take wording from the live `.claude/squads/plugin/process.md` where the rule is present. **Two rules are missing there and must be restored from the log's Change column:** row 48 (Tech Lead writes `style-contract.md` for a scope with a UI mock; UI AC cite it; QA lists all style findings per sha in one return) and row 49 (QA whitebox never asserts presentational values the mock fixes; QA blackbox owns them).
3. Process text inside `agents/*.md`: Start-of-session steps, handoff and routing duties, cost-rule reactions, roster editing recipe. These become rules targeted at that role. Identity and stance stay in the card (06).

## Rules for the conversion
- No meaning change except the fixes listed here; wording may be tightened by the Writing rule.
- Split every "(S: …)", "In M and L …" clause into variants (`-7a` / `-7b`) with `when:`.
- Fixes (review 2026-10-20, finding 4):
  - (a) HANDIN goes to the Tech Lead in S and to both QAs in M and L.
  - (b) In S the Tech Lead tells the Manager which tasks are ready in parallel. This duty is currently only in `manager.md:27`.
  - (c) A business doubt the Designer raises goes to the Manager as an `ASK`. The Tech Lead never hand-writes `escalations.md` (ADR 0007).
  - (d) Drop "The label shape is in process.md"; `squad-label` owns it.
  - (e) Token Coach rules sit in `iterations.md`; nothing cites a "Retro" section.
- Duplicates collapse into one rule: "two real samples" (process, qa-whitebox, tech-lead); the roster write recipe (manager, team-lead); the cost-rule reaction (7 cards); the start boilerplate (9 cards).
- `core.md` stays at or under 40 lines: task states, message types, the who-owns-what table in short form, the two-round rule, files-are-truth.
- The v7 changelog entry is machine-readable, as ticket 07 defines. Until 07 lands, list added IDs and the source of each.

## Technical AC
1. `squad-process lint` exits 0 on `templates/squad/process/`.
2. `mapping.md` has one row per source line: `source (file:line or log row) → rule ID`, or `dropped: duplicate of <ID>`, or `stays in card: identity/stance`. `test_process_conversion.py` checks that every non-blank, non-heading line of v6 and every log row from source 2 appears in it.
3. Rows 48 and 49 map to rule IDs (finding 1).
4. Evidence lists, per role and size (S, M, L), the composed byte size and rule count. Use a plain filter script over 03's output if 04 has not merged; otherwise use `squad-process compose`.
5. No rule text contains "(S:" or "In M and L"; `grep` output goes in the evidence.
6. A BA-style rule audit (the refine-process precedent) is a checker duty: QA whitebox walks `mapping.md` against the sources, and the finding list is in `qa-w.md`.
