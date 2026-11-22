# 01 Evidence

## Review
AC trace (run from `tests/`: `python3 -m unittest <file>`):

- AC1 | `test_team_lead_perms::test_team_lead_spawns_every_pod_role` | unittest
- AC2 | `test_team_lead_perms::test_team_lead_cannot_spawn_the_three_never_roles`, `..._may_respawn_itself_but_not_spawn_never_roles_under_other_names`, `test_refusal_has_no_side_effect` | unittest
- AC3 | `test_team_lead_name_must_match_its_roster_row` (row `Manager`, `QA Whitebox`, no row; no `labels/`, no herdr log), `test_team_lead_spawn_refuses_when_roster_is_missing` (01-B) | unittest; `--goal` and flat squad refused for a Team Lead (qaw FAIL fix)
- AC4 | `test_team_lead_role_not_on_team_is_refused_by_the_team_gate` | unittest
- AC5 | `test_retire_closes_every_pod_role`, `test_retire_refuses_never_roles_and_missing_row`; `test_crlf_squad_files::test_retire_team_lead_branch` | unittest
- AC6 | `test_respawn_refuses_never_roles_without_event_or_rename` (rows `Manager`, token-coach, team-lead; QA dry run prints `squad-spawn qa-whitebox qaw`), self-respawn in `test_team_lead_may_respawn_itself...` | unittest
- AC7 | `test_other_callers_spawn_any_role`, `test_retire_unchanged_for_manager_and_developer` | unittest
- AC8 | `grep -rn "only spawn dev\|only retire dev" bin tests` | no hit
- AC9 | `test_allow_set_is_exact_and_git_risks_ask`, `test_squadsettings::test_team_lead_empty_local_has_spawn_dev_and_herdr_entries`; `grep -c 'squad-spawn:\*' templates/squad/settings/team-lead.json` = 0
- AC10 | tests replaced in `tests/test_team_lead_perms.py`, none skipped
- AC11 | header comments of `bin/squad-spawn` (line ~90) and `bin/squad-retire` rewritten
- AC12, AC13 | see Behaviour
- AC14, AC15 | QA

## Behaviour
Targeted runs, all `OK`: `test_team_lead_perms` 14, `test_squadsettings` 25, `test_squad_spawn` 108, `test_squad_retire` 4, `test_squad_respawn` 33, `test_crlf_squad_files` 6 (updated: a QA row is now retired by a Team Lead, the Manager row refused), plus the other `grep -rl` hits: `test_squadupgrade` 45, `test_squad_close` 79, `test_architect_handoff` 11, `test_team_models` 19, `test_squad_usage_hook` 13, `test_squad_start` 49, `test_winlaunch` 9, `test_squad_usage` 30, `test_squadcommands` 8, `test_squad_manager_guard` 25, `test_rules_contract` 17, `test_rules_wording` 30, `test_templates` 8, `test_squadruntime` 74, `test_dev_rules_size` 9, `test_old_language_inventory` 2.
SQ-10: `test_windows_safe` 14 ok, `test_utf8_helpers` 14 ok, `test_instructions` 16 ok.

Limits (01-C): `grep -n SQUAD_RESPAWN bin/squad-spawn` shows only the event-log lines (557-558); the guard keys on `SQUAD_ROLE` only. It stops mistakes, not a Team Lead rewriting its own environment (a caller that sets `SQUAD_ROLE=manager` misses the allow entries and prompts the PO).
The new guard runs only from a home pinned at this branch's plugin; a 0.10.3 pin keeps the old dev-only text. ADR 0010 still says Developers only until ADR 0032 (ticket 04) merges.

## QA whitebox

### QA whitebox, ticket 01, sha 9a3361a (base 8d74fcb)

Verdict: FAIL (1 finding: AC3 / AC14 name-vs-row check can be bypassed).

#### Finding 1: the name-vs-row check (D2) runs only in the per-scope `--scope` branch; `--goal` and a flat squad skip it
- `bin/squad-spawn:148-158` (the D2 block) sits inside `else` of `if [[ -n $goal ]]` inside `if [[ -d $squad_dir/scopes ]]`. A caller with `SQUAD_ROLE=team-lead` who passes `--goal <g>`, or who runs in a flat squad (no `scopes/`), never reaches it. The role guard at line 91 only blocks the role argument, so `qa-whitebox` passes.
- Reproduced on 9a3361a with the `test_team_lead_perms.GateTest` fixture (ROSTER: `mgr` is row `Manager`), `--dry-run`, `SQUAD_ROLE=team-lead`, `SQUAD_NAME=tl`:
  - `squad-spawn qa-whitebox mgr --goal g` (goal folder with the same roster): exit 0, prints the herdr launch for QA Whitebox named `mgr`.
  - `squad-spawn qa-whitebox mgr` in a flat squad (roster at the squad folder): exit 0, same.
  - `squad-spawn qa-whitebox mgr --scope s`: exit 2 (as AC3 wants). So the guard works only on one of three paths.
- Why it matters: design D2's reason is that the never-roles must not be reached by spawning another role under a dead Manager's name. With `--goal` the Team Lead can do exactly that: the Manager's roster row is rewritten with a QA role and session. AC14 says "no path lets a team-lead caller reach manager, token-coach or a second team-lead: not by name-vs-row". Also the team gate does not run on the goal path, so a Team Lead could spawn a role that is not on `team:` there (`dev x --goal g` exits 0). A Team Lead has no goal and no flat-squad use.
- What would pass: for a Team Lead caller, refuse `--goal` (exit 2, stderr says a Team Lead spawns only inside its scope), and in a flat squad either run the same D2 check against `$squad_dir/roster.md` or refuse. Add one assertion to `test_team_lead_name_must_match_its_roster_row` (or one new test) for `--goal`: `qa-whitebox mgr --goal g` exits 2, no `labels/`, no herdr call. Re-run `test_team_lead_perms` and the AC12 list.

#### Checked and fine (no finding)
- AC1/AC2/AC3 (scope path)/AC4/AC5/AC6/AC7: pass in `test_team_lead_perms` (every pod role spawn 0; manager, token-coach, other team-lead exit 2, no labels, no herdr; D2 with `Manager`/`QA Whitebox` rows; missing roster exit 2; respawn refusal leaves no event/rename; retire rows). 01-A, 01-B, 01-D built as asked.
- AC8 grep: no hit. AC9: exactly the seven roles, `squad-spawn:\*` count 0; ask/deny untouched. AC11: headers rewritten, no stale "dev only" text.
- AC14 (c): `SQUAD_RESPAWN` appears only at `bin/squad-spawn:557-558` (event log), not in the guard. `SQUAD_ROLE` is the only key; spoofing it on the command line misses the allow entries (the limit, to quote in evidence).
- squad-respawn/squad-retire: role from row, lowercased, space to dash; refusal before the `respawn` event and rename (`bin/squad-respawn:57-63`); the pinned-runtime hand-off applies below 0.6.0 only, as before.
- Tests, detached checkout of 9a3361a, from tests/: the six handed-in files + test_windows_safe + test_utf8_helpers + test_instructions = 234 ok; the other 16 hits of the AC12 grep (test_architect_handoff, test_dev_rules_size, test_old_language_inventory, test_rules_contract, test_rules_wording, test_squad_close, test_squadcommands, test_squad_manager_guard, test_squadruntime, test_squad_start, test_squadupgrade, test_squad_usage, test_squad_usage_hook, test_team_models, test_templates, test_winlaunch) = 428 ok. No test skipped.
- `test_crlf_squad_files.py` change (qa row now allowed to retire, manager row refused) follows AC5; fine.
- Evidence: handed in with `squad-evidence check` exit 0 per the HANDIN.

#### Re-check at 0c65d44: PASS
Changed: `bin/squad-spawn:138-139` (a Team Lead caller with `--goal` or in a flat squad exits 2 before any effect), `tests/test_team_lead_perms.py` (`qa-whitebox mgr --goal g` exits 2, no labels, no herdr log). Finding 1 fixed: re-ran my repro on a detached checkout: `dev x --goal g` exit 2, flat squad `qa-whitebox mgr` exit 2, `--scope s` paths as before. Tests: the 6 files + SQ-10 three + test_squad_start + test_squad_manager_guard = 308 ok. No test skipped.

## QA blackbox

### 01 QA blackbox (sha 9a3361a)
Method: `live`. Scratch project (git repo, squad `q`, scope `s`, `team: tech-lead,qa-white,qa-black,designer,architect`, pin `plugin: 0.10.3 <9a3361a full sha>`), the branch extracted with `git archive` as the pinned runtime `_runtime/0.10.3-9a3361ace7f5` and first on `PATH` (as the pane gets it), stub `herdr` that logs every call (stateful for `agent get` / `rename`). Caller env `SQUAD_ROLE=team-lead SQUAD_NAME=q-tl-s`. Roster rows: q-mgr-s manager, q-tl-s team-lead, q-tl2-s team-lead, q-qaw-s `QA Whitebox`, q-qab-s qa-blackbox, q-coach-s token-coach, plus dev/ba/tech-lead/designer/architect rows. No code read. Scratch dirs removed after.
Plugin.json on the branch is 0.10.3 (bump rides 03), so the pin says 0.10.3.

| AC | what I did | what I saw | result |
|---|---|---|---|
| AC1 | `squad-spawn <role> x-<role> --scope s --prompt hi --dry-run` for dev, tech-lead, qa-whitebox, qa-blackbox, designer, architect (ba is not on this `team:`, see AC4) | each rc=0, "would run" output, stderr empty | pass |
| AC2 | manager / token-coach / team-lead under `other-tl` | rc=2, stdout 0 bytes, stderr `a Team Lead may not spawn manager` / `... token-coach` / `... another team-lead (other-tl)`; "only spawn dev" absent. Three real (non-dry) refusals in a row: herdr log 0 lines, no new files in the scope folder. `team-lead` under `q-tl-s` rc=0 | pass |
| AC3 | qa-whitebox under q-mgrrow (row manager) | rc=2 `a Team Lead may not spawn qa-whitebox under q-mgrrow: the roster says q-mgrrow is manager` (both roles named); under q-qab-s (row qa-blackbox) rc=2 likewise; under q-qaw-s (row `QA Whitebox`) rc=0; qa-blackbox under q-qab-s rc=0; under a name with no row rc=0 | pass |
| AC4 | `ba` not on team | rc=1, stdout 0, stderr `role ba is not on the team in .../scope.md (team: ...)`, no herdr call | pass |
| AC5 | `squad-retire <name> --no-notes` | dev, ba, tech-lead, qa-whitebox (`QA Whitebox` row), qa-blackbox, designer, architect: rc=0, `herdr pane close` called once. manager, token-coach, q-tl-s (own), q-tl2-s, unknown name: rc=2, 0 pane close, stderr `a Team Lead may not retire <name> (<role>); it retires the pod roles and Developers only` (`no roster row` for the unknown name) | pass |
| AC6 | `squad-respawn <name> --dry-run` | q-qaw-s rc=0, prints `squad-spawn qa-whitebox q-qaw-s --scope s ...`; q-mgr-s, q-coach-s rc=2 (`a Team Lead may not respawn ...`), q-tl2-s rc=2 (`... another team-lead`). Real runs of those three: rc=2, 0 `respawn` lines added to usage-events.jsonl, 0 herdr calls (so no rename). Real run for q-qaw-s: rc=0, `respawn` event written, rename, spawn, prompt. Team Lead self-respawn (q-tl-s) rc=0 | pass |
| AC7 | callers manager, dev, none: `spawn qa-whitebox`, `spawn manager`, `retire q-qaw-s`, `retire q-mgr-s`, dev `retire q-dev-s` | all rc=0 as before | pass |
| AC8 | `grep -rn "only spawn dev\|only retire dev" bin tests` on the branch | no hit | pass |
| AC9 (visible part) | grep of `team-lead.json` | exactly seven `Bash(squad-spawn <role>:*)` entries (architect ba designer dev qa-blackbox qa-whitebox tech-lead); `squad-spawn:\*` count 0. `ask`/`deny` unchanged and tests: QA whitebox | pass |
| AC15 | all of the above run from the pinned runtime on `PATH`. Same pane with a runtime at main 8d74fcb (0.10.3 code): spawn qa-whitebox and designer rc=2 `a Team Lead may only spawn dev`; `squad-retire q-qaw-s` rc=2 `a Team Lead may only retire dev (...)` (the expected limit) | pass |
| AC10-14 | tests, security read: QA whitebox / Tech Lead | not run by me | n/a |

Notes (not findings): a `dev` caller spawning a pod role passes the guard (the guard is for Team Lead only, AC7 "as before"). The dry-run of `squad-respawn` prints a warning, not an error, when the notes file is missing.

#### Re-check at 0c65d44 (diff 9a3361a..0c65d44: squad-spawn +2 lines, one test, evidence)
Same scratch method (branch as pinned runtime first on PATH, stub herdr); scratch dirs removed.
- `--scope` paths unchanged: qa-whitebox / qa-blackbox dry-run rc=0; manager refused rc=2 `a Team Lead may not spawn manager`; qa-whitebox under a manager row refused with both roles named; `--scope s` dev rc=0. pass
- New: Team Lead with `--goal g` for qa-whitebox: rc=2, stdout 0, `a Team Lead may not spawn qa-whitebox with --goal or in a flat squad; it spawns only inside its scope (--scope)`, 0 herdr calls, goal folder untouched. For `manager --goal`: rc=2 `may not spawn manager` (never-role text first). pass
- New: flat squad (no scopes/ folder), Team Lead: qa-whitebox and dev both rc=2 with the same `--goal or in a flat squad` text, no output. Manager in the same flat squad: rc=0 (only the legacy-squad warning). Manager `--goal` rc=0. pass
This text is beyond the written AC1-AC7 (additive, Team Lead only; AC7 callers unaffected): no AC broken.
