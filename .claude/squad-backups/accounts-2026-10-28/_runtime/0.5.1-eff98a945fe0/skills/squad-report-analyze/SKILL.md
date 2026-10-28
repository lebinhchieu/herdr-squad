---
name: squad-report-analyze
description: Read a scope's report digest and answer in chat with findings, each citing its digest signal and proposing one change. Use when the PO asks what the squad report shows, where time or cost went, or what to change.
---

# Analyze a squad report

Answers in chat from `squad-report` data. Bin: `${CLAUDE_PLUGIN_ROOT}/bin/squad-report`.

## Steps

1. `squad-report status <scope>`. Exit 0 (fresh): go to 2. Otherwise (stale or missing): run `squad-report <scope> --quiet --no-html` first, then go to 2.
2. `squad-report query <scope> digest`. Read nothing else yet.
3. **Findings:** one per digest signal that matters. Cite its id, give the number, propose one change.
4. **Detail** for one finding: `squad-report query <scope> task --task X`, `role --role R`, `blocks`, `returns`, `matrix` or `iterations`. Only these slices; do not open `data.json`.

## Rules

- Chat only: no file, no change to the squad's files.
- A proposal about the process is a suggestion for the PO to decide.
