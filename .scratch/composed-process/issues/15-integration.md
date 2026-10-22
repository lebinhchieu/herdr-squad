Status: ready-for-agent
Type: task
Task ID: 15
Touches: `.scratch/composed-process/issues/15-integration.md` (this ticket, replaces the old one), `git mv` of the three tracked `*.evidence/` folders listed below, `.scratch/composed-process/issues/15-integration/evidence.md` (new). Nothing under `templates/`, `bin/`, `agents/`, `skills/`, `tests/`.
Does not touch: any rule file (Developer rules at S sit at 5119/5120 B; this ticket must not change them), `skills/squad-process-update/history/**`.
Harness: `bin/squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_evidence test_process_conversion test_sizes test_dev_rules_size test_squadcompose test_templates`
Blocked by: 32 (passed, 3dcc7b2). Base: `squad/plugin/integrate-promote/plugin-dev-ip-1` @ 3dcc7b2.

# 15: Integration (final check of the stacked chain)

**Done when the base carries all four passed scopes (A, B, C1, C2) and ticket 32, no `*.evidence/` folder is left, lint and the targeted tests pass, and one live probe shows two roles reading only their own composed rules.**

## Why this is smaller than the old ticket
Scopes A, B, C1 and C2 each ended with their own integration task and are already stacked: sm-28 contains C1, B and A. There is nothing left to merge, only to prove, plus the evidence mop-up that ticket 21 promised (its "Leftovers"). The full suite is NOT in this ticket: the Tech Lead runs it once with `--tz` on the final sha after ticket 16 (the promotion edits files the suite reads), so one run covers both.

## What
1. Copy this file to `.scratch/composed-process/issues/15-integration.md` (replace the old one; same commit as nothing else) so the evidence folder has a sibling.
2. **Chain proof.** Quote exit codes of `git merge-base --is-ancestor <sha> HEAD` for each passed tip: A `b66036b`, B `4901cab`, C1 `2e81e5e`, C2 `853b0a4` (branch tip of sm-28), 32 `3dcc7b2`; and `git log --oneline 853b0a4..HEAD` (expect only 32's commits). A non-zero exit is BLOCKED, not fixed.
3. **Mop-up.** `git mv` (pure rename commit, separate from other edits) each tracked `.scratch/composed-process/issues/*.evidence` folder to the same name without the suffix: `20-manager-confirms-team-models`, `28-integration` (orphan: no `28-*.md`, stays an orphan folder, as ticket 21 did for 22), `32-s-review-subagent-sonnet-high`. Fix any link in a tracked doc by grep (`grep -rn '\.evidence' .scratch CONTEXT.md docs README.md` outside `skills/**/history/**` and closed squad folders). Use `git mv`, not `squad-evidence add`.
4. **Live probe** (temp dir under `/tmp`, nothing in the repo or the real squad folders): follow `.scratch/composed-process/issues/05-spawn-attaches-rules-and-pin/evidence.md` (scratch plugin repo with committed pin, stub `herdr`, real `squad-spawn`, then replay of the argv with `claude -p --model haiku`, no tools). The squad's `process.local.md` adds rule `PROBE-DEV` for `dev` only and `PROBE-QAW` for `qa-whitebox` only, each body a distinct marker phrase. Spawn a Developer and a QA whitebox in an M scope; each replay answers YES to its own marker and NO to the other's. Commands, argv and answers go in the evidence. Total spend under $0.05.
5. Evidence per the `evidence` skill into `.scratch/composed-process/issues/15-integration/evidence.md` (written by this branch's `squad-evidence`).

## Technical AC
1. Every `--is-ancestor` exits 0; `git log 853b0a4..HEAD` lists only 32's commits.
2. `find .scratch -name '*.evidence'` prints nothing; `git ls-files | grep '\.evidence/'` prints nothing; `git show --stat -M <mop-up commit>` lists only renames at 100% similarity; `squad-evidence check` exits 0 on each moved `evidence.md` (for 28, `check` only: no sibling ticket).
3. `bin/squad-process lint` exits 0. The Harness tests pass (counts in the evidence). `test_dev_rules_size` passes with composed Developer rules at S unchanged (5119 B, quote the number).
4. `git diff --stat 3dcc7b2..HEAD` shows only renames, `issues/15-integration.md` and `issues/15-integration/`, plus link fixes in tracked docs, each named.
5. The probe: each of the two roles answers YES to its own marker and NO to the other's (4 answers in the evidence); the argv shows each role's own composed file; scratch dirs removed and every process started stopped by PID at the end.
6. No full suite run by the Developer.

## Technical notes (Tech Lead)
- Ticket 21 AC 3 is final here; its evidence-folder rule is already in the base, so the new tool writes the new path.
- Do not edit any rule file: 32 left 1 B of headroom.
- `git mv` of a folder whose files are unchanged is the only way history follows; do not copy and delete.

## Comments
