# squad-report: decisions from the PO grill (rounds 1 and 2, 2026-10-19)

Visual rounds: `round1.html`, `round2.html` in this folder. Palette: Mango Parrot light (`/home/chieule/workspace/theme-vscode/themes/mango-parrot-color-theme.json`, light variant only).

## Settled
- **Time source:** derived after the fact from transcripts (`~/.claude/projects/**/<session>.jsonl`, found via `roster.md` session ids, as `bin/squad-usage` does) plus `messages.jsonl`. No new hooks. ADR 0009 removed the board, so no status stream exists.
- **Buckets:** working (turn gap <= 5 min while model/tool runs), waiting (inside a long tool call: background shell, Monitor, test-runner command such as `run_suite.py`), blocking (idle between a BLOCKED/ASK sent and its reply), idle (any other gap). 5 min and test-command patterns live in one small config file. Labelled "derived".
- **Cost:** estimated dollars at list price, reusing `bin/squad-usage` parsing and price table; tokens split input / cache read / cache write / output. Label "estimated, list price".
- **Data:** `<scope home>/report/data.json` is the only structured data (schema-versioned; no CSV). It also holds a small `digest` (ranked outliers).
- **HTML:** a view of `data.json`. Plugin ships small separate sources (`collect.py`, `template.html`, `report.css`, `report.js`); render inlines css, js and data into one self-contained `report.html`. No agent reads the generated file. Reason: AI tokens are spent only on files agents read or edit.
- **Generation uses zero LLM tokens:** one command (`squad-report <scope|goal|--all>`) prints the output path and a 5-line summary.
- **Coverage:** per-scope squads only (`scopes/<s>`, `scopes/_done/<s>`, goals = their scopes). Legacy flat squads unsupported. A running scope is flagged "partial".
- **Rollups:** a goal or any list of scopes is built from the scopes' `data.json`, never from raw transcripts again.
- **Task attribution:** layers, first match wins: Developer by roster `Owns` ("task NN") and worktree branch; other roles by the window from a task's first mention to its PASS; the rest is "scope overhead". The report shows % attributed. Only 58 of 429 win-compat messages carry a `task` field. No `process.md` change.
- **Returns:** a FAIL message = one return. Rework = FAIL to the task's next HANDIN (time and cost). Flag a task at 3 returns.
- **Views:** scope report: KPIs (total time, tokens by kind, est. cost, returns, % attributed), task table (time by bucket, tokens, cost, returns), role table (scope-wide), task x role drill-down, per-agent timeline coloured by bucket. Goal / multi-scope rollup: scopes table, totals, role totals, cost and time share per scope. In-page sort and filter, no server.
- **Second skill, analyze** (e.g. `squad-report-analyze`): reads only the `digest`, drills into the data by a query command only when a finding needs it, runs collect first if data is missing or older than the last message. Output in chat (findings + proposals); writes nothing; never edits `process.md`. Token Coach untouched.
- **Triggers:** on demand (`/squad:squad-report`) and hooked into `squad-close`: `--scope` runs collect + render FIRST (before retiring agents and moving the folder), `--goal` builds the rollup from its scopes' `data.json`; a report failure only warns, never blocks the close; `--dry-run` skips it.

## Open for the pod (BA + Designer first)
- `data.json` schema shape, skill and script names, file layout, test approach, v1 size.
- Report visual design (screens, states, flows) within the palette above.
- Whether the digest signals and views above are the right ones for the PO's questions: where did the time and money go, which tasks and roles, how much was blocked or waited, how many returns.

# Round 3 answers (PO, 2026-10-18)
Q14-Q18, Q20, Q21, Q24: yes (as proposed in `round3.html`). Changed or added:
- **Q19:** no `--all` backfill. Need: build the report on demand for a chosen existing scope (live or `_done`).
- **Q22:** wants a list of report files (`data.json`) that teammates send, and a rollup over them.
- **Q23:** "could change process to include naming tasks/tickets or anything else to support the report"; wants it if cheap in effort and tokens. Tech Lead priced it (one `process.md` line + roster template sentence, about 40 tokens per role per session): recommendation yes, PO approval as a role-instruction change.
- **Q25:** teammates have their own squads; the PO asks them for `data.json` and does the rollup. So `data.json` must be self-contained and shareable (`--redact` for titles and return reasons).
- **New question:** "Do we have data to show what was failed (returned reason)?" Yes: FAIL message text (`returns_list[].reason`, 200 chars), who returned it, and the long findings in `evidence/<task>/qa-*.md` (named, not read). Spec AC4.3-4.6.
