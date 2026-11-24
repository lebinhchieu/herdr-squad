# Task 02: Drop old-layout migration (squad-migrate, adopt)

Status: done (both QA PASS e31aaf8, evidence 5274494)
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Team: tech-lead, qa-white, qa-black. Suite: `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` (CLAUDE.md Running tests); full suite by Tech Lead on final sha. Branch from repo HEAD (main) unless noted. Hand in to both QAs. A risk flag or user-visible change found: `BLOCKED <task>`.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`.

Order changed (FINAL): 02 runs first, in parallel with 03; 01 builds on 02's passed sha. Branch from repo HEAD.

## Touches (Tech Lead confirms)
`bin/squad-migrate`, `bin/squadadopt.py`, `squad-process adopt`, `squad-start` warning about old layout, their tests, SKILL.md "Adopting" section, README/docs mentions.

## PO decision (Q1)
Yes drop `squad-migrate` + `squad-process adopt` (flat-to-per-scope converter and legacy adopt). Git history keeps them.

## AC
Tech Lead writes technical AC in `## Design notes` below.

## Design notes
(Tech Lead, 2026-10-28)

**ORDER CHANGE (Manager to confirm): 02 runs BEFORE 01, not after.** `squadadopt.py` reads `history/process-v6.md` + `process-v6.map.md` (lines 110, 547) and `squadprocess.squad_version`; `test_squadadopt` reads `history/process-v6.md`. 01 deletes all of those, so 01 cannot pass alone while `adopt` lives. New order: 02 ∥ 03, then 01 (branch from 02's passed sha), then 04. Replace "Depends on 01" above accordingly.

### Touches (confirmed; LC-9)
Delete: `bin/squad-migrate`; `bin/squadadopt.py` (after moving `scaffold`, below); `tests/test_squad_migrate.py`; `tests/test_squadadopt.py` (scaffold cases ported, below); `tests/fixtures/upgrade/live-squad.local.md` only if no test reads it after (only `test_squadadopt:408` does today; `test_squadupgrade` globs `fixtures/upgrade/overlays`: check before delete).
Edit:
- `bin/squad-process`: drop `adopt` from usage + dispatch; `scaffold` dispatch goes to the new module. No dead `squadadopt` import.
- NEW `bin/squadscaffold.py`: `scaffold`, `cmd_scaffold`, `main` (scaffold only), plus the helpers they use (`AdoptError`→rename `ScaffoldError`, `_atomic`, `_slurp`, `new_pin`, `_template_roles`; lines 40-106, 676-709 of squadadopt.py). `squad-process scaffold` and `/squad:squad-init` MUST keep working: they live in squadadopt.py today.
- Messages that name a removed command (same refusal/exit code, new text): `bin/squadupgrade.py:476,539` ("not adopted ... run adopt"), `bin/squadcompose.py:79,315-319`, `bin/squadteam.py:88`, `bin/squad-spawn:210`, `bin/squad-start:327` (flat layout: no longer "would convert it"), `bin/squad-log-message:2` (comment), `bin/squadprocess.py:269` stays for 01 (it dies there).
- `skills/squad-process-update/SKILL.md` ("Three paths" para, step 1 `squad-migrate`, whole "Adopting an old squad" section), `skills/squad-init/SKILL.md:15`, `skills/squad-start/SKILL.md:12` (check; flat-layout wording).
- `README.md` lines 27, 48, 49, 76 and `CONTEXT.md` 125, 137, 138: delete or minimally reword text naming `squad-migrate`/`adopt`; no new prose, no new terms (04 owns ADR 0019 and glossary additions).
- Tests (remove the dropped cases, never skip): `test_team_cli.py` (adopt/converter + squad-migrate team cases, import `squadadopt`), `test_utf8_helpers.py:176` + notice at :79, `test_windows_safe.py:118-123`, `test_squad_start.py:545`, `test_squadcompose.py:597,608`, `test_squad_spawn.py:203,807,817,962,972`, `test_squad_respawn.py:316`, `test_old_language_inventory.py` + `test_promotion_0_6_0.py` allow-lists (counts for `squad-migrate`, `squadadopt.py`, and any file whose count moves).

### Decisions (compatibility, LC-12)
1. **No silent removal.** `squad-process adopt` / `squad-migrate` are gone as commands. `squad-process adopt` then fails through argparse/`squadrules_cli` with a clean usage error (exit 2, no traceback). `bin/squad-migrate` simply does not exist (shell "not found"); do not leave a stub.
2. **Refusals stay refusals, text changes.** Old-format `scope.md` (`size:`/`design:`/`architecture:`/`qa-b:`) still exits 2 in compose/spawn/team; message tells the manual step: replace those lines by one `team:` line (ADR 0018; README states the roles). A squad with `process.md` and no `process.local.md` (legacy mode) KEEPS spawning with plugin rules (squadruntime/spawn/close mode detection stays: not in the PO's Q1); only the stderr hint changes (no `adopt`; point at `squad-process scaffold` / `/squad:squad-init` for a new composed squad). A flat squad: `squad-start` still refuses, text without "convert".
3. **Kept on purpose:** `sr.legacy_team` (≈10 test files use it as helper), `OLD_WHEN_KEYS`, old-format detection (`old_format_error`, `sc.old_format_error` caller in squadruntime:368). Do not rename or remove.
4. **Feature loss to report:** `squad-migrate --scope-to-goal` (wrap a scope in a goal) goes with the script; no agent, skill or hook calls it (grep). Manager to mention it at the PO check-in; ADR 0019 (task 04) records it. Not PO-blocking: Q1 said drop `squad-migrate`.

### Technical AC
Common (all tasks): C1 evidence.md lists each removed path/command with `grep -rn` proof of zero remaining references in bin/ hooks/ skills/ agents/ templates/ tests/ docs/ README.md CONTEXT.md CLAUDE.md (excluding `.worktrees`, `.scratch/_done`, `docs/adr/` history); C2 `grep -rl '<removed path or printed string>' tests/` run and every hit passes (CLAUDE.md); C3 targeted tests green, suite receipt on the final sha; C4 no edit outside Touches.
- T1 `bin/squad-migrate`, `bin/squadadopt.py`, both test files gone; `git grep -n "squadadopt\|squad-migrate\|squad-process adopt"` outside `docs/adr/`, `.scratch/`, `skills/*/changelog.md` and ticket/history text returns nothing.
- T2 Scaffold survives: `squad-process scaffold --squad-dir <scratch>` output identical to before (QA blackbox diffs against main's output on a scratch dir); the scaffold test cases from `test_squadadopt.py` live in a new `tests/test_squadscaffold.py` with the same assertions (list moved vs dropped cases in evidence: no scaffold coverage lost). Output byte-identical; error text changes only where `AdoptError` becomes `ScaffoldError`, and evidence lists each changed message. `squad-init` SKILL still references only existing commands (`test_instructions` command-exists test green).
- T1b `tests/test_squadupgrade.py:278` glob `live-squad.local.md` (comment "built by `adopt`") is edited when its fixture goes (drop the glob entry and comment); `tests/fixtures/upgrade/live-squad.local.md` deleted only if that glob is gone; evidence states which. Add this file to Touches.
- T3 `squad-process adopt` → exit 2, one-line usage error, no traceback; `squad-process --help`/module docstring lists no `adopt`.
- T4 Old-format `scope.md` in a scratch home: `squad-process compose dev --home <h>` exits 2, stdout empty, stderr names `scope.md:<line>` and the manual `team:` step, not a removed command. Legacy squad (process.md only) `squad-spawn` still spawns, stderr hint has no `adopt`. Flat squad: `squad-start` exits non-zero with a message that does not say it converts.
- T5 `squad-process upgrade --check` on a squad without `process.local.md`: still refuses (exit 2), message names no removed command.
- T6 Allow-list tests (`test_old_language_inventory`, `test_promotion_0_6_0`) updated to exact new counts, not loosened.
- T7 No behavioural change to composed squads: `squad-process compose/upgrade/team/lint/runtime/prune/mode`, `squad-start`, `squad-spawn` for a composed squad: existing tests unchanged and green.
- T8 Tech Lead runs the full suite `--tz` on the final sha (receipt in `$SCOPE_DIR/evidence/`).
- Risk: breaking CLI contract (decided above, no PO escalation: PO already said drop in Q1). Deploy order: none (plugin-only; ship with 01). Rollback: git revert; no data written.
