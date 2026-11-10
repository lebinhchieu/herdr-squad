# Improvement ideas (Fable advisor, call 2, asked for in chat by Chieu)

Evidence: process-log (12 overlay rules), 5 Coach backlogs, `bin/` tool list, the 12 findings in `review-findings.md`.
Not checked: tool source, hooks, role cards. Every tool idea starts with a check of what exists (`--help`). A saving is a number only where `squad-usage` / `squad-report` show it; otherwise the metric is named.
Type: **rule** (templates), **tool** (`bin/`, hooks), **card** (`agents/`, needs Chieu's OK). Size: S/M/L.
Areas: C communication, X shared context, T tokens, Q quality, W working time.

| # | Idea | Area | Type | Size |
|---|---|---|---|---|
| 1 | `squad-spawn --task NN` builds the first prompt from the task file, `duties:`, `roster.md` | C, T, Q | tool | M |
| 2 | One check table per ticket (AC, how checked, Dev, QA-w, QA-b); replaces SQ-2 trace | Q, C | rule + tool | M |
| 3 | One merge-check command (GOAL-7, MRG-2, MRG-5, SQ-6, SQ-7) | Q, W | tool | M |
| 4 | Smaller attached rules: drop the index, phase rules printed by the tool that starts the phase | T, X | tool | M |
| 5 | Bundle 2-3 small tickets (each at most 2 files): one Developer, one HANDIN, one QA pass, one verdict line per ticket | T, W | rule | S |
| 6 | Review pack per HANDIN: AC, diff stat, hunks, test commands, evidence path (blackbox copy has no code) | T, Q | tool | M |
| 7 | Standing approvals in the brief (Chieu ticks what needs no ask, e.g. full suite on the final sha) | W | rule | S |
| 8 | Fresh Manager after a long wait when the cache expired, not only above the respawn line | T | rule | S |
| 9 | Task hook wakes the plan owner on `passed`, 3rd return, `blocked` | W, C | tool | M |
| 10 | Rule changes are experiments: each overlay rule names its metric; no change in 2 scopes -> remove | Q, T | rule | S |
| 11 | `squad-report` phase breakdown: turns and tokens per ticket by phase | T, W | tool | M |

## Detail

1. **Spawn builds the prompt.** Evidence: a Manager's first Developer prompt named the wrong HANDIN target (Coach backlog); SPAWN-3, SPAWN-6, SIZE-6c are hand-copying. Check first: what `--task` injects today. Risk: low.
2. **One check table.** Evidence: 4 AC breaks found only by final QAs (po-inbox-tui); 8 of 16 findings accepted with no fix. Columns name commands, not code, so QA blackbox stays blind (SAFE-10). Needs agreement with SQ-2.
3. **Merge-check command.** Evidence: SQ-6 / SQ-7 were added after sibling branches went untested together and main moved unchecked. Check `squad-merge-record` first.
4. **Smaller attached rules.** Evidence: the Manager took about half of one goal's cache-read (watchdog2). Only move rules that a tool can print at the right moment (merge, close, Coach).
5. **Bundle small tickets.** Evidence: 14-18 turns per ticket even on small ones (Coach backlog); a version bump took its own Developer (18 turns). Not SQ-9: both QAs still check. Risk: one FAIL holds the bundle. Fits this scope's wording tickets.
6. **Review pack.** Evidence: final-check QAs ended at 207k and 179k reading 4 tickets (po-inbox-tui backlog).
7. **Standing approvals.** Evidence: this scope had 5 inbox items before any spawn. Risk: less control; it is Chieu's choice.
8. **Fresh Manager after a long wait.** Evidence: 2 cache expiries at 89k while waiting on Chieu (Coach backlog). COST-9 acts only above the respawn line. Verify the cache lifetime first.
9. **Events wake the plan owner.** Evidence: 144 Manager turns in one scope (watchdog2). Check `squad-watchdog` first.
10. **Experiments.** Evidence: 12 overlay rules, all `upstream: proposed`; the log shows one removal.
11. **Phase breakdown.** The Coach may not read transcripts, so nobody knows where the 14-18 turns go. Its number decides ideas 5 and 6.

## Not proposed (already rejected)
SQ-9 one checker for text-only tickets; "TL/QA fresh only above 60k".
