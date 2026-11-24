# Evidence 02
sha: d4a022c
## Behaviour
- New rules in `templates/squad/process/suites.md`: SUITE-7, SUITE-7b (tech-lead, qa-whitebox; aware team-lead), SUITE-7c (dev, qa-whitebox, qa-blackbox), SUITE-7d (manager). `files.md` FILE-6 row `base-failures.md`, owner: the suite owner (Tech Lead, else QA whitebox, else Developer).
- SUITE-7 names `$SQUAD_DIR/base-failures.md`, its five columns and the owner chain (AC1). `grep -n '_done' suites.md`: empty; SUITE-7d runs no test (AC2).
- `python3 bin/squad-process lint`: exit 0.
- Ticket text fixed: "the PO's keep", AC5 (no Chieu in rule text), Duties line.
- Developer bytes: worst no-designer/no-architect team 5473 -> 5759 B (+286 of 400 B budget); LIMIT 5580 -> 5866.
- Tests (cd tests; python3 -m unittest): test_windows_safe, test_utf8_helpers, test_instructions, test_rules_contract, test_small_files_equivalence, test_sizes: OK. test_dev_rules_size: only `test_every_team_set_fits_the_limit` fails, for design teams (e.g. ('designer',) 5978 B): known failing on base (tl-design §5), no FAIL.

## QA blackbox

### QA blackbox 02, sha d4a022c

Method: `squad-process rule <ID> --plugin-root <worktree>`, `compose <role>` on a scratch squad dir (no overlay), `lint`.

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 rule names `$SQUAD_DIR/base-failures.md`, columns, owner chain | live | `rule SUITE-7`, `rule FILE-6` | SUITE-7: owner "Tech Lead, else QA whitebox"; columns test name, sha it fails on, one-line cause, first scope that saw it, fix ticket or the PO's keep; a Developer who is the owner reads the rule. FILE-6 row owner: "Tech Lead, else QA whitebox, else Developer" | pass |
| AC2 no rule asks the Manager to run tests or read `_done/` | live | read SUITE-7..7d; `grep _done suites.md` | no hit; SUITE-7d: "The Manager runs no test and reads no other scope's folder ([SAFE-6], [SAFE-7])" | pass |
| AC3 file listed in files.md with owner | live | `rule FILE-6` | row present, owner as above | pass |
| AC4 lint | live | `squad-process lint` | exit 0 | pass |
| AC5 no name in rule text (ticket-fixes §2) | live | grep Chieu in suites.md, files.md | none; "the PO's keep" | pass |
| Spec items 3-5 behaviour | live | composed roles | SUITE-7b (tech-lead, qa-whitebox; team-lead aware): run grep/test AC on base before first spawn, fix the ticket, add the failing test as a row. SUITE-7c (dev, qa-whitebox, qa-blackbox): look the name up; listed = not run again, no FAIL; unlisted = run on base once, send to owner. SUITE-7d (manager): tells the PO of old rows at check-in | pass |
| `upgrade --check` on plugin squad | live | run | 18 unaffected, nothing needs a decision | info |

Follow-up (not FAIL): none. Byte budget and tests: QA whitebox.

## QA whitebox

### QA whitebox, ticket 02, sha d4a022c

Verdict: PASS.

#### Checked
- AC4: `python3 bin/squad-process lint` exit 0.
- AC1: SUITE-7 (suites.md) names `$SQUAD_DIR/base-failures.md`, the five columns (test, sha, cause, first scope, fix ticket or keep), append only, owner Tech Lead else QA whitebox, Developer reads `squad-process rule SUITE-7`.
- AC2: `grep -n _done suites.md` empty; SUITE-7d (manager) runs no test, reads no other scope's folder.
- AC3: files.md row `base-failures.md` (in `$SQUAD_DIR`), owner = the suite owner chain.
- Targeting (T-table, composed rules, sweep of 5 team shapes): SUITE-7 tl + qa-w; SUITE-7b tl + qa-w (team-lead aware); SUITE-7c dev + qa-w + qa-b only; SUITE-7d manager only; ba none.
- T8: worst no-designer/architect Developer team 5759 B (<= LIMIT 5866, +286 of 400 budget). All 224 over-limit sweep rows are design/architect teams (base failure, tl-design §5, no FAIL).
- Pass: test_windows_safe, test_utf8_helpers, test_instructions, test_rules_contract, test_small_files_equivalence, test_sizes. test_dev_rules_size: only test_every_team_set_fits_the_limit, design teams (known on base). test_templates (grep hit of files.md): 1 failure on `Write(//tmp/**)` settings list; same on base cbd1ea2, environment, untouched by the diff.

#### Follow-ups (not FAIL)
1. SUITE-7 and SUITE-7b reach QA whitebox even when a Tech Lead is on the team, so both get the owner duty; the "else QA whitebox" step lives in text only. A `when:` on the team could narrow it.
2. Ticket `## Comments` is empty; no AC asks for it here.
