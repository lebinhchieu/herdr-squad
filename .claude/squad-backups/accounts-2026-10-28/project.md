# Project source map

**Where each kind of truth lives in this project. Roles read this instead of guessing paths.** Filled in by `/squad:squad-init`; the Manager keeps it current.

| What | Where |
|---|---|
| Project instructions | None in the code repo. Teammates follow `/home/chieule/workspace/squad/CLAUDE.md` (squad repo) and the `claude-accounts` skill (`~/.claude-3/skills/claude-accounts/SKILL.md`, must stay in sync with behaviour). |
| Requirements | `~/.claude-accounts/HANDOFF.md` (commands, how it works); scope briefs in `$SCOPE_DIR/scope.md`. |
| Business AC | `$SCOPE_DIR/` (BA + QA blackbox); no standing AC file. |
| Technical AC / done rules | No repo rules. Done = behaviour checked by running the launcher/script (bash, WSL, inside herdr where needed) and `HANDOFF.md` + the `claude-accounts` skill updated. |
| Decisions | None yet; decisions go in `HANDOFF.md`. |
| Open questions for outside people | `.claude/squads/accounts/open-points.md` (create on first use); the PO answers. |
| Tasks / tickets | `$SCOPE_DIR/tasks/` |
| Evidence | next to the ticket: <ticket path minus .md>/ (reviewers' working files and receipts: $SCOPE_DIR/evidence/) |
| Code repos | `/home/chieule/workspace/squad` (this repo), source in `tools/claude-accounts/` (ADR 0012). `~/.claude-accounts` holds installed copies and state files only; the PO runs `tools/claude-accounts/install.sh` after a merge. Developers get a normal worktree of the squad repo. |
| Test and lint commands | `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` (see CLAUDE.md); launcher tests `tests/test_ca_launchers.py`, `tests/test_ca_autoswitch.py`, harness `tests/ca_stubs.py`. Syntax: `bash -n <script>`, `python3 -m py_compile tools/claude-accounts/bin/cautoswitch`. |
| UI conventions / design system | none |
| Running app | No web app. QA blackbox runs `c1/c2/c3/c/cdefault/cswitch/cautoswitch` in a herdr pane (`HERDR_ENV=1`) and reads `cswitch.log`, `default`, `workspace-default/`. Accounts: 1 = `~/.claude`, 2 = `~/.claude-2`, 3 = `~/.claude-3`. Never read or print tokens. |

## Outside decision makers
- PO (Chieu Le): account policy (thresholds, default account). Questions go to `open-points.md`, never to them directly.
