# Evidence: 08 Settings are template plus a squad overlay, merged at spawn

## Known limits

Known limit (B08-7): a local file cannot remove a template entry. `permissions.allow`, `deny` and `ask` are unions, so removing a template allow is a plugin change, not a squad overlay.
Other notes: a fail-closed exit 2 (QA blackbox without `codePaths`) leaves `roles/<agent>.rules.md` behind in composed mode (non-blocking, both QAs).
Final sha passed by both QAs: c8f4029.

## QA whitebox

### QA whitebox 08, c8bd1cd (round 1): FAIL

Ran: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadsettings test_squad_spawn test_team_lead_perms test_model_effort_settings test_windows_safe` → 100 OK. Merge logic, codePaths expansion, truth table, Team Lead and QA-b cases: correct and tested.
Also ran squad-spawn by hand in a scratch composed squad (scope.md pin = this worktree's HEAD, `settings/dev.local.json`, fake herdr).

#### Findings
1. **bin/squad-spawn:153-157, composed mode + overlay + `--dry-run` exits 1.** Reproduce: scratch squad with `process.local.md`, scope.md `plugin: 0.4.1 <sha>`, `settings/dev.local.json`; `squad-spawn dev x --scope sc1 --dry-run` → `no settings template for dev at …/_runtime/0.4.1-<sha12>/templates/squad/settings/dev.json`, exit 1. `squad-process runtime --dry-run` does not materialise the runtime, so `tpl_root=$runtime` points at nothing. Same spawn without `--dry-run` works (effective file written to `<home>/roles/x-dev-1.settings.json`, passed via `--settings`, Team Lead-style merge correct). `--dry-run` is the preview used by `squad-respawn --dry-run` and the tests. Pass: dry-run on a composed overlay squad exits 0 and prints the `--settings <home>/roles/<agent>.settings.json` argv, without writing it (e.g. read the template from the plugin root when the runtime is not materialised, or skip the merge in dry mode); test for it.
2. **No test for the composed-mode pinned template (HANDIN claim; open item from A).** `tests/test_squadsettings.py` `SpawnTest` builds only legacy-mode squads (`process.md`), so `tpl_root=$runtime` (squad-spawn:153) is never exercised; finding 1 hides there. Pass: a composed-squad spawn test where the pinned runtime's template differs from the running plugin's template and the effective file shows the pinned one.
3. **No test that a real (non-dry) spawn writes the effective file.** `SpawnTest` is dry-only; the `printf > $settings` at squad-spawn:212 has no assertion. I verified by hand it works. Pass: one test using the fake herdr that reads `roles/<agent>.settings.json` and checks it is valid JSON, has the local scalar and the unioned allow list, and no `CODE_PATHS_SET_BY_SQUAD_INIT`.

4. **bin/squadsettings.py:expand_code_paths, fail-closed rule (Tech Lead ruling, tasks/design.md "08"):** placeholder present and `codePaths` empty or missing must exit 2 and spawn nothing; c8bd1cd silently drops the entry (`test_placeholder_dropped_without_code_paths` asserts the opposite) so a QA blackbox with a bare `{}` overlay can read the code. Also design.md says the qa-blackbox effective file gets `Read(//<root>/.worktrees/**)` as `squad-init` does; not produced. Pass: exit 2 test via squad-spawn (nothing written, nothing started), worktrees entry test, old test replaced.

#### Notes (not blocking)
- `permissions.ask` and other lists are replaced by the local value (only allow/deny union), as the ticket says; no test pins that.
- No-local/no-full-file path keeps the placeholder (before-08 behaviour); effective files never contain it.

### Round 2: b32ab34 (diff c8bd1cd..b32ab34): PASS

Ran `test_squadsettings test_squad_spawn test_team_lead_perms test_model_effort_settings test_windows_safe test_squad_respawn` → 122 OK. Re-ran by hand in a scratch composed squad with fake herdr:
- Finding 1 fixed: `--dry-run` on composed + `dev.local.json` exits 0, prints `--settings <home>/roles/d1.settings.json`.
- Finding 3 fixed: non-dry writes `roles/d1.settings.json` (tmp + mv).
- Finding 4 fixed: qa-blackbox `{}` overlay exits 2 with a clear message, nothing started (herdr log shows only `agent list`); with `codePaths` the effective deny has `Read(//x/bin/**)` and `Read(//<project>/.worktrees/**)`, no placeholder.
- Finding 2 fixed: ComposedSpawnTest present (pinned wins, moved pin reaches next spawn, missing pinned template exits 1).

Non-blocking: a fail-closed refusal (exit 2) happens after compose, so `roles/<agent>.rules.md` is left behind (harmless; no agent, label or worktree created). B08-7 (local cannot remove a template allow) goes in evidence as a known limit, as the Developer said.

### Round 3: c8f4029 (diff b32ab34..c8f4029): PASS
QA-b finding (composed squad with no local file used the running plugin's template): `settings=` and `key_of` now read `$tpl_root`; the dry-run fallback to the plugin root still precedes them. New `test_no_local_file_still_uses_the_pinned_template`. Ran the 6 test files: 123 OK.

## QA blackbox

### QA blackbox: ticket 08 (settings overlay), sha c8bd1cd

Verdict: **FAIL** (1 finding, B08-5). Method: scratch squad in /tmp (git repo, stub `herdr`, copy of the template settings), `bin/` from branch rcu-3 @ c8bd1cd, `squad-spawn` with and without `--dry-run`, effective file read from `scopes/<scope>/roles/<agent>.settings.json`. No code read. No screenshots (CLI only).

| # | Check | Did | Saw | Result |
|---|---|---|---|---|
| 1 | Old layout (full `dev.json`, no local) | `squad-spawn dev x1 --dry-run` | one stderr warning "full settings file, not an overlay; ticket 09 (adopt) converts it", argv `--settings <squad>/settings/dev.json --model sonnet --effort medium` as before | pass |
| 2 | Overlay merge (dev.local.json: model opus, effort high, allow +2 (1 dup of template), deny +1, custom key, codePaths) | `squad-spawn dev x2` | `--settings <home>/roles/x2.settings.json`; model opus, effort high; allow = template + `Bash(mytool:*)` only (dup dropped, nothing lost); deny + `Read(//secret/**)`; custom key kept; advisorModel kept; placeholder `CODE_PATHS_SET_BY_SQUAD_INIT` absent; no `codePaths` key | pass |
| 3 | Team Lead, empty `{}` local | spawn | effective allow has `Bash(squad-spawn dev:*)` and `Bash(herdr agent list/get/read:*)` | pass |
| 4 | QA blackbox with codePaths | spawn | deny contains `Read(//…/src/**)`, `Read(//…/lib/**)`; no placeholder | pass |
| 5 | `--model haiku --effort low` flags over local | dry-run | argv shows haiku/low | pass |
| 6 | Relative codePaths | spawn | exit 2, "codePaths … must be a list of absolute paths" | pass |
| 7 | Malformed local JSON | spawn | exit 2, "cannot read overlay … Expecting property name…" | pass |
| 8 | Template missing (pinned runtime) | spawn | exit 1, "no settings template for dev at …/_runtime/…/dev.json" | pass |
| 9 | Both full and local present | dry-run | warning "dev.json is ignored: dev.local.json wins", local used | pass |
| 10 | Overlay case uses the **pinned** template | composed squad (`process.local.md`, pin written by `squad-start`, SQUAD_PLUGIN_DIR = branch); edited the pinned `_runtime/…/templates/squad/settings/dev.json` (model haiku, extra allow `PINNED-MARK`), local `{}` | effective file has model haiku and `PINNED-MARK` | pass |
| 11 | **No local file, composed pinned squad**: pinned template is used | same edited pin, no `dev.local.json` and no full file; `squad-spawn dev c5 --dry-run` | `--settings <running plugin>/templates/squad/settings/dev.json --model sonnet`; the pinned template (haiku, PINNED-MARK) is ignored | **FAIL** |

#### Finding F1 (AC B08-5: pod runs on its pinned runtime's settings)
Given a composed squad pinned to runtime R, when a role has no `settings/<role>.local.json`, then `--settings` and the model/effort come from the **running plugin's** template, not R's. Row 10 and 11 differ only by the presence of a local file. This is the open item from scope A ("08: spawn `--settings` path (still the running plugin's template)"), and the spec's L1 (version skew inside one pod). After a plugin upgrade, such a role gets new-plugin settings while the rest of the pod runs the pin. Expected: same pinned template as row 10 (or the pinned template file path).

Cleanup: scratch dir /tmp/qab08.xEkx only; no servers or sessions started (stub herdr).

---
### Re-test at c8f4029 (after returns b32ab34, c8f4029): **PASS**
Same scratch method (script outside repo: /tmp/qab-tools/t08.sh; scratch deleted after). Composed squad pinned by `squad-start`; pinned runtime's `dev.json` edited (model haiku, allow `PINNED-MARK`).

| Check | Saw | Result |
|---|---|---|
| F1 / B08-5: no local file | `--settings <squad>/_runtime/0.4.1-c8f4029f5fbd/templates/squad/settings/dev.json --model haiku` (pinned values) | pass |
| Local `{}` | effective: model haiku, PINNED-MARK present, no placeholder | pass |
| Local model/effort/allow/deny | opus/high, allow union no dups, deny added | pass |
| Flags | `--model haiku --effort low` | pass |
| Team Lead `{}` | `Bash(squad-spawn dev:*)`, herdr entries | pass |
| QA-b codePaths | denies `Read(//…/src/**)` and `Read(//…/.worktrees/**)`; no placeholder | pass |
| QA-b local without codePaths | exit 2, message names the missing list; no agent started | pass |
| Relative codePaths / bad JSON | exit 2 with clear message | pass |
| full + local | warning "dev.json is ignored: dev.local.json wins" | pass |
| B08-6: pin moved to 9.9.9, new template has NEWPIN-MARK / opus | next spawn uses `_runtime/9.9.9-…/dev.json`, model opus | pass |
| Legacy squad (process.md, full dev.json) | argv `--settings <squad>/settings/dev.json` + warning naming 09 | pass |

Minor, not a FAIL: a refused QA-b spawn (exit 2) leaves `roles/<agent>.rules.md` behind (no settings, no roster row, no session).
B08-7 known limit (local cannot remove a template allow) seen: union only.
