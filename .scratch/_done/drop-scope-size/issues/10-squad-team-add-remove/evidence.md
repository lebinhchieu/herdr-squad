# Evidence: 10 `squad-team add|remove`
sha: d792d78

## Behaviour
- `bin/squad-team add|remove ROLE [--po-ok] [--at-boundary] [--dry-run] [--home D] [--squad-dir D] [--plugin-root R]` (logic in `bin/squadteam.py`, reuses `squadcompose.read_home/load_rules/choose/heading/duties_line` and `squadrules.parse_team/resolve_duties`). Role is a role name or team token (`qa-whitebox` or `qa-white`); `manager`/`dev`/`token-coach` and unknown names exit 2.
- Refuses (exit 2, `scope.md` byte-identical, nothing on stdout): pin below 0.6.0 or unparsable pin, goal home, undecided team (add and remove: no command writes the first `team:`), old `size:` format (points at `squad-process adopt`), unknown/implicit role, add of a present role, remove of an absent role, designer/architect add without `--po-ok`, remove without `--at-boundary`; a pin other than the running version needs `--plugin-root`. Each flag has a refusal test and a pass test.
- Edit keeps commentary `(note)`, other lines, CRLF and BOM byte for byte; tokens go in `TEAM_KEYS` order; removing the last role writes `team: none`; only the first `team:` line changes. Write is atomic (temp file + `os.replace`); injected `os.replace` failure keeps the original and leaves no temp file.
- Output: `team:` new list, `duty X: old -> new` per changed owner, `spawn:`/`retire:` for the joiner/leaver, `respawn:` list in ROLES order. Respawn = roles on both teams whose rule IDs, headings, bodies or (index roles) `duties:` line differ; header-only change lists nobody. Tests: add team-lead (manager, tech-lead, dev), add qa-white (manager, tech-lead), remove qa-white, add designer with a design-only Manager rule (only manager), add designer with none (none); plus an independent before/after `compose` comparison on three transitions.
- Hostile `team:` value (`qa-white; touch X`, `$(touch X)`, backticks) is rejected by `parse_team`; nothing runs. Hostile role arg likewise.
- Rule pointer (DECISION 10): SIZE-13 and TEAM-7 now name `squad-team add|remove`; `test_instructions` (the Tech Lead's pending failure from 05) is green. Changelog v9 SIZE-13 / TEAM-7 lines extended (IDs were already listed).
- D1 scaffold is not mine: ticket's file list is the three new files; `legacy_scaffold` removal stays with the cutover ticket (12). `squad-team` is not in `templates/squad/settings/manager.json` allow list (outside this ticket's files): the Manager will be prompted until it is added.
- Lint baseline (G2b), `bin/squad-process lint`: base 6389642 empty, exit 0; branch empty, exit 0.
- Tests green: test_squad_team (26), test_instructions, test_squadcompose, test_team_cli, test_squadupgrade, test_processlint, test_squadadopt, test_team_duties, test_sizes, test_manager_m_l, test_process_history, test_squadprocess(_apply), test_squadrules, test_windows_safe, test_crlf_squad_files.

## QA whitebox

### QA whitebox 10 — PASS on d792d78 (Tech Lead's final sha)
- Lint exit 0 empty. Tests OK: test_squad_team (26), test_instructions, test_sizes, test_windows_safe, test_crlf_squad_files, test_processlint, test_team_duties.
- Diff read: bin/squad-team, bin/squadteam.py (every refusal is a ComposeError before scope.md is touched; token from fixed TEAM_KEYS; atomic os.replace; BOM/CRLF kept), SIZE-13/TEAM-7 pointers, changelog.
- Live (REV-5b) on a temp CRLF scope.md with commentary, pin 0.6.0 + --plugin-root: dry run unchanged; add team-lead -> `plan-owner: manager -> team-lead`, spawn team-lead, respawn manager, tech-lead; 5 CRs kept, commentary kept, canonical order; add designer needs --po-ok; add present / remove absent refused; remove needs --at-boundary; remove down to `team: none`; hostile role name refused, nothing ran. Pin 0.5.2 refused (rc 2, scope.md unchanged).
- Note (non-blocking): on this branch `running_version()` is still 0.5.2 (bump is ticket 13), so without --plugin-root a 0.6.0 pin is refused as "other than running"; correct by design.

## QA blackbox

### QA blackbox, task 10 (HANDIN d792d78, branch squad/plugin/drop-scope-size/plugin-dev-dsz-10)

Method: `bin/squad-team add|remove ROLE --home D` on scratch `scope.md` files (mktemp dir), CLI only, no code read. AC judged: 16(d), 17, 19, 30, 22-style refusals; 16(a-c,e,f) and 18 are Manager steps (live run L).

| AC | Did | Saw | Result |
|---|---|---|---|
| 16(d) | `team: team-lead, qa-white`, `add ba` | `scope.md` team: `ba, team-lead, qa-white`; prints `duty business-ac: ticket -> ba`, `duty doubt-owner: manager -> ba`, `spawn: ba`, `respawn: manager, team-lead`; other scope.md lines (`goal`, `model dev`, `touches`) untouched | PASS (respawn list accuracy: judge in live run L, branch rules are not integrated yet) |
| 17 | `add designer`, `add architect` without `--po-ok` | exit 2 `adding designer waits for the PO's yes; ask the PO, then add --po-ok`; team: unchanged | PASS |
| 17 | `add designer --po-ok` | exit 0, team gains `designer`, `spawn: designer` | PASS |
| 19 | `remove ba` without `--at-boundary` | exit 2 `remove only at an iteration boundary with the PO's OK`; unchanged | PASS |
| 19 | `remove ba --at-boundary` | exit 0, team drops `ba`; prints `duty business-ac: ba -> ticket`, `duty doubt-owner: ba -> manager`, `retire: ba`, respawn list | PASS |
| 19 | `remove qa-white --at-boundary` (team `team-lead`) | each duty it held with new owner (`tech-ac -> dev`, `code-check -> manager`, `handin-target: qas -> team-lead` ...), `retire: qa-whitebox` | PASS |
| 30 | `add wizard`; `add qa-whitebox` (already on team as qa-white); `add dev`; `remove tech-lead` (not on team) | exit 2 each, clear text, unchanged | PASS |
| dry-run | `add ba --dry-run`, `remove team-lead --at-boundary --dry-run` | prints plan + `dry run: scope.md not changed`; file unchanged | PASS |
| 22/26 | `size: L` scope; blank `team:` | exit 2 pointing at `squad-process adopt` / "the team is undecided; the Manager writes the first `team:`" | PASS |
| G7 | `team: ba; touch X` | exit 2 unknown token, X not created | PASS |

Not observed: that the respawn list equals exactly the roles whose composed text changes (the task branch still composes old-size rule text until 06/07/08 merge). Check in live run L on the integration sha.

#### Findings
None so far. Verdict waits for the Tech Lead's final sha (REV-3).

## Tech Lead review

sha d792d78 (final code, 10): TL re-ran test_squad_team 26, instructions/sizes/windows_safe 75 OK, lint empty; read bin/squadteam.py: refusals before write, atomic write, pin/size/undecided/goal guards. No finding.
