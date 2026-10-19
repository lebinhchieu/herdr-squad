# Evidence: 03 role files, screenshots inline
sha: 3557ec8e7600d780b56dc1f02c73e5f74c477e3a

## Behaviour

No UI: command output only. Layout contract used (`evidence.md` here, no `dev-evidence.md`).

### AC1: harness passes; no `dev-evidence` in `agents/`

Harness, with an empty placeholder `bin/squad-evidence` (removed after the run):

```
----------------------------------------------------------------------
Ran 66 tests in 0.014s

OK
```

Without it, one existing test fails: `test_every_command_an_instruction_tells_agents_to_run_exists` checks that every `squad-*` command a role file names exists in `bin/`. The tool is ticket 01's file, not on this branch; it passes once 01 is merged (ticket 04).

```
FAIL: test_every_command_an_instruction_tells_agents_to_run_exists (test_instructions.InstructionsTest.test_every_command_an_instruction_tells_agents_to_run_exists)
Ran 66 tests in 0.015s
FAILED (failures=1)
```

`grep -rn "dev-evidence" agents/`:

```
exit=1
```

### AC2: cited `process.md` sections exist

`test_process_citations` is in the harness above: OK. No new section cited.

### AC3: bullets state who, when, outcome; no copied rule

Edited bullets: `agents/dev.md` (Design, S-size, new "Assemble the evidence."), `agents/tech-lead.md` (In S you are also the checker), `agents/qa-whitebox.md` (Write findings), `agents/qa-blackbox.md` (Joining, Write evidence), `agents/manager.md` (Check-in), `agents/team-lead.md` (iteration summary). Each cites a rule by clause only. `test_dev_copies_reports_to_evidence_and_sends_a_diff_check_after_a_pass` passes unchanged.

### AC4: no change outside Touches

`git diff --stat cb14419 HEAD` (code commit `3557ec8e7600d780b56dc1f02c73e5f74c477e3a`):

```
 agents/dev.md              |  5 +++--
 agents/manager.md          |  2 +-
 agents/qa-blackbox.md      |  4 ++--
 agents/qa-whitebox.md      |  2 +-
 agents/team-lead.md        |  2 +-
 agents/tech-lead.md        |  2 +-
 tests/test_instructions.py | 26 ++++++++++++++++++++++++++
 7 files changed, 35 insertions(+), 8 deletions(-)
```

## Tech Lead review

### Tech Lead review: ticket 03

sha: 3557ec8e7600d780b56dc1f02c73e5f74c477e3a (evidence-only follow-up 0572249; `git diff --name-only 3557ec8 0572249` lists only `.scratch/evidence-inline/issues/03-role-files.evidence/evidence.md`)

**PASS**

- Diff stays inside Touches (6 agent files + `tests/test_instructions.py`); `grep -rn dev-evidence agents/` empty.
- Ran the harness on the branch: 65 OK, 1 expected failure: `test_every_command_an_instruction_tells_agents_to_run_exists` names `squad-evidence`, which is ticket 01's file. It must be green on the merge in ticket 04 (AC there).
- Each edited bullet names who acts, when, outcome; no process.md rule copied; no new process.md section cited.
- `evidence.md` follows the layout contract; no screenshots (none apply), command output fenced.
- Follow-up for 04: after 01 is merged, `squad-evidence add` this file as `## Tech Lead review`.

#### Return 1 — PASS (Tech Lead)
Code sha cd368f4 (diff vs b398258: agents/manager.md and agents/dev.md, one line each). Restores "evidence links" in the Check-in bullet and "hand in to the **Tech Lead** instead of the QAs" in dev.md; stray .pyc deleted; tests untouched. Ran test_manager_inbox_read, test_pod_contact_routes, test_squadinbox, test_instructions: 99 OK. Full suite --tz re-runs on the final evidence tip.
