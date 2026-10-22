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
