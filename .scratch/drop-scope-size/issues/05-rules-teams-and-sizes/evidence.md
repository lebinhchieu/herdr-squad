# Evidence: 05 Rules teams.md + sizes.md
sha: 9ffa44f

## Behaviour
- `sizes.md` (43 rules) is in team language: 33 kept (retargeted or reworded), 10 tombstoned in `_removed.md` (`why:` + `replaced_by:`), none says "size" outside `SIZE-n` IDs (`test_text_never_says_size`, `\bsize\b(?!-\d)` grep returns nothing from the two files). New `teams.md`: TEAM-1..7 (Done variants for qa-white only / qa-black only / no QA, QA whitebox behaviour check, BA alone, Tech Lead code check, removing a role). `FILE_ORDER` already has TEAM (ticket 01).
- Kept-alive set (D2, Tech Lead ANSWER 05): IDs cited outside sizes.md in live files, found by `git grep -noE 'SIZE-[0-9]+[a-z]?' -- . ':!templates/squad/process/sizes.md' ':!skills/*/history' ':!skills/squad-process-update/changelog.md' ':!tests' ':!.scratch'`: SIZE-1, 2, 5c, 7a, 13, 14, 16, 22 (starting, lifecycle, review, messages, promotion, spawning, who). SIZE-21a is also kept: the v8 history snapshot cites it and lint walks `skills/`. Not touched here: the files that cite them (tickets 06/07/08 own them).
- One rule per (duty, acting role): `when:` is one duty or presence key plus `qa-black`/`design`/`architecture`. Checked for all 128 teams: no rule of the two files acts on an absent role; Done rules (SIZE-2, TEAM-1..3) are broadcast to every pod role and are the only ones whose `roles:` may list a role the team lacks (`test_no_rule_of_the_two_files_acts_on_an_absent_role...`). `who <rule>` lists exactly the acting roles per duty value (table-driven over DUTIES, C7).
- Four shapes (both QAs, qa-white only, qa-black only, no QA): Done text, behaviour check owner, BA with or without QA blackbox (`test_done_text_by_the_four_shapes`, `test_who_checks_behaviour_by_shape`). Both-QAs text says one PASS is never enough; qa-white-only text never says QA blackbox PASS; no-QA text has the Manager confirm `evidence.md` `## Behaviour` and `## Review`.
- Manager proposal table (SIZE-1) has a row for each of the seven roles; SIZE-22 is the 12-row chain table (replaces SIZE-22/22a).
- Lint baseline (G2b), `bin/squad-process lint`: base 6ec3a75 empty, exit 0; branch empty, exit 0 (diff identical).
- Changelog v9: added TEAM-1..7; changed/retargeted/removed listed per ID with a reason (>10 chars); test_sizes Changelog test accepts `changed:` or `retargeted:` for an ID kept with a rewritten body and ignores `_removed.md` blocks.
- Tests run green: test_sizes (34), test_manager_m_l, test_qab_optional (2 skipped, below), test_architect_handoff, test_pod_rules_process, test_squadadopt, test_instructions, test_squadcompose, test_team_duties, test_squadrules, test_squadprocess, test_squadprocess_apply, test_squadupgrade, test_process_history, test_processlint, test_team_lead_role, test_team_models, test_squadruntime, test_squadinbox, test_squadinbox_answer, test_windows_safe, test_crlf_squad_files.
- Fixture edits forced by retargets (not in the ticket's file list): `test_squadadopt.py` used SIZE-4/SIZE-16 text, now FILE-4/NOTE-2 bullets; `test_architect_handoff.py` and `test_pod_rules_process.py` assertions moved to the new text.
- Left for other tickets (asked to the Tech Lead): (1) 18 `qa-b` `when:` lines in evidence.md, lifecycle.md, review.md, spawning.md are tickets 07/08's files; none remains in sizes.md. (2) Two `test_qab_optional.py` tests (`test_dev_gets_behaviour_per_ac_and_no_blackbox_handin`, `test_m_without_qa_blackbox_has_no_ba_in_rev_21`) are skipped with a reason: they assert REV-19/21 composition, which needs those files retargeted (ticket 07). (3) The `squad-team` pointer in SIZE-13/TEAM-7 waits for ticket 10: `test_instructions` fails on a command that does not exist yet.

## QA whitebox

### QA whitebox 05 — PASS on 9ffa44f (code 6d33099)
Checked in worktree plugin-dev-dsz-5 (read-only).
- Tests (cd tests; unittest): test_sizes 34, test_manager_m_l 9, test_qab_optional 11 (2 skipped, ticket 07), test_architect_handoff, test_pod_rules_process, test_instructions, test_team_duties, test_squadcompose, test_squadadopt, test_process_history, test_processlint, test_team_lead_role, test_squadprocess, test_squadupgrade, test_windows_safe, test_crlf_squad_files: all OK.
- Lint: exit 0, empty (= base). G4: `\bsize\b(?!-\d)` in sizes.md/teams.md: none. G5: 10 tombstones with why:/replaced_by:, changelog v9 per ID with reasons; kept IDs justified by live citations (D2).
- Live compose (REV-5b-style, real engine) for teams full / qa-white / none / qa-black / team-lead+tech-lead: rule sets per role match the duties line (e.g. qa-white only: TEAM-1, TEAM-4, SIZE-5a/6a/6c; none: TEAM-3, SIZE-7a/8a; full: SIZE-2, 5b, 6b absent from Manager). No rule acts for an absent role (TEAM-1..3 broadcast, accepted).
- R9: 5 `qa-b` `when:` lines in sizes.md retargeted; 18 remain in review/evidence/lifecycle/spawning, owned by 07/08 (their tickets carry R9). Not a finding here.
- Fixture edits outside file list (test_squadadopt, test_architect_handoff, test_pod_rules_process): forced by retargets, TL accepted.
Forward notes: 07 re-enable 2 skipped test_qab_optional tests; 10 owns the `squad-team` pointer (SIZE-13/TEAM-7); SIZE-18 now `plan-owner = team-lead` (was size L).

## QA blackbox

### QA blackbox, task 05 (code sha 6d33099, handin 9ffa44f, branch squad/plugin/drop-scope-size/plugin-dev-dsz-5)

Scratch homes with a hand-made `scope.md` per shape; `squad-process compose <role> --home D --plugin-root <worktree> --out F` for manager, dev, team-lead, qa-whitebox, qa-blackbox, ba, tech-lead. Looked at the SIZE-/TEAM- rule blocks (this ticket's files). CLI only, no screenshots. Verdict waits for the Tech Lead's final sha (REV-3).

| AC / check | What I did | What I saw | Result |
|---|---|---|---|
| All shapes compose | S, M, L, L no qa-black, M+designer, M+architect, qa-white alone, qa-black alone, tech-lead+qa-black, undecided; 7 roles each | exit 0 everywhere | PASS |
| Word "size" in SIZE-/TEAM- prose (AC 29, 04a) | `grep -iw size` on those blocks, all roles | only rule IDs (`SIZE-n`); no prose use, no `[if ... size` in these blocks | PASS |
| `qa-b` in sizes.md / teams.md | grep | 0 hits | PASS |
| Proposal rule, a row per role (AC 1) | SIZE-1 in Manager text | table: BA, Tech Lead, Team Lead, QA whitebox, QA blackbox, Designer, Architect, each with propose-when and silent default; unsure -> add; task count loses; nothing spawned before PO confirms; one table per goal scope; risk flags; PO may override, logged | PASS |
| Signals for AC 2-5 | read SIZE-1 | screen/flows -> Designer; data model, new dependency -> Architect; QA blackbox "no observable change"; QA whitebox out only for the five conditions; risk flags -> Tech Lead + QA whitebox | PASS (live Manager run still owed, step L) |
| Done per shape (AC 13, 14) | Manager text per team | both QAs: SIZE-2 "QA whitebox PASS and QA blackbox PASS ... One PASS is never enough"; qa-white only: TEAM-1; qa-black only: TEAM-2 (PASS + `## Review` confirmed); none: TEAM-3 (Developer's checks, `evidence.md`, `## Review`, Manager confirms); no shape gets another shape's text | PASS |
| Behaviour check without qa-black (AC 13) | qa-whitebox text, qa-white only | TEAM-4: checks Developer's `## Behaviour` against business AC | PASS |
| BA alone, Tech Lead without qa-white | TEAM-5, TEAM-6 | TEAM-5: QA whitebox checks `## Behaviour` against the BA's AC; TEAM-6: Tech Lead confirms the Developer's `## Review` | PASS |
| `duties:` line, shapes of AC 9 | Manager header | S: manager/dev/dev/ticket/manager/manager/manager; M: qa-white, qa-black checks, hand-in qas; L: team-lead, tech-lead, ba; L no qa-black: behaviour qa-white, ui manager; M+designer: ui qa-black; M+architect: choice architect; matches today's SIZE-22/22a | PASS |
| SIZE-22 chains | read table | each chain ends at Manager, Developer or ticket; Architect folded in; PO decides irreversible choices | PASS |
| Team change: SIZE-13, 14, 16, TEAM-7 | read | late signal -> role; Designer/Architect wait for PO's yes; Handover; respawn; log; remove only at iteration boundary with PO's OK; passed tasks stay passed | PASS |
| Tombstones (G5) | `_removed.md` | removed SIZE IDs carry `why:` and `replaced_by:` | PASS |
| `squad-process lint` | run on the branch | exit 0, no output | PASS |

Notes (not 05 failures):
1. `squad-process who SIZE-22` / `who TEAM-3` still print S/M/L preset rows; `who` rewrite is a later ticket (AC 29 `who` check).
2. Composed text from rules of tickets 06-08 still has `[if size ...]`, `qa-b`, and "size" prose; Dev rules still carry both Manager and QA whitebox HANDIN lines for every team and compose to 7.5-9.4 KB (AC 24 limit 5120): tickets 06-08, 11. Dev said the 2 `test_qab_optional` tests wait for 07.
3. SIZE-18 "when the scope is large" reads like a size notion. Optional reword.
4. AC 1-6 still need the live Manager run (step L).

## Tech Lead review

### TL review 05 (code 6d33099, evidence 9ffa44f, base 6ec3a75)
- lint empty; test_sizes, manager_m_l, qab_optional (2 skipped, re-enable in 07), squadadopt, architect_handoff, pod_rules_process, instructions, squadcompose, squadrules, windows_safe, crlf OK. evidence check --base 6d33099 exit 0 (9ffa44f evidence-only).
- teams.md TEAM-1..7, sizes.md retargeted, _removed.md 41 lines with why/replaced_by, changelog v9 rows. No `qa-b` left in sizes/teams. SIZE-21a kept (history snapshot cites it).
- Final sha named: code 6d33099 / evidence 9ffa44f.
### 03 (13ed665): QAW FAIL F1 (team --home missing dir exits 0 - my miss), F2 AC 21 -> moves to ticket 12 (design 10). Dev fixes F1; new final sha pending.
