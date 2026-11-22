# 03 Role instructions, roster headers and bump: evidence

Note (D9): contradicts ADR 0010 and "spawns and retires Developers" in ADR 0030; ADR 0032 (ticket 04) amends both. Not merged yet.
sha: 6cd2a70
## Review

AC trace (details in `## Checks`):
- AC1 | `grep -n "role but\|spawns and retires Developers\|you spawn Developers" agents/team-lead.md` | no hit
- AC2 | `grep -n "spawn only the Team Lead" agents/manager.md` | line present
- AC3 | `grep -n "Only the Manager edits this file" templates/scope/roster.md templates/goal/roster.md` | no hit; tests/test_templates.py
- AC4 | `grep -n '"version"' .claude-plugin/plugin.json`; `grep -c 0.10.3 .claude-plugin/plugin.json` | 0.10.4; 0
- AC5 | `squad-process lint` | exit 0, no output
- AC6-AC8 | unittest list in Behaviour | `cd tests; python3 -m unittest <file>`
- AC9 | `git merge-base --is-ancestor` | yes yes

## Behaviour

Merged branch 02 (0296d2a) into 01 (0c65d44). Ancestor check: 01 sha 0c65d44 in HEAD: yes; 02 sha 0296d2a in HEAD: yes.
Run from `tests/`, all OK: test_instructions, test_templates, test_promotion_0_6_0, test_squadruntime, test_old_language_inventory, test_team_lead_perms, test_rules_contract, test_windows_safe, test_utf8_helpers (SQ-10), plus every `grep -rl "agents/team-lead\|agents/manager\|roster.md" tests/` hit (test_squad_spawn, _retire, _respawn, _close, _start, _usage, _watchdog, test_squadsettings, test_squadboard_*, test_process_writing, etc.): OK. test_squadreport_collect has 2 skips that exist on base. The fixture scripts in the hit list are not tests. No test edited, none newly skipped.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | grep: no hit | | |
| AC2 | grep: line present | | |
| AC3 | grep no hit; test_templates ok | | |
| AC4 | grep 0.10.4, count 0 | | |
| AC5 | squad-process lint exit 0 | | |
| AC6 | unittest list ok | | |
| AC7 | windows_safe, utf8, instructions ok | | |
| AC8 | none skipped | | |
| AC9 | ancestor yes yes | | |
