# 0031: A PO-confirmed upgrade also moves the open home the Manager runs in

Status: accepted (fix-update; Chieu answered Q1-Q3 on 2026-11-21)

Amends 0016: "an upgrade applies between scopes only" now has one exception, below.

**Decision:** after `/squad:squad-process-update` has applied the squad's upgrade (`plugin.pin` moved), the skill offers Chieu, in a second inbox item, to move the home the Manager runs in (a lone scope, or a goal and its open scopes) to the squad's pin. `squad-process homes --check | --apply [--yes]` lists those homes with their pins and, on Chieu's yes, rewrites only the `plugin:` line of each chosen home's file to the pin in `plugin.pin`. It first composes every role of each chosen home at the new pin with that pin's own engine and refuses (exit 2, nothing written) a home that does not compose. It then asks each live agent of a moved home to save its notes and respawns it at once with the new runtime's `squad-respawn`; the calling Manager is told to respawn itself last. An agent that does not settle is left `pending` (exit 4), never killed. Other open homes are not offered; `homes --check` warns when one would no longer compose.

**Why:**
- A home pinned at an old plugin composes against the squad's overlay, which an upgrade has already moved to the new plugin. A `replace` or `remove` op whose hash or target changed makes compose exit 2, so that home stops spawning and respawning (reproduced 2026-11-21 against `_runtime/0.10.0-432b8ea8144f`). The upgrade therefore reaches into running homes whether or not Chieu moves them; the move lets him choose it for the home he works in.
- Chieu works in one home and asked to be offered it (Q1 (a)); a second item (Q2 (a)) keeps the rule decisions and the home move apart; live agents restart at once (Q3 (b)) so the home does not run two rule versions.

**Consequences:**
- The target is `plugin.pin`, never the running plugin, so the tool works from a pinned runtime; the skill still needs a session whose plugin is the new one for the squad upgrade itself.
- The move is reversible: one process-log row per home holds the old pin; moving back is the same one-line edit.
- Respawn at once costs each agent a fresh context (notes only); a Developer's worktree and branch are kept.
- Known limit: homes outside Q1 (a) stay on their pin and may stop composing; they are warned about, not moved.
- Known limit: the real herdr behaviour (an agent mid-turn, the new tab) is covered by a stub only.

**Alternatives rejected:**
- Offer every open home in the squad (Q1 (b)): more to confirm than Chieu works in.
- Same item as the rule decisions (Q2 (b)): the home move depends on the applied pin.
- List who needs a respawn and respawn at a quiet point (Q3 (a)): the home would run two rule versions meanwhile.
