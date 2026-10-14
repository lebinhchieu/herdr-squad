---
name: squad-process-update
description: Bring a squad's process.md up to this plugin's version - explains what changed, keeps the squad's own edits, asks only about real conflicts, writes nothing until the PO confirms. Use when the PO says "migrate the process" or a squad warns that its process.md is behind.
disable-model-invocation: true
---

# Update a squad's process.md

Runs in the Manager's session on the PO's word. The PO never edits a file by hand. You touch only `process.md` and `process-log.md` of the squad (and a temp file outside it). All mechanics are `${CLAUDE_PLUGIN_ROOT}/bin/squad-process`; you explain, ask and decide nothing for the PO.

## Steps

1. **Pick the squad:** the name the PO gave, else the only one under `.claude/squads/`. Run `squad-process version --squad-dir <squad>`. Current: say so and stop. Ahead of the plugin, or a flat layout (no `scopes/`): say why and stop (`squad-migrate` first for a flat layout; update the plugin when ahead).
2. **Plan:** `squad-process plan --json --squad-dir <squad>`. Tell the PO in plain words: version V → P; each changelog item (title, sections, why); which sections are `clean` (plugin text replaces the old), which are `local` or `local-section` (the squad's own edits, kept as they are), which are `conflict`. Say plainly: nothing is written until they confirm. Items with `manual` need the PO's hand: say what.
3. **Each conflict:** show what the squad changed (`squad_vs_old`) next to what the plugin changed (`old_vs_new`), and both full wordings. Ask: ours, theirs, or the PO's own wording (write it to a temp file, `file:<path>`). Never choose for the PO.
4. **Compose, then show:** `squad-process compose --out <temp file outside the squad> --resolve "<heading>=ours|theirs|file:<path>" ... --squad-dir <squad>`, then `squad-process apply --file <temp> --squad-dir <squad>` **without** `--yes`. Show the diff and any `WARNING lint` lines (tell the PO what they mean; never reword a squad's own edit to silence them). Ask the PO to confirm the whole result.
5. **Only after a clear yes:** `squad-process apply --file <temp> --yes --squad-dir <squad>`. A no, or no answer: stop; the squad is untouched and the warning comes again next start.
6. **Report:** the backup path, the log rows written, and the changed sections (tell live roles to re-read those sections of `process.md`). Run `squad-process check --squad-dir <squad>`: it must say current.

## Rules

- The skill adds no prose of its own to `process.md`: the combined file holds plugin text, the squad's own text and the version line.
- The writing rule is the Writing rule in `agents/manager.md`; it arrives with the plugin update, not with this migration. Copy no rule text here. `apply` prints lint findings as a warning only.
- Log rows and changelog `why` are one line each.
- Any refusal (exit 2) is reported to the PO in its own words; do not work around it.
