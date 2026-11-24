# Evidence: 03 03 Developer stays until the evidence check is clean

## Review, QA whitebox

### QA whitebox, ticket 03, sha e90513d

Verdict: FAIL (1 finding).

#### Checked, passes
- `squad-process lint` exit 0 (EVID-2d `when:` parses). who: LC-20f team-lead; LC-20b, EVID-2d dev; EVID-2e team-lead, aware manager; EVID-9e / EVID-9c via their `when:`.
- AC1: LC-20f keeps the Developer until both PASS and the evidence commit, `squad-evidence check <folder>`, retire only on exit 0, quotes exit code and sha; LC-20b points at it. AC2: `grep -n 'to the Manager' evidence.md` has no evidence-assembly hit; EVID-2d sends to the Team Lead, "Nobody asks the Manager to assemble it". EVID-2e, EVID-9e moved to the Team Lead.
- T8: worst no-designer/architect team 5490 B (+17, budget 200), LIMIT 5580 holds; `test_every_team_set_fits_the_limit` fails only for design teams (base).
- Pass: test_windows_safe, test_utf8_helpers, test_instructions, test_rules_contract, test_rules_wording, test_sizes, test_small_files_equivalence, test_squadcompose.

#### Finding (breaks AC4)
1. `.scratch/upstream-proposals/issues/03-evidence-before-retire.md:31` `## Comments` is empty. AC4 (as rewritten by the Developer) says "Comments list which plugin rule replaces each (LC-20f, EVID-2d)" for the SQ-20 and EVID-2d overlay ops; the list sits only in `evidence.md`. Same finding as ticket 01.
   Pass: one line under `## Comments`: SQ-20 -> LC-20f, EVID-2d replace -> plugin EVID-2d (squads drop the ops by hand after re-pin). Doc-only; I re-check that file only.

### Re-check, sha 9fcfd1a

Verdict: PASS. Diff e90513d..9fcfd1a changes only `.scratch/upstream-proposals/issues/03-evidence-before-retire.md`: `## Comments` now names SQ-20 -> LC-20f and EVID-2d -> plugin EVID-2d. Finding 1 fixed; AC4 met. Rest of e90513d checks stand (doc-only change).

## Review, QA blackbox

### QA blackbox 03, sha e90513d

Method: `squad-process compose <role> --plugin-root <worktree>` on a scratch squad dir with no overlay (the real plugin squad's stale EVID-2d `replace` makes compose stop with "overlay written for @ecb878fe, plugin now @8983d961"; that is the expected re-pin decision, not a defect).

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 no rule retires a Developer before `squad-evidence check` exits 0 | live | composed team-lead and dev rules (team with Tech Lead, and team-lead + qa-white + qa-black) | team-lead gets LC-20f: "Keep the Developer until both checkers sent PASS and its evidence commit is in. Run `squad-evidence check <folder>` on the final sha; only on exit 0 retire it and record STATUS <task>: passed, quoting the exit code and sha." dev's LC-20b: "stay until the Team Lead retires you ([LC-20f])". No other composed team-lead rule retires a Developer after PASS (the rest are context-driven, COST-5/COST-6b, or the task-accepted `squad-retire` line) | pass |
| AC2 no evidence HANDIN to the Manager when a Team Lead is on the team | live | grep composed manager/dev/team-lead rules for evidence + "to the Manager" | no hit; EVID-2d sends `HANDIN <task>: evidence sha <sha>` to the Team Lead and says "Nobody asks the Manager to assemble it"; EVID-2e/9e now "Team Lead", Manager aware | pass |
| AC3 lint, `when:` of EVID-2d parses | live | `squad-process lint`; composed dev with no Tech Lead | lint exit 0; EVID-2d "Assemble evidence, the task's Developer" present for dev in that team | pass |
| AC4 upgrade --check output, replacements named | live | `upgrade --check --squad-dir .claude/squads/plugin --plugin-root <worktree>` | EVID-2d `stale` (needs a decision, `--resolve EVID-2d=...`), SQ-20 listed under review as kept. Replacements are named in evidence.md, not in the ticket's `## Comments` (empty) | pass (see follow-up) |
| AC5 "the PO", no name | live | read the changed rules | no name | pass |

Follow-ups (not FAIL, SQ-4):
- AC4 asks that Comments list LC-20f and EVID-2d as the replacements and the upgrade output be quoted; the ticket's `## Comments` is empty and evidence.md paraphrases. Add them in the doc-only evidence commit (as 01).
- After re-pin, the plugin squad's own overlay stops compose until `EVID-2d` is resolved (`keep | take | file:`). Known and expected; the PO or Manager takes that step.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `squad-process who LC-20f` acts team-lead, `when: handin-target = qas`; LC-20b names [LC-20f] | `squad-process who LC-20f`; `squad-process who LC-20b` | - |
| AC2 | `grep -n 'to the Manager' templates/squad/process/evidence.md` empty | `grep -n 'to the Manager' templates/squad/process/evidence.md` | - |
| AC3 | `squad-process lint` exit 0 | `squad-process lint` | - |
| AC4 | `upgrade --check` output quoted in `## Behaviour` | `git diff e90513d 9fcfd1a -- .scratch/upstream-proposals/issues/03-evidence-before-retire.md` | - |
| AC5 | no name in rule text | `grep -n -i 'chieu' templates/squad/process/evidence.md templates/squad/process/lifecycle.md` | - |

## Behaviour

### Behaviour
- `python3 bin/squad-process lint` exit 0.
- `squad-process who`: LC-20f acts team-lead (qas path); LC-20b dev; EVID-2d dev (tech-ac = qa-white); EVID-2e, EVID-9e team-lead, aware manager.
- `grep -n 'to the Manager' templates/squad/process/evidence.md`: no hit.
- SQ-10 + hits (`cd tests; python3 -m unittest test_windows_safe test_utf8_helpers test_instructions test_dev_rules_size test_rules_wording test_sizes`): 91 tests, 1 failure: `test_every_team_set_fits_the_limit`, team ('designer',) 5692 B > 5580. Known failing on base (tl-design §5: 224 design/architecture sets); no designer/architect team set is over.
- Byte budget (worst no-designer, no-architect team): base 5473 B, now 5490 B (+17 B, budget 200). LC-20f has no `aware: dev` (it cost +297 B), so LIMIT stays 5580.
- `upgrade --check`: EVID-2d `stale` (replace written for @ecb878fe); SQ-20 shown as `add`, kept. Replacements: SQ-20 -> LC-20f, EVID-2d replace -> plugin EVID-2d. Squads drop the ops after re-pin.

- `upgrade --check` output (SQ-20, EVID-2d lines):
```
  EVID-2d stale: the plugin changed the rule your `replace` was written for (@ecb878fe -> @8983d961)
    --resolve EVID-2d=<keep | take | file:<path>>
  SQ-20 (topic evidence): the plugin changed EVID-2b Assemble evidence
  SQ-20 (topic evidence): the plugin changed EVID-2d Assemble evidence, the task's Developer
  SQ-20 (topic evidence): the plugin changed EVID-9c Evidence
```
