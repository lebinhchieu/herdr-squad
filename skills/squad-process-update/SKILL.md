---
name: squad-process-update
description: Upgrade a composed squad's rules to this plugin's version, rule by rule - explains what changed, applies what the squad's overlay does not touch, asks only about stale or removed operations, writes nothing until the PO confirms. Use when the PO says "upgrade the process".
disable-model-invocation: true
---

# Upgrade a squad's rules

Runs in the Manager's session on the PO's word. The PO never edits a file by hand. All mechanics are `${CLAUDE_PLUGIN_ROOT}/bin/squad-process`; you explain, ask and decide nothing for the PO. Nothing is written until the PO confirms. Mechanics: `squad-process upgrade` and `upstream`.

1. **Check:** `squad-process upgrade --check --squad-dir <squad>`. Exit 0 or 3: go on (exit 0 still goes through step 3, so the pin moves; step 2 is skipped when nothing is flagged; say how many operations were handled silently). Exit 3: flagged items follow. Exit 1: show the message as written and stop, writing nothing; it means the old pin's runtime was not found, or no newer plugin was found (`--old-root <old plugin folder>` and `--new-pin "<version> <sha>"` are the manual fallback only, for a plugin that is neither a git checkout nor in `installed_plugins.json`). Exit 2: report it as written. A `using plugin <v>` line on stderr is normal in a pinned session; keep it for the report.
2. **One inbox answer item** for all flagged items: `squad-inbox add --kind answer --title "Process upgrade <old> -> <new>: <n> decisions" --body-file <file> --options "(a) <ID> keep; (b) <ID> take; ..."`. The body file explains each flagged item in plain words: the rule ID and title, what the plugin changed and why (the changelog line for that ID), the squad's own text, and each option with its consequence. One option per ID-and-choice; the PO's answer names one choice for every ID.
   - **stale** (plugin changed a rule the squad replaced): `keep` = squad text stays, re-checked against the new rule; `take` = squad text dropped, plugin text used; `file:<path>` = the PO's new wording (write it to a temp file first).
   - **removed** (plugin removed a rule the squad replaced): `drop` = squad text dropped; `retarget:<ID>` = squad text moves to the named new rule (offer the plugin's `replaced_by` IDs); `local` = squad text becomes a squad-only rule `SQ-n`.
   Items under "review (not blocking)" are only mentioned: a squad rule shares a topic with a plugin change.
3. **The answer** comes back from the inbox as one choice per ID; pass each as `--resolve <ID>=<choice>` (none when nothing was flagged). Run `squad-process upgrade --apply --squad-dir <squad> --resolve ... ` **without** `--yes`, show the result (it exits 3 with `NOT APPLIED` and writes nothing; exit 0 is applied, or `already on plugin ...; nothing to do.`), ask for the PO's yes, then run it again with `--yes`. A no or no answer: stop; nothing was written.
4. **Home:** only after step 3 applied. Run `echo $SCOPE_DIR $GOAL_DIR`. Both empty: say "no goal or scope session, nothing to move" and go to step 5. Else `squad-process homes --check --squad-dir <squad>` (the home is the env default); this moves only that goal or scope and a goal's open scopes, no other home. Exit 1: show the message as written and stop. Exit 2 (a refused home): show its words, offer only the homes that compose.
   - Exit 0 and no `will refuse` line: say "your <goal|scope> is already on <pin>"; no item. A `will refuse` line goes in the report only.
   - Exit 3: ONE inbox item, `squad-inbox add --kind answer --title "Move <home> to plugin <new>: <n> homes" --body-file <file> --options "(a) move all and respawn now; (b) move only <home>; (c) leave them"` ((b) only when the home is a goal). The body file lists per offered home: kind, name, pin now -> new, whether it composes there, the live agents (roster `live` rows, the Manager last) that will save notes and respawn at once, the cost (each reads its notes in a new tab; a Developer mid-ticket keeps its worktree), and any `will refuse spawn and respawn` home that is not offered. Plain words.
   - The answer is the yes: (a) `squad-process homes --apply --yes --squad-dir <squad>`; (b) the same with `--only <goal home name>`; (c) stop. Show the printed result, every `pending <name>` line and what the PO does about it.
5. **Report:** the squad's backup path, log rows and new pin, and the `using plugin` line when printed; for each home the old and new pin or why it stayed; the stranded warnings; the pending agents.
6. **Your own respawn:** after the report, write `roles/<you>.notes.md`, put one line in `iterations/<n>.md` ("plugin pin moved, Chieu said yes"), run `squad-respawn $SQUAD_NAME` and say the new session opens in a new tab. A (c) or no move: no respawn.
7. **Upstream:** `squad-process upstream` lists the squad's `upstream: proposed` operations (why and body) for a plugin ticket. Offer it; never file it for the PO.

Never choose for the PO. Any refusal is reported in its own words.
