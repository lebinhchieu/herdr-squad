# Evidence: 31 New sizes, slice 4: whole-template checks and changelog
sha: f0a965a

## QA whitebox

### 31 QA whitebox — PASS @f0a965a

Checked: clean worktree at f0a965a; diff 2f56772..f0a965a (sizes.md +1 `when: size = L` on SIZE-18, spawning.md SPAWN-4 "the plan", test_sizes.py +169, changelog).
Ran: `squad-process lint` ok; `test_sizes test_process_history test_squadupgrade test_squadruntime` 124 OK. Rule IDs changed (SIZE-18, SPAWN-4) grepped in tests: only test_sizes.

#### AC
- AC1/3/8/9/10: orphan test, absent-role-name tests, allow-list (SIZE-17a-e + START-8/11/13/14/15/16 only, each with reason, staleness test) OK. SPAWN-4 reworded, SIZE-18 fixed by `when`, no allow-list.
- AC2: mutation (SPAWN-5a roles -> tech-lead) → orphan test fails naming SPAWN-5a at S and M. Mutation (REV-15 names Tech Lead) → manager-text test fails. Both revert-clean (done in /tmp copy).
- AC4: OWNERS rows for plan/spawning, tech AC, business AC, code check, behaviour check, full suite, promote.md, hand-in; migration/irreversible choice by composed-text + acts tests. OK.
- AC5: risk-flag and business-doubt text tests OK.
- AC6: changelog test diffs IDs against 2e81e5e (skips if base absent in the clone — only a risk in a shallow clone).
- AC7: evidence lists scopes/goals and quotes decision 9. OK.

#### Follow-up (not blocking)
- Mixed `roles:` lists (present+absent, e.g. COST-2, FILE-1) are treated as join-on-move-up; AC1 is enforced by composed-text names of Tech Lead/Team Lead/the BA only. Manager prose at S still mentions "QA" as explanation (REV-15 "QA blackbox cannot read worktrees", ITER-1 "QA checks"): not an actor, not in AC3's list.

## QA blackbox

### QA blackbox, ticket 31 (sizes slice 4) @ f0a965a — PASS; ticket 17 FINAL PASS on f0a965a

Method: scratch squad /tmp/qab19 (S/M/L), Dev-31 worktree as plugin root; compose of manager/dev/qa-whitebox/qa-blackbox/designer at S, M, L; `who` over all 323 rule IDs; `rule` spot checks; code not read.

| AC | Did | Saw | Result |
|---|---|---|---|
| No pointer to an absent role at S, M | scan composed text of 5 roles | dev, QAs, designer: 0 hits (dev S 4716 B, M 4629 B). Manager: only tables (FILE-6/7, SIZE-22), START-5 lifetimes, move-up rules (SIZE-2/13/15) and PROMO-3b "no BA" | PASS |
| No orphan duty | `who` of every ID at S, M | orphans = only SIZE-17a-e and START-8/11/13/14/15/16 (role cards / move-up), exactly the allow-list; the rest act on a present role (mixed rules are joins on move-up) | PASS |
| SPAWN-4 / SIZE-18 | `rule`, `who` | SPAWN-4 "after the plan names the UI tasks"; SIZE-18 acts only at L | PASS |
| Owners per size | `rule SIZE-22` | all 12 duties have an owner at S, M, L | PASS |
| Changelog | read v7 entry | lists retargeted IDs (SIZE-22, REV-21b, SUITE-2d, MSG-11a, REV-22, SPAWN-4…), per-item why | PASS |
| CLAUDE.md:46 | read | suite owner S Developer, M QA whitebox, L Tech Lead | PASS |
| E1 | escalations.md | no open row; rules follow Manager rec (a) | PASS |

### Ticket 17 final (slices 17 @4a3cb36, 29 @626bdce, 30 @2f56772, 31 @f0a965a)
All business AC 17.1–17.4 met; 17.5 (old-size scopes keep pinned meanings): only sizes-and-models is open under old meanings (legacy squad, no pin; Dev's evidence in 31/evidence.md, deploy order quoted from tech-ac decision 9). Open non-blockers: LC-25/26 and universal rules compose for absent roles but name none in dev/QA text.
