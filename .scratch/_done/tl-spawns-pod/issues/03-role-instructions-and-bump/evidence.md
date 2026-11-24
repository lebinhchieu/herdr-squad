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
| AC1 | grep: no hit | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC2 | grep: line present | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC3 | grep no hit; test_templates ok | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC4 | grep 0.10.4, count 0 | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC5 | squad-process lint exit 0 | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC6 | unittest list ok | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC7 | windows_safe, utf8, instructions ok | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC8 | none skipped | read and run at 6cd2a70: pass | read at 6cd2a70: pass |
| AC9 | ancestor yes yes | read and run at 6cd2a70: pass | read at 6cd2a70: pass |

## QA whitebox

### QA whitebox, ticket 03, sha 6cd2a70 (evidence commit ea82861 on top)

Verdict: PASS. No findings.

- AC9 integration: `git merge-base --is-ancestor 0c65d44 6cd2a70` and `... 0296d2a 6cd2a70` both true.
- AC1: `grep -n "role but\|spawns and retires Developers\|you spawn Developers" agents/team-lead.md` no hit; card names manager, token-coach and another team-lead as never. AC2: manager.md Stance line present.
- AC3: "Only the Manager edits this file" no hit in either roster template; both headers match the Design; table header row unchanged.
- AC4: plugin.json `0.10.4`, count of `0.10.3` is 0; changelog v23 says "Plugin 0.10.4".
- AC5: `squad-process lint` exit 0 and no cited `[ID]` of the two agent cards is missing from the process folder.
- AC6/AC7/AC8: detached checkout of 6cd2a70, from tests/: test_instructions, test_templates, test_promotion_0_6_0, test_squadruntime, test_old_language_inventory, test_team_lead_perms, test_rules_contract, test_windows_safe, test_utf8_helpers, test_architect_handoff, test_processlint plus every .py hit of `grep -rl "agents/team-lead\|agents/manager\|roster.md" tests/` = 1054 tests, all ok. (2 skips: `test_squadreport_collect.RealDataShape`, no real scope in a worktree; not new. 2 errors were my own non-module names `fixtureboard/...` passed to unittest, not tests.)
- Follow-up (not an AC): the Team Lead card description still says "started by the squad Manager (squad-spawn)" and the other agent cards say the same; unchanged by design.

## QA blackbox

### 03 QA blackbox (sha 6cd2a70; ea82861 on top is evidence-only, diff checked: only evidence.md)
Method: `live` = read the files at the commit with `git show` / `git grep` / `git diff main` (agent cards, rosters, plugin.json are text agents read; no code read).

| AC | what I did | what I saw | result |
|---|---|---|---|
| AC1 | grep `role but\|spawns and retires Developers\|you spawn Developers` in agents/team-lead.md; read lines 3, 6, 12 | no hit; description and intro: "spawn(s), respawn(s) and retire(s) every pod role on `team:` and the Developers"; Stance: "never spawn, respawn or retire `manager`, `token-coach` or another `team-lead`" (and still never relays a blocked pane or permission prompt); Tools line keeps squad-spawn/retire/respawn | pass |
| AC2 | read agents/manager.md Stance | new line: "You spawn only the Team Lead and, at the close, the Token Coach; the Team Lead spawns the rest of the pod and watches its context." | pass |
| AC3 | grep `Only the Manager edits this file` in both rosters; read headers | no hit; scope header: "`squad-spawn` adds a row; whoever spawned an agent fills its Owns and Status. The Manager keeps its own row and the Team Lead's. Look up a topic's owner here before asking the Manager." (same as FILE-5b); goal header keeps "the goal Manager's own file; the goal Manager edits it"; table header row `\| Agent \| Role \| Scope \| Owns \| Status \| Session \|` unchanged (diff touches only line 3) | pass |
| AC4 | read plugin.json, changelog | `"version": "0.10.4"`, `grep -c 0.10.3` = 0; changelog has `## v23 — 2026-11-22` and "Plugin 0.10.4" | pass |
| AC5 | cited IDs in the two cards | [CORE-3], [MSG-19]: both exist in the process folder (core.md, messages.md). `squad-process lint`: not run by me | pass (cites) |
| AC9 | `git merge-base --is-ancestor` | 0c65d44 (01) yes, 0296d2a (02) yes | pass |
| AC6-8 | tests, lint, SQ-10 runs | QA whitebox / Tech Lead | n/a |
