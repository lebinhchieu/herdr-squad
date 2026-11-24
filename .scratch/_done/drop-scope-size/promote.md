# Promote: drop-scope-size (plugin 0.6.0)

Source: `tasks/spec.md`, `tasks/adr-0018-team-replaces-size.md`, `tasks/tech-design.md` D1-D8, PO answers I1-I8 (E4, 2026-10-27; I8 = P2: every team shape is valid).

## Promoted (ticket 13)
| Target | Edit |
|---|---|
| `docs/adr/0018-team-replaces-size.md` | ADR 0018, status accepted; states it overrides 0016 (Sizes, Duty owners) and 0017 (Manager never proposes Architect/Designer; the two flags) |
| `docs/adr/0016-...`, `0017-...` | one line each: "Amended by 0018" |
| `CONTEXT.md` | **Size** and the design/architecture flag entries removed; **Team**, **Duty owner**, **Checker** added; keys `qa-white`/`qa-black`, the term QA kept; role entries no longer say "present in S/M/L"; Risk flag reworded |
| `README.md` | team proposal replaces sizing; 0.6.0 breaking note with the converter path |
| `skills/squad-process-update/changelog.md` | v9 header, snapshot line and text (rule IDs appended by tasks 05-12) |
| `skills/squad-process-update/history/process-v9/` | snapshot = `templates/squad/process/` |
| `.claude-plugin/plugin.json` | 0.6.0 |
| `templates/squad/process/_removed.md` | tombstones checked: each has `why:` and `replaced_by:` |

`process-version:` in `templates/squad/process.md` stays 6: the integer is retired by ADR 0016 (the version is the plugin's and the changelog's `## v9`).

## Open items (not decided, not done here)
- F3: the Manager records a `team:` PO inbox reply in `scope.md` by hand; no command writes it. Follow-up outside this scope; no rule text change, no changelog row.
- Deploy steps 1-5 of `tech-design.md` (LC-12) run by the PO after merge: converter dry run, apply, `squad-process upgrade`.
