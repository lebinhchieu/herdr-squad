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
- `squad-report <scope>` with all transcripts gone: refuse, exit 2, existing `data.json` kept (a rebuild must not overwrite a good file with an empty report); some missing: builds partial (`no_transcript:<agent>`).
- `redacted` in the rollup = some return has a null reason; `data.json` has no redact marker (schema v1).
- `squad-close` passes `--squad <folder>` to `squad-report` (squad-close resolves the squad by git toplevel; squad-report only by `--squad`/`$SQUAD_DIR`).
- A digest item's quotes (return reasons) live inside `text`; digest item fields are fixed.
- Browser check of `report.html`: `playwright-cli` blocks `file:`; serve the folder with `python3 -m http.server` on 127.0.0.1.

**Alternative rejected:** counting a gap as working when <= 5 min; a new activity hook (ADR 0009 removed the stream); CSV; TOML config (no `tomllib` on the Python floor).
