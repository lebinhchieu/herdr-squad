# Evidence: 04 rules, ADR, glossary, changelog, version 0.10.10

## Review

### Review

AC trace:
- AC1 | merge of 01 (22593e0), 02 (e1e4e88), 03 (c3edb63) into this branch, no conflict; tests below | `git log --merges`
- AC2 | tests/test_rules_wording.py `test_bundle_long_wait_and_experiment_rules` (COST-8b, `squad-respawn --lazy`) | python3 tests/test_rules_wording.py
- AC3 | same test, COST-15 strings; `git diff main -- templates/squad/process/cost.md` shows no edit to COST-3, COST-5, COST-10b | python3 tests/test_rules_wording.py
- AC4 | test_rules_wording, test_instructions, test_processlint, test_process_writing | python3 tests/<file>.py; compose for manager and dev lists COST-15 in the `rules:` line
- AC5 | docs/adr/0033-watchdog-respawns-roles.md | read
- AC6 | skills/squad-process-update/changelog.md `## v28` | read
- AC7 | CONTEXT.md **Lazy respawn**, **Cold cache**, **Idle** after **Watchdog** | read
- AC8 | `grep -rn '0\.10\.9' .claude-plugin tests/` empty | grep
- AC9 | ADR and glossary exist (promote.md rows 1-2) | ls, read
- AC10 | test_windows_safe, test_utf8_helpers, test_instructions | python3 tests/<file>.py
- AC11 | no watchdog, respawn or herdr run; compose ran on a mktemp -d home | read

### Behaviour

Tests run (all OK): test_rules_wording (30), test_rules_contract, test_squadupgrade, test_promotion_0_6_0, test_squadruntime, test_squad_start, test_squad_respawn, test_squad_spawn, test_lazy_hook, test_squad_watchdog (unittest discover), test_processlint (31), test_process_writing; SQ-10: test_windows_safe (14), test_utf8_helpers (14), test_instructions (16). No full suite (DECISION 0). The first lint run flagged COST-8b and COST-15 over 60 words; both shortened.

`grep -rln '0\.10\.9' . --exclude-dir=.git --exclude-dir=.scratch`: only `skills/squad-process-update/changelog.md` (past entries and the v28 rollback line): kept. `.claude-plugin/plugin.json` now 0.10.10; marketplace.json has no `version` (grep, 0 hits); no test pins 0.10.9.

Rule index: `squad-process compose` in a scratch home lists COST-15 for `manager` and `dev`.

Open follow-up: a real UserPromptSubmit `session_id` equal to `squad-spawn --session-id`, to be confirmed once on the first lazy respawn in a scratch squad (not run here, safety).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | git log --merges; targeted tests OK | bin/hooks identical to 01-03; 358 targeted OK | scratch squad: prompt, lazy respawn, hook flow OK |
| AC2 | test_rules_wording OK | COST-8b read, test diff | composed manager rules read |
| AC3 | test_rules_wording OK; cost.md diff | COST-15 read; 3/5/10b not in diff | composed rules, diff only 8b+15 |
| AC4 | 4 test files OK; compose index | 5 test files + compose index OK | rules: line of manager and dev has COST-15 |
| AC5 | read ADR 0033 | ADR read, 0028/29/32 unedited | ADR read |
| AC6 | read changelog v28 | changelog v28 read | changelog read |
| AC7 | read CONTEXT.md | CONTEXT.md read; old entries unedited | glossary read |
| AC8 | grep 0.10.9 | plugin.json 0.10.10; grep clean | plugin.json 0.10.10, grep clean |
| AC9 | files exist | promote.md matches diff | - |
| AC10 | SQ-10 three files OK | SQ-10 three files green | fake herdr only |
| AC11 | no live run | no live run | fake herdr only |

## QA whitebox

### QA whitebox 04 — sha 9d0da3b — PASS
Checked in a throwaway detached worktree (removed). No herdr, watchdog, respawn or spawn run; compose ran on a mktemp scratch home.

#### Checks (my column)
| AC | Check | Result |
|---|---|---|
| AC1 | merged tree's bin/squad-watchdog, squad-respawn, squad-spawn, squad-lazy-hook, hooks.json identical to the passed branches 03/01/02 (git diff empty); 04's own commit touches no bin/hooks; targeted run test_lazy_hook, test_squad_respawn, test_squad_spawn, test_squad_watchdog, test_squad_start, test_squad_log_message, test_squadtask: 358 OK | OK |
| AC2 | COST-8b text read: before the hour, lazy respawn by watchdog at 55 min over 50k (COST-15), Manager may run `squad-respawn --lazy`; `roles: manager`/`topic: cost` kept; test lines updated, nothing weakened (diff) | OK |
| AC3 | COST-15 present, roles list = COST-13b roles + dev, `aware: manager`, `topic: cost`; 3 sentences; COST-3/5/10b not in the diff | OK |
| AC4 | test_rules_wording 30, test_instructions+test_processlint+test_process_writing+test_windows_safe+test_utf8_helpers 76, test_rules_contract+test_hooks_json 23: OK. `squad-process compose` on a scratch home (scope.md copied): COST-15 in the index of dev, qa-whitebox, team-lead, designer, manager | OK |
| AC5 | ADR 0033 read: decision, why, 0032 exception + env scrub, guards, consequences, rejected alternative, status accepted; 0028/0029/0032 files exist and unedited | OK |
| AC6 | changelog v28 above v27: Plugin 0.10.10, why per change, Deploy, Rollback | OK |
| AC7 | CONTEXT.md +10 lines after Watchdog: Lazy respawn, Cold cache, Idle (two meanings); existing entries not edited | OK |
| AC8 | plugin.json 0.10.10; `grep 0.10.9` in .claude-plugin/ and tests/: none; repo-wide only changelog (past entry + v28 rollback line); marketplace.json has no version | OK |
| AC9/PROMO-8 | promote.md rows (ADR, glossary, rules, lazy contract) match what the diff holds; nothing extra promoted | OK |
| AC10 | docs/rules/version only besides the merge; the SQ-10 three files green (above) | OK |

#### Follow-ups (not FAIL)
- CONTEXT.md **Idle**: the existing "idle" entries are not given a link back to it (AC7 says cross-linked); the new entry points at them in words only. Cosmetic.
- Still open from 02: confirm a real UserPromptSubmit session_id on the first live lazy respawn.
- Known failing on base: test_templates::test_designer_may_write_only_ui_design_files (also on main 87372fd; SQ-17 grep of scopes/_done iterations: 0 hits, first listing).

#### Verdict
PASS 04 on 9d0da3b.

## QA blackbox

### QA blackbox 04 (9d0da3b)

| AC | shot/live | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 merge of 01-03 | live | scratch squad `/tmp/qab04` (fake herdr, fake transcripts, branch code) ran watchdog tick, `squad-respawn --lazy` via the watchdog, `squad-lazy-hook` | all three tickets' behaviour works together (below) | pass |
| AC2 COST-8b | live | `squad-process compose` in the scratch squad, read the manager rules file | rule says notes written + lazy respawn before the PO wait passes the hour, watchdog at 55 min over 50k, `squad-respawn --lazy` yourself; `roles: manager` | pass |
| AC3 COST-15 | live | read composed rules; `git diff main` on cost.md | 3 sentences, all required points; roles list incl. dev; COST-3/5/10b untouched (diff has only the 8b and 15 hunks) | pass |
| AC4 index | live | `rules:` line of manager and dev rules files | COST-15 listed in both | pass |
| AC5 ADR 0033 | live | read | status accepted; watchdog not a role; why; exception to 0032 + env scrub; guards incl. `SQUAD_WATCHDOG_COLD=0`; consequences; rejected alternative | pass |
| AC6 changelog | live | read v28 above v27 | Plugin 0.10.10, changed list with why, Deploy (Chieu), Rollback | pass |
| AC7 glossary | live | read CONTEXT.md | Lazy respawn, Cold cache, Idle (two meanings) next to Watchdog | pass |
| AC8 version | live | read plugin.json, grep `0.10.9` in `.claude-plugin`, `tests/` | 0.10.10; no hit | pass |
| AC10/11 | live | no watchdog/respawn run on live squads; my runs only with fake herdr in /tmp | n/a | pass |

#### Integrated lazy flow (scratch squad: manager, team lead, dev, all idle 58 min, context 90k, work open)
1. Tick 1: watchdog sent one `COLD CACHE ... write roles/<you>.notes.md ... the watchdog restarts you afterwards` prompt to each of the three.
2. I wrote notes for manager and dev only. Tick 2 (+2 min): manager and dev were respawned (`respawned lazy`): tab created, agent started with a new `--session-id`, **no `agent prompt` to the new session**; `roles/<name>.lazy` holds that session id. The Team Lead (no notes) got a 2nd prompt and was not restarted; tick 3: `gave up: notes not written t-tl`.
3. First message through `bin/squad-lazy-hook` with the new session id: output adds "You were respawned ... read your notes <path> ... Then answer this message."; the marker is consumed. A second message: no output. A message from another session id: no output, the dev's marker kept.
4. Child env carries `SQUAD_ROLE=manager`/`dev`, `SQUAD_NAME` of the role (not the watchdog's).

#### Follow-ups (non-blocking)
- A failed lazy respawn is logged with the last stderr line: in my scratch run the log read "legacy squad: plugin rules attached ..." / "no `plugin:` pin ..." (warnings) while the real cause was an agent-name clash from my stub. The reason in `watchdog.log` can mislead.
- A failed respawn marks the role "gave up" and is not retried in the same idle spell (by design per ADR guards).
- Still open from 01-03: confirm a real UserPromptSubmit `session_id` equals the `--session-id` of the first real lazy respawn.
