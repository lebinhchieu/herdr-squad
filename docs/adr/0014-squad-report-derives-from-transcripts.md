# Squad report derives from transcripts, zero LLM tokens

Status: accepted (squad-report)

**Decision:** time, tokens and cost per scope, task and role are derived after the fact from `~/.claude/projects` transcripts + `messages.jsonl` + `inbox.jsonl` + roster; no new hook; generation calls no model.

**Why:** a gap between two transcript records is classified by the record that **ends** it (peer / human / plugin message, task notification, model or tool record), never by a fixed "<= 5 min is working" rule (measured: most 30 s-5 min gaps end in a peer message). ADR 0009 removed the activity stream, so a new activity hook is not added; the transcripts already hold every record.

**Consequences:**
- `data.json` (schema_version, additive-only within a version) is the only structured output; `report.html` is a view that inlines css/js/data from plugin-shipped sources; no agent reads the generated file.
- Cost is an estimate at list price from a config price table; the harness's own `cost-state` is a cross-check, not a source.
- A report failure never blocks `squad-close`. Reports are local (`.claude/squads` is git-ignored) and disposable.
- Task id of a message = the first token after its type; the hook's `task` field is not used.
- Report output: ids, names, numbers, titles cut at 120 chars; never message or transcript text; HTML built with `textContent`, data escaped inside the JSON script tag.
- `bin/squadtranscript.py` is the one place that reads transcripts; `squad-usage` and `squad-report` import it.
- `squad-report <scope>` with all transcripts gone and the scope has messages: refuse (exit 2, "no transcripts left for <scope>"), existing `data.json` kept (a rebuild must not overwrite a good file with an empty report); no messages at all: empty report; some transcripts missing: builds partial (`no_transcript:<agent>`).
- `redacted` in the rollup = some return has a null reason; `data.json` has no redact marker (schema v1).
- `squad-close` passes `--squad <folder>` to `squad-report` (squad-close resolves the squad by git toplevel; squad-report only by `--squad`/`$SQUAD_DIR`).
- A digest item's quotes (return reasons) live inside `text`; digest item fields are fixed.
- Browser check of `report.html`: `playwright-cli` blocks `file:`; serve the folder with `python3 -m http.server` on 127.0.0.1.

**Alternative rejected:** counting a gap as working when <= 5 min; a new activity hook (ADR 0009 removed the stream); CSV; TOML config (no `tomllib` on the Python floor).

## Addendum (report-ui-fix)

- `data.json` v1 gains additive `scope.goal` and `scope.rollup_href` (relative path to the goal's rollup report.html, null when no goal or the file is missing). schema_version stays 1.
- Roster rows with the same agent name are folded into one agent; a row with a session wins over an empty one.
- The scope banner "partial" shows only when `scope.status == "running"`; other `partial_reasons` have their own banners.
- Layout and DOM of report.html are tested with headless Chrome `--dump-dom` (skipped without Chrome) plus CSS-string asserts; pixel comparison is QA screenshots against the mock, not in the suite.
- `scope.goal` is validated (no `/`, `\`, `..`, leading `.`); `rollup_href` shown only when the rollup report exists at build time; stale until the scope is rebuilt.
