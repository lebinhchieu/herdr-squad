Status: ready-for-agent
Type: task
Task ID: 16
Touches: `CONTEXT.md`, `docs/adr/0016-process-composed-per-role.md` (status), `docs/adr/0005-process-versioning.md` (status), `docs/adr/0006-process-writing-rule.md` (note), `README.md` (process section)
Blocked by: 15

# 16: Promotion

**Done when the glossary and ADRs describe the composed process and nothing in them describes the retired copy-and-merge.**

## What
- **CONTEXT.md:**
  - add **Rule**, **Rule ID**, **Overlay**, **Composed rules**, **Plugin pin**, **Tombstone**, each with `_Avoid_`;
  - redefine or retire **Process version** (the pin replaces it), **Section view** (retired), **Process update** (now per rule) and **Process changelog** (ID lists);
  - add relationships: a Scope runs on one Plugin pin; an Agent reads its Composed rules.
- **ADR status:** 0016 `accepted (composed-process)`; 0005 `superseded by 0016`; 0006 amended note kept.
- **README:** a process section of at most 15 lines.

## Technical AC
1. Every term above appears once in CONTEXT.md, and no other section uses a retired term in its old meaning (`grep` output in the evidence).
2. QA whitebox checks the edits match this ticket and add nothing the effort did not decide.
