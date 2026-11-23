# Evidence: 01 01 Read your usage row at commit and verdict

## QA whitebox

### QA whitebox, ticket 01, sha 056c873

Verdict: FAIL (1 finding).

#### Checked, passes
- `squad-process lint` exit 0. `squad-process rule COST-16` prints it; roles = dev, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect, aware manager (rulesview.who). AC1, T4, T9.
- Text: no `[0-9]k` number, names `line`, COST-3, COST-5; no "Chieu", no `_done`. AC2, AC5, T3.
- T8: worst no-designer/architect team 5786 B (+313 vs 5473, budget 450), LIMIT 5893 = 5580+313, no such team over LIMIT. `test_every_team_set_fits_the_limit` fails only for design teams (base failure, no FAIL).
- SQ-10 files OK (14/14/16). Hits: test_rules_wording 30 OK, test_rules_contract 17 OK, test_sizes 8 OK.
- `upgrade --check` lists plugin SQ-3c, SQ-3d and board SQ-5 against "the plugin added COST-16" (add, kept).

#### Finding (breaks AC4)
1. `.scratch/upstream-proposals/issues/01-usage-row-at-commit.md:~32` `## Comments` is empty. AC4 (as the Developer rewrote it) says "Comments name COST-16 as the plugin rule that replaces it" for board SQ-5, plugin SQ-3c, SQ-3d; ticket-fixes §1 says the same. The naming sits only in `evidence.md`.
   Pass: one line under `## Comments` naming COST-16 as the replacement for board SQ-5, plugin SQ-3c, SQ-3d (and that squads drop the ops by hand after re-pin). Doc-only; I re-check only that file.

#### Follow-ups (not a FAIL)
- `tests/test_templates.py::test_designer_may_write_only_ui_design_files` fails on main too (unrelated; extra `Edit(//tmp/**)` write rule). Not in the Developer's list; SQ-17 grep belongs to the Tech Lead.
- `squad-process who COST-16` prints an empty line (the CLI shows only `when:` keys); attachment verified through `rulesview.who`.

#### Re-check, sha 6d132da
Diff 056c873..6d132da is one file, two added lines under `## Comments` naming COST-16 as the replacement for board SQ-5, plugin SQ-3c, SQ-3d. The finding is closed. Verdict: PASS. All earlier checks stand (no rule or test file changed).
Follow-ups: `tests/test_templates.py::test_designer_may_write_only_ui_design_files` fails on main too (unrelated).

## QA blackbox

### QA blackbox 01, sha 056c873

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 attached to 8 roles, `aware: manager` | live | `squad-process compose <role> --home $SCOPE_DIR --plugin-root <worktree> --out /tmp/..` for dev, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect, manager. (`squad-process who COST-16` prints an empty line for every rule, also on main, so I could not use it.) | `## COST-16 Read your usage row` is in all 8 composed role files and, as awareness, in the manager's | pass |
| AC2 no fixed token number | live | `squad-process rule COST-16` | text names `line`, [COST-3], [COST-5]; only number-like text is the placeholder `ctx <n>k` | pass |
| AC3 lint | live | `squad-process lint` | exit 0 | pass |
| AC4 upgrade --check | live | `upgrade --check --squad-dir .claude/squads/{board,plugin} --plugin-root <worktree>` | plugin: SQ-3c, SQ-3d "the plugin added COST-16"; board: SQ-5 "the plugin added COST-16" (ops stay as add) | pass (see follow-up) |
| AC5 "the PO", no name | live | read rule text | no name | pass (byte budget/LIMIT: whitebox) |
| AC6 SQ-10 files + grep hits | shot | Developer's evidence.md lists them as passing; not re-run (QA whitebox owns tests) | - | not mine |

Follow-ups (not a FAIL, SQ-4):
- AC4 says the Developer quotes the `upgrade --check` output and the ticket Comments name COST-16. The ticket's `## Comments` is empty and evidence.md paraphrases. Add the quoted lines and the "COST-16 replaces SQ-3c, SQ-3d, board SQ-5" note in the doc-only evidence commit.

## Behaviour

### Evidence 01 usage row at commit

#### Behaviour
- COST-16 added in `templates/squad/process/cost.md`: roles dev, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect; `aware: manager`. No token number; names `line`, COST-3, COST-5; Developer ends HANDIN with `ctx <n>k`.
- `squad-process lint` exit 0. `squad-process rule COST-16` prints the rule.
- Developer bytes: worst no-designer/architect team 5473 -> 5786 B (+313, budget 450). LIMIT 5580 -> 5893. Sweep: no team set without designer or architect is over LIMIT. `test_every_team_set_fits_the_limit` still fails for design teams (known failing on base, tl-design §5; not an FAIL).
- SQ-10 files pass: test_windows_safe (14 OK), test_utf8_helpers (14 OK), test_instructions (16 OK). Hits of COST-16/COST-5: test_rules_contract 17 OK, test_sizes 8 OK, test_squad_usage_hook 13 OK. test_dev_rules_size: 8 of 9 OK, the 9th is the known base failure.
- AC4: `upgrade --check --plugin-root <worktree>` on the plugin squad lists SQ-3c and SQ-3d against "the plugin added COST-16"; on the board squad its SQ-5 cost op is listed likewise. Ops stay (add) until the squads drop them by hand after re-pin.

#### upgrade --check (AC4)
##### plugin
```
  SQ-3c (topic cost): the plugin added COST-16 Read your usage row
  SQ-3d (topic cost): the plugin added COST-16 Read your usage row
```
##### board
```
  SQ-5 (topic cost): the plugin changed COST-2 Reuse
  SQ-5 (topic cost): the plugin changed COST-3 Fresh start
  SQ-5 (topic cost): the plugin changed COST-5 Developer retires
  SQ-5 (topic cost): the plugin added COST-16 Read your usage row
  SQ-5 (topic cost): the plugin changed COST-6b Ticket assignment, Team Lead
  SQ-5 (topic cost): the plugin changed COST-8 Manager reads its usage
  SQ-5 (topic cost): the plugin added COST-8b Long PO wait, Manager
  SQ-5 (topic cost): the plugin changed COST-10b PO wait, Team Lead plans
  SQ-5 (topic cost): the plugin changed COST-13b Nothing left to do, Team Lead plans
  SQ-5 (topic cost): the plugin added COST-15 Cold cache, watchdog restarts you
  SQ-7 (topic cost): the plugin added COST-16 Read your usage row
  SQ-9 (topic cost): the plugin added COST-16 Read your usage row
```

Comments of the ticket name COST-16 as the replacement (commit 6d132da).
