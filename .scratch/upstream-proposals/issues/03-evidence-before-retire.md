# 03 Developer stays until the evidence check is clean

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Problem

LC-20b tells the Developer to send `STATUS NN: passed` on every `PASS`, and the Team Lead then retires it. But EVID-2b and EVID-2d say the Developer assembles the evidence after all PASSes. So a Developer can be retired before the evidence is assembled. In tl-wake-status 01 was reported passed with empty QA cells, and a second Developer (13 turns) had to fill them.

EVID-2d is titled "Manager" and sends `HANDIN ... evidence sha` to the Manager. The Team Lead is always on the team since v20, so the Tech Lead redirected this twice.

## Change

- EVID-2d: retitle it "Assemble evidence, the task's Developer". Send the `HANDIN <task>: evidence sha <sha>` to the plan owner (the Team Lead). Add: "Nobody asks the Manager to assemble it."
- LC-20b: the Team Lead keeps the Developer until both checkers have PASSed and the evidence commit is in. It runs `squad-evidence check <folder>` on the final sha. Only on exit 0 does it retire the Developer and record `STATUS <task>: passed`, quoting the exit code and sha.
- Check that EVID-2e and EVID-9e (the Manager checks the evidence commit) still match, or move them to the Team Lead.

## AC

- AC1: on the QA path (`handin-target = qas`) no rule retires a Developer before `squad-evidence check` exits 0 on its evidence sha. The no-QA path (`handin-target = team-lead`) is gated by LC-27.
- AC2: no rule sends the evidence `HANDIN` to the Manager when a Team Lead is on the team.
- AC3: `python3 bin/squad-process lint` exits 0, and the `when:` line of EVID-2d parses.
- AC4: the Developer quotes `squad-process upgrade --check --squad-dir <dir> --plugin-root <worktree>` output; the SQ-20 and EVID-2d ops show as `add` (kept) or `stale`, and Comments list which plugin rule replaces each (LC-20f, EVID-2d). The squads drop the ops by hand after re-pin.
- AC5: rule text says "the PO", never a name.

## Duties

SQ-10: `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`, plus the `grep -rl` hits of EVID-2b, EVID-2d, EVID-2e, EVID-9c, EVID-9e, LC-20b, LC-20f.

## Comments
