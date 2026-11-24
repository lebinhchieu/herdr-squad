# Evidence: 06 Small edits: rm, UI AC, notes pointers
sha: 7fe7fc4
## Behaviour
- SQ-6b merge: branches merged by passed sha into this worktree; `git merge-base --is-ancestor <sha> HEAD` is true for 6d132da (01), 9fcfd1a (03), a728476 (04), d4a022c (02, on branch -04), 9306e09 (05, on branch -03). One conflict, the `LIMIT` line of `tests/test_dev_rules_size.py` (01 vs 02); resolved, then set finally by 06.
- AC1: SAFE-11 and SAFE-11b are `roles: all`; `test_scratch_rule_reaches_every_role_without_cd_out` composes every role: both rules present, each at most 60 words, "anywhere under `/tmp`" kept, no "out before". `test_safe11_rm_examples_match_allow_and_no_ask` (the `$` assertion dropped: the mktemp form has `$D`) passes. The example is `rm /tmp/<dir>/<file>`, not `rm -f`: the settings allow `rm`, `rm -r`, `rm -rf`, `rmdir` under `/tmp/*` only.
- AC2: `grep -rn '0.10.10' .claude-plugin templates skills` hits only changelog lines 20 and 29 (the v28 entry); `plugin.json` says 0.10.11. Changelog v29 covers 01-06 with what/why, Deploy, Rollback.
- AC3: `python3 bin/squad-process lint` exit 0 (REV-8 is 60 words or fewer).
- LIMIT (tl-design section 4): measured worst case over every team set, designer and architect sets included: 6858 B (tech-lead, designer, architect, goal yes, qa light). LIMIT = 6950 (+92, cap +120). Worst no-designer team 5473 (base) -> 6354; growth by ticket: 01 313, 02 286, 06 265 B (budget 500); the rest is 03-05. `test_every_team_set_fits_the_limit` passes in full.
- AC4 + SQ-10: test_windows_safe 14, test_utf8_helpers 14, test_instructions 16, test_sizes 8, test_small_files_equivalence 2, test_squadcompose 44, test_squadsettings 25, test_dev_rules_size 9, test_squad_merge_check 9: all OK. test_qab_optional passes with SQUAD_DIR unset; with this session's SQUAD_DIR it fails 1 (`who SIZE-8b` stops: "EVID-2d: overlay written for @ecb878fe, plugin now @8983d961", the plugin squad's stale EVID-2d overlay from 03; expected until re-pin, not a regression).
- `upgrade --check` against the plugin squad: stops at `EVID-2d stale` (03); `review` lists SQ-3c (COST-16), SQ-4/SQ-10 and REV-8, SQ-20 and the EVID rules. Replacements are in each ticket's Comments (01-06).
- `base-failures.md` does not exist yet (no Tech Lead has written it); the "fixed by 06" row is the Tech Lead's to add (SAFE-4, SUITE-7). Not done by me.
- No full suite run (not asked).
- Return of 3f14b8c (QA whitebox FAIL): REV-8 said "size", which `test_promotion_0_6_0::NoSizeWord` forbids in rule text. Now "viewport width" (60 words, lint exit 0). Reran test_promotion_0_6_0, test_dev_rules_size, test_squadcompose, test_sizes, test_windows_safe, test_utf8_helpers, test_instructions, test_rules_wording, test_rules_contract, test_small_files_equivalence: all OK. Follow-up (dropped "and records the agreement") left as is: it does not fit 60 words.

## Review, QA whitebox

### QA whitebox, ticket 06, sha 3f14b8c (f9b7a9f + doc-only AC2 reword)

Verdict: FAIL (1 finding).

#### Finding (breaks AC4 and an existing test)
1. `templates/squad/process/review.md:84` (REV-8) now says "names the **size** it is checked at". `tests/test_promotion_0_6_0.py::NoSizeWord::test_rules_have_no_size_word_outside_the_tombstones` (grep `(?i)\bsize\b(?!-\d)` over `templates/squad/process`) fails: `{'templates/squad/process/review.md': 1} != {}`. It passes on base c853707, so this diff causes it. AC4 requires every `grep -rl` hit of a changed string to run; the test file is a hit of `templates/squad/process` and the Developer's run list skipped it.
   Pass: reword without the word "size" (for example "the viewport width it is checked at"), rerun `test_promotion_0_6_0`.

#### Checked, passes
- Diff f9b7a9f..3f14b8c: only the ticket file, AC2 line; doc-only. 3f14b8c is a descendant of f9b7a9f.
- SQ-6b: 6d132da, 9fcfd1a, a728476, d4a022c, 9306e09 are all ancestors of HEAD.
- AC1: SAFE-11 and SAFE-11b `roles: all`; composed rules of all 10 roles hold both; no "cd out before rm"; example `rm /tmp/<dir>/<file>` matches the settings allow list. REV-8 in ba/qa-b; NOTE-1 pointers sentence in the 8 note roles.
- AC2 (reworded): plugin.json 0.10.11; the only `0.10.10` hits under `.claude-plugin templates skills` are in the v28 changelog entry.
- AC3: lint exit 0.
- Byte cap: measured max over all 128 team sets 6858 B <= LIMIT 6950; worst no-designer team 6354; `test_every_team_set_fits_the_limit` passes.
- Pass (SQUAD_* env unset): test_windows_safe, test_utf8_helpers, test_instructions, test_rules_contract, test_rules_wording, test_small_files_equivalence, test_sizes, test_squadcompose, test_squadsettings, test_dev_rules_size, test_qab_optional, test_processlint, test_old_language_inventory, test_squad_start, test_squadupgrade, test_squad_merge_check, test_squad_spawn.
- `test_templates::test_designer_may_write_only_ui_design_files` fails the same on base (`Write(//tmp/**)` settings list), not from this diff.

#### Follow-up (not FAIL)
- REV-8 also dropped "and records the agreement" from the original sentence; the ticket only asked to leave out the "retire the BA" sentence.

### Re-check, sha 5f5868a

Verdict: PASS. Diff 3f14b8c..5f5868a: REV-8 "size" -> "viewport width" (review.md) plus one evidence line. Lint exit 0. 191 tests OK with SQUAD_* env unset, including test_promotion_0_6_0 (NoSizeWord), test_rules_wording, test_rules_contract, test_dev_rules_size. Finding 1 fixed. Follow-up stands (REV-8 lacks "records the agreement"; not a FAIL).

### Final sha 7fe7fc4 (Tech Lead DECISION, REV-3)

Verdict: PASS. Supersedes my earlier verdicts on f9b7a9f, 3f14b8c, 5f5868a.
- REV-8 body byte-identical to base c853707 ("records the agreement" restored; follow-up closed).
- REV-8b "UI AC width and clock": roles ba, qa-blackbox, same `when:`/topic as REV-8; composed rules hold REV-8b only for ba and qa-blackbox (37 words, under 60); none for dev or other roles.
- Ticket Comments and changelog v29 name REV-8b. Lint exit 0. Max Developer bytes over all team sets 6858 <= LIMIT 6950.
- 321 tests OK (SQUAD_* unset): test_promotion_0_6_0, test_rules_wording, test_rules_contract, test_windows_safe, test_utf8_helpers, test_instructions, test_small_files_equivalence, test_sizes, test_squadcompose, test_squadsettings, test_dev_rules_size, test_qab_optional, test_processlint, test_old_language_inventory, test_squad_start, test_squadupgrade.
- Earlier checks of f9b7a9f (SAFE-11/11b all roles, NOTE-1, version bump, SQ-6b ancestry) are untouched by the later diffs.

## Review, QA blackbox

### QA blackbox 06, sha f9b7a9f

Method: `unset SQUAD_DIR SCOPE_DIR GOAL_DIR`; `squad-process compose <role> --plugin-root <worktree>` on a scratch squad dir (no overlay) for all 10 roles; `squad-process rule <ID>`; grep; `git merge-base --is-ancestor`.

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 SAFE-11 all roles, no "cd out before rm" | live | composed manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect, dev, token-coach | SAFE-11 and SAFE-11b in all 10; 0 hits of "cd out before" in any. SAFE-11: "`rm` there takes only a literal absolute path: `rm /tmp/<dir>/<file>`, or `rm -rf "$D"` after `D=$(mktemp -d)`". SAFE-11b: "Run `rm` alone: no `cd`, `&&` or `;` ..., no glob, relative path or `$(...)` target. Why: Claude Code's dangerous-rm check ..." | pass |
| AC2 old version not found | live | `grep -rn '0.10.10' .claude-plugin templates skills`; plugin.json | `plugin.json` 0.10.11. Only hits: changelog lines 20 and 29, the v28 entry (history). Accepted under the AC2 wording the Tech Lead set in tl-design §6, which the Manager's DECISION 06 pointed at | pass (see follow-up) |
| AC3 lint | live | `squad-process lint` | exit 0 | pass |
| AC4 targeted tests | shot | not re-run (QA whitebox owns tests); Developer's evidence lists the touched and hit test files, all OK, known base failure fixed by the new LIMIT | - | not mine |
| REV-8 edit | live | `rule REV-8` | UI AC names size and value/rule, one example for "shortest", "fits" or a count limit; relative time names the fixed clock; no "retire the BA" sentence | pass |
| NOTE-1 edit | live | `rule NOTE-1` | `Pointers` at most 5 paths, each with a line range or section; after a respawn read only these before the first reply ([COST-7]) | pass |
| changelog covers 01-06 | live | read v29 | entries for 01, 02, 03, 04, 05, 06 with what/why; Deploy and plugin 0.10.11 | pass |
| integration: siblings merged | live | `git merge-base --is-ancestor` for 056c873, 6d132da, 9fcfd1a, e90513d, a728476, 854a024, d4a022c, 9306e09 | all ancestors of f9b7a9f | pass |
| no PO name / `_done` / version in new rule text | live | grep added lines under `templates` vs c853707 | no hit | pass |

Follow-ups (not FAIL, SQ-4):
- AC2 as written in the ticket ("finds nothing") is met only for `.claude-plugin` and `templates`; two historical v28 changelog lines still say 0.10.10. Fine under the Tech Lead's reworded AC2; the ticket's AC line itself still reads the old wording.
- The ticket's SAFE-11 example is `rm -f /tmp/<dir>/<file>`; the rule shows `rm /tmp/<dir>/<file>` (settings allow `rm`, `rm -r`, `rm -rf`, `rmdir` under `/tmp/*`, not `rm -f`). The Developer explained this in the ticket Comments; I accept it.
- The real plugin squad's stale EVID-2d overlay stops `compose` until re-pin (expected, from 03).

#### Re-check, sha 5f5868a
Diff 3f14b8c..5f5868a: REV-8 says "names the viewport width it is checked at" (was "the size"); one doc-only evidence line. Lint exit 0. The rest of REV-8 is unchanged (value or rule, one example for "shortest", "fits" or a count limit, fixed clock for a relative time). Verdict: PASS.
Follow-up (not FAIL): "viewport width" is narrower than the ticket's "size it is checked at"; a UI AC about height would not be named by it. Accepted: the ticket's examples are width-driven and QA whitebox asked for the change.

#### Re-check, sha 7fe7fc4 (supersedes 5f5868a, per the Team Lead's DECISION 06)
Checked, verdict held until the Tech Lead names the final sha (REV-3).

| What | how | what I saw | result |
|---|---|---|---|
| REV-8 back to base | `rule REV-8` | "Agree the business AC before work starts, as Given/When/Then a user can observe in the running app. The BA writes them where `project.md` says AC live and records the agreement." | pass |
| REV-8b holds the UI clause | `rule REV-8b` | names the viewport width it is checked at, the value or rule, one example for "shortest", "fits" or a count limit; a relative time names the fixed clock | pass |
| REV-8b reaches ba and qa-blackbox | compose on a scratch squad with `team: ba, team-lead, tech-lead, qa-white, qa-black` | ba and qa-blackbox get REV-8 and REV-8b; qa-whitebox, tech-lead, team-lead, manager, dev get neither. (On a team without a BA neither rule composes: its `when:` is `business-ac = ba and qa-black = yes`.) | pass |
| lint | `squad-process lint` | exit 0 | pass |
| other 06 checks | composed all 9 roles; grep; plugin.json | SAFE-11, SAFE-11b on all roles; NOTE-1 on all but dev (as before); plugin.json 0.10.11; the only 0.10.10 hits are v28 changelog lines; changelog v29 line for REV-8/REV-8b | pass |

## Review, Tech Lead

### Tech Lead review, integration sha (SQ-6, REV-3)

Final sha: f9b7a9fcfe9336423f0da4a7ace1bf270396300d (branch squad/plugin/upstream-proposals/plugin-dev-upstream-proposals-06), worktree clean. Base c853707. Doc-only edits wait until every verdict is in.

#### SQ-6: passed branches are ancestors of 06
`git merge-base --is-ancestor <passed sha> f9b7a9f`: 01 6d132da yes, 02 d4a022c yes, 03 9fcfd1a yes, 04 a728476 yes, 05 9306e09 yes. No related sibling is left unmerged.

#### Targeted tests on f9b7a9f (run by the Tech Lead, from `tests/`, `python3 -m unittest <module>`)
SQ-10 files: test_windows_safe 14 OK, test_utf8_helpers 14 OK, test_instructions 16 OK.
Hits of the changed IDs and strings: test_dev_rules_size 9 OK (the sweep that failed on base now passes for all 128 team sets), test_squadsettings 25 OK, test_rules_contract 18 OK, test_squad_merge_check 9 OK, test_small_files_equivalence 2 OK, test_rules_wording 30 OK, test_squadcompose 44 OK, test_sizes 8 OK, test_squadrules 46 OK, test_processlint 31 OK.
`python3 bin/squad-process lint`: exit 0.

#### Design checks
- LIMIT 6950; measured worst case 6858 B (tech-lead+designer+architect, goal yes, qa light), room 92 B (<= 120). Growth of the worst no-designer team: 01 313, 02 286, 06 265 B, each inside its budget (450, 400, 500).
- plugin.json 0.10.11; `grep -rn 0.10.10 .claude-plugin templates skills` hits only the v28 changelog entry (history). Changelog v29 covers 01-06 with Deploy and Rollback.
- No `SQ-6`, `SQ-7` left in `bin/` or `templates/`.
- SAFE-11 and SAFE-11b: roles all (Manager FINAL).
- test_squadsettings: the removed `assertNotIn("$", ...)` is replaced by the existing `if "$" not in c` guard; the ask check stays for every example, the allow check stays for literal ones. Note for Chieu: `rm -rf "$D"` does not match the `Bash(rm -rf /tmp/*)` allow glob, so it may still prompt; the example is from guardian SQ-35, kept as ticketed.
- CONTEXT.md: **Base failures file** entry added (promotion, PROMO-4).
- `$SQUAD_DIR/base-failures.md` written with the one row, fix "fixed by 06".

Verdict: Tech Lead review passes at f9b7a9f. Full suite not run: waiting for the PO's yes (SUITE-1).

#### Update: final sha 7fe7fc4 (REV-3), supersedes f9b7a9f and 3f14b8c
f9b7a9f and 3f14b8c failed `test_promotion_0_6_0::NoSizeWord` (REV-8 said "size"; QA whitebox found it, my hit list had missed it). REV-8 is back to its base body; the UI clause is REV-8b "UI AC width and clock" (ba, qa-blackbox, no dev). On 7fe7fc4 (worktree clean) I ran: lint exit 0; test_windows_safe, test_utf8_helpers, test_instructions, test_promotion_0_6_0, test_dev_rules_size, test_squadsettings, test_rules_contract, test_squad_merge_check, test_small_files_equivalence, test_rules_wording, test_squadcompose, test_sizes, test_squadrules, test_processlint, test_qab_optional, test_old_language_inventory, test_team_duties, test_squadruntime all OK. test_templates has 1 failure that also fails on c853707 (base-failures.md row 2). `squad-evidence check` on 06's folder: exit 0 (the QA-cells commit caf8b13 is inside the range; rerun on the last evidence sha).
Verdict: Tech Lead review passes at 7fe7fc4.
