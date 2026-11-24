# Evidence: 08 GOAL-6e names a role the team may not have
sha: (see HANDIN)
## Behaviour
- GOAL-6e (`goal.md`): "(the Tech Lead's table)" -> "(the touched-files table in `tasks/`)". `grep -rn "Tech Lead's table" templates` is empty.
- SUITE-7 (`suites.md`) named "Tech Lead, else QA whitebox" and reached a QA whitebox on a team with no Tech Lead. It is now three rules, one per suite owner: SUITE-7 (`roles: tech-lead`, `when: suite-owner = tech-lead`), SUITE-7e (`qa-whitebox`, `suite-owner = qa-white`), SUITE-7f (`dev`, `suite-owner = dev`, a pointer to `squad-process rule SUITE-7`). SUITE-7b gained the lead-in "If you keep the base-failures file ([SUITE-7]), ". No body names a role. 7e's columns sentence is reworded: lint rejects a 12+ word sentence repeated across rules.
- `tests/test_dev_rules_size.py` LIMIT 6950 -> 7050: measured worst case 7002 B (team-lead+qa-black+designer+architect, goal yes, qa light), +48 B. Changelog v29 SUITE line lists 7e and 7f.
- Tests, `SQUAD_*` unset, from `tests/`: test_architect_handoff, test_rules_contract, test_rules_wording, test_squadcompose, test_sizes, test_dev_rules_size, test_promotion_0_6_0, test_squadrules, test_instructions: 185 OK. `squad-process lint` exit 0.
- AC4 (defect class): the grep over 01-06's added text hit GOAL-6e and SUITE-7 (fixed), `files.md:72` (FILE-6, `roles: manager`, left as the Tech Lead ruled) and EVID-2b (`when: tech-ac = tech-lead`, fine).
- Follow-ups from QAs (not FAILs): a non-owner QA whitebox or Developer gets SUITE-7b/7c citing [SUITE-7] without SUITE-7 (`squad-process rule SUITE-7` resolves it); a Developer owner gets 7f but not 7b; SUITE-7f has no column list.
- SQ-10 (rule text attached to roles), `SQUAD_*` unset: test_windows_safe, test_utf8_helpers, test_instructions: 44 OK.

## qa-w

### QA whitebox, ticket 08, sha ee9ef83 (base 4945bca, ancestor)

Verdict: PASS.

#### Checked
- Diff 4945bca..ee9ef83: `goal.md` (GOAL-6e: "the Tech Lead's table" -> "the touched-files table in `tasks/`"), `suites.md` (SUITE-7 first sentence), the ticket. `roles:`, `aware:`, `topic:` unchanged. AC5 lists goal.md only; suites.md is added by the Tech Lead's DECISION 08 in the ticket Comments.
- AC1: `test_architect_handoff` passes in full.
- AC2: `grep -rn "Tech Lead's table" templates` empty.
- AC3: test_rules_contract, test_rules_wording, test_squadcompose, test_sizes, test_dev_rules_size, test_promotion_0_6_0 pass; lint exit 0. 257 tests OK with SQUAD_* unset (plus test_squadrules, test_instructions, test_windows_safe, test_utf8_helpers, test_small_files_equivalence, test_qab_optional, test_processlint).
- AC4: `git diff c853707 HEAD -- templates | grep '^+' | grep "Tech Lead|QA whitebox|..."` I reran: two hits left, `evidence.md` EVID-2b (`roles: dev`, `when: tech-ac = tech-lead`, role guaranteed) and `files.md:72` FILE-6 (`roles: manager`). Matches the Developer's list. Neither reaches a team without the role.

#### Follow-up (not FAIL)
1. SUITE-7 now says "the `suite-owner` in your `duties:` line", but a composed QA whitebox file carries no `duties:` header (`bin/squadcompose.py:59` HEADER_TEAM_ROLES = manager, team-lead, tech-lead). QA whitebox, one of the two roles the rule reaches, cannot see that line; with a Tech Lead present it may think it keeps the file. Fix later: `when: suite-owner = tech-lead` / `= qa-white` split, or say "the Tech Lead's row in `roster.md`" free of titles.

### Return 1, sha 495e865 (base 4945bca)

Verdict: PASS. Supersedes my PASS on ee9ef83.
- SUITE-7 split by suite owner: SUITE-7 (`roles: tech-lead`, `when: suite-owner = tech-lead`), SUITE-7e (qa-whitebox, `= qa-white`), SUITE-7f (dev, `= dev`). Composed rules over 5 team shapes: a Tech Lead gets only SUITE-7; QA whitebox gets 7e only when there is no Tech Lead; the Developer gets 7f only when neither exists; QA whitebox with a Tech Lead gets no owner rule. The `duties:` pointer is gone (my follow-up closed). No role title in the three rule bodies.
- SUITE-7b lead-in "If you keep the base-failures file". Changelog line names 7e, 7f. GOAL-6e unchanged since ee9ef83.
- LIMIT 6950 -> 7050; measured max over all team sets 7002 B <= 7050; worst no-designer team 6507.
- Lint exit 0. 302 tests OK with SQUAD_* unset (the 9 files of the HANDIN plus test_windows_safe, test_utf8_helpers, test_small_files_equivalence, test_qab_optional, test_processlint, test_team_duties, test_squadsettings).

#### Follow-ups (not FAIL)
1. A Developer who owns the file gets SUITE-7f but not SUITE-7b (the base check before the first spawn reaches tech-lead and qa-whitebox only). Same gap as before the split.
2. Ticket 02 AC1 ("the rule names ... its owner chain"): the chain is now only in the FILE-6 row and the `when:` guards, as the Tech Lead ruled.

## qa-b

### QA blackbox 08, sha ee9ef83 (verdict held for the Manager's ruling)

Method: `squad-process rule`, `compose <role>` on a scratch squad dir (team with a Tech Lead), grep, `git diff --stat`, lint.

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 test_architect_handoff passes | - | QA whitebox's test | not mine | - |
| AC2 `grep -rn "Tech Lead's table" templates` empty | live | grep | 0 hits; GOAL-6e now says "(the touched-files table in `tasks/`)" | pass |
| AC3 lint | live | `squad-process lint` | exit 0 (other test files: QA whitebox) | pass |
| AC4 defect-class grep | shot | Developer's Comments list each hit with its `roles:`/`when:` | clear | pass (shot) |
| AC5 diff lists goal.md (and the TL-widened suites.md) and the ticket | live | `git diff 4945bca HEAD --stat` | goal.md, suites.md, the ticket only | pass |

Finding (ruling asked of the Manager, SQ-4): SUITE-7 now says "the `suite-owner` in your `duties:` line". Composed tech-lead rules carry that header line (`suite-owner=tech-lead`); composed qa-whitebox rules carry no `duties:` line and no `suite-owner`, yet qa-whitebox still gets SUITE-7 on a team with a Tech Lead. FILE-6's owner-chain row is `roles: manager`. So QA whitebox (and a Developer owner) cannot tell from its rules whether it owns `base-failures.md`. Also ticket 02 AC1 ("names its owner chain") no longer holds for SUITE-7; the Tech Lead's DECISION 08 changed it in 08's Comments.

#### Verdict: FAIL on ee9ef83 (Manager ruling, FINAL)
Ticket 02 AC1 is a written AC of a passed ticket; a Tech Lead decision in 08's Comments cannot rewrite it. Two findings, both break it:
1. QA whitebox (suite owner on a team with no Tech Lead) gets SUITE-7 but its composed rules have no `duties:` line, so it cannot read that it keeps `base-failures.md`.
2. A Developer who is the owner has no composed `duties:` line and gets no SUITE-7 at all.
Required: each role that can be the suite owner reads, in its own composed rules, that it keeps `base-failures.md`, and no rule names a role that is absent. The Tech Lead picks the form (e.g. SUITE-7 variants with `when: suite-owner = <role>`, like EVID-2b).

#### Re-check, sha 495e865: PASS
Method: `compose <role> --plugin-root <worktree>` on three scratch teams; lint.

| Team (owner) | qa-whitebox | tech-lead | dev | what I read |
|---|---|---|---|---|
| A: team-lead, tech-lead, qa-white, qa-black (tech-lead) | SUITE-7b, 7c (not owner) | SUITE-7 "You keep `$SQUAD_DIR/base-failures.md` ... columns ..." | SUITE-7c only | pass |
| B: team-lead, qa-white, qa-black (qa-white) | SUITE-7e "You keep `$SQUAD_DIR/base-failures.md` ... Each row holds ..." | - | SUITE-7c only | pass |
| C: team-lead, qa-black (dev) | SUITE-7b, 7c | - | SUITE-7f "You keep `$SQUAD_DIR/base-failures.md` as [SUITE-7] says; read it with `squad-process rule SUITE-7`" | pass |

- Lint exit 0. No role title in the bodies of SUITE-7, 7e, 7f. Both earlier findings are fixed: every possible owner reads in its own composed rules that it keeps the file.
- Follow-up (not FAIL): in teams A and C qa-whitebox (and in A and B dev) gets SUITE-7b and SUITE-7c, which cite [SUITE-7]/the file, while SUITE-7 itself is not in its composed rules; `squad-process rule SUITE-7` resolves it. SUITE-7f has no column list, only the pointer.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1-AC5 | 9 test files, `SQUAD_*` unset, 185 OK; `squad-process lint` 0; `grep -rn "Tech Lead's table" templates` empty; `squad-process who` SUITE-7/7e/7f: one role, one `suite-owner` each; AC4 grep quoted in ticket Comments | `cd tests; python3 -m unittest test_architect_handoff test_rules_contract test_rules_wording test_squadcompose test_sizes test_dev_rules_size test_promotion_0_6_0`; `grep -rn "Tech Lead's table" templates`; `git diff c853707 HEAD -- templates` grep for role titles; `git diff --stat 4945bca HEAD`; `python3 bin/squad-process lint` | composed tech-lead, qa-whitebox, dev on three teams (owner tech-lead, qa-white, dev): each gets SUITE-7, 7e, 7f; no role title in the bodies; lint 0 (qa-b.md, sha 495e865) |
