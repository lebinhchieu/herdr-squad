
sha: 9306e09
## Behaviour
- `python3 bin/squad-process lint` exit 0.
- Attachments (rule headers): LC-14 tech-lead, aware manager (when tech-lead = yes; added after QA blackbox FAIL); LC-28 manager, team-lead; START-18 manager; SPAWN-9 team-lead. No `dev` added, so Developer bytes +0 B, LIMIT unchanged.
- `grep -n '_done\|0\.10\|Chieu'` over the added lines of the diff: no hit. START-18 step 4 names `squad-process homes --check` verbatim; the old "pin 0.10.4" text is gone (SQ-22 text was never in the plugin rule).
- SQ-10 + hits (`cd tests; python3 -m unittest test_windows_safe test_utf8_helpers test_instructions test_rules_contract test_small_files_equivalence test_sizes test_dev_rules_size`): 81 tests, 1 failure: `test_every_team_set_fits_the_limit`, team ('designer',) 5692 B > 5580. Known failing on base (tl-design §5, 224 design/architecture sets); not caused by 05 (no dev attachment).
- `upgrade --check --squad-dir .claude/squads/plugin --plugin-root <worktree>`: SQ-21 and SQ-22 listed as `review: the plugin changed START-18 / SPAWN-9`; SQ-1 and SQ-8 unaffected (kept); EVID-2d `stale` comes from 03. Replacements are in the ticket's Comments; squads drop the ops by hand after re-pin.
```
  SQ-21 (topic start): the plugin changed START-18 Manager start
  SQ-22 (topic spawning): the plugin changed SPAWN-9 Team Lead spawns and retires the pod
```
- Ticket text fixes applied: "Chieu" -> "the PO" in the Edit table, AC4 (adoption), AC5 (no name), Duties line, Comments.

## Review, QA whitebox

### QA whitebox, ticket 05, sha fc6f3f0

Verdict: PASS.

#### Checked
- AC3: `squad-process lint` exit 0.
- AC1 / agreed design (tl-design §3, qaw-technical-ac T for 05): LC-14 keeps its tech-lead attachment (+1 sentence); LC-28 reaches manager and team-lead only; START-18 step 4 manager only, names `squad-process homes --check`; SPAWN-9 team-lead. Composed dev and QA rules hold none of the four (Developer bytes +0).
- AC2/AC5: `git diff 5db40ff fc6f3f0 -- templates`, added lines grep for `_done`, `0.10` and the PO's name: empty. "pin 0.10.4" text gone.
- AC4: `upgrade --check` shows SQ-21 (START-18) and SQ-22 (SPAWN-9) as `review`; ticket Comments name the replacing rule for SQ-1, SQ-8, SQ-21, SQ-22.
- Pass: test_windows_safe, test_utf8_helpers, test_instructions, test_rules_contract, test_rules_wording, test_small_files_equivalence, test_sizes, test_squadcompose, test_dev_rules_size (155 tests, 1 failure: design team 5692 B > 5580, known on base).

#### Follow-ups (not FAIL)
1. LC-14 diff is more than the added sentence: it also reworded the opening and dropped "the Manager writes them into the plan". Nothing else in the diff needs it, so restore the clause if a later pass touches the rule.
2. LC-28 lost the overlay's actor: "Before the Team Lead hands out a task, the Manager checks". Both roles get the rule, but it names no one.
3. SQ-1 overlay also named the Manager (ordering); LC-14 reaches only the Tech Lead, as the design and ticket Edit table say.

### Re-check, sha 9306e09

Verdict: PASS. Diff fc6f3f0..9306e09 is one line: `aware: manager` on LC-14 (lifecycle.md). Lint exit 0; manager's composed rules now hold LC-14 (aware) and LC-28; dev and QAs hold neither; worst no-design Developer team 5490 B <= 5580; same 155 tests, only the known design-team failure. Follow-ups 1 and 2 above stand, not FAIL.

## Review, QA blackbox

### QA blackbox 05: fc6f3f0 FAIL (1 finding); 9306e09 PASS

Method: `squad-process rule <ID> --plugin-root <worktree>`, `compose <role>` on a scratch squad dir (no overlay), `lint`, `upgrade --check`.

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 each edit lands in target rule or one new rule, attaches to the roles in the overlay op | live | composed manager, team-lead, tech-lead, dev, ba, qa-* | LC-28 (new): manager, team-lead (= SQ-8). START-18: manager (= SQ-21). SPAWN-9: team-lead (SQ-22: Manager part is only the dropped "older pin" text, Manager ruling: passes). LC-14: tech-lead only; overlay SQ-1 roles are tech-lead and manager, and the Manager orders tickets. Manager does not get LC-14 | **fail** |
| AC2 no `_done/` or plugin version in rule text | live | grep the four rules | no new `_done/` or version text (START-18's existing "Never read a `_done/` folder" is old) | pass |
| AC3 lint | live | `squad-process lint` | exit 0 | pass |
| edits match the ticket table | live | read the four rules | LC-14 sentence; LC-28 mirrors SQ-8 incl. 45 min; START-18 step 4 names `homes --check`, ASK the PO, never re-pin a running scope; SPAWN-9 QAs first + one retry, "pin 0.10.4" gone | pass |
| AC4/AC5 (Developer's added) | live | `upgrade --check` | SQ-21 -> START-18 and SQ-22 -> SPAWN-9 listed under review; SQ-1, SQ-8 unaffected (kept); ticket Comments name LC-14, LC-28, START-18, SPAWN-9 | pass |

Finding 1 (breaks AC1, Manager ruling 2026-11-24): LC-14 reaches only the Tech Lead. Add the Manager (`aware: manager` is enough). No change to SPAWN-9.

#### Re-check, sha 9306e09
Diff fc6f3f0..9306e09 is one line: `aware: manager` on LC-14. Lint exit 0. Composed rules: manager now gets START-18, LC-14, LC-28; tech-lead LC-14; team-lead LC-28, SPAWN-9; dev none. Finding 1 fixed; AC1 met. Verdict: PASS.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | rule headers: LC-14 tech-lead, LC-28 manager+team-lead, START-18 manager, SPAWN-9 team-lead | composed manager, team-lead, tech-lead, dev rules (qa-w.md) | `compose <role>` on a scratch squad dir; LC-14 reaches manager after 9306e09 (qa-b.md) |
| AC2 | `git diff -U0 -G_done -G0.10` on the added lines: no hit | `git diff 5db40ff fc6f3f0 -- templates`, added lines grep for `_done`, `0.10` and the PO's name: empty | grep the four rules for `_done/` and version text |
| AC3 | `python3 bin/squad-process lint` exit 0 | `squad-process lint` exit 0 | `squad-process lint` exit 0 |
| AC4 | `upgrade --check` quoted in evidence.md; Comments list replacements | `upgrade --check`; ticket Comments name the four rules | `upgrade --check`: SQ-21, SQ-22 under review |
| AC5 | no `Chieu` in added rule text | same grep as AC2, empty | read the ticket Comments |
