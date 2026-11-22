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
