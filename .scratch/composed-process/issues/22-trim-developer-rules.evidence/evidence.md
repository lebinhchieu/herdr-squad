# Evidence 22: Developer composed rules at most 5 KiB

## Behaviour

Tests: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_dev_rules_size test_squadrules test_squadcompose test_pod_rules_process test_suite_rules_process test_task_id_rule test_team_lead_role test_manager_m_l test_designer_handoff test_pod_contact_routes test_process_citations test_instructions test_squad_spawn test_windows_safe test_process_conversion` plus `test_crlf_squad_files test_manager_inbox_read test_model_effort_settings test_process_history test_process_writing test_squadprocess_apply test_squadprocess test_squadruntime test_win_utf8_process test_squadprocess_show` → 268 + 164 OK. `squad-process lint` exits 0, prints nothing.

### Technical AC
1. **Size test.** `tests/test_dev_rules_size.py::test_every_combination_fits_5_kib` composes `dev` at the 12 size x design x goal cells (fixture home, `--now` injected, no `--plugin-root`) and asserts `<= 5120`. `test_must_keep_duties_by_rule_id` asserts a marker per must-keep duty by rule ID in every cell (CORE-1/2/6, START-6/10, MSG-3, MSG-4a ("Manager" at S) / MSG-4b ("Team Lead" at M, L), MSG-11a/b, LC-18, LC-19 (design), LC-20a/b, REV-13a/b, REV-14a/b, EVID-2b, COST-3, COST-5, SAFE-1a, SAFE-3, SAFE-4, SAFE-11, SUITE-2a).
2. **Table.** Totals below; per-rule table after it. Slack at the worst cell: 29 B (M or L, design yes, goal either). A real agent name and scope name are longer than the fixture's (`dev`, `s`), so a live file runs about 30 B larger; the bar is the fixture.
3. **IDs.** None removed, renamed or reused; `_removed.md` unchanged; `squad-process lint` exit 0. Other eight roles: below.
4. **Wording tests.** Assertion map below.
5. **Probe.** Below.
6. **Duty check.** One duty moved: the S design screenshot sentence (EVID-5) now sits in LC-19; every other must-keep duty is in the composed file. Nothing was dropped to meet the target.

### Totals (bytes of `squad-process compose dev`, before = base 822e219)
| size | design | goal | before | after |
|---|---|---|---|---|
| S | yes | yes | 10953 | 5035 |
| S | yes | no | 10811 | 5033 |
| S | no | yes | 10096 | 4787 |
| S | no | no | 9954 | 4785 |
| M | yes | yes | 10643 | 5091 |
| M | yes | no | 10501 | 5089 |
| M | no | yes | 10160 | 4843 |
| M | no | no | 10018 | 4841 |
| L | yes | yes | 10643 | 5091 |
| L | yes | no | 10501 | 5089 |
| L | no | yes | 10160 | 4843 |
| L | no | no | 10018 | 4841 |

Worst before: 10953 (S, design, goal). Worst after: 5091 (M or L, design). S: 9954..10953 → 4785..5035. M, L: 10018..10643 → 4841..5091.

### Per-rule table (rules in any Developer composition before; bytes of heading + body, largest cell)
Total of this table: before 12087 B (union of cells, each rule once), after 5290 B (union).
| rule | what happened | before B | after B | carrier / note |
|---|---|---|---|---|
| CORE-1 | kept | 131 | 131 | |
| CORE-2 | shortened + carries MSG-1 | 178 | 196 | |
| CORE-3 | shortened | 208 | 167 | |
| CORE-4 | shortened | 148 | 134 | |
| CORE-5 | shortened | 105 | 99 | |
| START-6 | shortened + absorbs START-7 | 416 | 309 | |
| START-10 | shortened | 365 | 256 | |
| GOAL-6b | retargeted away from dev (now: tech-lead) | 217 | 0 | the task file cites [GOAL-6b] (SIZE-6a/6b sentence, issue 15); dev reads it with `squad-process rule` (CORE-6) |
| PROMO-5 | retargeted away from dev (now: tech-lead) | 185 | 0 | task file cites [PROMO-5] (issue 16); CORE-6 |
| MSG-1 | retargeted away from dev (now: -) | 498 | 0 | CORE-2 now says "to the agent name in `roster.md`"; HANDIN/FAIL shape in REV-13, REV-14 |
| MSG-2 | retargeted away from dev (now: -) | 156 | 0 | MSG-3 carries "point at files, never paste them" and "name the ID after the type" |
| MSG-3 | shortened + carries MSG-2 | 160 | 139 | |
| MSG-4b | kept | 108 | 108 | |
| MSG-5 | retargeted away from dev (now: aware: others) | 156 | 0 | MSG-4b / MSG-11b name the Team Lead as the Developer's contact |
| MSG-7b | retargeted away from dev (now: manager, team-lead, ba, tech-lead, qa-w, qa-b, designer) | 170 | 0 | same, MSG-11b |
| MSG-9 | retargeted away from dev (now: others) | 183 | 0 | the DECISION message names the roles it binds; Developers read it in the file at next ticket (CORE-5) |
| MSG-10 | retargeted away from dev (now: others) | 173 | 0 | settings: a permission prompt reaches the PO through the agent's own notice; MSG-11a/b "a permission prompt goes nowhere" |
| MSG-11b | shortened | 328 | 266 | |
| LC-1 | retargeted away from dev (now: tech-lead) | 108 | 0 | LC-20a/b "Done when ... PASS" |
| LC-3a | retargeted away from dev (now: team-lead) | 159 | 0 | REV-14a/b: "After `FAIL` fix every finding and re-verify"; the FAIL message points at findings |
| LC-5 | retargeted away from dev (now: team-lead) | 193 | 0 | the Team Lead assigns the next ticket (LC-5 is its rule) |
| LC-6 | retargeted away from dev (now: team-lead) | 109 | 0 | COST-5 (Developers retire); the Team Lead assigns queued tickets |
| LC-18 | shortened | 378 | 302 | |
| LC-20b | shortened | 143 | 112 | |
| REV-3 | retargeted away from dev (now: tech-lead, qa-w, qa-b; aware team-lead) | 196 | 0 | the Tech Lead names the final sha; dev hands in that sha (REV-13) |
| REV-4 | retargeted away from dev (now: qa-whitebox, tech-lead) | 220 | 0 | the Tech Lead's technical AC require two real samples |
| REV-6 | retargeted away from dev (now: qa-whitebox, tech-lead) | 183 | 0 | the Tech Lead's technical AC carry the payload-shape class |
| REV-13b | kept | 172 | 172 | |
| REV-14b | shortened | 203 | 204 | |
| REV-15 | retargeted away from dev (now: tech-lead) | 198 | 0 | task file cites [REV-15]; CORE-6 |
| EVID-1 | retargeted away from dev (now: tech-lead, qa-w, qa-b) | 285 | 0 | EVID-2a / EVID-4 name `evidence.md` and the embed form |
| EVID-2a | rewritten (M and L only) + carries EVID-1 | 95 | 157 | |
| EVID-2b | shortened | 295 | 268 | |
| EVID-3b | retargeted away from dev (now: qa-w, qa-b, team-lead) | 96 | 0 | EVID-2b same |
| COST-1 | retargeted away from dev (now: others) | 323 | 0 | COST-3 carries the Stop-hook reaction (notes, then `squad-respawn`) |
| COST-2 | retargeted away from dev (now: others) | 93 | 0 | COST-3 |
| COST-3 | shortened + carries COST-1/2/9 | 174 | 208 | |
| COST-5 | shortened | 142 | 124 | |
| COST-7 | retargeted away from dev (now: others) | 149 | 0 | START-6 reads own notes; rules are attached |
| COST-9 | retargeted away from dev (now: others) | 76 | 0 | COST-3 (fresh session) |
| COST-11 | retargeted away from dev (now: others) | 107 | 0 | Manager / Team Lead decide step-ups |
| NOTE-1 | shortened | 482 | 191 | |
| SAFE-1a | shortened + carries SAFE-5 | 334 | 168 | |
| SAFE-2 | retargeted away from dev (now: all but dev) | 83 | 0 | settings deny of Jira and Confluence write tools (`templates/squad/settings/dev.json` deny list) |
| SAFE-3 | shortened | 176 | 154 | |
| SAFE-4 | kept | 90 | 90 | |
| SAFE-5 | retargeted away from dev (now: all but dev) | 155 | 0 | SAFE-1a "Commit only to your own `squad/...` branch" |
| SUITE-2a | shortened | 135 | 132 | |
| START-7 | retargeted away from dev (now: others) | 131 | 0 | START-6 step 2 ("in a goal also goal.md and shared/") |
| LC-2 | retargeted away from dev (now: tech-lead, team-lead) | 178 | 0 | LC-19: `Design:` ticket waits for `Status: final` |
| LC-19 | shortened + absorbs LC-2, EVID-5 | 290 | 239 | |
| SIZE-5a | retargeted away from dev (now: tech-lead) | 116 | 0 | Tech Lead owns business AC in S; MSG-11a (business doubt moves the scope up) |
| SIZE-8a | retargeted away from dev (now: tech-lead) | 160 | 0 | EVID-4 |
| MSG-4a | kept | 100 | 100 | |
| MSG-7a | retargeted away from dev (now: manager, tech-lead) | 148 | 0 | the ruling itself starts with `FINAL:`; a new fact is an `ASK` (MSG-11a) |
| MSG-11a | shortened | 353 | 238 | |
| LC-20a | shortened | 140 | 109 | |
| REV-13a | kept | 132 | 132 | |
| REV-14a | shortened | 168 | 164 | |
| EVID-3a | retargeted away from dev (now: tech-lead) | 72 | 0 | EVID-2b "each review file in `$SCOPE_DIR/evidence/<task>/`" |
| EVID-4 | shortened + carries SIZE-8a | 306 | 221 | |
| SIZE-10a | retargeted away from dev (now: tech-lead, dev→tech-lead) | 155 | 0 | LC-19 (screenshots in S) |
| EVID-5 | retargeted away from dev (now: tech-lead) | 201 | 0 | LC-19 carries the S design-screenshot sentence |

Retargeted rules and their new role sets at M (`squad-process who <ID>`):
- `GOAL-6b`: M: acts: tech-lead; aware: -
- `PROMO-5`: M: acts: tech-lead; aware: -
- `MSG-1`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-2`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-5`: M: acts: team-lead; aware: manager, ba, tech-lead, qa-whitebox, qa-blackbox, designer
- `MSG-7b`: M: acts: manager, team-lead, ba, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-9`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-10`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `LC-1`: M: acts: tech-lead; aware: -
- `LC-3a`: M: acts: team-lead; aware: -
- `LC-5`: M: acts: team-lead; aware: -
- `LC-6`: M: acts: team-lead; aware: -
- `REV-3`: M: acts: tech-lead, qa-whitebox, qa-blackbox; aware: team-lead
- `REV-4`: M: acts: qa-whitebox, tech-lead; aware: -
- `REV-6`: M: acts: qa-whitebox, tech-lead; aware: -
- `REV-15`: M: acts: tech-lead; aware: -
- `EVID-1`: M: acts: tech-lead, qa-whitebox, qa-blackbox; aware: -
- `EVID-3b`: M: acts: qa-blackbox, qa-whitebox, team-lead; aware: -
- `COST-1`: M: acts: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `COST-2`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `COST-7`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `COST-9`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `COST-11`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `SAFE-2`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, token-coach; aware: -
- `SAFE-5`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, token-coach; aware: -
- `START-7`: M: acts: ba, team-lead, tech-lead, qa-whitebox, designer; aware: -
- `LC-2`: M: acts: tech-lead, team-lead; aware: -
- `SIZE-5a`: M: acts: -; aware: -
- `SIZE-8a`: M: acts: -; aware: -
- `MSG-7a`: M: acts: -; aware: -
- `EVID-3a`: M: acts: -; aware: -
- `SIZE-10a`: M: acts: -; aware: -
- `EVID-5`: M: acts: -; aware: -

Dev-only rules cannot have an empty `roles:` (lint: `missing roles:`), so GOAL-6b, PROMO-5, REV-15, LC-1, SIZE-8a went to the **Tech Lead**, who writes the task files that cite them, and LC-3a, LC-6 to the **Team Lead**. This adds those IDs to those two compositions (see below); QA whitebox may rule it should be otherwise.

`squad-process rule REV-4` (reachable for a Developer; its `allow` now has `Bash(squad-process rule:*)` and `who`):
```
## REV-4 Real samples
Code that parses another tool's output (pane text, logs, an API) needs two real samples, including the constant or idle case, before a pattern is trusted. The Tech Lead's technical AC require them.
```

### Other eight roles, before/after (compose at M, design yes, goal yes; base vs this sha)
| role | IDs added | IDs lost | IDs with changed text | bytes before → after |
|---|---|---|---|---|
| ba | CORE-6 | - | CORE-2..5, COST-3, MSG-1, MSG-3, NOTE-1, SAFE-3, START-6 | 9674 → 9049 |
| designer | CORE-6 | - | same | 7209 → 6584 |
| manager | CORE-6 | - | same minus START-6, plus the Index list (new/moved lines) | 39066 → 38481 |
| qa-blackbox | CORE-6, SAFE-11 | - | same | 9256 → 8824 |
| qa-whitebox | CORE-6, SAFE-11 | - | same | 10003 → 9571 |
| team-lead | CORE-6, LC-3a, LC-6 | - | same, SIZE-6b | 17426 → 17212 |
| tech-lead | CORE-6, GOAL-6b, LC-1, PROMO-5, REV-15 | - | same, plus the Index list (SIZE-6a gains its sentence at S only) | 25312 → 25208 |
| token-coach | CORE-6 | - | CORE-2..5, SAFE-3 | 3224 → 3329 |

Count line: no role lost an ID; the ticket's `lost dev` set only shrinks the Developer file. The shared text edits are the shortened rules the ticket listed (MSG-1, MSG-3, NOTE-1, COST-3 absorbing COST-1/2, START-6) plus CORE-2/3/4/5 and SAFE-3, trimmed a few bytes each to meet 5 KiB. MSG-1 lost its type table (CORE-2 lists the types). `SIZE-6a/6b` gained one sentence each: "cite the on-demand rules in the task file" was in no rule (searched SIZE-6, LC, `cite`).

Scratch rule SAFE-11: composed files containing both `mktemp -d` and `${VAR:?}`: dev, qa-whitebox, qa-blackbox = 3 of 9; the other six 0 (`test_scratch_rule_reaches_dev_and_both_qas_only`).

### Probe (AC 5, Haiku, \$0.002 of the \$0.10 cap)
`claude -p "<Answer from your attached rules only … (a) a message type (b) a rule you were not given (c) may you push …>" --model haiku --plugin-dir . --agent squad:dev --append-system-prompt-file dev.rules.md --output-format json --tools ""` with `dev.rules.md` = `squad-process compose dev --home <M, design yes, goal yes>`. Full output: `probe-output.json`.
```
(a) Send it with SendMessage to the agent in roster.md as `<TYPE> <TASK-ID>: <text>`. Types: ASK, ANSWER, DECISION, BLOCKED, HANDIN, PASS, FAIL, STATUS. [CORE-2]
(b) `squad-process rule <ID>`. [CORE-6]
(c) NO. Commit only to your own `squad/<squad>/<scope>/<agent>` branch. [SAFE-1a]
GOAL-6b text: NO (not in my attached rules)
mktemp -d: YES (SAFE-11)
```
CORE-2, CORE-6 and SAFE-1a answered; GOAL-6b correctly absent, SAFE-11 present.

### Assertion map (old test → new)
- `test_pod_rules_process.test_pod_contact_and_team_lead_to_manager`: the dev assertion of MSG-5 text → asserts QA whitebox still gets it and `MSG-5` is not in dev's file (MSG-5 left dev; carrier MSG-4b/MSG-11b).
- `test_suite_rules_process.test_tech_lead_runs_it_and_others_never`: "The full suite is…" → "the full suite is the Tech Lead's" (SUITE-2a shortened).
- `test_suite_rules_process.test_integration_and_light_lines_…` and `test_integration_task_runs_targeted_tests`: dev's composed file → `squad-process rule GOAL-6b` output (on demand); the Tech Lead assertions unchanged.
- `test_task_id_rule.test_rule_is_targeted_at_every_role_and_size`: BULLET follows the shortened MSG-3 (no more "a Developer's roster `Owns` reads `ticket NN`"; `test_rosters_say_ticket_nn` still covers the roster templates).
- `test_pod_contact_routes.test_team_lead_routes_in_m_and_l`, `test_s_paths_stay`, `test_qa_blackbox_copies_team_lead_only_and_dev_blocked_route`: new MSG-11b / LC-20a / MSG-11a wording ("the Team Lead (plan or order)", "`STATUS?` answers go to the Team Lead", "a permission prompt goes nowhere", "Tell the Tech Lead and wait; the Manager retires you").
- `test_process_citations.test_an_unknown_pointer_is_reported`: breaks `[WHO-1a]` in CORE-3 instead of `Rules: [MSG-1].` (CORE-2 no longer carries that pointer).
- `test_instructions.RuleDutiesTest.test_dev_copies_reports_…`: REV-15 read from `squad-process rule REV-15`; the Tech Lead's file must contain `## REV-15`; REV-14b assertions unchanged.
- New: `test_dev_rules_size` (7 tests).

### Cited on demand
Issues 15 (`.scratch/composed-process/issues/15-integration.md`) and 16 (`16-promotion.md`) are the integration and promotion tickets whose task files cite `[GOAL-6b]` and `[PROMO-5]`; SIZE-6a/6b now say so.
