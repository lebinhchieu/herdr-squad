# 10b — Prune the five R1 rules-wording test files (PO E4 = a, 2026-10-31)

Status: ready. Owner of criteria: Tech Lead. One Dev. Base: `e24f306` (ticket 10 final, branch `plugin-dev-solve-windows-9`).
Goal: cut the exact-wording and golden-matrix tests; keep the net that catches a rule dropped or sent to the wrong role.
Same rules as ticket 10 (`tasks/10-prune-tests.md`: sections (a) keep rule, (b) delete candidates, (c) never delete, (d) hard limits, (e) report). This file only adds what is new.

## Files (only these five; nothing else in tests/)
| File | Tests now (lines) |
|---|---|
| `tests/test_squadrules.py` | 61 (509) |
| `tests/test_squadcompose.py` | 81 (744) |
| `tests/test_sizes.py` | 34 (564) |
| `tests/test_team_duties.py` | 39 (345) |
| `tests/test_small_files_equivalence.py` | 2 (169) |

Disjoint from the integration task (dev-10). The integration Dev merges 10b last, after FINAL.

## KEEP (the net)
1. **Lint and citations**: every test that runs `processlint` or checks that a cited `[ID]` resolves (also in `test_processlint`, `test_process_citations`; do not touch those files).
2. **One composed-per-role structure test per role** (manager, team-lead, tech-lead, qa-whitebox, qa-blackbox, ba, designer, dev, token-coach, architect): composed rules file for that role exists, has the role's `duties:` line, and contains the rule IDs that role must own (IDs only, not sentences). If a role has several now, keep the one with the most IDs checked and fold the missing IDs into it.
3. **The duty-owner table test** (`duties:` owner per duty vs the roster/WHO rules). One test.
4. One shape for `test_small_files_equivalence`: keep the one shape that differs, plus one default shape.
5. Any test whose docstring or comment names a regression, incident, ADR or ticket id: keep (ticket 10 section (c)).

## CUT
- Exact-wording asserts (a sentence or phrase of a rule, template or help text).
- Per-shape / per-size / per-role golden matrices where one case shows the same path.
- Duplicates of a kept test; tests that only assert something is absent that no code can bring back.
A test merged into a kept one counts as removed + named survivor.

## Technical AC
1. Linux (Debian/WSL) per-file `python3 -m unittest -q <stem>` OK for each of the five files and for `test_processlint`, `test_process_citations`, `test_instructions`, `test_pod_rules_process` (they read the same composed files). Zero new skips (`git diff e24f306 -- tests | grep '^+.*skip'` empty).
2. **Net proof, by mutation** (one run, in a scratch copy, never committed): for 3 roles, delete one rule ID from the role's composed file or move a duty to another role; the kept structure test or duty-table test must fail. Write the 3 results in the report.
3. Counts: `def test_` in the five files at HEAD = before minus removed rows. Expected cut about 40-60% of the 217 tests; a smaller cut needs a reason per file.
4. `removed.tsv` and `prune-report.md` (ticket 10 format: file::test | rule | reason | survivor) in the 10b ticket evidence folder; copy of the report to `$SCOPE_DIR/evidence/10b/` at the handed-in sha (REV-15). Add a short "Kept net" table: role -> kept test name.
5. `git diff --name-only e24f306 -- bin templates agents skills docs` empty (tests only).
6. Windows: the five files do not run launches; run `python -m unittest <stem>` for each on Windows and record result; it must not be worse than before (compare to base).
7. `squad-evidence check <10b folder> --base <code sha>` exit 0.
8. No full suite (the Tech Lead runs it once on the integration sha). Touched files only.

## HANDIN
Code sha + evidence sha to the Tech Lead, then both QAs after FINAL. Evidence: `.scratch/windows-native/issues/10b-prune-r1/evidence.md` (the Dev creates the ticket file from this text; QA-w samples removed rows, QA-b has little to run: Windows per-file results only).

## Added 2026-10-31 (PO: "test_team_duties looks stale") — what is stale, decided by the Tech Lead
Evidence: `drop-scope-size` made `team:` the only language. `sr.legacy_team(size, ...)` (S/M/L -> team) has no caller in `bin/` (only its definition, squadrules.py:251). It stays as a test fixture builder (8 test files use it: rulesview, test_dev_rules_size, test_old_language_inventory, test_qab_optional, test_sizes, test_small_files_equivalence, test_squadcompose, test_team_duties); cleanup ticket 02 says "kept on purpose". `read_home` is live (squadcompose, squadruntime, squadteam, squadrules_cli); its `size:`/old-line path is a live REFUSAL (ComposeError), not dead code.

**test_team_duties.py (39 tests)**
- CUT (stale, old size model), 16: `Equivalence` all 6 (today's S/M/L owners table `OLD`, the six named shapes), `LegacyTeam` all 9, `ChangelogV9` 1 (heading wording).
- CUT (trivial/duplicate), 2 of `Sweep`: `test_resolve_is_pure_and_takes_any_iterable`, `test_decided_team_has_no_missing_fact`.
- KEEP: `Sweep` 128-sets one-owner-per-duty (this IS the duty-owner table test) + `thirteen_duties_every_chain_ends...` + the two `when`-key tests; `RoleKey` 2; `ParseTeam` 6; `LintWhen` 8. About 21 stay.
- Remove the `legacy_team` import/`OLD` table from the file when nothing in it uses them.

**test_sizes.py (34 tests, "Ticket 17: S/M/L" era)** judge each class by "does it test the team model or the size model":
- CUT (size model): `DutyOwners`, `Slice3Owners`, `Slice2Owners`, `S_DeveloperReview` (keep nothing: `test_dev_rules_size` keeps the 5 KiB check), `RespawnReadable`, `SizeRules`, `Changelog` (v7 wording).
- `WholeTemplate`: keep `test_every_duty_has_an_owner_per_size` only if it runs on teams, not sizes; else cut with the rest.
- KEEP (team model, `TeamRules`): `no_rule_of_the_two_files_acts_on_an_absent_role_for_any_of_the_128_teams`, `who_lists_exactly_the_acting_roles...`, `every_duty_has_a_rule_per_acting_role`, `text_never_says_size`, `manager_proposal_has_a_row_for_every_role`, `chain_table_names_every_duty`, `every_pointer_to_a_size_rule_in_the_templates_resolves`. Cut `done_text_by_the_four_shapes`, `who_checks_behaviour_by_shape`, `architecture_ac_rules_follow...`, `tombstones...`, `qa_b_is_gone...` (wording / history) unless a docstring names a regression.
- Rename nothing; do not rename the file (other files may import it). If the file ends with fewer than 10 tests, say so in the report.

**Follow-up (not in 10b, no bin/ edit):** drop `legacy_team` from `bin/squadrules.py` after the 8 test files build their teams from explicit lists. Low value (about 10 lines), touches 8 test files: Tech Lead suggests NOT doing it now; list it in the promote notes as "known leftover".
