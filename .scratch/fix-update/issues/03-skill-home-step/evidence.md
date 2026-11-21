# 03 Skill: Home step after the squad upgrade; changelog v21 and plugin 0.10.2: evidence
sha: 5bb415d
## Review
AC trace:
- AC1 | `grep -n "keep their" skills/squad-process-update/SKILL.md` prints nothing; `grep -n 'homes --check\|homes --apply --yes\|--only\|(a) move all\|--kind answer\|squad-respawn \$SQUAD_NAME' skills/squad-process-update/SKILL.md` | grep
- AC2 | `## Behaviour`, `upgrade --apply` on a scratch squad with nothing flagged moves `plugin.pin` | CLI run
- AC3 | SKILL.md steps 3-4 (Home only after applied; both env empty -> nothing to move; only the env home and a goal's open scopes); QA blackbox walks the dialog | read + CLI
- AC4 | `## Behaviour`: real `squad-inbox add` output and `homes` output | CLI run
- AC5 | `grep -rn '0\.10\.1' .claude-plugin/` prints nothing; `plugin.json` 0.10.2; `changelog.md` `## v21`; README.md:57 already lists `homes` (ticket 05 / 01) | grep
- AC6 | `cd tests; python3 -m unittest test_promotion_0_6_0 test_squadupgrade test_squad_spawn`: 156 tests, OK | unittest
- AC7 | `## Behaviour` (no `bin/` change)

## Behaviour
SQ-10 is not triggered: no `bin/` file and no printed text changed (`git diff --stat 4d555a8..HEAD`: SKILL.md, changelog.md, plugin.json). SKILL.md is 25 lines. `grep -rl 'squad-process-update' tests/` hits only `test_promotion_0_6_0.py` (run, OK); `test_squad_spawn` ran too, OK.

Missing 0.10.1 changelog entry: `git log -- skills/squad-process-update/changelog.md` last touches `c2826ff` (v20, 0.10.0); no v-block for 0.10.1. Not invented; told the Team Lead.

Scratch squad (`scaffold`, goal `g`, scopes `s1`, `s2` with `goal: g`, all pinned `0.10.1 824ba64`; old runtime = `git archive 824ba64`, `--old-root`; new plugin = this branch at 5bb415d). `SQUAD_ROLE=manager`.

### AC2: exit 0 of the check still applies and moves the pin
```
$ plugin.pin before
0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec
$ upgrade --check
upgrade: plugin 0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec -> 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84
plugin changes: added 0, changed 0, removed 0, retargeted 0
overlay: 0 operations: 0 unaffected, 0 re-targeted, 0 dropped, 0 need a decision
nothing needs a decision.
exit 0
$ upgrade --apply (no --yes)
upgrade: plugin 0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec -> 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84
plugin changes: added 0, changed 0, removed 0, retargeted 0
overlay: 0 operations: 0 unaffected, 0 re-targeted, 0 dropped, 0 need a decision
nothing needs a decision.

overlay after: 0 operations; pin moves to 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84
NOT APPLIED (add --yes after the PO confirms).
exit 3
$ upgrade --apply --yes
backup: /tmp/squad-backups/sq-process.local-2026-11-21-2.md
log rows:
| 2026-11-21 | Upgraded plugin 0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec -> 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84; running scopes keep their scope.md pin | squad-process upgrade --apply |
applied: overlay 0 operations; plugin.pin = 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84
exit 0
$ plugin.pin after
0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84
$ upgrade --apply --yes (again)
already on plugin 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84; nothing to do.
exit 0
```

### AC4: homes and the inbox item (goal case)
```
$ homes --check (home = goal g)
home                         pin now                target                 state
goal g                       0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
scope s1                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
scope s2                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
exit 3
$ squad-inbox add --kind answer --title "Move g to plugin 0.10.2: 3 homes" --body-file body.md --options "(a) move all and respawn now; (b) move only g; (c) leave them"
1 new item in the inbox: Move g to plugin 0.10.2: 3 homes
```
Body file:
```
Plugin 0.10.2 is applied to the squad. Your goal `g` and its open scopes can move too (3 homes).

- goal g: 0.10.1 -> 0.10.2, composes at the new pin
- scope s1: 0.10.1 -> 0.10.2, composes at the new pin
- scope s2: 0.10.1 -> 0.10.2, composes at the new pin

Live agents asked to save notes and respawn at once: none in this fixture (a real run lists the roster `live` rows, the Manager last). Each reads its notes in a new tab; a Developer mid-ticket keeps its worktree.
Not offered (would refuse spawn and respawn): none.
```
```
$ homes --apply (no --yes)
home                         pin now                target                 state
goal g                       0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
scope s1                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
scope s2                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
NOT APPLIED (add --yes after Chieu confirms)
exit 3
$ homes --apply --yes --only g
home                         pin now                target                 state
goal g                       0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
scope s1                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
scope s2                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
moved goal g: 0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec -> 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84
exit 0
$ homes --check after
home                         pin now                target                 state
goal g                       0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 at-target
scope s1                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
scope s2                     0.10.1 824ba6422c46b18f59ba06f60c3f5ab56326acec 0.10.2 5bb415dfad8df5db4d6886c967bade68e8f3fd84 moves
exit 3
```
Not run by me (QA blackbox walks them): lone scope, no home, refused home, pinned session, refusal.
