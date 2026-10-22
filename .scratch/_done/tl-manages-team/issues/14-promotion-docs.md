# T14 · ADR 0011, CONTEXT.md, README and plugin version
Status: ready-for-agent
Type: task
Blocked by: none (wording comes from design.md decisions 16-23; the Tech Lead writes `promote.md` section E3 first)
Repo: /home/chieule/workspace/squad
Spec: Promotion rule in `process.md` (the scope's last task, committed on the integration branch) · Design: ../design.md E3

## Files this task touches (and no others)
`docs/adr/0011-layered-squad-settings.md` (new), `docs/adr/0005-process-versioning.md` and `docs/adr/0008-spawn-overrides-survive-respawn.md` (one "Amended by 0011:" line each, below `Status:`), `CONTEXT.md`, `README.md`, `.claude-plugin/plugin.json` (version only), `tests/test_docs_layered_settings.py` (new).

## Do
1. Read `$SCOPE_DIR/promote.md`, section "E3" (the Tech Lead's exact wording) and write the ADR in the style of 0010 (decision, why, consequences, alternatives rejected: layering unstamped files; trimming denies; auto-apply on every spawn; deep-merging objects). Note the amendment of 0005 (process.md can now apply itself when no section conflicts) and 0008/0010 (scalars from the combined file).
2. `CONTEXT.md`: glossary terms **layered settings**, **stamp**, **full copy**, **effective settings**, each one line, using the repo's existing style; no duplicate of an existing term.
3. `README.md`: the `squad-spawn` row (generated file, `--show-settings`), a `squad-settings` row, `squad-migrate` row (`--to layered-settings`), the sentence about `settings/<role>.json` (line ~62) matches decision 16.
4. `.claude-plugin/plugin.json` `version`: `0.4.0`, the value of `MIN_PLUGIN` in T10 (the PO releases it).
5. Test: `MIN_PLUGIN` (import `squadsettings` when it exists on the integration branch; skip when it does not) is `<=` the plugin.json version; ADR 0011 exists and the two amendment lines point at it; the README names `--show-settings` and `--to layered-settings`.
6. **Run only the test file you touched**; never the full suite. `PYTHONDONTWRITEBYTECODE=1`. Follow the repo rule for editing instruction files (`CLAUDE.md` is not touched here).

## Technical AC (AC-15)
- AC-15.1 Every fact in the ADR appears in design.md decisions 16-23 and nothing else (QA-W diffs the two).
- AC-15.2 No glossary term duplicates an existing one; README rows agree with the real `--help` output of the scripts (paste in `dev-evidence.md`).

## Amendments (Tech Lead, 2026-10-17, from QA-W v6)
- **A19** The `MIN_PLUGIN <= plugin.json version` test compares numeric tuples; add the case `"0.10.0" > "0.4.0"`.
- **A16, A18 (ADR text, done at integration in T15 if T14 has already been handed in):** ADR 0011 says a missing template deny is adopted by default in the trim, and names the risk that a future Claude Code key named `remove` or `squadSettings` would collide with the squad's keys.
