# Evidence 22: Developer composed rules at most 5 KiB

## Behaviour

Tests: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_dev_rules_size test_squadrules test_squadcompose test_pod_rules_process test_suite_rules_process test_task_id_rule test_team_lead_role test_manager_m_l test_designer_handoff test_pod_contact_routes test_process_citations test_instructions test_squad_spawn test_windows_safe test_process_conversion test_crlf_squad_files test_manager_inbox_read test_model_effort_settings test_process_history test_process_writing test_squadprocess_apply test_squadprocess test_squadruntime test_win_utf8_process test_squadprocess_show` → 432 OK. `squad-process lint` exits 0, prints nothing.

### Technical AC
1. **Size test.** `tests/test_dev_rules_size.py::test_every_combination_fits_5_kib` composes `dev` at the 12 size x design x goal cells (home pinned, agent `plugin-dev-role-cards-upgrade-12`, scope `role-cards-upgrade`, `--now` injected, no `--plugin-root`) and asserts `<= 5120`. That is the live-length header; the plain fixture header (`dev`, `s`, unpinned) is about 70 B smaller. `test_must_keep_duties_by_rule_id` asserts a marker per must-keep duty by rule ID in every cell (CORE-1/2/6, START-6/10, MSG-3, MSG-4a ("Manager", S) / MSG-4b ("Team Lead", M, L), MSG-11a/b, LC-3a, LC-18, LC-19 (design), LC-20a/b, REV-13a/b, REV-14a/b, EVID-2b, COST-3, COST-5, SAFE-1a/3/4/11, SUITE-2a).
2. **Table.** Totals and per-rule table below. Worst cell with live-length header: 5106 B (S, design, goal), slack 14 B; with the plain fixture header 5031 B.
3. **IDs.** None removed, renamed or reused; `_removed.md` unchanged; lint exit 0. Other eight roles: below.
4. **Wording tests.** Assertion map below.
5. **Probe.** Below (AC 5 and BA's BT-4).
6. **Duty check.** Nothing dropped to meet the target. Moved: S design screenshots (EVID-5 → EVID-4), "returned task" kept as LC-3a for dev (REV-14a/b stay after-PASS).

### Totals (bytes of `squad-process compose dev`; before = base 822e219)
| size | design | goal | before | after (plain fixture) | after (live-length header) |
|---|---|---|---|---|---|
| S | yes | yes | 10953 | 5036 | 5106 |
| S | yes | no | 10811 | 5034 | 5105 |
| S | no | yes | 10096 | 4856 | 4927 |
| S | no | no | 9954 | 4854 | 4926 |
| M | yes | yes | 10643 | 5011 | 5081 |
| M | yes | no | 10501 | 5009 | 5080 |
| M | no | yes | 10160 | 4831 | 4902 |
| M | no | no | 10018 | 4829 | 4901 |
| L | yes | yes | 10643 | 5011 | 5081 |
| L | yes | no | 10501 | 5009 | 5080 |
| L | no | yes | 10160 | 4831 | 4902 |
| L | no | no | 10018 | 4829 | 4901 |

### Per-rule table (every rule in any Developer composition before; heading + body bytes, largest cell)
Union of cells, each rule once: before 12087 B, after 5208 B (+ new CORE-6, SAFE-11).
| rule | what happened | before B | after B | carrier / note |
|---|---|---|---|---|
| CORE-1 | kept | 131 | 131 | |
| CORE-2 | shortened + carries MSG-1 | 178 | 196 | |
| CORE-3 | shortened | 208 | 165 | |
| CORE-4 | shortened | 148 | 123 | |
| CORE-5 | shortened | 105 | 91 | |
| START-6 | shortened + absorbs START-7 | 416 | 300 | |
| START-10 | shortened | 365 | 257 | |
| GOAL-6b | retargeted away from dev (now: tech-lead) | 217 | 0 | task files cite [GOAL-6b] (SIZE-6a/6b sentence; tasks/integration.md); dev reads it with `squad-process rule` (CORE-6) |
| PROMO-5 | retargeted away from dev (now: tech-lead) | 185 | 0 | task file cites [PROMO-5]; CORE-6 |
| MSG-1 | retargeted away from dev (now: -) | 498 | 0 | CORE-2 now says "to the agent name in `roster.md`"; HANDIN shape in REV-13 |
| MSG-2 | retargeted away from dev (now: -) | 156 | 0 | MSG-3: "point at files, never paste them", ID after the type |
| MSG-3 | shortened + carries MSG-2 | 160 | 139 | |
| MSG-4b | shortened | 108 | 105 | |
| MSG-5 | retargeted away from dev (now: aware: others) | 156 | 0 | MSG-4b / MSG-11b name the Team Lead as contact |
| MSG-7b | retargeted away from dev (now: all but dev) | 170 | 0 | same, MSG-11b |
| MSG-9 | retargeted away from dev (now: all but dev) | 183 | 0 | the DECISION message names the roles it binds |
| MSG-10 | retargeted away from dev (now: all but dev) | 173 | 0 | settings: permission prompts reach the PO via the agent's own notice |
| MSG-11b | shortened | 328 | 232 | |
| LC-1 | retargeted away from dev (now: tech-lead) | 108 | 0 | LC-20a/b "Done when ... PASS" |
| LC-3a | shortened | 159 | 103 | |
| LC-5 | retargeted away from dev (now: team-lead) | 193 | 0 | the Team Lead assigns the next ticket |
| LC-6 | retargeted away from dev (now: team-lead) | 109 | 0 | COST-5; the Team Lead assigns queued tickets |
| LC-18 | shortened | 378 | 290 | |
| LC-20b | shortened | 143 | 101 | |
| REV-3 | retargeted away from dev (now: tech-lead, qa-w, qa-b; aware team-lead) | 196 | 0 | the Tech Lead names the final sha; dev hands in that sha (REV-13) |
| REV-4 | retargeted away from dev (now: qa-whitebox, tech-lead) | 220 | 0 | the Tech Lead's technical AC require two real samples |
| REV-6 | retargeted away from dev (now: qa-whitebox, tech-lead) | 183 | 0 | the Tech Lead's technical AC carry the payload-shape class |
| REV-13b | kept | 172 | 172 | |
| REV-14b | shortened | 203 | 183 | |
| REV-15 | retargeted away from dev (now: tech-lead) | 198 | 0 | task file cites [REV-15]; CORE-6 |
| EVID-1 | retargeted away from dev (now: tech-lead, qa-w, qa-b) | 285 | 0 | EVID-2a / EVID-4 name `evidence.md` and the embed form |
| EVID-2a | shortened (M and L only) + carries EVID-1 | 95 | 150 | |
| EVID-2b | shortened | 295 | 269 | |
| EVID-3b | retargeted away from dev (now: qa-w, qa-b, team-lead) | 96 | 0 | EVID-2b same |
| COST-1 | retargeted away from dev (now: all but dev) | 323 | 0 | COST-3 carries the Stop-hook reaction (notes, then `squad-respawn`) |
| COST-2 | retargeted away from dev (now: all but dev) | 93 | 0 | COST-3 |
| COST-3 | shortened + carries COST-1/2/9 | 174 | 206 | |
| COST-5 | shortened | 142 | 124 | |
| COST-7 | retargeted away from dev (now: all but dev) | 149 | 0 | START-6 reads own notes; rules are attached |
| COST-9 | retargeted away from dev (now: all but dev) | 76 | 0 | COST-3 |
| COST-11 | retargeted away from dev (now: all but dev) | 107 | 0 | Manager / Team Lead decide step-ups |
| NOTE-1 | shortened | 482 | 188 | |
| SAFE-1a | shortened + carries SAFE-5 | 334 | 168 | |
| SAFE-2 | retargeted away from dev (now: all but dev) | 83 | 0 | settings deny of Jira and Confluence write tools (`templates/squad/settings/dev.json`) |
| SAFE-3 | shortened | 176 | 153 | |
| SAFE-4 | kept | 90 | 90 | |
| SAFE-5 | retargeted away from dev (now: all but dev) | 155 | 0 | SAFE-1a "Commit only to your own `squad/...` branch" |
| SUITE-2a | shortened | 135 | 132 | |
| START-7 | retargeted away from dev (now: others) | 131 | 0 | START-6 step 2 ("in a goal also goal.md and shared/") |
| LC-2 | retargeted away from dev (now: tech-lead, team-lead) | 178 | 0 | LC-19: `Design:` ticket waits for `Status: final` |
| LC-19 | shortened (LC-2 moved to its carrier) | 290 | 171 | |
| SIZE-5a | retargeted away from dev (now: tech-lead) | 116 | 0 | Tech Lead owns business AC in S; MSG-11a |
| SIZE-8a | retargeted away from dev (now: tech-lead) | 160 | 0 | EVID-4 |
| MSG-4a | shortened | 100 | 97 | |
| MSG-7a | retargeted away from dev (now: manager, tech-lead) | 148 | 0 | the ruling itself starts with `FINAL:`; a new fact is an `ASK` (MSG-11a) |
| MSG-11a | shortened | 353 | 204 | |
| LC-20a | shortened | 140 | 109 | |
| REV-13a | kept | 132 | 132 | |
| REV-14a | shortened | 168 | 143 | |
| EVID-3a | retargeted away from dev (now: tech-lead) | 72 | 0 | EVID-2b "each review file in `$SCOPE_DIR/evidence/<task>/`" |
| EVID-4 | shortened + carries SIZE-8a, EVID-5 | 306 | 284 | |
| SIZE-10a | retargeted away from dev (now: tech-lead) | 155 | 0 | EVID-4 (screenshots in S) |
| EVID-5 | retargeted away from dev (now: tech-lead) | 201 | 0 | EVID-4 carries the S design-screenshot sentence |

New for dev: CORE-6, SAFE-11.

Retargeted rules and their role sets at M (`squad-process who <ID>`):
- `GOAL-6b`: M: acts: tech-lead; aware: -
- `PROMO-5`: M: acts: tech-lead; aware: -
- `MSG-1`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-2`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-5`: M: acts: team-lead; aware: manager, ba, tech-lead, qa-whitebox, qa-blackbox, designer
- `MSG-7b`: M: acts: manager, team-lead, ba, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-9`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `MSG-10`: M: acts: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: -
- `LC-1`: M: acts: tech-lead; aware: -
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

`squad-process rule REV-4` (a Developer may run it: dev `allow` has `Bash(squad-process rule:*)` and `who`):
```
## REV-4 Real samples
Code that parses another tool's output (pane text, logs, an API) needs two real samples, including the constant or idle case, before a pattern is trusted. The Tech Lead's technical AC require them.
```

### Other eight roles, before/after (compose at M, design yes, goal yes, base vs this sha)
Gains are the named ones the Tech Lead ruled on (ASK 22, answer (a)): dev-only on-demand rules need a role that plans work citing them, so GOAL-6b, PROMO-5, REV-15, LC-1, SIZE-8a go to the Tech Lead and LC-6 to the Team Lead; the carrier is the task file that cites them (SIZE-6a/6b now say "cite the on-demand rules"; integration.md and trim.md draft). Gained IDs, with bytes added; no role lost an ID.
| role | IDs added (+bytes) | IDs lost | IDs with changed text | total bytes before → after |
|---|---|---|---|---|
| ba | CORE-6 +162 | - | CORE-2, CORE-3, CORE-4, CORE-5, COST-3, MSG-1, MSG-3, MSG-4b, NOTE-1, SAFE-3, START-6 | 9674 → 9010 |
| designer | CORE-6 +162 | - | CORE-2, CORE-3, CORE-4, CORE-5, COST-3, MSG-1, MSG-3, MSG-4b, NOTE-1, SAFE-3, START-6 | 7209 → 6545 |
| manager | CORE-6 +162 | - | CORE-2, CORE-3, CORE-4, CORE-5, COST-3, MSG-1, MSG-3, MSG-4b, NOTE-1, SAFE-3 | 39066 → 38447 |
| qa-blackbox | CORE-6 +162, SAFE-11 +184 | - | CORE-2, CORE-3, CORE-4, CORE-5, COST-3, MSG-1, MSG-3, MSG-4b, NOTE-1, SAFE-3, START-6 | 9256 → 8785 |
| qa-whitebox | CORE-6 +162, SAFE-11 +184 | - | CORE-2, CORE-3, CORE-4, CORE-5, COST-3, MSG-1, MSG-3, MSG-4b, NOTE-1, SAFE-3, START-6 | 10003 → 9532 |
| team-lead | CORE-6 +162, LC-6 +109 | - | CORE-2, CORE-3, CORE-4, CORE-5, COST-3, MSG-1, MSG-3, MSG-4b, NOTE-1, SAFE-3, SIZE-6b, START-6 | 17426 → 17007 |
| tech-lead | CORE-6 +162, GOAL-6b +232, LC-1 +108, PROMO-5 +185, REV-15 +196 | - | CORE-2, CORE-3, CORE-4, CORE-5, COST-3, MSG-1, MSG-3, MSG-4b, NOTE-1, SAFE-3, START-6 | 25312 → 25187 |
| token-coach | CORE-6 +162 | - | CORE-2, CORE-3, CORE-4, CORE-5, SAFE-3 | 3224 → 3307 |

Changed text is the shortened shared wording the ticket listed (MSG-1, MSG-3, NOTE-1, COST-3 absorbing COST-1/2, START-6) plus CORE-2..5 and SAFE-3 trimmed to fit 5 KiB; MSG-1 lost its type table (CORE-2 lists the types). SIZE-6b/6a gained the "cite the on-demand rules" sentence (no existing rule said it). SIZE-8a is S only, so it shows in no M composition. The Team Lead and Tech Lead tests still pass (`test_team_lead_role`, `test_manager_m_l`, `test_pod_contact_routes`).

Scratch rule SAFE-11: composed files containing `mktemp -d` and `${VAR:?}`: dev, qa-whitebox, qa-blackbox = 3 of 9; the other six 0 (`test_scratch_rule_reaches_dev_and_both_qas_only`).

### Probe (AC 5 and BT-4; Haiku, \$0.004 of the \$0.10 cap)
`claude -p "<question>" --model haiku --plugin-dir . --agent squad:dev --append-system-prompt-file dev.rules.md --output-format json --tools ""`, `dev.rules.md` = `squad-process compose dev` (M, design yes, goal yes). Full output: `probe-output.json`, `probe-bt4.json`.

AC 5 (message type / rule not given / push):
```
(a) Send it with SendMessage to the agent in roster.md as `<TYPE> <TASK-ID>: <text>`. Types: ASK, ANSWER, DECISION, BLOCKED, HANDIN, PASS, FAIL, STATUS. [CORE-2]
(b) `squad-process rule <ID>`. [CORE-6]
(c) NO. Commit only to your own `squad/<squad>/<scope>/<agent>` branch. [SAFE-1a]

GOAL-6b text: NO (not in my attached rules)
mktemp -d: YES (SAFE-11)
```
BT-4 (five floor markers, pointer rule): hand in, evidence, no push, suites and returned task all YES; for an integration task the Developer answers it runs `squad-process rule <ID>` (CORE-6) once the task file names the ID.
```
1. "how to run it" (REV-13b): YES
2. "squad-evidence check" (EVID-2b): YES
3. "Never push, rebase" (SAFE-1a): YES
4. "two suite runs never overlap" (SUITE-2a): YES
5. "On `FAIL`: fix every finding" (LC-3a): YES

Integrate-scope-branches rule: not in my attached rules, and I don't have its ID. Run `squad-process rule <ID>` (CORE-6) once the ID is known, or ask the Team Lead for it.
```

### Assertion map (old test → new)
- `test_pod_rules_process.test_pod_contact_and_team_lead_to_manager`: dev's MSG-5 text → QA whitebox still gets it, `MSG-5` is not in dev's file (carrier MSG-4b/MSG-11b).
- `test_suite_rules_process.test_tech_lead_runs_it_and_others_never`: "The full suite…" → "the full suite is the Tech Lead's" (SUITE-2a shortened).
- `test_suite_rules_process` integration tests: dev's composed file → `squad-process rule GOAL-6b` output ("is handed in"); Tech Lead assertions unchanged.
- `test_task_id_rule.test_rule_is_targeted_at_every_role_and_size`: BULLET follows the shortened MSG-3; `test_rosters_say_ticket_nn` still covers the roster templates.
- `test_pod_contact_routes`: new MSG-11a/b and LC-20a/b wording; the "permission prompt goes nowhere" line deleted (it lived in MSG-11a/b and MSG-10; MSG-10 still tells the other roles).
- `test_process_citations.test_an_unknown_pointer_is_reported`: breaks `[WHO-1a]` in CORE-3 (CORE-2 no longer carries a pointer).
- `test_instructions.RuleDutiesTest.test_dev_copies_reports_…`: REV-15 read from `squad-process rule REV-15`; the Tech Lead's file must contain `## REV-15`.
- New: `test_dev_rules_size` (7 tests).
