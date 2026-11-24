# Task 19: cost.md overlaps and unclear words

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Also run tests/test_windows_safe.py, tests/test_utf8_helpers.py, tests/test_instructions.py (SQ-10) and quote the result in `## Behaviour`. Source: `.claude/squads/plugin/goals/process-fixes/answers/respawn-rules-review.md`. No version bump in this task.

Status: handed in
Source: finding 7 (Chieu E17 a).
Files: templates/squad/process/cost.md, tests/test_rules_wording.py, upgrade fixtures only if a test needs them (grep `tests/` for COST-9, COST-1, COST-8b). A deleted rule may need the project's way of recording a removed rule (see tests/fixtures/upgrade/*/_removed.md); follow what `squad-process lint` and the tests require.
Ticket: commit this file's content as `.scratch/process-fixes/issues/19-cost-overlaps.md` in your first commit.
Base: the task 18 sha (same branch). No merge into main.

## AC
- AC1 COST-9 (Idle) is deleted. Nothing else in the template or the code points at it as a live rule (grep).
- AC2 COST-1 (the cost hook) is merged into COST-3: one rule says "when a Stop-hook message says a cost rule fired, or at your line, after a compaction: write notes, then `squad-respawn`". COST-1's roles (ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect) still get it through COST-3 (COST-3 already covers them). The "limits are absolute tokens, never a percent" sentence is kept in COST-3.
- AC3 COST-8b says: after a PO wait longer than 1h, write notes and respawn at the next quiet point (not "at any context length"; COST-8 already says respawn on a cache expiry). The `CACHE_TTL_S` pointer stays.
- AC4 COST-3 no longer says "on a new task" alone: it says what it means for a role that lives one session per scope (start fresh when the PO's wait or a new ticket makes the old context useless), or drops the phrase if QA whitebox and the Developer agree it adds nothing; the decision is written in the design notes.
- AC5 `squad-process lint` passes before and after; the existing wording and upgrade tests pass (extend them, never skip one).

## Design notes
Touched files: templates/squad/process/cost.md, _removed.md, notes.md (pointer [COST-1] -> [COST-3]), tests/test_rules_wording.py. Upgrade fixtures are frozen old data: not edited.
- COST-1 and COST-9 deleted; both recorded in `_removed.md` as "removed in v13" (changelog top is v12; the v13 entry rides task 20, TA4), `replaced_by: COST-3`.
- COST-3 carries "never a percent", the Stop-hook trigger, the compaction trigger and `squad-respawn`; kept under the 60-word lint limit (57 words).
- "On a new task" decision (AC4): replaced by "when a new ticket or PO wait makes old context useless" (what it means for a role that lives one session per scope). No bare "new task".
- COST-8b: "at the next quiet point (a merge, a close, or no role building)" instead of "at any context length"; the `CACHE_TTL_S` pointer stays.
- I agree with TA1-TA6 as written.

## Technical AC (QA whitebox, coarse on purpose; Developer may propose changes in the design notes, 2 exchanges max)
- TA1 Removed rules are recorded: `templates/squad/process/_removed.md` gets `## COST-9 (removed in v13)` and `## COST-1 (removed in v13)` with `why:` and `replaced_by: COST-3` (use the next version number as the file's other entries do). `squad-process lint` passes before and after (quote both in `## Behaviour`).
- TA2 No live pointer to a removed rule: `grep -rnE 'COST-9|COST-1\b' templates bin hooks agents skills README.md CONTEXT.md docs` shows only `_removed.md` and `skills/*/changelog.md`. Known hit: `templates/squad/process/notes.md:21` says `[COST-1]`; point it at `[COST-3]`. List `.claude/squads/*/process.local.md` hits of the two IDs in `## Behaviour` (report, do not edit them).
- TA3 COST-3 keeps its `roles:` line (all 8 roles) and carries: "absolute tokens, never a percent", the Stop-hook message trigger, the compaction trigger, `squad-respawn`. One wording test in tests/test_rules_wording.py checks those four on a composed role (not 8 roles x 4 strings).
- TA4 COST-8b: has `1h`, `CACHE_TTL_S`, "next quiet point", and no longer "at any context length"; the two existing asserts (test_rules_wording.py:228-229) still pass unchanged or are updated, never removed.
- TA5 "On a new task" decision (AC4) is in the design notes in one line. Whichever way, the composed COST-3 has no bare "new task".
- TA6 Run: tests/test_rules_wording.py, tests/test_processlint.py, tests/test_instructions.py, tests/test_old_language_inventory.py, tests/test_windows_safe.py, tests/test_utf8_helpers.py, plus every `grep -rl` hit for COST-1, COST-9, COST-8b (the frozen `tests/fixtures/upgrade/*/cost.md` copies are old test data, do not edit them). The changelog entry is NOT in this task (task 20, see its TA4).

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 COST-9 deleted, no live pointer | `test_cost_3_carries_the_cost_hook_and_cost_1_and_9_are_gone` (no `## COST-9 ` in a composed role); grep below | `cd tests && python3 -m unittest test_rules_wording` |
| AC2 COST-1 merged into COST-3 (hook trigger, compaction, `squad-respawn`, "never a percent"; `_removed.md` entries) | same test (4 strings in COST-3 of a composed qa-whitebox, `_removed.md` regex for COST-1 and COST-9) | same |
| AC3 COST-8b: "next quiet point", no "at any context length", `CACHE_TTL_S` kept | `test_bundle_long_wait_and_experiment_rules` (old two asserts kept, three added) | same |
| AC4 no bare "new task" in COST-3 | same new test (`assertNotIn("new task")`) | same |
| AC5 lint before and after; wording and upgrade tests pass | `bin/squad-process lint --plugin-root . --squad-dir $SQUAD_DIR`; test_processlint, test_squadupgrade, test_squadrules | see Behaviour |

