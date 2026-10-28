Status: ready-for-agent
Type: task
Task ID: 16
Touches: `CONTEXT.md`, `README.md`, `docs/adr/0005-process-versioning.md`, `docs/adr/0006-process-writing-rule.md`, `docs/adr/0008-spawn-overrides-survive-respawn.md`, `docs/adr/0010-team-lead-runs-the-pod.md`, `docs/adr/0016-process-composed-per-role.md`, `.scratch/composed-process/issues/16-promotion.md` (this ticket, replaces the old one) and `.scratch/composed-process/issues/16-promotion/evidence.md`
Does not touch: `docs/adr/0015-*` (already updated in ticket 21), `CLAUDE.md` (done in ticket 29), any rule file, `bin/`, `agents/`, `tests/`, `skills/`
Harness: `bin/squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_templates test_sizes test_process_writing test_instructions`
Blocked by: 15 (passed). Base: the sha the Tech Lead names when 15 passes.

# 16: Promotion

**Done when the glossary, README and ADRs describe the composed process and the new sizes, and nothing in them describes the retired copy-and-merge or the old sizes.**

## What
Apply `/home/chieule/workspace/squad/.claude/squads/plugin/goals/composed-process/promote.md` exactly (read it first; in the evidence cite its row numbers 1-7, do not copy it). It holds the exact wording per file in Blocks A-E. Do not add a fact it does not hold; if a sentence there looks wrong against the code, stop and `ASK 16:` the Tech Lead.

Order of commits: (1) ticket file copy, (2) ADRs, (3) README, (4) CONTEXT.md, (5) evidence. One commit per file group so a review reads one diff at a time.

## Technical AC
1. Every term in Block C appears once as `**Term**:` in CONTEXT.md (count printed in the evidence by `python3 -I`); `Process version` and `Section view` appear nowhere in CONTEXT.md, README.md or `docs/adr/0016-*.md` (ADR 0005's history text may keep its own words; list the hits).
2. `grep -n "S (Tech Lead\|(S: Tech Lead\|process-version\|M (+ BA" README.md CONTEXT.md` prints nothing; the Size, Risk flag, Done, Manager, BA, Team Lead, Tech Lead, Single point of contact, Manager traffic, QA, Integration task, Token Coach, Promotion entries read as Block D says.
3. ADR statuses: 0016 `accepted (composed-process, …)`, 0005 `superseded by 0016 (composed-process)`; 0006, 0008, 0010 carry the amendment line of Block rows 3-5; the old "once accepted" wording is gone. `git diff` of ADR 0005/0006/0008/0010 shows no body line removed other than those named in Block rows 2-4.
4. README: a `## The process` section of at most 15 lines placed before `## The layers`; line 21 sizes sentence, lines 28, 32, 43, 44, 50 changed as the table says; no other README line changed.
5. Wording of the S Done rule says Sonnet at high effort for the review subagent and keeps the advisor on Opus; `grep -n "Opus" CONTEXT.md README.md docs/adr/0016-*.md` shows only advisor lines.
6. `git diff --stat` shows only the Touches files. Lint and the Harness tests pass (counts in the evidence). No full suite run by the Developer.
7. Block A's every fact is traceable: the evidence has a table "ADR 0016 bullet → source" (`decisions.md` line, summary, or ticket) for each bullet, and flags none it could not source.

## Technical notes (Tech Lead)
- This ticket writes no code and no rule, so Developer rules stay at 5119/5120 B.
- `promote.md`'s Block C/D wording is final; wording changes are `ASK`s, not edits. The Tech Lead reviews the diff against it line by line.
- After this passes the Tech Lead runs the full suite `--tz` once on the final sha (receipt in `evidence/`), writes the goal summary and appends the goal decisions.

## Comments
