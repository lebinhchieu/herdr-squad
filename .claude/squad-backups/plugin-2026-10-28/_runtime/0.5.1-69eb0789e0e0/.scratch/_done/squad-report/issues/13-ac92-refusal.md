Status: ready-for-agent
Type: task
Task ID: 13
Touches: `bin/squadreport_build.py` (build(), the Refused line ~86), `tests/test_squad_report_cli.py` (or the build test file that holds the refusal test), `docs/adr/0014-squad-report-derives-from-transcripts.md` (the one Consequences line below)
Does not touch: schema, other modules
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_report_cli`
Blocked by: none (on top of the integration branch `squad/plugin/squad-report/plugin-dev-sr-12` @ e8d5ce4)

# 13: AC9.2 as the BA narrowed it (refuse only when messages exist)

**Done when `build()` refuses only a scope that has messages but no transcripts.** BA rule (spec.md:98): some transcripts gone = partial (AC7.2); all gone **and the scope has messages** = refuse, one line `no transcripts left for <scope>`, exit 2, write nothing, keep existing `data.json` and `report.html`; **no messages at all** = AC7.3 empty report, not a refusal.

## What
In `build()`: `if c.sources["transcripts"] == 0 and c.sources["messages"] > 0: raise Refused("no transcripts left for %s" % c.name)`. A scope with no messages and no transcripts builds the AC7.3 empty report (data.json + report.html written, the empty state of ticket 05).

ADR 0014 line to replace (and the same line in `$SCOPE_DIR/promote.md`, which I update): `- \`squad-report <scope>\` with all transcripts gone and the scope has messages: refuse (exit 2, "no transcripts left for <scope>"), existing \`data.json\` kept (a rebuild must not overwrite a good file with an empty report); no messages at all: empty report; some transcripts missing: builds partial (\`no_transcript:<agent>\`).`

## Technical AC
1. Test: messages present, no transcripts -> exit 2, stderr exactly one line `squad-report: no transcripts left for <scope>` (prefix as the other refusals), existing `data.json` and `report.html` bytes unchanged.
2. Test: no messages, no transcripts -> exit 0, `data.json` written with `partial: true`, `report.html` renders the empty state; two runs on equal input equal bytes except `generated_at`.
3. Some transcripts present -> unchanged (partial, `no_transcript:<agent>`).
4. Primary behaviour only (qa: light). One commit, final sha named by the Developer in the HANDIN.
