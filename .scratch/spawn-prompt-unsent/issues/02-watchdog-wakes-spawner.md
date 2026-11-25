# 02: watchdog wakes the spawner of an agent that never started

Status: ready-for-agent
Duties: design notes = Developer (## Design notes); technical AC = Developer; business AC = this ticket; code check = Developer's `## Review`, confirmed by the Manager; behaviour check = Manager confirming `## Behaviour`; hand in to the Team Lead; passed = `squad-evidence check` exits 0 (no QA); suite and promote.md = Developer; no full suite without Chieu's yes
Aim: Watchdog wakes the spawner of an unstarted agent
Estimate: 1h 30m
Depends on: 01
Files: bin/squad-watchdog, tests/test_squad_watchdog.py, .claude-plugin/plugin.json, skills/squad-process-update/changelog.md
Test harness: tests/test_squad_watchdog.py (stub herdr)
Ticket path: `.scratch/spawn-prompt-unsent/issues/02-watchdog-wakes-spawner.md` (committed by 01).

## Problem
After 01, a spawn whose agent did not start leaves `roles/<name>.unsent`. If the spawner missed the stdout line, nobody acts; the agent sits idle with its prompt typed.

## Change
| Marker age | Agent status | Watchdog does |
|---|---|---|
| any | working | removes the marker |
| >= 2 min | idle/done | one message to the spawner (marker name, else the Team Lead, else the Manager), names the agent and `herdr agent send-keys <name> Enter` |
| any | blocked | nothing (Chieu's to answer) |
| agent gone/retired | - | removes the marker |

At most one message per marker; logged in the watchdog log. The watchdog never sends Enter itself into an agent pane.

## AC
1. Marker + idle agent >= 2 min: exactly one `herdr agent prompt <spawner>` naming the agent; a later pass sends none.
2. Agent `working`, gone or retired: marker removed, no message. `blocked`: no message.
3. Spawner missing from the roster: the Team Lead, else the Manager, gets it.
4. Version bump: `.claude-plugin/plugin.json` 0.11.3; `grep -rn '0\.11\.2' .claude-plugin/` prints nothing; changelog entry.
5. Existing watchdog tests stay green; `grep -rl 'squad-watchdog' tests/` hits run.
6. `promote.md` written (lasting rule or "nothing to promote").

## Rules for this ticket
- Verify: run the `/mattpocock-skills:code-review` skill on your diff against the task base (Chieu's ask; no QA on this team). `## Review` starts with an AC trace, then that review's findings and what you did with each. `## Behaviour` holds the test output per AC.
- Same as 01 (scratch squad only, SQ-10 three files, `grep -rl` hits).

## Team Lead notes
- Base 4049f8e dry-run (SQ-15): tests/test_squad_spawn.py 122 OK; tests/test_squad_watchdog.py 114 OK (run `cd tests && python3 -m unittest test_squad_watchdog`; the file has no runner). No base failures.
- Read this ticket and its `Files:` (at most 4 more) before the first Edit or Write (SQ-27). No Edit, Write or STATUS by turn 15: send `STATUS NN: still reading <what>, <n> more turns` to the Team Lead.
- Developer retires only after the Team Lead's `squad-evidence check` exit 0 (SQ-20).

## Design notes (Developer)

## Comments
