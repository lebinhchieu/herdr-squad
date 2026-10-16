# 02 Haiku study

Status: done
Blocked by: none (the share column needs 01's script: see Notes)
Owner: Developer 2 (spawned by the Manager)
Output: `.scratch/audit-token/haiku.md`, `.scratch/audit-token/fixtures/<candidate>/`, `.scratch/audit-token/scripts/ab.py`

Find where Haiku can do a role's work or a sub-step without losing quality, with a small A/B on fixture tasks. Read `spec.md` (Technical design) first. Measurement only: no change to `agents/*.md` or anything outside `.scratch/audit-token/`.

## Business AC
(copied from `scopes/audit-token/business-ac.md`; the BA owns them; bar RS-1..RS-3 as in ticket 01)

- **AT-02-B1** `haiku.md` lists the candidates (QA receipt checks, Token Coach, read-only fan-out subagents, board/log summaries, and any more found), each with its share of total spend from AT-01. A candidate with no AT-01 share is written "not measurable" and classed unproven: it cannot be a go (BA ruling after AT-01 PASS, business-ac.md v4). A candidate under 2% is minor before any test.
- **AT-02-B2** For each tested candidate: same input to Haiku and to the current model, at least 2 runs per arm, on a fixture task. Report tokens, cost-weighted cost and defects found by the QA AC. Spread shown. The fixture's pass/fail checks (the QA-AC list that counts defects) are written and saved BEFORE any arm runs.
- **AT-02-B3** Each candidate ends with one verdict: **go** (passes RS-1..RS-3), **go with guard** (allowed only when an automatic step-up to Sonnet on failure makes the FINAL output pass the same checks with zero QA-AC loss; the guard's cost is in the net saving; a Haiku result accepted with a known loss is no-go), **no-go** (fails RS-3 or RS-2). "Go with guard" needs the step-up actually run on at least one Haiku failure case, with its final output scored. A "go" never rests on one run.
- **AT-02-B4** What Haiku got wrong in each no-go, in one line.
- **AT-02-B5** Read-only (as AT-01-B5).
- **AT-02-B6** For each A/B the fixture, the prompt and both outputs are saved in the repo; the Haiku output is judged by the same checks as the current model's. Any go states its saving in the AT-01 unit. A verdict links to its AT-01 spend row. Each candidate's fixture has at least one good case and one bad case, so an always-FAIL or always-PASS model cannot score zero defects.

## Technical AC
(agreed with plugin-qaw-audit-token, 2026-10-16)

- **T1 Reproducible.** `scripts/ab.py` (or a documented shell file) runs every arm from the committed fixture and prompt, and scores each output with the committed checks, with no manual step. Exact commands, the resolved model id of each arm (read from `message.model` in the run's transcript, not assumed from the alias) and the run date are in `haiku.md`.
- **T2 Fixtures first.** Per candidate: `fixtures/<candidate>/{input/,prompt.md,checks.py}`. `checks.py` encodes the defects (planted or known) and has its own self-test: it fails on a deliberately wrong output and passes on a known-good one (both committed). Git history shows the `checks.py` commit before the first arm output commit; the report cites both shas.
- **T2b Good and bad cases.** Each fixture holds at least one input whose correct answer is "pass" and one whose correct answer is "fail" (for a receipt check: a matching-sha OK receipt, a sha mismatch, and a `clean=no` one). `checks.py`'s self-test also shows that an always-PASS and an always-FAIL answer each score defects.
- **T3 Same input.** Both arms get the byte-identical prompt and input directory (a copy, outside the repo, e.g. a fresh temp dir), run headless (`claude -p --model <alias>`), no squad hooks or settings loaded. n per arm is stated per candidate (minimum 2; n=1 is an anecdote and never a go). Spread is shown.
- **T4 Measured like AT-01.** Tokens and dollars per run are read from the run's transcript, deduped by `message.id`, with the same price table and the same code (import or copy from 01's script; say which). Subagent lines counted.
- **T5 Scoring.** Quality is scored only by `checks.py` (defects per run, pass/fail per check), not by reading the output and judging. A defect list per run is saved. A judge-LLM is not used.
- **T6 Guard case.** For "go with guard": the step-up runs on a real Haiku failure, its final output is scored with the same checks, and the guard's tokens are added to the arm's cost. If no Haiku failure occurs in the runs, the verdict is "go" only if n >= the stated minimum and zero defects; else "unproven".
- **T7 Can't run.** If an arm can't run (model access, budget), the report says so and the verdict is "no-go: unproven". No extrapolated numbers.
- **T8 Budget cap.** At most 12 headless runs in total (e.g. 3 candidates x 2 arms x 2 runs). More needs the Manager's OK first; the report states the total cost of the study itself. Candidates not tested are assessed on paper and marked "untested: not a go".
- **T9 Candidate choice.** Test the candidates with the best chance of passing RS-2, taken from AT-01's per-role shares when available. Deterministic-check candidates suit this study best (planted defects in a receipt, a usage table with a known top driver, a log with known facts, a repo question with a known answer).
- **T10 Safety.** Runs happen outside the repo and outside `.claude/squads`; fixtures hold no real transcript content or secrets (hand-made or from non-sensitive repo files). Run processes are stopped by PID. Nothing written outside `.scratch/audit-token/` except the temp run dirs, which are removed. `git diff --stat <base>..HEAD` shows only `.scratch/audit-token/`.
- **T12 One price table (BA ruling).** Costs use AT-01's table (passed at def08da: Sonnet 5.5 cache read $0.10, Haiku from the vendor page), by importing or byte-copying `PRICES` from `audit.py` and saying which. No separate "assumed" prices.
- **T13 Comparator and RS-2.** A verdict compares like with like: the production alternative to a Haiku sub-step is the running session doing the step in one extra turn (or a Sonnet subagent), not a cold-start Sonnet run. State the comparator, its marginal cost (take it from AT-01's per-message cost for that role), the Haiku call's cost, and the net saving over the baseline window = (occurrences in the baseline x net saving per occurrence) vs the 2% bar ($5.94 at def08da). Occurrences come from a count you can cite (a grep count of receipt checks or summaries in the logs), or the candidate is "not measurable". A role's share is a ceiling, never the saving.
- **T14 Report hygiene.** The results table has one cell per column (the current table is shifted: the Sonnet cost cells repeat Haiku's, and the ratio and defect columns hold the wrong values). Counts in the text match the data (6 fixtures, 24 runs; not "five"). An untested candidate is "untested: not a go" (T8), not "no-go". Remove the statement that AT-01's script is not available: it is in your branch.
- **T11 Done evidence.** Copy `fixtures/<candidate>/` (prompt, input, a plain-language list of what each check tests; the script itself may stay in the repo) into `evidence/AT-02/fixtures/`, so QA blackbox can recompute without the repo. Each `runs/*.json` has a run timestamp. `evidence/AT-02/dev-evidence.md`: the base sha, commands, the checks self-test output, the sha order from T2, per-run defect tables, total study cost, `git diff --stat`.

## Notes for the Developer
- **Order:** the final verdict table (AT-02-B1, B3) is filled only after AT-01 has a passed share table. "go (RS-2 pending)" is not a verdict: allowed values are go, go with guard, no-go (a candidate under 2% of total spend is marked minor). AT-02 does not close before AT-01.
- The share column (AT-02-B1) comes from AT-01's script. Until 01 has a passed branch, build fixtures and checks (T2) and leave shares `pending`. The Manager spawns you with `--base` on 01's passed commit if it is ready by then, or tells you to fill the column afterwards.
- Never `pkill` by name; stop only the PIDs you started.

## Comments

- 2026-10-16 Dev AT-04: merged into the integration branch; passed both QAs.
