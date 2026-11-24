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

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `grep -n "keep their" SKILL.md` prints nothing; grep of the named commands hits | grep 'keep their' on SKILL.md: no hit; grep -c of homes --check, homes --apply --yes, --only, (a)/(b)/(c), inbox add --kind answer, squad-respawn $SQUAD_NAME: all >= 1 | grep -n "keep their" SKILL.md prints nothing; SKILL.md names homes --check, homes --apply --yes, --only, (a)/(b)/(c), squad-inbox add --kind answer, squad-respawn $SQUAD_NAME (read at e728bb8) |
| AC2 | evidence `## Behaviour` AC2: `upgrade --apply --yes` moved `plugin.pin` 0.10.1 -> 0.10.2, exit 0 | read SKILL.md steps 1 and 3 (exit 0 goes through apply, --yes after the yes); read evidence AC2 run (pin 0.10.1 -> 0.10.2) | live: scratch squad pin 0.10.1, nothing flagged: check exit 0, apply w/o --yes exit 3 NOT APPLIED, with --yes plugin.pin 0.10.1 -> 0.10.2 (evidence/03/qa-b.md) |
| AC3 | SKILL.md steps 3-4 read; dialog cases left to QA blackbox | read SKILL.md step 4 (only after step 3, both env empty -> nothing to move, env home plus goal scopes only); dialog cases are QA blackbox's | live: lone scope, goal+2 scopes ((a) and (b)), no home (text), refused home, pinned session, refusal: see evidence/03/qa-b.md |
| AC4 | evidence `## Behaviour` AC4: `homes --check` exit 3, `squad-inbox add` output, `homes --apply --yes --only g` | read evidence AC4: homes --check exit 3, inbox add output, homes --apply --yes --only g | live: homes --check exit 3 and squad-inbox add output for the goal case (qa-b.md) |
| AC5 | `grep -rn '0\.10\.1' .claude-plugin/` empty; v21 in changelog.md; README.md:57 has `homes` | grep -rn '0\.10\.1' .claude-plugin/: no hit; plugin.json 0.10.2; changelog.md v21 read; README.md:57 lists homes; git log of changelog.md shows no 0.10.1 entry | plugin.json 0.10.2; grep 0.10.1 .claude-plugin/ prints nothing; changelog v21 names homes, respawn, exit-0 fix, discovery, Deploy hand-move + rollback; README:57 lists homes |
| AC6 | `python3 -m unittest test_promotion_0_6_0 test_squadupgrade test_squad_spawn`: 156 OK | from tests/: unittest test_promotion_0_6_0 test_squadupgrade test_squad_spawn: 156 OK; grep -rl squad-process-update tests/ hits only test_promotion_0_6_0 | n/a: QA whitebox's AC |
| AC7 | evidence `## Behaviour`: no bin/ change, SQ-10 not triggered | git diff --stat bdbbe04 5bb415d: no bin/ file | n/a: QA whitebox's AC |

## QA whitebox

### QA whitebox 03 (sha e728bb8, code 5bb415d): PASS

Checked diff bdbbe04..5bb415d (SKILL.md, changelog.md, plugin.json) against AC1-AC7.
- AC1 no "keep their" hit; every named command present. AC2 steps 1 and 3 send exit 0 through apply; evidence run moves the pin. AC3 text: Home step only after step 3, both env empty -> nothing to move, only the env home and a goal's open scopes. AC4 real inbox output and homes output in evidence. AC5 plugin.json 0.10.2, no `0.10.1` in .claude-plugin/, changelog v21 names homes, respawn stage, exit-0 fix, pinned-session discovery, Deploy line with the by-hand step and rollback; README.md:57 lists homes. AC6 I ran test_promotion_0_6_0 test_squadupgrade test_squad_spawn from tests/: 156 OK. AC7 no bin/ file in the diff.
- SKILL.md is 25 lines.

Follow-ups (not FAIL):
- No changelog block for 0.10.1 exists (v20 is 0.10.0). Developer reported it to the Team Lead; not invented.
- bin/ still prints the log row "running scopes keep their scope.md pin" on `upgrade --apply --yes`. After this scope homes can move, so the words are stale. Outside 03 (AC7: no bin/ change); candidate for a later ticket.
- Not checked by me: the dialog walk (QA blackbox) and a real run of the skill in a live session.

## QA blackbox

### 03 QA blackbox on e728bb8 (CLI output, no screenshots)
I read `skills/squad-process-update/SKILL.md` and followed it step by step, running the commands it names. I only follow the text; I do not read code. Scratch squads: old pin 0.10.1 (main 5aadae0), new plugin = branch e728bb8 (0.10.2); `SQUAD_INSTALLED_PLUGINS` empty; herdr stub on PATH for the respawn. Not run: a real mid-session Manager, live agents mid-turn, a new tab (Chieu's merge check).

| AC / case | What I did | What I saw | Result |
|---|---|---|---|
| check AC1 | `grep -n "keep their" SKILL.md`; read the steps | no hit; text names `homes --check`, `homes --apply --yes`, `--only`, (a)/(b)/(c), second `squad-inbox add --kind answer`, last step `squad-respawn $SQUAD_NAME` | pass |
| check AC2 | step 1 `upgrade --check` on a squad at 0.10.1 with nothing flagged; step 3 without, then with `--yes` | check exit 0 `nothing needs a decision`; apply without yes exit 3 `NOT APPLIED`, pin unchanged; with yes `applied: ... plugin.pin = 0.10.2 e728bb83...`, `plugin.pin` 0.10.1 5aadae0 -> 0.10.2 e728bb8 | pass |
| Goal + 2 scopes | step 4 with GOAL_DIR set: `homes --check` | exit 3, table: goal g1, scope s1, scope s2 all `moves`; a lone scope s3 in the same squad is not listed | pass |
| Goal (b) | `homes --apply --yes --only g1` | `moved goal g1: ...`, `pending tl-g1: ... notes.md is missing` (stub agent, no notes), `caller mgr-g1: last step: ...`, exit 4; check after: g1 at-target, s1 and s2 still `moves` | pass |
| Goal (a) | `homes --apply --yes` | moved goal g1, s1, s2; one `pending` line per live agent without notes; caller line; exit 4; check after: all at-target, exit 0 | pass |
| Inbox item (goal) | `squad-inbox add --kind answer --title "Move goal g1 to plugin 0.10.2: 3 homes" --body-file ... --options "(a) ...; (b) move only g1; (c) leave them"` | `1 new item in the inbox: Move goal g1 to plugin 0.10.2: 3 homes`, row in escalations.md with the three options (needs SQUAD_ROLE=manager and the escalations table, as a real Manager has) | pass |
| Lone scope | SCOPE_DIR=s3, step 4 | `homes --check` lists only scope s3 (`moves`, exit 3); apply moved s3, pending s3-dev, exit 4; check after at-target exit 0 | pass |
| No home | `echo $SCOPE_DIR $GOAL_DIR` empty | per the text: say nothing to move, go to the report; no homes command is run (text read; `homes` itself with no home exits 2 `no home: run inside a scope or goal session`) | pass |
| Already on the pin | `homes --check` after a move | exit 0, table with `at-target`, no item | pass |
| Refused home | goal g1, scope s2 `plugin: garbage` | `homes --check` exit 2, s2 `refused` with the reason `plugin: line 7: expected ...`; `homes --apply --yes` refuses: `refused scope s2: ... (deselect it with --only)`, exit 2, no scope.md or goal.md changed; also a scope with team `nonsense-role` shows `refused` with its reason; `--only g1 s1` then moves only those | pass |
| Pinned session | runtime = git archive of e728bb8 (0.10.2, no .git), squad pin 0.10.2, known marketplace fixture -> checkout 0.10.3; the same dialog from the runtime | step 1 stderr `this session runs plugin 0.10.2; using plugin 0.10.3 from <n3> (known marketplace herdr-squad)`, exit 0; apply moved pin to 0.10.3; `homes --check` same line then table exit 3; `homes --apply --yes --only g1` moved the goal, wrote the 0.10.3 runtime, exit 4 | pass |
| Refusal | same pinned runtime, known file missing | `upgrade --check` and `homes --check` exit 1 `cannot pin the running plugin ... no newer squad plugin was found`, `searched: ... (0 entries)`, both ways out; squad files unchanged (md5 listing before/after) | pass |
| check AC5 | read | plugin.json 0.10.2; `grep -rn '0\.10\.1' .claude-plugin/` no hit; changelog `## v21` names homes, respawn stage, exit-0 fix, pinned-session discovery, Deploy with the hand-move for 0.10.0/0.10.1 sessions and `plugin back to 0.10.1`; README line 57 lists `homes` | pass |

AC6 and AC7 are QA whitebox's. 

Follow-ups (no AC break):
1. Refused-home case: step 4 tells the Manager to offer only the homes that compose, but option (a) and the apply command as written (`homes --apply --yes`, no `--only`) refuse in that case and write nothing (verified exit 2). The text could say: pass `--only <the composing homes>` for (a).
2. `upgrade --apply --yes` still logs `running scopes keep their scope.md pin` (printed row, bin text), which now contradicts the Home step. No bin change in this ticket; a later one could reword it.
