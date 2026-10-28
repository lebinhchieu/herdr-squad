# 01 Token audit

Status: done
Blocked by: none
Owner: Developer 1 (spawned by the Manager)
Output: `.scratch/audit-token/audit.md`, `.scratch/audit-token/scripts/audit.py` (+ fixture, see T2)

Measure where the squad's tokens really go: per role, per phase, per token type, per model, per scope, with the top 5 cost drivers and a proposed fix each. Read `spec.md` (Technical design) first. Measurement only: no change outside `.scratch/audit-token/`.

## Business AC
(copied from `scopes/audit-token/business-ac.md`; the BA owns them)

Bar for "real saving" RS-1..RS-3:

| # | Test | Passes when |
|---|---|---|
| RS-1 Measured | Numbers, not reasoning | Baseline and effect are computed from transcripts / `usage-events.jsonl` in cost-weighted units (price per model for input, cache read, cache write 5m/1h, output; the price table is printed). The report names the script, so a reader can re-run it. Baseline covers every closed scope and live run available, with its count, and shows spread (min / median / max), not one scope |
| RS-2 Share | Matters against total | Net saving >= 2% of total squad spend over the baseline window. "Net" = after the extra cost the change adds (hook turns, step-ups, retries, rework, extra respawns). Below 2% is "minor": listed, never recommended, unless it costs no code (a wording change in `process.md`) |
| RS-3 No quality loss | QA AC still pass | On the same fixture or replayed tasks, no QA AC that passed before fails after; first-pass QA PASS rate not lower; QA returns not higher. Rework tokens count in RS-2 |

- **AT-01-B1** `audit.md` states the baseline: number of sessions, scopes, the date range, and what is missing (a session with no transcript is named, not skipped silently).
- **AT-01-B2** Spend per role, per phase (plan / build / QA / retro) and per token type (input, cache read, cache write, output), each as cost-weighted units and share of total.
- **AT-01-B3** Top 5 cost drivers ranked by share of total. Each: the number, where it comes from (script + source rows), a proposed fix, and a class: **real** (passes RS-1..RS-3 on paper with the measured effect), **minor** (fails RS-2), **unproven** (says what to measure).
- **AT-01-B4** Each "real" fix names the files it would change and whether it is a role-instruction change (needs PO approval).
- **AT-01-B5** Read-only; the report holds numbers and file paths only, no transcript text.
- **AT-01-B6** Re-running the script on the same data gives the same totals.
- **AT-01-B7** Every claim cites evidence QA can open (path + row/line or query). No citation fails.

## Technical AC
(agreed with plugin-qaw-audit-token, 2026-10-16)

- **T1 Reproducible.** Every number cites its source (file glob, session ids or message ids) and the script that produced it. The script is committed, runs as `python3 -I .scratch/audit-token/scripts/audit.py --until <ISO> ...`, writes only to a path under `.scratch/audit-token/`, and a re-run gives the same numbers. `audit.md` states the `--until` cutoff and the exact command.
- **T2 No double count.** Usage is deduped by `message.id`; each token field is the max over the lines of an id. A committed fixture transcript (`scripts/fixtures/`, hand-made, no real content) with a message id on 3 lines and known totals is checked by `audit.py --selftest`; the report says the selftest passed, with its output saved in `evidence/AT-01/`. Also state the naive-sum inflation on one real session (a count, no text).
- **T3 Subagents.** Lines with `isSidechain` and `<session>/subagents/*.jsonl` are counted, tagged `subagent`, and attributed to the parent session's role. Reported as their own row (needed by AT-02's fan-out candidate). The report notes that `bin/squad-usage` skips them.
- **T4 Cost.** Per-type tokens (input, cache read, cache write 5m vs 1h, output) and dollars, per role, per phase, per model, per scope. The price table is printed with source and date (use the `claude-api` skill or the vendor pricing page; name which). A model with no price is listed under "unpriced", never given a guessed price. `thinking_tokens` is part of `output_tokens`: not added again. `speed` other than `standard` is flagged if present. Every "X%" names its denominator (total, or that role).
- **T5 Scope of data.** The report lists which squads, scopes and sessions are in and out, with the reason. In: `plugin` and `squad-board` squads, live and `_done`. Out: other projects' folders (E1). Paths resolved with `realpath`; the `~/.claude-2` symlink must not double count (the report gives the count of distinct session files). Nothing is written outside `.scratch/audit-token/`; `git diff --stat <base>..HEAD` shows only that path.
- **T6 Attribution.** Role and scope come from the transcript's `agent-name` record, cross-checked with roster rows and `usage-events.jsonl` session ids. Report the coverage: sessions attributed / total, and the "unattributed" and "non-squad" lines with their share of spend. A respawned role's earlier sessions are counted (the roster has only the latest: say how many sessions it would have missed).
- **T7 Drivers.** Each top-5 driver has the arithmetic of its estimated saving, the extra cost it adds (net, RS-2), the metric that moves after the build and where to read it. Existing work (`.scratch/token-coach/spec.md`: 120k/100k rules, model per role, Stop hook, Token Coach) is not re-proposed as new: the report says what it already covers and what its measured effect is (before/after, or "not measurable: why").
- **T8 Spread.** Per-scope totals show min / median / max across scopes, not one number (RS-1).
- **T9 Done evidence.** `evidence/AT-01/dev-evidence.md` has: the base sha (QA diffs `git diff --stat <base>..HEAD`), the command, the selftest output, `git diff --stat`, and the five numbers QA whitebox will spot-check, each with its raw lines' file and ids. No `tests/` change; `tests/run_suite.py --if-changed` is run once and its skip receipt saved.

## Notes for the Developer
- Start from `bin/squad-usage` (`read_session`, `find_transcript`) for the field names, but do not import it: copy what you need so the script is standalone.
- Validate the parsing on two real samples first, including an idle one (a Manager session with few turns) and a long one, before building the tables.
- Work from the worktree on your own branch; commit before any suite run.

## Comments

- 2026-10-16 Dev AT-04: merged into the integration branch; passed both QAs.
