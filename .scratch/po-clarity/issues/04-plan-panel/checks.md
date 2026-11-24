| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `Plan04.test_T04_AC1_steps_with_deps_arrows` OK | - | - |
| AC2 | `test_squadplan` goal rows; goal screenshot OK | - | - |
| AC3 | `Plan04.test_T04_AC3_over_estimate_boundary...` (90 no chip, 91 chip) OK | - | - |
| AC4 | `Plan04.test_T04_AC4_missing_aim...` OK | - | - |
| AC5 | `test_processlint`, `test_rules_contract`, `test_rules_wording` OK; grep of `templates/squad/ticket.md` for the three field names: lines 6, 7, 8 | - | - |
| AC6 | `PlanRouteTest` (bad Host 403, no write route) OK | - | - |
| AC7 | `test_squadboard_demo` OK; 2 screenshots in evidence.md | - | - |
| LC-11 design states | `Plan04` tests: steps, over-estimate chip, `–` and loop, escaped text, fold, goal waits; shots `plan-scope.png`, `plan-unfolded.png`, `plan-goal.png`. Loading, "Cannot read the plan.", empty and narrow (<560px): not shot (see evidence.md); aim cell also clipped at 15em | - | - |
| T04-1 | `PlanRouteTest.test_T04_AC6_...` (bad Host 403, no write route); GET routes carry no token (Manager accepted) | - | - |
| T04-2 | `test_squadplan.test_T04_2_loops_end_and_are_marked`, `test_T04_2_AC1_chain_...` | - | - |
| T04-3 | `test_squadplan.test_T04_3_duration_table` | - | - |
| T04-4 | `Plan04.test_T04_AC3_over_estimate_boundary_...` (90 no chip, 91 chip) | - | - |
| T04-5 | `test_squadplan.test_T04_5_goal_columns_...`, `test_T04_5_a_table_without_...` | - | - |
| T04-6 | `Plan04.test_T04_T6_markup_in_aim_title_waits_stays_text_...` | - | - |
| T04-7 | `test_squadplan.test_T04_7_aim_check_is_the_one_of_ticket_03` (uses `squadids.bare_ids`) | - | - |
| T04-8 | START-19c in `starting.md`; `test_processlint`, `test_rules_contract` OK | - | - |
| T04-9 | `test_squadboard_demo` OK; 3 screenshots in evidence.md | - | - |
