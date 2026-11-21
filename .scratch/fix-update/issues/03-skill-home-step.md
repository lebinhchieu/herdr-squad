# 03 Skill: after the squad upgrade, offer to move the Manager's goal or scope (and a goal's scopes); changelog and version bump
Duties: Developer builds and writes design notes (this file is the design) and the evidence; technical AC are in this file (Tech Lead, agreed with QA whitebox); business AC = this ticket as written; QA whitebox code check; QA blackbox behaviour check (reads the skill text and the printed output, runs the CLI in a scratch squad); hand in to both QAs
Files: skills/squad-process-update/SKILL.md, skills/squad-process-update/changelog.md, .claude-plugin/plugin.json, README.md
Evidence: .scratch/fix-update/issues/03-skill-home-step/evidence.md
Status: ready
After: 02 (build on 02's branch; the passed sha of 02 is `--base`)

Ticket path: `.scratch/fix-update/issues/03-skill-home-step.md`. Touched files are an estimate (LC-9b); a change re-issues this file.
SQ-5: this is the last ticket of the scope that touches plugin files (04 edits `docs/adr/` and `CONTEXT.md` only), so the version bump rides here.
Harness: `tests/squadtest.py` `PluginCopy`, `tests/test_squadupgrade.py` `Base`; the skill is text, so its checks are `grep`s on `SKILL.md` and a run of the commands it names in a scratch squad. No new test file.

## Problem
`SKILL.md` stops at the squad's rules: step 4 says "Open scopes keep their `scope.md` pin; they move at the next scope". Chieu's brief: while he works in a goal or scope, the skill should ask him to move that home too. Chieu's answers (iterations/1.md): Q1 (a) only the home the Manager runs in, plus a goal's open scopes; Q2 (a) a second inbox item, after the squad upgrade is applied; Q3 (b) the moved home's live agents respawn at once.

## Verified facts that shape the text (Tech Lead, 2026-11-21)
- Today's step 1 sends exit 0 straight to step 4, so `upgrade --apply` never runs and `plugin.pin` stays old (the check on this squad exits 0 with `plugin.pin` still 0.10.0 while the repo is 0.10.1). The home step needs `plugin.pin` moved first, so exit 0 must still go through apply -> show -> Chieu's yes -> `--yes` (apply prints `already on plugin ...; nothing to do.` and exits 0 when there is nothing to write).
- In a Manager session pinned to an older runtime, `squad-process` on PATH is that runtime's, and `squad-process upgrade --check` exits 2 `cannot pin the running plugin ... is not a git checkout and no installed squad@* entry ...` (run in this scope). A runtime older than this release has no `homes` command at all (`invalid choice`, exit 2). The skill is therefore only usable, and the home step only exists, in a session whose plugin is the new one; the text must say so instead of failing quietly.

## Design (SKILL.md)
1. **Step 1 and 3 fix:** exit 0 of the check -> still run step 3's apply (no `--resolve`), show, ask the yes, `--yes`. Step 2 (the answer item) is skipped when nothing is flagged.
2. **New step "Home":** after step 3 applied (exit 0 with `applied:` or `already on plugin`; a no from Chieu stops here), run `echo $SCOPE_DIR $GOAL_DIR`. Both empty: say "no goal or scope session, nothing to move" and go on. Else `squad-process homes --check --squad-dir <squad>` (home = the env default).
   - exit 0 and no `will refuse` line: one sentence, "your <goal|scope> is already on <pin>"; no item. A `will refuse` line is reported in the final report only.
   - exit 3: ONE inbox item, `squad-inbox add --kind answer --title "Move <home> to plugin <new>: <n> homes" --body-file <file> --options "(a) move all and respawn now; (b) move only <home>; (c) leave them"` (b only when the home is a goal). The body file lists, per offered home: kind, name, pin now -> new, whether it composes at the new pin, the live agents that will be asked to save notes and respawned at once (roster `live` rows, the Manager itself last, by the skill), what that costs (each agent reads its notes in a new tab; a Developer mid-ticket keeps its worktree), and any `will refuse spawn and respawn` homes that are not offered (stranded). Plain words, no rule IDs without a title.
   - exit 2 (a refused home): show its own words; offer only the homes that compose; never route around it.
   - The answer is the yes (nothing was written before it): (a) `homes --apply --yes --squad-dir <squad>`; (b) the same with `--only <goal home name>`; (c) stop. Show the printed result, including every `pending <name>` line and what Chieu does about it.
   - Unknown command (`invalid choice: 'homes'`) or the exit 2 `cannot pin the running plugin` of step 1: say "this session runs an older plugin; run /squad:squad-process-update from a session that loads the new plugin" and stop; write nothing.
3. **Step 4 rewrite:** drop "Open scopes keep their `scope.md` pin; they move at the next scope". The report states: the squad's backup path, log rows and new pin; for each home the old and new pin or why it stayed; the stranded warnings; the pending agents.
4. **Last step, the Manager's own respawn:** after the report is sent to Chieu, write `roles/<you>.notes.md`, put one line in `iterations/<n>.md` (SQ-14: a respawn within 30 minutes of your last needs a reason there: "plugin pin moved, Chieu said yes"), run `squad-respawn $SQUAD_NAME`, and tell Chieu the new session opens in a new tab. A `(c)` or no move: no respawn.
5. Keep the skill's style: Chieu never edits a file; the skill chooses nothing for him; the new text stays short (the file is 17 lines now, aim for under 30).

## AC
- AC1 `grep -n "keep their" skills/squad-process-update/SKILL.md` prints nothing; the skill names `homes --check`, `homes --apply --yes`, `--only`, the (a)/(b)/(c) options, the second `squad-inbox add --kind answer`, and the last step `squad-respawn $SQUAD_NAME`.
- AC2 The text sends check exit 0 through apply (`--yes` after Chieu's yes), and a run of `squad-process upgrade --apply --squad-dir <scratch> --yes` on a scratch squad with no flagged items moves `plugin.pin` (the evidence shows it before/after).
- AC3 The Home step is reached only after a successful squad apply and never when `$SCOPE_DIR` and `$GOAL_DIR` are both empty; it never offers a home other than Q1 (a)'s. QA blackbox walks the dialog in a scratch squad: lone scope, goal with two open scopes, no home, a refused home, and an older-runtime session, with the printed lines as evidence.
- AC4 Evidence includes the real inbox item (`squad-inbox add` output) for the goal case and the CLI output of `homes --check` / `--apply` it quotes.
- AC5 SQ-5 bump: `.claude-plugin/plugin.json` version 0.10.1 -> 0.10.2; `grep -rn '0\.10\.1' .claude-plugin/` prints no version line; `skills/squad-process-update/changelog.md` gets a `## v21` block (format of v20: `Plugin 0.10.2.`, added/changed, a Deploy line for Chieu with rollback `plugin back to 0.10.1`) naming `squad-process homes`, the respawn stage, the exit-0 fix and the pinned-runtime limit; README.md:57 lists `homes`. The Developer checks `git log -- skills/squad-process-update/changelog.md` for a missing 0.10.1 entry and tells the Team Lead (does not invent one).
- AC6 Technical: `tests/test_promotion_0_6_0.py` (version/changelog test) and `tests/test_squadupgrade.py` pass; `grep -rl 'squad-process-update' tests/` hits are run (`tests/test_squad_spawn.py` has legacy cases: run them, do not edit unless the grep shows a changed string).
- AC7 No `bin/` or printed-text change here, so SQ-10 is not triggered; the Developer says so in `## Behaviour`.

## SQ-1 (deletes and moves)
Deletes or moves no file. Readers of the lines removed from `SKILL.md`: none (`grep -rn 'keep their .scope.md. pin' .` over the repo outside `.scratch/` and `.claude/squads/` finds only this skill; confirmed).

## Comments
