# Review findings: squad process rules (Fable advisor, call 1, approved at E4)

Reviewed: `templates/squad/process/*.md` on main (last change 3bfb74a, ITER-17) plus the 12 overlay rules `SQ-1..SQ-8` in `process.local.md`.
The Manager's attached rules come from the pinned runtime 9dab683 (0.7.5), which is older than main (main has LC-27, ITER-17, `--task`). Wording below is from main; I grepped each rule ID.
`squad-process lint`: clean (no output).
Route: **T** = template wording (a Developer ticket edits `templates/squad/process/`), **P** = tool/plugin (`bin/`, hooks), **R** = role card (`agents/`, needs Chieu's approval), **O** = overlay (`process.local.md`).

| # | Finding | Route | Size |
|---|---|---|---|
| 1 | Half-finished rename "done" -> "passed" | T | S |
| 2 | PASS with no QA: EVID-3a vs REV-1 / TEAM-3 / LC-27 | T | S |
| 3 | QA blackbox: REV-9 vs SIZE-8b / SIZE-17d / START-13 | T | S |
| 4 | Who decides an irreversible choice | T | S |
| 5 | Cost thresholds patch a hook that does not fire | P + T + O | M |
| 6 | Rules attached to nobody (REV-5a, EVID-5) | T | S |
| 7 | Gaps from the wrong `when:` key | T | S |
| 8 | Developer reuse vs "one session per task" | T | S |
| 9 | Dead clause "never suggest it to the PO" | T | S |
| 10 | Wrong or dangling citations | T | S |
| 11 | Overlay rules name absent roles; all `upstream: proposed` | O -> T | M |
| 12 | Smaller items | T/R | S |

## 1. "done" vs "passed" (T)
LC-27: "only `merged` is done, `passed` is not." Still using "done" for passed: LC-1 (title and text), SIZE-16, SIZE-17c, START-1 ("Done means"), START-19 ("dependencies are done"), TEAM-7 ("new Done"), SPAWN-8a/8b ("after its task is done"), GOAL-3b/3c, COST-8 ("every DONE"), LC-18 (project "done" tests is fine).
Effect: SPAWN-8a read literally retires a Developer only after the merge.
Fix: replace by "passed" where it means checked; keep "done" only for merged.

## 2. PASS with no QA (T)
EVID-3a: "your `PASS` is the verdict" (Manager, no QA). REV-1, TEAM-3 and LC-27: the Manager sends no `PASS`, only `FAIL`; passed = evidence check exits 0.
Fix: reword EVID-3a to "your confirmation (no `PASS`) is the verdict".

## 3. QA blackbox independence (T)
REV-9: check each AC first from the Developer's committed shots. SIZE-8b, SIZE-17d, START-13: check on the running app; the Developer's `## Behaviour` does not count as your check.
Fix: pick one. Suggest: shots are a starting point; blackbox runs the app for every AC the shot does not clearly prove, and never signs off from shots alone.

## 4. Irreversible choice (T)
SIZE-22: "the PO decides every time". WHO-2d: "Manager, after an advisor call", PO-listed items stay with the PO. SIZE-22 also cites WHO-2e, which attaches only with an Architect.
Fix: one rule: Architect/Tech Lead/Manager recommend, Chieu decides; cite the row that is always attached.

## 5. Cost thresholds patch a hook (P + T + O)
Three overlay `why:` lines say "no `fresh` event fired". SQ-3 (100k), SQ-3b (150k), SQ-3c (150k), COST-3 (+50k, max 180k), COST-8, COST-9, ITER-12 give five different triggers. COST-5/5a tell the Developer to act on `fresh`, but COST-3 is not attached to the Developer.
Fix: (P) find why `squad-usage --check` misses `fresh` and fix the tool; (T) then one threshold rule per role.

## 6. Rules attached to nobody (T)
REV-5a and EVID-5 have an empty `roles:` line. REV-22, LC-19 and LC-19b send the Developer to them.
Fix: give them `roles: dev` (REV-5a) and `roles: dev` (EVID-5), or inline the text.

## 7. Wrong `when:` key (T)
- ITER-3b needs `qa-black = yes`: a whitebox-only team has no summary writer, yet MRG-1 reads the summary.
- EVID-2b/2d/2e key on `tech-ac`: with `tech-ac = dev` no rule says who assembles evidence.
- REV-14a: a commit after PASS goes back to the checkers; no exception for the evidence-only commit (MRG-2 allows it).

## 8. Developer reuse (T)
START-5 "one session per task" and START-2a "one Developer per ready task" conflict with COST-6a, LC-6b and the reuse paragraph of SPAWN-5a.
Fix: START-5: "one session per task, or per queued run of tasks in one area".

## 9. Dead clause (T)
SPAWN-4/4a "never suggest it to the PO" attaches only when the role is already on the team; SIZE-1 says to propose every optional role.
Fix: delete the clause.

## 10. Citations (T)
- ITER-2, ITER-17, CORE-3 cite WHO-2 (absent without a Tech Lead) and WHO-1b (PO cell is "n/a"); they miss WHO-5, WHO-3a, WHO-1d.
- GOAL-6b cites the promotion rows (WHO-2b/2c/2f) for the suite owner.
- SUITE-1b and SUITE-2d cite SUITE-1 (Tech Lead only); SIZE-24b cites PROMO-2 (Tech Lead only).

## 11. Overlay (O -> T)
SQ-1, SQ-6 name the Tech Lead; SQ-3c, SQ-8 name the Team Lead; this team has neither. All 12 are `upstream: proposed`. This scope can fold the good ones into the templates and drop the overlay.

## 12. Smaller (T / R)
- MSG-8a waits 10 min before a ping; SPAWN-10a says "Idle with work assigned -> send STATUS?" with no wait.
- Suite rules (SUITE-1/1b vs SUITE-3/3b) read both "full run needed to reach the PO" and "full run only on Chieu's yes". State: default is targeted; a full run needs Chieu's yes.
- "Chieu" is hard-coded in generic templates (SUITE-1, 1b, 2d, GOAL-6b). Use "the PO" in the template.
- MSG-9 example `DECISION SET-13, SET-14` breaks MSG-3 (task id = `NN` alone).
- The rule index attached to every session is about 200 lines; CORE-6 already gives a lookup. Shorten it.

## Not checked
The tools (`bin/`), hooks and role cards (`agents/`) were not read. Findings 5 and 12 may change after reading them.
