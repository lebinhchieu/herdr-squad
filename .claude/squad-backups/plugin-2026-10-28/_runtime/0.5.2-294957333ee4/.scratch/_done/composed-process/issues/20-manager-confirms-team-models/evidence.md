# Evidence: 20 Manager confirms the team's models

**The Manager's first move shows one table of roles, models, efforts and advisor ([START-3b]); the PO's changes go to `scope.md` as `model <role>: <model> <effort>`; `squad-spawn` reads them between a recorded override and squad settings.**

Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_team_models test_squad_spawn test_model_effort_settings test_windows_safe test_squad_start test_instructions test_sizes test_squad_migrate test_templates test_squadcompose test_dev_rules_size test_qab_optional test_squad_respawn test_process_history test_squadupgrade test_squadruntime` (OK after the steps below). `squad-process lint` clean. sha: see the HANDIN.

## Behaviour

Tests in `tests/test_team_models.py` (20), stub herdr, argv read from `--dry-run` or the herdr log:

- **Precedence** (`PrecedenceTest`, values differ per level: template `sonnet medium`, settings `haiku low`, scope.md `opus xhigh`, override `sonnet[1m] max`): settings beat template; scope.md beats settings; a recorded override (replayed by `squad-respawn --dry-run`) beats scope.md; flags beat scope.md per key (`--model` alone keeps scope.md's effort); other roles are untouched; a Team Lead's `dev` spawn (`SQUAD_ROLE=team-lead`) picks the line up; a flat squad is unchanged.
- **Parse** (`ParseTest`): `model dev: sonnet`, `… turbo`, missing colon, `model:`, bad model chars, extra token → exit 2 naming the line and `scope.md`; a malformed line of another role also refuses, with no worktree and no herdr call; duplicate role → exit 2; unknown role → warning, ignored; prose starting with "model" and an HTML comment are not model lines; a `scope.md` made from the template (it now carries the format comment) yields no override.
- **Never recorded** (`RecordedTest`): a real spawn from scope.md writes no `.overrides`; after editing `scope.md`, `squad-respawn --dry-run` passes no `--model` and the next new spawn uses the new value (mid-scope change applies to the next spawn/respawn only); a `--effort` flag is recorded, the scope.md model is not.
- **`squad-start --resume --dry-run`** (`StartResumeTest`): `manager model: haiku (from scope.md)`; with a recorded override and `--effort max`: `opus (from recorded override)` / `max (from flag)`.
- **Rule** (`RuleTest`): START-3b has the table, keep/change offer, format and example, defaults, next-spawn rule, "only when the PO asks", the precedence; goal Manager "for each scope"; `squad-process who START-3b` shows `manager` acting at S, M and L; SIZE-1 points at it.
- **Advisor column**: shown as the effective value, read-only unless 18's probe found an off value (START-3b text; tech-ac decision 6). No code reads or writes it.

## Notes for the checkers

- `golden.json` (`tests/fixtures/qab/golden.json`) diff is hashes only (12 lines). On base f0a965a `test_qab_optional...golden` already failed 5 subtests (manager S/M/L yes, M/S no): ticket 31's SPAWN-4 edit in `spawning.md` without regenerating the golden. This ticket regenerated all roles with the test's own `compose`/`normalise`: manager (31's SPAWN-4 plus START-3b and the SIZE-1 pointer) and tech-lead (START-3b and SIZE-1 index lines only; their composed text lists both IDs). Every other role's hash is unchanged.
- Files outside the ticket's first Touches, each approved by the Tech Lead (DECISION 20): `templates/scope/scope.md` (format comment), `skills/squad-process-update/changelog.md` (START-3b added, SIZE-1 retargeted), `tests/fixtures/qab/golden.json`.
- Deploy: unchanged from tech-ac decision 9 (legacy squads get the new rules at their next respawn).

## QA blackbox

### QA blackbox — ticket 20 (team models) — sha 2267991

Method: scratch squad /tmp/qab19/r, stub `claude`/`herdr`, `squad-spawn --dry-run`, `squad-start --resume --dry-run`, `squad-process who/compose`. Branch squad/plugin/sizes-and-models/plugin-dev-sm-20. No code read.

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 first-move rule at every size | `squad-process who START-3b`; `compose manager` for S/M/L homes; compose dev/qa-b/team-lead | `S: acts: manager; M: acts: manager; L: acts: manager`; START-3b in Manager rules at S, M, L; absent from dev, qa-blackbox, team-lead. Rule text: one table (role, model, effort, advisor), keep/change offer, write changed rows to scope.md, then spawn; goal Manager per scope | PASS |
| 2 `model <role>: <model> <effort>` used by spawn | scope.md `model dev: haiku low`; settings dev.json = sonnet medium | baseline `--model sonnet --effort medium`; with line `--model haiku --effort low`; qa-blackbox (no line) unchanged `sonnet high` | PASS |
| 3 precedence | flags `--model opus --effort high` over scope.md; recorded `dev-x.overrides` (opus/max) via `squad-respawn` path (passes it as flags); scope.md over settings (above); `--model opus` alone | flags: `opus high`; flag model only: `opus low` (effort falls to scope.md per field); recorded override is replayed as flags by squad-respawn (read in code-free output: respawn dry-run needs roster, so checked as flag case); settings/template lose to scope.md | PASS (respawn replay not run end-to-end here) |
| 4 malformed / unknown | lines `model dev: haiku`, `model dev haiku low`, `model dev: haiku ultra`, `model dev: `, duplicate `model dev:` x2; `model wizard: haiku low` | each malformed: exit 2, `malformed line in …/scope.md: <line> (expected: model <role>: <model> <low|medium|high|xhigh|max>)`; duplicate exit 2 `role dev given twice`; unknown role: `warning: … unknown role 'wizard' … (ignored)`, spawn proceeds rc=0 with the dev line applied | PASS |
| 5 mid-scope | changed scope.md between two dry-run spawns; looked for anything touching running agents | next spawn picks up new value; spawn never edits other agents' files (roles/ unchanged); rule text says respawn running agents only when PO asks | PASS |
| squad-start --resume | scope.md `model manager: opus high`, no recorded override | `manager model: opus (from scope.md)`, `effort: high (from scope.md)`; recorded override → `(from recorded override)`; flags → `(from flag)`; none → `(from squad settings)` | PASS |
| Tests | `cd tests; python3 -m unittest test_team_models` | 20 tests OK | PASS |

Notes (not fails): model name is not validated (`model dev: banana low` accepted, spawn rc=0); flag/scope.md precedence is per field (model flag + scope.md effort mix).

## QA whitebox

### 20 QA whitebox — PASS @2267991

Checked: clean worktree; diff 34b65bc..2267991 (19 merged first, fb09501) — squad-spawn scope.md level, squad-start resume/dry-run sources, START-3b, SIZE-1 pointer, scope.md template comment, changelog (START-3b, SIZE-1), golden.json hashes.
Ran (PYTHONDONTWRITEBYTECODE=1): lint ok; test_team_models test_squad_spawn test_model_effort_settings test_windows_safe test_squad_start test_sizes test_qab_optional test_instructions + golden readers test_squadcompose test_squadinbox test_squadrules test_squadupgrade + test_process_history test_squadruntime test_dev_rules_size → 473 tests OK (golden: the 5 red manager subtests from 31 are green).
Live data: ran squad-spawn's gate regex over every real scope.md in the repo + the template: no line gated (no false "malformed").

#### AC
- Precedence per level with distinct values (template/settings/scope.md/recorded override/flags), argv from stub: OK. Team Lead `dev` spawn picks the line up: OK. Flat squad unchanged: OK.
- Malformed → exit 2 naming line; unknown role warns; duplicate refuses; prose/HTML comment not model lines: OK.
- scope.md value never in `.overrides`; mid-scope change applies at next spawn/respawn: OK. Resume dry-run shows scope.md level: OK.
- `who START-3b`: manager at S, M, L; goal Manager per scope in text: OK. Advisor column read-only, no code: OK.
- golden.json: hashes only; regenerated by the test's own compose/normalise; unchanged roles' hashes unchanged.

#### Follow-up (not blocking)
- A goal Manager's own spawn (no scope_dir) reads no scope.md — correct for "per scope", but a `model manager:` line only applies to a scope Manager.
- Files outside original Touches (scope.md template, changelog, golden.json) were approved by TL DECISION 20.
