# 02: process rules for the goals file, the pass message to the plan owner, the Team Lead card; version bump

Duties: design notes dev; technical AC qa-white (with dev); business AC ticket; code check qa-white; behaviour check qa-black; promote.md qa-white; full suite qa-white (targeted tests by default).
Files: templates/squad/process/starting.md, templates/squad/process/files.md, templates/squad/process/messages.md, templates/squad/process/lifecycle.md, agents/team-lead.md, skills/squad-process-update/changelog.md, .claude-plugin/plugin.json, docs/adr/0028-watchdog-follows-goals-file.md, tests (hits of grep)

Owner: Developer (design notes in this file). Depends on: 03 (passed; start from its branch, reuse its worktree). Last ticket touching plugin files: carries the version bump ([SQ-5]). Role-facing text: Chieu approves at check-in.
Ticket file the Developer commits: `.scratch/watchdog-should/issues/02-process-goals-and-pass-message.md` (copy this into it).

## Why
03 makes the watchdog read `<home>/goals.md`. Nothing in the rules says who writes it or when. Separately: [LC-20b] says "tell the plan owner" with no message type; `agents/team-lead.md` says its context fills with HANDIN/PASS/FAIL copies while [MSG-19] says it is not copied.

## Technical AC
1. Rule (Manager, in `starting.md` or `files.md`, one rule stated once): the Manager alone writes `goals.md` ([FILE-6] row added). It adds a row, status `in progress`, when Chieu asks for something (at [START-19] from the brief, and on each later request in chat); sets `done` when every task of that goal has passed; sets `blocked` + reason + inbox item id only when nothing else can go on and Chieu must act, and also writes the inbox item ([ITER-4]). It runs `squad-watchdog ensure` after writing a new goal. Columns exactly as in tasks/03.md.
2. [START-19] (scope and goal Manager) writes the first goal row from the brief.
3. [LC-20a/20b/20e]: the Developer tells the plan owner with `STATUS NN: passed <sha>` (one line); no new message type. [MSG-6]: Team Lead tells the Manager one line when a goal is done or blocked ([MSG-6] list gains this item). Never a per-ticket pass.
4. `agents/team-lead.md`: the "copies" sentence matches [MSG-19] (it reads `squad-ledger`, is not copied).
5. `changelog.md` gets a v18 entry in the existing format (added, changed, why); plugin version `0.9.5` in `.claude-plugin/plugin.json`; `grep -rn '0\.9\.4' .claude-plugin skills bin templates agents` shows no stale hit outside history/changelog/ADRs.
6. ADR `docs/adr/0028-watchdog-follows-goals-file.md`: goals file replaces the ticket-based wake for idle; supersedes the wake text of ADR 0022; short (at most 30 lines).
7. Rules stay within their byte caps; `squad-process lint` passes before and after; no rule mentions a date or an incident.
8. [SQ-10]: run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` plus every hit of `grep -rl '<changed rule id or string>' tests/` and quote results in `## Behaviour`.
9. `evidence.md` `## Checks` has no `\|`; `squad-evidence checks <evidence.md>` exits 0 before HANDIN; `## Review` starts with the AC trace ([SQ-2]).

## Manager notes
- SQ-15 dry run on the base (03's passed sha) before the first spawn; golden tests that print rule text may need updates, name them in `## Review`.
- Tests of rule text: no new test file; extend `tests/test_instructions.py` only for a real regression risk.

## Technical AC added by QA whitebox (base 1861e6d checked; agree with the Developer here)
10. Developer byte cap: `python3 -I -m unittest discover -s tests -p test_dev_rules_size.py` passes. On the base the largest composed Developer rules are 5573 B against LIMIT 5580 (7 B headroom), and [LC-20a/20b/20e] are Developer rules. Net change to those three must be zero or smaller (reword, do not add); raising LIMIT needs a Manager ruling and an amendment note in ADR 0025, not a silent edit. (The uncommitted tree seen at my first look already fails 4 tests of that file.)
11. AC1 "columns exactly as in tasks/03.md": that file is not in the worktree; the source is the `bin/squad-watchdog` docstring: `| # | Goal | Status | Reason | Updated |`, Status `in progress`, `done` or `blocked`. The rule must say the same and no more (the reader takes any other word as `in progress`).
12. The new Manager rule has `roles: manager` and a topic; `squad-process who <ID>` shows only Manager (and no Developer compose grows). Hits to run besides AC8: `tests/test_rules_contract.py`, `tests/test_sizes.py`, `tests/test_small_files_equivalence.py`, `tests/test_dev_rules_size.py`, `tests/test_processlint.py`, `tests/test_rules_wording.py`.
13. AC6 ADR: the text of ADR 0022 that is superseded is its reason list for the sleep (`all tickets passed`, `team idle with open tickets`, line 9); name that line. ADR 0022 has no passed-wake text.
14. `STATUS NN: passed <sha>` in LC-20: use the same wording in all three rules; [MSG-6] new item names "goal done or blocked", not a ticket pass.
