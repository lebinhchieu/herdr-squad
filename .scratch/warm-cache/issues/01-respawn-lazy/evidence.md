## Review

AC trace
- AC1 | tests/test_squad_respawn.py::test_lazy_respawn_spawns_with_lazy_no_prompt_and_marks_the_event | python3 -m unittest test_squad_respawn
- AC2 | tests/test_squad_spawn.py::test_lazy_writes_the_marker_and_sends_nothing_not_even_a_wait, test_lazy_with_prompt_or_task_exits_2_and_starts_nothing | python3 -m unittest test_squad_spawn
- AC3 | tests/test_squad_spawn.py::test_a_plain_spawn_removes_a_stale_lazy_marker | same
- AC4 | test_lazy_respawn_... (default half: prompt sent, no marker, no `lazy` key; usage text) | same
- AC5 | test_lazy_respawn_... (`"lazy": true` only when lazy) + readers below | same
- AC6 | test_lazy_writes_the_marker... (dry run says "would write", writes nothing) | same
- AC7 | test_windows_safe, test_utf8_helpers green; marker asserted byte-exact `<sid>\n` | python3 -m unittest

## Behaviour

Readers of `usage-events.jsonl` in `bin/`, each ignores an unknown key:
- `bin/squad-usage:115` `orphan_fresh`: reads only `o.get("agent")` and `o.get("rule")` (`respawn` still clears a fresh).
- `bin/squad-usage-hook:25`: `jq select(.session == $s and .rule == $r)`; no other field read.
- `bin/squad-manager-guard:119`: writer (claim_lock append); `seen_keys` (line 88) reads only `session`, `role`, `rule`.
- `bin/squad-event`, `bin/squad-retire`, `bin/squad-spawn`: writers.

Tests run: test_squad_respawn (34 ok), test_squad_spawn (119 ok), grep hits + SQ-10 files (test_windows_safe, test_utf8_helpers, test_instructions, test_crlf_squad_files, test_winlaunch, test_team_lead_perms, test_squad_start, test_squad_usage_hook, test_squad_manager_guard, test_squad_usage, test_templates): 198 run, 1 fail: test_templates::test_designer_may_write_only_ui_design_files (Write(//tmp/**) in the designer settings; `templates/` untouched by this ticket; zero hits in `scopes/_done/*/iterations/*.md`).

## QA whitebox

### QA whitebox 01 — sha cd95bc1 — PASS

Checked in a throwaway detached worktree (removed after). Fake herdr only (the tests' own); no live names.

#### Checks (my column)
| AC | Check | Result |
|---|---|---|
| AC1 | read diff bin/squad-respawn (`--lazy` parsed, spawn line adds `--lazy` instead of `--prompt`; notes check, Team Lead refusal, overrides, rename untouched); `python3 -m unittest test_squad_respawn` 34 OK (new lazy test: dry-run line has `--lazy`, no `--prompt`, no events; real run has `agent start`, no `agent prompt`) | OK |
| AC2 | read bin/squad-spawn: exit 2 with --prompt/--task before any herdr call; prompt block (wait, Enter, warning) is inside `if [[ -n $prompt ]]`, so skipped; test with idle fake herdr and `SQUAD_SPAWN_START_WAIT=600` returns; `test_squad_spawn` 119 OK | OK |
| AC3 | `rm -f` of marker for every spawn; stale-marker test | OK |
| AC4 | default respawn half of the new test: prompt sent, no marker, no `lazy` key; usage text lists `--lazy` in both scripts | OK |
| AC5 | `"lazy": true` only when lazy (`+ if $lazy == 1`); readers: squad-usage `orphan_fresh` reads agent+rule, squad-usage-hook jq selects session+rule, manager-guard `seen_keys` reads session/role/rule: all ignore unknown keys; `test_squad_usage` 30, `test_squad_usage_hook` 13, `test_squad_manager_guard` 25 OK | OK |
| AC6 | marker written after `--set-session` and before the prompt step (same place as C1); dry-run says "would write <path> (<uuid>)", writes nothing (asserted) | OK |
| AC7 | bash only, jq already used; marker byte-exact `<sid>\n` (asserted); `test_windows_safe` 14, `test_utf8_helpers` 14, `test_instructions` 16, `test_crlf_squad_files` 6, `test_winlaunch` 9, `test_team_lead_perms` 14, `test_squad_start` 49, `test_squad_retire` 4 OK | OK |
| evidence | Dev's `squad-evidence check` exit 0 reported | accepted |

#### Findings
None breaking.

#### Known failing on base
`test_templates::test_designer_may_write_only_ui_design_files`: fails the same way on `main` (87372fd) in my worktree, `templates/` untouched. SQ-17 grep over scopes/_done iterations: 0 hits, so first listing.

#### Follow-ups (not FAIL, SQ-4)
- `squad-spawn --lazy` also exits 2 when env `SQUAD_SPAWN_TASK` is set (it is the documented twin of `--task`). Harmless today (nothing in bin/ exports it); if the watchdog ever runs under it, a lazy respawn fails after the old pane is renamed. Ticket 03 should not export it.

## QA blackbox

### QA blackbox: ticket 01 (squad-respawn --lazy, squad-spawn --lazy), sha cd95bc1

Method: `live`, in a scratch squad (git project and squad under /tmp, scope `sc1`). I used a logging fake herdr (stateful: agent list, rename, start, close) and a stub `claude`. No real herdr, no live names, no worktrees. Source code was not read. Scratch dirs removed afterwards.

| AC | How | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 lazy respawn: no prompt, rest as today | live | `squad-respawn nm --lazy` as Manager; the old agent `nm` was live | herdr calls: rename nm→prev-N, `agent start nm --session-id S ...`, `pane close` of the old pane last. No `agent prompt`, no send-keys. Roster row `nm` has session S. `roles/nm.lazy` = S | pass |
| AC1 overrides kept | live | spawned `nm` with `--model opus --effort max`, then ran `--lazy` and a plain respawn | both starts carry `--model opus --effort max` | pass |
| AC1 missing-notes refusal / `--force` | live | removed `nm.notes.md`, `--lazy`; then `--lazy --force` | refused with the NOTE-1 message, rc 1, nothing renamed. `--force` respawned, marker written | pass |
| AC1 Team Lead refusal | live | `SQUAD_ROLE=team-lead`, `squad-respawn tl --lazy` | "a Team Lead may not respawn another team-lead", rc 2, no marker | pass |
| AC1 `--dry-run` | live | `squad-respawn nm --lazy --dry-run` | prints the rename, the `squad-spawn ... --lazy` line and the pane close; no `roles/nm.lazy`, no herdr change | pass |
| AC2 spawn --lazy | live | `SQUAD_SPAWN_START_WAIT=300`, fake herdr stays `idle`, `squad-spawn qa-blackbox nm --scope sc1 --lazy` | returns in 0.24 s; no prompt, no Enter, no wait or "did not start" warning, no "without --prompt" warning; marker `<sid>\n` (LF only, `od -c`), same id as the roster | pass |
| AC2 `--lazy` with `--prompt` or `--task` | live | both combinations | "--lazy sends no first message: drop --prompt and --task", rc 2, no herdr call | pass |
| AC3 plain spawn removes marker | live | marker present, `squad-spawn ... --prompt hello` | marker gone, prompt sent | pass |
| AC4 default respawn | live | `squad-respawn nm` | `agent prompt nm RESPAWN: ...` sent; no marker; event `{"rule":"respawn"}` with no `lazy` key; usage text of both scripts lists `--lazy` | pass |
| AC5 event | live | lazy respawn | `{"agent":"nm","role":"qa-blackbox","rule":"respawn","lazy":true}`; `rule` is `respawn` | pass |
| AC5 readers ignore the new key | shot | read the Developer's `## Behaviour` list; I did not read code | n/a | covered by QA whitebox |
| AC6 marker timing, dry-run | live | `squad-spawn --lazy --dry-run` | "would write .../nm.lazy (<sid>)" and nothing written. After a failed start the marker was not written | pass |
| AC7 tests | live | `python3 -m unittest test_squad_respawn test_squad_spawn` | 153 OK. `test_templates` fails the same on main 87372fd (pre-existing, `templates/` untouched) | pass |

Verdict: PASS.

Follow-ups (not blocking):
- A respawn whose spawn fails (fake `agent start` exits 1) still appends the `respawn` event, and the lazy flavour adds `lazy:true`. The old agent is put back and rc is 1. The default respawn does the same, so this is pre-existing. The watchdog (03) should expect a failed lazy respawn to leave an event behind.
- `test_templates::test_designer_may_write_only_ui_design_files` fails on main too (known failing on base).
