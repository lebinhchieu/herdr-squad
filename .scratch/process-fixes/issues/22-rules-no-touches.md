# Task 22: rule text and docs without touches

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"; templates/ changes include goldens). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Also run tests/test_windows_safe.py, tests/test_utf8_helpers.py, tests/test_instructions.py (SQ-10) and quote the result in `## Behaviour`. Chieu wants `touches` gone: "I do not need it". No version bump in this task (SQ-5).

Status: ready (after 21; same worktree)
Files: templates/squad/process/starting.md (START-3 step 2, START-19 wording), templates/squad/process/goal.md (GOAL-1), templates/squad/process/files.md (FILE-6), skills/squad-start/SKILL.md, README.md, CONTEXT.md, tests/test_templates.py and every `grep -rl` hit (upgrade fixtures and goldens included).
Ticket: commit this file's content as `.scratch/process-fixes/issues/22-rules-no-touches.md` in your first commit.
Base: the task 21 sha (same branch). No merge into main.

## AC
- AC1 START-3: the "Overlap" step is removed and the remaining steps are renumbered; no rule cites "step 2". Other rules cite START-3 only by id (grep `\[START-3`).
- AC2 GOAL-1: the `squad-start` command line has no `--touches`; the paragraph about `--yes` for an overlap is gone.
- AC3 FILE-6 `scope.md` row no longer lists `touches:`. START-19 and the START-2 text keep "what each depends on", and drop "what it touches" only where it meant the touches line (the Developers' design notes keep their own touched-files wording).
- AC4 Docs: SKILL.md, README and CONTEXT have no `touches` / overlap wording left that describes the removed feature (grep; list what is left and why in `## Behaviour`).
- AC5 `squad-process lint` passes before and after; wording, template and upgrade tests pass (a changed golden is regenerated with the project's way, never skipped).

## Design notes
Touched files: templates/squad/process/{starting,goal,files}.md, skills/squad-start/SKILL.md, README.md, tests/test_templates.py. CONTEXT.md: no change (its only `touches` hits, lines 209 and 227, are the verb in other senses).
- Agree with QA whitebox T1-T6. Not edited: cost.md, bin/squad-usage-hook, plugin.json, changelog (SQ-5). Other `touches` wordings (starting.md:17,19,201, lifecycle, sizes, merge, suites) stay.
- START-3: step 2 removed, the old step 3 is now step 2. No rule cites a step number of START-3 (grep).
- GOAL-1: `--touches <paths>` removed from the command; the `--yes` overlap bullet removed (`--yes` is gone from squad-start since task 21).
- SKILL.md (beyond the AC list): step 4 also asked the user for "what repos or paths the work touches ... for `--touches`"; that sentence is removed too, as is the "Exit 3 = overlap" bullet and `--touches` in the command.
- Left on purpose: README.md:55 `--yes` (it is `squad-process upgrade --yes`).
- Test: one test in test_templates.py (no `--touches` or overlap wording in the five files, START-3 has two steps, FILE-6 has no `touches:`). No golden or upgrade fixture mentions the changed text (grep over tests/).


## Technical AC (QA whitebox; Developer: reply in Design notes if you disagree, 2 rounds, LC-4/CORE-4)
Facts from my grep of main 7d4b71d: `touches` as the removed feature sits in `starting.md:50` (START-3 step 2) and `:194` (START-19); `goal.md:8-9` (GOAL-1, the `--touches` line and the `--yes` line); `files.md:76` (FILE-6); `SKILL.md:20,24` (command and "Exit 3 = overlap"); `README.md:45`. All other `touches` hits are other senses and stay: `starting.md:17,19,201`, `lifecycle.md:50,57,127,134`, `suites.md`, `sizes.md:113`, `merge.md:18`, `cost.md:47,54` (cost.md is the respawn-words scope's file: do not edit), CONTEXT.md:209,227, `squadteam.py:64`, `squadinbox.py:781`.
- T1 START-3 has two steps ("Manager reads the brief..." becomes 2). `grep -rn 'START-3\b' templates skills README.md CONTEXT.md` shows only citations by id, none saying "step 2" or "step 3". START-3b is untouched.
- T2 GOAL-1: the command line has no `--touches`; the `--yes` overlap bullet is gone; the rest of the rule is unchanged. `grep -rn -- '--yes\|--touches' templates skills README.md CONTEXT.md` has no hit about overlap.
- T3 FILE-6 row for `scope.md` has no `touches:`. START-19 goal-Manager bullet keeps "what each depends on" and drops "and what it touches". START-2 text, `starting.md:17,19,201` and the lifecycle lines are not edited.
- T4 SKILL.md: command line has no `--touches`; the "Exit 3 = overlap" bullet is gone and the remaining steps read right (the "Any other error" bullet stays). README:45 drops the overlap check and `--touches`. CONTEXT has no wording for the removed feature (grep `touches\|overlap`; list what remains and why in `## Behaviour`).
- T5 `squad-process lint` passes before and after (quote both). `grep -rl` of each changed string over `tests/`: run every hit (expect `test_templates.py`, `test_processlint.py`, `test_instructions.py`, any rule-text golden or upgrade fixture); a golden that changes is regenerated the project's way, none skipped. Plus the three SQ-10 files. No full suite.
- T6 Scope check: `git diff --stat <task 21 sha>..HEAD` touches no file outside the Files line; not `cost.md`, `bin/squad-usage-hook`, `plugin.json`, `CHANGELOG`/`changelog.md` (version and changelog ride respawn-words task 20, SQ-5; Manager: say if `processlint` demands a changelog line for changed rule text, I found no such test).

## Review
| AC | Test | How run |
|---|---|---|
| AC1 | tests/test_templates.py `test_no_rule_or_doc_describes_the_removed_touches_option` (START-3 steps are 1, 2) | `cd tests && python3 -m unittest test_templates`; `grep -rn 'START-3\b' templates skills README.md CONTEXT.md` |
| AC2 | same test (no `--touches` in goal.md) | same |
| AC3 | same test (FILE-6 row); `git diff bd83778 -- templates/squad/process/starting.md` for START-19 | same |
| AC4 | same test for SKILL.md and README.md; CONTEXT.md untouched, grep list in evidence.md | `grep -rn -i 'touches\|overlap' skills/squad-start README.md CONTEXT.md` |
| AC5 | `python3 bin/squad-process lint` (exit 0 before and after); wording, template, upgrade tests | see evidence.md |
