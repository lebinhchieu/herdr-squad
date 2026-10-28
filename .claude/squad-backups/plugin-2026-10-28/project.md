# Project source map

**Where each kind of truth lives in this project. Roles read this instead of guessing paths.** Filled in by `/squad:squad-init`; the Manager keeps it current.

| What | Where |
|---|---|
| Project instructions | `CLAUDE.md` (issue tracker, triage labels, domain docs, running tests), `README.md`, `CONTEXT.md` |
| Requirements | `.scratch/<feature-slug>/spec.md` |
| Business AC | In each spec's user stories; per-task AC in `$SCOPE_DIR/tasks/` task files |
| Technical AC / done rules | `CLAUDE.md` (surgical changes, no slop); tests pass (see below) |
| Decisions | `docs/adr/` and `CONTEXT.md` (glossary); feature design notes in `.scratch/<feature-slug>/` |
| Open questions for outside people | `$SCOPE_DIR/escalations.md` (answered by the PO) |
| Tasks / tickets | `.scratch/<feature-slug>/issues/NN-<slug>.md` (one ticket per file, `Status:` line) |
| Evidence | next to the ticket: <ticket path minus .md>/evidence.md (older tickets: <ticket path minus .md>.evidence/, still read) (reviewers' working files and receipts: $SCOPE_DIR/evidence/) |
| Code repos | `/home/chieule/workspace/squad` (single repo; no submodules). Code: `agents/`, `bin/`, `hooks/`, `skills/`, `templates/`, `tests/` |
| Test and lint commands | Tests: repo `CLAUDE.md` → Running tests (`python3 tests/run_suite.py --receipt <dir> --if-changed <task base>`; `--tz` for integration/promotion). Lint: none configured |
| UI conventions / design system | PO inbox mod (`hooks/po-inbox/`); squad-report HTML: Mango Parrot light palette (`/home/chieule/workspace/theme-vscode/themes/mango-parrot-color-theme.json`, light only). |
| Running app | The CLI tools in a scratch squad (a temp dir with a stub `claude` and herdr; see `tests/test_squad_start.py`); the PO inbox mod is checked with `claude plugin test`. squad-report: `playwright-cli` blocks `file:`, so serve the report folder with `python3 -m http.server` bound to 127.0.0.1 and open it there; stop the server by PID after. |

## Outside decision makers
- PO (Chieu Le): scope, goals, anything the spec leaves open. Questions go to `$SCOPE_DIR/escalations.md`, never to them directly.

## Rules for lasting docs
- Glossary changes go to `CONTEXT.md` and decisions to `docs/adr/NNNN-<slug>.md`, via the `/domain-modeling` skill. The promotion task at a scope's end follows this.
