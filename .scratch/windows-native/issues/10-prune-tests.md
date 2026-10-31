# 10 — Prune tests (PO order 2026-10-31)

Status: ready-for-agent (draft by Tech Lead). Owner of criteria: Tech Lead. Goal: **less suite time and fewer lines, same protection.**
PO words: "dive into current tests, clean up unnecessary tests as much as possible".
Now: 88 files in tests/, ~20.3k lines, ~1,200 test methods. No full-suite run (run_suite, `--tz`, receipts) until this ticket is final.

## Base and parallel start
- Base = sha after 03d is final (same tests/ tree). One fresh Dev. QA batch B5 = this ticket alone.
- Option to start earlier: only files **no Dev branch of this scope changes** (checked: `git diff --name-only caf9f6e <branch> -- tests`, branches dev-1..6). Safe now (no merge conflict later):
  `test_advisor_rules, architect_handoff, designer_handoff, dev_rules_size, hooks_json, inbox_body_guide, instructions, manager_inbox_read, manager_m_l, model_effort_settings, po_inbox_contract, po_inbox_mod, pod_contact_routes, pod_rules_process, process_citations, process_writing, processlint, promotion_0_6_0, qab_optional, retro_rules, sizes, small_files_equivalence, squad_report_cli, squad_report_query, squad_team, squadcompose, squadinbox, squadreport_collect, squadreport_digest, squadreport_embed, squadreport_html, squadreport_rollup, squadreport_rollup_ui, squadreport_tasks, squadrules, squadtranscript, suite_rules_process, task_id_rule, team_cli, team_duties, team_lead_role`.
  Not safe until 03d/06 final (a branch edits them): the other 38 files, incl. `test_squad_spawn, test_squad_close, test_ca_launchers, test_ca_autoswitch, test_squadruntime, test_squad_start, test_squadinbox_answer, test_squad_evidence, test_squadreport_ui, test_run_suite, test_ca_win`.
  Plan: Dev starts on the safe list; the rest waits for 03d + 06 on the integration base.

## Keep rule (a)
Per `scope.md` Test economy: **one test per AC or real regression risk.** A test stays when it answers "which bug does this catch that no other test catches?". Keep the one test that covers a risk best (real script, real files); drop the rest of its family.

## Delete candidates (b)
1. **Duplicates**: two tests that fail on the same defect (same script, same assert, different name; a unit test whose behaviour a CLI test already runs end to end).
2. **Matrices**: loops over many inputs/roles/shapes where one or two cases show the same code path (example: `test_small_files_equivalence` 7 shapes x roles golden; keep one shape plus the one that differs).
3. **Trivial-code tests**: constants, getters, pass-through, argparse help text, "file exists".
4. **Tests of removed behaviour**: old language/layout/size/board/history, migrations that no longer exist (check `docs/adr` 0009, 0018, 0019 and `test_old_language_inventory`), tests that only assert something is *absent* that no code could bring back.
5. **Over-specified text / golden tests**: assert exact wording of a rule, template, help or error text so every edit breaks them. Replace by a structural assert (heading/ID exists, lint passes) or delete. See risk R1.
6. **Slow for what they prove**: sleeps, real browser, many subprocess launches. Keep one smoke per feature; move the rest to a cheaper in-process check, or delete.

## Never delete (c)
- Any test that guards a Windows fix of this scope (tickets 01-09): `test_winlaunch, test_no_bare_bash` (guard + ratchet), `test_windows_safe, test_win_utf8_process, test_utf8_helpers, test_squadinbox_win, test_squadio, test_ca_win, test_crlf_squad_files, test_squadinbox_body_crlf, test_log_append_stress`, the pin-fallback tests of 02, the untrack/size test of 04, the pick_bash tests of 07, and every `os.name == "nt"` skip with its cause.
- Any test that names a bug fix (docstring/comment says "regression", an incident, a ticket id, an ADR): keep unless the code it guards is gone (then item 4, with the proof in the report).
- Test helpers other files import (`ca_stubs, winlaunch, rulesview, *_fixtures, run_suite`): change only if a deleted test was their last user; then delete the dead helper too.

## Hard limits (d)
- Linux (Debian) green on every touched file; **zero new skips** (an existing skip may go only if its test is deleted for a rule above).
- Never weaken an assert to make a test pass. Never delete a test because it fails; a failing test is a finding, not a candidate.
- Do not change product code (`bin/`, `templates/`, `agents/`, `skills/`). Tests and test helpers only. If a test reveals dead product code, list it in the report; no edit.
- Windows: no `tests/` change may drop a Windows-run file below what 03c/03d recorded as passing.
- Commit per group of files (smallest unit = one file), so QA can revert a group.

## Report (e): `prune-report.md`
Dev writes it next to the ticket evidence (`.scratch/windows-native/issues/10-prune-tests/prune-report.md`, EVID-1) and copies it to `$SCOPE_DIR/evidence/10/` at the handed-in sha (REV-15). Content:
1. **Size/time view, slowest first.** One table, sorted by baseline seconds (Linux, per-file `python3 -m unittest -q <stem>` with `PYTHONDONTWRITEBYTECODE=1`, as run_suite does): `file | tests before | tests after | lines before/after | seconds before/after | verdict (pruned / kept / skipped-scope)`. Time only for the 15 largest files by lines plus the 3 browser files (`test_squadreport_ui, test_squadreport_rollup_ui, test_run_suite`) — not a full-suite run; per-file runs only. Total row: tests, lines, seconds of the measured files.
2. **Removed tests**: one row per removed test: `file::test | rule (b-1..6) | one-line reason | covered by <other test>` (for b-1, b-2 name the surviving test). A test merged into another counts as removed + named survivor.
3. **Kept-on-purpose**: files with Windows guards (c) listed with one line each, so QA sees they were considered.
4. **Not touched, why**: the files left alone (e.g. already minimal).
Target (not a gate): -25% test methods and a visible cut in the slowest files. A smaller cut is fine if the report says why the rest earns its place.

## Technical AC (QA whitebox checks by sampling, not re-reading all)
1. Linux counts: for every touched file `Ran N` after = before - removed rows of the report (script: count `def test_` in `git show <base>:file` vs HEAD, diff must equal the report's rows).
2. No new `skip`/`skipIf`/`expectedFailure` lines in the diff (`git diff <base> -- tests | grep '^+.*skip'` empty, except unchanged moves).
3. Section (c) files: `git diff --stat <base> -- <those files>` shows no removed `def test_` lines.
4. Sample 10 removed rows across (b-1..b-6), at least 3 from the biggest files: confirm the reason is true and the named survivor exists and covers the same risk (mutation: break the product line, survivor must fail).
5. `git diff --name-only <base> -- bin templates agents skills` empty.
6. Evidence check: `squad-evidence check <10 folder> --base <code sha>` exit 0.
7. Full suite is **not** run by the Dev. The suite owner runs it once after this ticket and the integration (SUITE-1..4), `--tz`, WSL clone.

## HOLD (Manager FINAL, 2026-10-31): R1 files untouched until the PO answers
Dev leaves these five files alone: `test_squadrules, test_squadcompose, test_sizes, test_team_duties, test_small_files_equivalence`. Report lists them as "held (R1)". All other files in this ticket may be pruned. The Manager sends the answer; then the Tech Lead updates this section.

## Risks for the PO (decision needed, see R1)
- **R1 — rules-wording tests protect the process files.** Many tests (`test_squadrules, test_squadcompose, test_sizes, test_team_duties, test_*_rules*, test_retro_rules, test_task_id_rule, test_pod_*`, golden tables in `test_small_files_equivalence`) assert what the composed process says per role. They break on every rule edit (cost) but are the only net against a rule dropped or sent to the wrong role (damage: a role silently loses a duty). Proposal: keep (1) `processlint` / citations resolve, (2) one composed-per-role structure test per role, (3) the duty-owner table test; delete exact-wording and per-shape golden matrices. PO may instead say "keep all rules tests" or "cut hard".
- R2 — Linux-only suite: if a deleted test was the only one that ran on Windows, 03d's Windows state could shrink silently. Mitigated by hard limit 4.

## Comments
