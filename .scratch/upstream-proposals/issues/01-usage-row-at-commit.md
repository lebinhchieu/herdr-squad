# 01 Read your usage row at commit and verdict

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Problem

The usage Stop hook (`bin/squad-usage-hook`) fires only at the end of a turn, and only once per session per rule (line 26). A Developer in one long turn reached 225k and 287k with no `fresh` event (plugin task-claim-gates). A Tech Lead reached 316k, a BA 167k and a Team Lead 159k (squads-mod). Board saw 9 Developers over 120k.

## Change

Add one cost rule for every role except the Manager (COST-8 already covers the Manager):

- Run `squad-usage` in the same command as each `git commit`, `HANDIN`, `PASS`, `FAIL` or `DECISION` you send.
- Past your `line` column: act as COST-3 (respawn), or COST-5 for a Developer (retire, or respawn once mid-ticket). Save findings or notes first.
- A Developer ends each `HANDIN` with `ctx <n>k`.

Use the `line` column. Do not add a fixed 100k or 150k.

## AC

- AC1: the new rule (COST-16) is attached to dev, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer and architect, with `aware: manager` (`squad-process who <ID>`). COST-8 already covers the Manager.
- AC2: it names no fixed token number; it points at `line` and at COST-3 / COST-5.
- AC3: `python3 bin/squad-process lint` exits 0.
- AC4: the Developer quotes `squad-process upgrade --check --squad-dir <dir> --plugin-root <worktree>` for `.claude/squads/board` and `.claude/squads/plugin`; each source op (board SQ-5, plugin SQ-3c, SQ-3d) shows as `add` (kept) or `stale`, and Comments name COST-16 as the plugin rule that replaces it. The squads drop the ops by hand after re-pin.
- AC5: the rule text says "the PO", never a name; the Developer's composed bytes grow by at most 450 B (measured 313 B) and `LIMIT` is raised by that measured amount only.
- AC6: Duties: SQ-10 files (`tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`) plus `grep -rl` hits of COST-16.

## Comments
