---
name: squad-report
description: Build the time and cost report of a scope or goal (data.json + report.html) and show where it is. Use when the PO asks for the squad report, or runs /squad:squad-report <scope|goal|file list>.
disable-model-invocation: true
---

# Squad report

Runs the CLI `${CLAUDE_PLUGIN_ROOT}/bin/squad-report`; it does the work, you relay it.

## Steps

1. **Pick the run** from what the PO gave:
   - a scope or goal name: `squad-report <name>`
   - several `data.json` files: `squad-report rollup <file>...`
   - nothing: `squad-report` (current scope or goal)
2. **Relay** the first output line (the path of `report.html`, else `data.json`) and the 5-line summary as printed.
3. A refusal (exit 2) or error: say the one line it printed and stop. Do not work around it.

## Rules

- Writes nothing else; the CLI writes only the `report/` folder (or the rollup folder).
- To answer a question about the numbers, use `squad-report-analyze`, not this skill.
