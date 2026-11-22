# 04 Promotion: evidence

Note: ADR 0032 amends ADR 0010 and the "Developers only" sentence of ADR 0030; neither is edited. Not merged yet.
sha: 5dcef6d
## Review

AC trace (details in `## Checks`):
- AC1 | `ls docs/adr | grep -c 0032` | prints 1 (base 0)
- AC2 | `grep -n "spawns and retires only Developers\|spawns and retires the Developers\|spawns Developers," CONTEXT.md` | no hit (base 3); Pod entry checked, left alone
- AC3 | `git diff --stat <03 evidence sha>..HEAD` | only ADR 0032, CONTEXT.md, this folder
- AC4 | `grep -n "squad-respawn" docs/adr/0032-team-lead-spawns-the-pod.md` | 1 hit; Consequences name name-vs-row check and pin 0.10.4
- AC5 | `cd tests; python3 -m unittest test_old_language_inventory` | 2 tests OK; `grep -rl "CONTEXT.md\|docs/adr" tests/` hits only tests/fixtures/board/t28/04.md (a fixture, not a test)
- AC6 | read ADR Known-limit lines | the two limits of promote.md, verbatim

## Behaviour

ADR text is promote.md section 1 verbatim; the three CONTEXT.md entries (Manager, Team Lead, Coordinator) carry section 2 wording. SQ-10 needs no run (no bin/, printed text or role text edited).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | count 1 | read and run at 5dcef6d: pass | read at 5dcef6d: pass |
| AC2 | no hit | read and run at 5dcef6d: pass | read at 5dcef6d: pass |
| AC3 | diff stat lists 3 paths | read and run at 5dcef6d: pass | read at 5dcef6d: pass |
| AC4 | grep 1 hit | read and run at 5dcef6d: pass | read at 5dcef6d: pass (text part) |
| AC5 | inventory 2 OK | read and run at 5dcef6d: pass | read at 5dcef6d: pass (text part) |
| AC6 | verbatim | read and run at 5dcef6d: pass | read at 5dcef6d: pass |

## QA whitebox

### QA whitebox, ticket 04 (promotion), sha 5dcef6d: PASS

Run myself on a detached worktree of 5dcef6d.
- AC1: `docs/adr/0032-team-lead-spawns-the-pod.md` exists (count 1, base 0).
- AC2: the three old phrases have no hit in CONTEXT.md; Manager, Team Lead and Coordinator lines equal promote.md section 2; Pod entry (line 83) says only "group of agents that delivers one scope", left alone.
- PROMO-8: ADR text is identical to the fenced block of promote.md section 1 (`diff` empty). Nothing the scope did not decide.
- AC3: `git diff --name-only 5dcef6d~1 5dcef6d` = evidence.md, CONTEXT.md, ADR 0032. 0010 and 0030 untouched.
- AC4: `grep -c squad-respawn` on the ADR = 1. Read against the merged code: spawn guard (never manager/token-coach/other team-lead), D2 name-vs-row block (squad-spawn ~150-160), retire role-from-row refusal, respawn refusal (~57-63), team-lead.json per-role squad-spawn allows, pin 0.10.4 matches plugin.json. The --goal / flat-squad refusal for a Team Lead is not in the ADR but is not contradicted.
- AC5: `python3 -m unittest test_old_language_inventory` = 2 OK.
- AC6: Known-limit lines = the two of promote.md, verbatim.

Follow-ups (not FAIL): ADR does not mention the Team Lead's --goal / flat-squad refusal (added in ticket 01 fix); optional one line.

## QA blackbox

### 04 QA blackbox (sha 5dcef6d)
Method: `live` = read the committed docs with `git show` / `git grep` and compare against `promote.md`. No code read.

| AC | what I did | what I saw | result |
|---|---|---|---|
| AC1 | `git ls-tree` count of 0032 in docs/adr; `diff` of the ADR with the fenced block of promote.md section 1 | count 1; the file is identical to promote section 1 (Status, `Amends 0010 and 0030` line, Decision, Why, Consequences, Alternatives rejected) | pass |
| AC2 | `git grep` the three old phrases in CONTEXT.md; read the three entries against section 2 | no hit; Manager (l.12), Team Lead/Coordinator (l.20) and Team Lead role (l.24) carry the section 2 wording; Manager and Coordinator entries cite ADR 0032. Pod entry (l.83, "The group of agents that delivers one scope") says nothing about Developers only, left alone | pass |
| AC3 | `git diff --stat` on docs/adr/0010* and 0030* between 6cd2a70 and 5dcef6d; changed files of the ticket | ADR 0010 and 0030 untouched; ticket changes docs/adr/0032, CONTEXT.md and evidence files only | pass |
| AC4 | grep ADR | `squad-respawn` present; Consequences name the name-vs-row check and the pin must be 0.10.4 or later with `/squad:squad-process-update` and the respawn. Contradiction with the three scripts: QA whitebox reads them | pass (text) |
| AC6 | read Known-limit lines | the two limits of promote.md (second copy of a role, Architect before the plan), nothing added | pass |
| AC5 | test runs | QA whitebox / Tech Lead | n/a |

Follow-up (not blocking): 01 later added a Team Lead refusal with `--goal` or in a flat squad (0c65d44); the ADR's Enforcement bullet does not mention it. Text is not wrong, only incomplete.
