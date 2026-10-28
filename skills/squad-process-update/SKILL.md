---
name: squad-process-update
description: Upgrade a composed squad's rules to this plugin's version, rule by rule - explains what changed, applies what the squad's overlay does not touch, asks only about stale or removed operations, writes nothing until the PO confirms. Use when the PO says "upgrade the process".
disable-model-invocation: true
---

# Upgrade a squad's rules

Runs in the Manager's session on the PO's word. The PO never edits a file by hand. All mechanics are `${CLAUDE_PLUGIN_ROOT}/bin/squad-process`; you explain, ask and decide nothing for the PO. Nothing is written until the PO confirms. Mechanics: nothing is written until the PO confirms. Mechanics: `squad-process upgrade` and `upstream`.

1. **Check:** `squad-process upgrade --check --squad-dir <squad>`. Exit 0: say how many operations were handled silently (the output counts them) and go to step 4. Exit 3: flagged items follow. Exit 1: the old pin's runtime is missing; show the message. Exit 2: report it as written.
2. **One inbox answer item** for all flagged items: `squad-inbox add --kind answer --title "Process upgrade <old> -> <new>: <n> decisions" --body-file <file> --options "(a) <ID> keep; (b) <ID> take; ..."`. The body file explains each flagged item in plain words: the rule ID and title, what the plugin changed and why (the changelog line for that ID), the squad's own text, and each option with its consequence. One option per ID-and-choice; the PO's answer names one choice for every ID.
   - **stale** (plugin changed a rule the squad replaced): `keep` = squad text stays, re-checked against the new rule; `take` = squad text dropped, plugin text used; `file:<path>` = the PO's new wording (write it to a temp file first).
   - **removed** (plugin removed a rule the squad replaced): `drop` = squad text dropped; `retarget:<ID>` = squad text moves to the named new rule (offer the plugin's `replaced_by` IDs); `local` = squad text becomes a squad-only rule `SQ-n`.
   Items under "review (not blocking)" are only mentioned: a squad rule shares a topic with a plugin change.
3. **The answer** comes back from the inbox as one choice per ID; pass each as `--resolve <ID>=<choice>`. Run `squad-process upgrade --apply --squad-dir <squad> --resolve ... ` **without** `--yes`, show the result (it exits 3 with `NOT APPLIED` and writes nothing; only exit 0 means applied), ask for the PO's yes, then run it again with `--yes`. A no or no answer: stop; nothing was written.
4. **Report:** the backup path, log rows and new pin from the output. Open scopes keep their `scope.md` pin; they move at the next scope.
5. **Upstream:** `squad-process upstream` lists the squad's `upstream: proposed` operations (why and body) for a plugin ticket. Offer it; never file it for the PO.

Never choose for the PO. Any refusal is reported in its own words.
