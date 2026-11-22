# 02 Rule text: evidence

Note (D9): contradicts ADR 0010 and the "spawns and retires Developers" sentence of ADR 0030; ADR 0032 (ticket 04) amends both. Not merged yet.
sha: 0296d2a
## Review

AC trace (details in `## Checks`):
- AC1 | `grep -rn "spawns and retires Developers\|retire only Developers\|spawns Developers; you do not" templates/squad/process/` | no hit
- AC2-AC8 | `tests/test_rules_contract.py`, `tests/test_rules_wording.py`, `tests/test_qab_optional.py` | `cd tests; python3 -m unittest <file>`
- AC9 | awk loop over SPAWN-3/4/4a | `roles: manager, team-lead` x3
- AC10 | `git diff main --stat -- _removed.md` empty; rule-ID diff per edited file empty | run
- AC11 | `skills/squad-process-update/changelog.md` top entry v23 | read
- AC12-AC15 | unittest list below | run

## Behaviour

Run from `tests/`: `python3 -m unittest test_rules_contract test_rules_wording test_dev_rules_size test_sizes test_small_files_equivalence test_qab_optional test_old_language_inventory test_processlint test_windows_safe test_utf8_helpers test_instructions test_promotion_0_6_0` -> Ran 158 tests, OK.
SQ-10 files (test_windows_safe, test_utf8_helpers, test_instructions) are in that run: OK.
Tests updated: `test_rules_contract.py` (renamed `test_team_lead_spawns_and_retires_the_pod`, new SPAWN-9 content assertion, new `roles:` retarget and no-ID-removed test, SPAWN-2b assertion), `test_qab_optional.py` (SIZE-21a phrase). None skipped.
AC10: `_removed.md` diff empty; rule-ID diff empty for spawning, cost, starting, sizes, files, messages, who, goal.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | grep command above: no hit | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC2 | test_rules_contract test_spawning_cost_and_safety_follow_the_team: ok | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC3 | test_team_lead_spawns_and_retires_the_pod: ok | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC4 | test_rules_wording: ok | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC5 | read spawning/starting/messages: phrase present | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC6 | test_qab_optional SIZE-21a: ok | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC7 | read files/goal/who: ok | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC8 | read SPAWN-10b: ok | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC9 | awk loop: team-lead on all three | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC10 | diff checks: empty | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC11 | changelog v23 read | read and grep at 0296d2a: pass | read live at 0296d2a: pass |
| AC12 | 158 tests ok | 169 tests ok at 0296d2a; see QA whitebox | - |
| AC13 | 158 tests ok | 169 tests ok at 0296d2a; see QA whitebox | - |
| AC14 | included in 158: ok | 169 tests ok at 0296d2a; see QA whitebox | - |
| AC15 | test_rules_contract no-size-word test: ok | read and grep at 0296d2a: pass | read live at 0296d2a: pass |

## QA whitebox

### QA whitebox, ticket 02, sha f0855f7 (base 8d74fcb)

Verdict: FAIL (1 finding, a test that passes on base now fails).

#### Finding 1: test_architect_handoff fails on the branch (breaks a pinned test, AC12)
- Command (detached checkout of f0855f7, from tests/): `python3 -m unittest test_architect_handoff` -> FAILED (failures=2); same command on main: 11 ok.
- Failing: `NoLeakTest.test_a_scope_without_the_flag_carries_no_architecture_rule_for_any_role` for role=team-lead, sizes M and L (`tests/test_architect_handoff.py:50`: a scope without `architecture` must put no word "architect" in any non-Manager role's rules).
- Cause: the Team Lead's composed rules now carry "Architect" without the flag, from two places:
  - `templates/squad/process/sizes.md` SIZE-13: `aware: team-lead` was added, and the rule names "an irreversible choice (Architect)" and "`--po-ok` for the Designer or Architect".
  - `templates/squad/process/spawning.md` SPAWN-9 (roles: team-lead): "Designer and Architect join only after the PO's yes."
  Both reach the Team Lead (`composed("team-lead","M")` shows 3 hits, all from these two).
- Why it matters: AC12 says every pinned test the edit breaks is updated, never skipped, and the ticket's grep list missed this file (it is a hit of `grep -rl "SPAWN-\|SIZE-13\|..." tests/`). The handed-in run (158 ok) did not include it. A newly failing existing test is a FAIL (SQ-4).
- What would pass: the Team Lead's composed rules carry no "architect" when `architecture = no`. Ways, Developer/Tech Lead's choice: reword the SPAWN-9 sentence without the role names (e.g. "a role that needs the PO's yes joins only after it"); and either gate the Architect words of SIZE-13 for the Team Lead or do not give SIZE-13 `aware: team-lead` (then the Team Lead's "spawn the joiner from the Handover" duty needs another home, e.g. SPAWN-9, which already says it). Do not edit the test to allow the word: the no-leak rule is its purpose. After the fix re-run `test_architect_handoff` and the 158-test list.

#### Checked and fine (no finding)
- AC1 grep: no hit. AC9 roles lines: team-lead on SPAWN-3, 4, 4a and START-4a. AC10: `_removed.md` untouched; rule-ID lists identical to main for all 8 edited process files.
- AC2-AC8, AC11 (v23 entry, "Plugin 0.10.4", Deploy/Rollback lines), AC7 (FILE-5b/5c, goal.md, who.md): text read against the ticket, matches.
- Re-ran the handed-in list on f0855f7: 158 ok (test_rules_contract, test_rules_wording, test_dev_rules_size, test_sizes, test_small_files_equivalence, test_qab_optional, test_old_language_inventory, test_processlint, test_windows_safe, test_utf8_helpers, test_instructions, test_promotion_0_6_0). No test skipped in the diff.
- Follow-up (not an AC): `evidence.md` AC2-AC8 trace rows point at whole test files, not the tests that cover each AC; fine as is.

#### Re-check at 0296d2a: PASS
Changed files re-read: spawning.md (SPAWN-9 no role names), sizes.md (SIZE-13 `aware: team-lead` dropped), starting.md (START-3 line names the Team Lead), changelog.md (matches). Finding 1 fixed: `test_architect_handoff` 11 ok. Re-ran detached checkout, from tests/: test_architect_handoff + the 12-file list = 169 ok; test_templates ok (START-3 hit). Rule IDs identical to main in every edited process file; the old-phrase grep has no hit.
Follow-up: SIZE-13 no longer reaches the Team Lead, so the Team Lead's handover duty lives only in SPAWN-9 (as the Developer said); ticket 02 AC6 text and design D6 name `aware: team-lead` for SIZE-13: update the wording in the ticket if it is committed.

## QA blackbox

### 02 QA blackbox (sha f0855f7)
Method: `live` = read the rule text at f0855f7 (extracted to a temp dir, removed after) and ran the AC greps. No code read.

| AC | how | what I saw | result |
|---|---|---|---|
| AC1 | live: grep `spawns and retires Developers\|retire only Developers\|spawns Developers; you do not` over process/ | no hit (rc 1) | pass |
| AC2 | live: read SPAWN-2b, 2c | 2b: Manager spawns `team-lead` and `token-coach` only, Team Lead spawns each remaining role on `team:`; "every other role on" gone. 2c: Team Lead spawns Developers and pod roles, "you spawn neither" | pass |
| AC3 | live: read SPAWN-9, 8b | title "Team Lead spawns and retires the pod" (no "only"); body has "spawns, respawns and retires", names manager, token-coach, another team-lead as never; Token Coach via ITER-6b; late role via squad-team add / Handover / SIZE-13; Designer, Architect after PO's yes. 8b: "a Developer or any pod role ... once its work is accepted" | pass |
| AC4 | live: read COST-10b | "the Team Lead retires every pod role over 60k and respawns the roles the next iteration needs"; "Manager retires every pod" gone | pass |
| AC5 | live: read START-2c, START-5, MSG-5, MSG-6 | all three phrases present; START-5 one line after table: Manager spawns Team Lead and Token Coach, Team Lead every other row; MSG-6 bullet "the Manager adds it and the Team Lead spawns it" | pass |
| AC6 | live: read SIZE-13, SIZE-21a | 13: Manager runs squad-team add, writes Handover; Team Lead spawns joiner, respawns listed roles. 21a: Manager spawns Team Lead and Token Coach, Team Lead the rest of team and Developers | pass |
| AC7 | live: read FILE-5b/5c, goal.md l.8, who.md l.104 | 5b: whoever spawned fills Owns/Status, Manager keeps own and Team Lead's row; 5c "rows of the agents you spawned" ("Developers you spawned" gone); goal.md: Manager spawns each Team Lead, Team Lead the rest; who.md row reads "Manager; Team Lead for the pod roles and Developers" | pass |
| AC8 | live: read SPAWN-10b | "the pod keeps running" | pass |
| AC9 | live: awk roles: lines | SPAWN-3, SPAWN-4, SPAWN-4a, START-4a: `roles: manager, team-lead` | pass |
| AC10 | live: diff of `## ID` lists main vs f0855f7 for the 8 files; `git diff --stat` on _removed.md | identical ID lists; _removed.md untouched | pass |
| AC11 | live: read changelog top | `## v23 — 2026-11-22` is the top entry, "Plugin 0.10.4", changed list with why, Deploy (Chieu) with plugin update + /squad:squad-process-update + homes pin move + "0.10.3 or older keeps old guard; bare respawn changes nothing", Rollback | pass |
| AC15 | live: grep added lines for dates, "formerly", size words | none | pass |
| AC12-14 | not mine (tests, suite receipts: QA whitebox / Tech Lead) | not run by me | n/a |

Follow-ups (not AC): `starting.md` l.38 still says the Manager "spawns the pod only after the PO confirms"; the Manager now spawns only the Team Lead and Token Coach, so "the pod" is stale there.

#### Re-check at 0296d2a (diff f0855f7..0296d2a, rule text only)
- starting.md l.38: "spawns the Team Lead only after the PO confirms; the Team Lead spawns the rest of the pod": my follow-up is fixed. pass
- SPAWN-9 last sentence now "A role that needs the PO's yes joins only after it ([SIZE-13])" (AC3 wording named Designer and Architect; SIZE-13 still names both with `--po-ok`): meaning kept. pass, follow-up below
- SIZE-13 `aware: team-lead` removed, changelog line matches (SIZE-21a only). AC6 text of SIZE-13 unchanged. AC11 still consistent. pass, follow-up below
- AC1-AC11, AC15 re-read on the changed lines only (LC-3b): unchanged result, pass.
Follow-ups: (1) SPAWN-9 no longer names Designer and Architect itself; (2) the Team Lead no longer has SIZE-13 attached though SPAWN-9 and MSG-6 cite [SIZE-13]; it reads it with `squad-process rule SIZE-13`.
