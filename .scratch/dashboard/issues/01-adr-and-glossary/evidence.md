# Evidence 01 adr and glossary

## Behaviour
- T01.AC1: `docs/adr/0020-dashboard-replaces-removed-board.md` exists (0020 is next after 0019); names `board-ui.json`, `open-questions.md` and the `tickets: <feature-slug>` line in `scope.md`.
- T01.AC2: its second paragraph says it supersedes only the "Known loss" line of 0009 and plainly names the one other 0009 line it contradicts ("nothing reads `escalations.md` as a Needs-you list"). `0009-board-removed.md` has a "Partly superseded by 0020" line under Status. 0007's "no cross-home view" is kept (Consequences).
- T01.AC3: `CONTEXT.md` has `## Dashboard` with Needs you, Parked question, Ready for review, Work time (one definition each, worded from `features.md` lines 45-46, 58, 164), plus Dashboard, Picker, Choice, Panel, Approx; three Relationships lines added.
- T01.AC4: `0007-inbox-sits-on-escalations.md` Consequences has one line pointing to `open-questions.md`.
- Also: `.scratch/dashboard/` holds `spec.md`, `architecture.md`, `issues/01..17`, `ui-design/design-v4.md` and `proto-v5.html`; ticket 18 not copied (not listed in 01).
- No code, no tests. `grep -rl 'CONTEXT.md\|docs/adr\|0009-board-removed\|0007-inbox' tests/` found no file.
