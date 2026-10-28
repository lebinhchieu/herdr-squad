---
name: squad-process-update
description: Bring a squad's process.md up to this plugin's version - explains what changed, keeps the squad's own edits, asks only about real conflicts, writes nothing until the PO confirms. Use when the PO says "migrate the process" or a squad warns that its process.md is behind.
disable-model-invocation: true
---

# Update a squad's process.md

**Three paths.** A squad with `process.local.md` is composed: use "Composed squads" below. A squad with only `process.md` is legacy: it uses the v6 section merge in "Steps" (`apply` needs `--legacy`). `squad-process upgrade` on a legacy squad says "not composed" and writes nothing.

Runs in the Manager's session on the PO's word. The PO never edits a file by hand. You touch only `process.md` and `process-log.md` of the squad (and a temp file outside it). All mechanics are `${CLAUDE_PLUGIN_ROOT}/bin/squad-process`; you explain, ask and decide nothing for the PO.

## Steps

1. **Pick the squad:** the name the PO gave, else the only one under `.claude/squads/`. Run `squad-process version --squad-dir <squad>`. Current: say so and stop. Ahead of the plugin, or a flat layout (no `scopes/`): say why and stop (update the plugin when ahead).
2. **Plan:** `squad-process plan --json --squad-dir <squad>`. Tell the PO in plain words: version V → P; each changelog item (title, sections, why); which sections are `clean` (plugin text replaces the old), which are `local` or `local-section` (the squad's own edits, kept as they are), which are `conflict`. Say plainly: nothing is written until they confirm. Items with `manual` need the PO's hand: say what.
3. **Each conflict:** show what the squad changed (`squad_vs_old`) next to what the plugin changed (`old_vs_new`), and both full wordings. Ask: ours, theirs, or the PO's own wording (write the body only, without the heading line, to a temp file: `file:<path>`; the section's own heading line as first line is dropped, any other heading line is refused). A section the squad deleted but the new version keeps is a conflict too: `ours` is not offered, only theirs or own wording. Never choose for the PO.
4. **Compose, then show:** `squad-process compose --out <temp file outside the squad> --resolve "<heading>=ours|theirs|file:<path>" ... --squad-dir <squad>`, then `squad-process apply --legacy --file <temp> --squad-dir <squad>` **without** `--yes`. Show the diff and any `WARNING lint` lines (tell the PO what they mean; never reword a squad's own edit to silence them). Ask the PO to confirm the whole result.
5. **Only after a clear yes:** `squad-process apply --legacy --file <temp> --yes --squad-dir <squad>`. A no, or no answer: stop; the squad is untouched and the warning comes again next start.
6. **Report:** the backup path, the log rows written, and the changed sections (tell live roles to re-read those sections of `process.md`). Run `squad-process check --squad-dir <squad>`: it must say current.

## Rules

- The skill adds no prose of its own to `process.md`: the combined file holds plugin text, the squad's own text and the version line.
- The writing rule is the Writing rule in `agents/manager.md`; it arrives with the plugin update, not with this migration. Copy no rule text here. `apply` prints lint findings as a warning only.
- Log rows and changelog `why` are one line each.
- Any refusal (exit 2) is reported to the PO in its own words; do not work around it.

## Composed squads (rule by rule)

Same session, same promise: nothing is written until the PO confirms. Mechanics: `squad-process upgrade` and `upstream`.

1. **Check:** `squad-process upgrade --check --squad-dir <squad>`. Exit 0: say how many operations were handled silently (the output counts them) and go to step 4. Exit 3: flagged items follow. Exit 1: the old pin's runtime is missing; show the message. Exit 2: report it as written.
2. **One inbox answer item** for all flagged items: `squad-inbox add --kind answer --title "Process upgrade <old> -> <new>: <n> decisions" --body-file <file> --options "(a) <ID> keep; (b) <ID> take; ..."`. The body file explains each flagged item in plain words: the rule ID and title, what the plugin changed and why (the changelog line for that ID), the squad's own text, and each option with its consequence. One option per ID-and-choice; the PO's answer names one choice for every ID.
   - **stale** (plugin changed a rule the squad replaced): `keep` = squad text stays, re-checked against the new rule; `take` = squad text dropped, plugin text used; `file:<path>` = the PO's new wording (write it to a temp file first).
   - **removed** (plugin removed a rule the squad replaced): `drop` = squad text dropped; `retarget:<ID>` = squad text moves to the named new rule (offer the plugin's `replaced_by` IDs); `local` = squad text becomes a squad-only rule `SQ-n`.
   Items under "review (not blocking)" are only mentioned: a squad rule shares a topic with a plugin change.
3. **The answer** comes back from the inbox as one choice per ID; pass each as `--resolve <ID>=<choice>`. Run `squad-process upgrade --apply --squad-dir <squad> --resolve ... ` **without** `--yes`, show the result (it exits 3 with `NOT APPLIED` and writes nothing; only exit 0 means applied), ask for the PO's yes, then run it again with `--yes`. A no or no answer: stop; nothing was written.
4. **Report:** the backup path, log rows and new pin from the output. Open scopes keep their `scope.md` pin; they move at the next scope.
5. **Upstream:** `squad-process upstream` lists the squad's `upstream: proposed` operations (why and body) for a plugin ticket. Offer it; never file it for the PO.

Never choose for the PO. Any refusal is reported in its own words.
