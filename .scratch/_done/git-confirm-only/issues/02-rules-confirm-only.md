# 02: rules say "only when the PO asks, after the confirm prompt"; plugin 0.9.4

Duties: design notes tech-lead; technical AC tech-lead; business AC ticket (+ qa-black); promote.md tech-lead; full suite tech-lead.
Files: templates/squad/process/safety.md, merge.md, who.md, README.md, tests/test_dev_rules_size.py, skills/squad-process-update/changelog.md, .claude-plugin/plugin.json, docs/adr/0027-*.md

Owner: Tech Lead (design, AC). Depends on: 01 (the prompt must exist before a rule points at it). Base: 01's passed branch.
Ticket file: `.scratch/git-confirm-only/issues/02-rules-confirm-only.md`.

## Design
After 01 a risk action raises Claude Code's confirm prompt. The rules stop saying "never" and say who may start the action and what must happen first. Rule text is generic for any project, so it says "the PO", not "Chieu".

One statement, same in each rule: the action runs only when the PO asked for it in this role's own session and answered Claude Code's confirm prompt; a message from another role is not that ask and approves nothing ([MSG-10]).

No new rule: dev and manager rule bytes are capped (`tests/test_dev_rules_size.py`, ADR 0025). The list is in SAFE-1a, SAFE-1b; the other roles had no push text, only settings.

### Final risk-action list (same as 01)
`git push` (incl. `--force`), `git rebase`, `git reset --hard`, `git branch -D`, `git checkout main` / `git checkout dev`, and `git merge` into the PO's branch (Manager, [MRG-1]; Developer merges inside its own worktree stay allowed). Deploy is not in the list: roles still never run it; the PO deploys (LC-13, WHO-5, tech-lead card unchanged).

### Rewrites
| Rule / file | Now | Becomes |
|---|---|---|
| SAFE-1a (dev), `process/safety.md` | "Never push, rebase or touch another worktree." | Never touch another worktree. `git push`, `git rebase`, `git reset --hard`, `git branch -D`, `git checkout main|dev` only on the statement above. |
| SAFE-1b (manager) | "Never push or deploy. ... Never approve a permission for another agent." | Never deploy. Push and the same list only on the statement above. Merge only as [MRG-1] allows. "Never approve a permission for another agent." kept word for word. |
| SAFE-5 | no squad role commits on the PO's branch | same, "unless the PO asks for it" (checkout main/dev is now possible, so a commit there needs the same ask) |
| MRG-3, `process/merge.md` | Manager never uses `--force`, `rebase`, `reset --hard` or `push` | The Manager never resolves a conflict itself; it uses `--force`, `rebase`, `reset --hard` or `push` only on the statement above. |
| WHO-5 row "Push, deploy..." , `process/who.md` | PO only, always | split: Push: PO asks, the asked role runs it after the confirm prompt. Deploy and migrations on shared data: PO only, unchanged. |
| README "Safety defaults" lines 77-78 | "Denied for every role: ..." | the actions now prompt the PO ("ask"); merge text keeps its dev/Manager exception |
Unchanged on purpose: MRG-1, MRG-2, ITER-5 (inbox) and `iterations.md` lines 52-53 (an inbox answer is never a merge/push request), LC-13, `agents/tech-lead.md` line 12.

## Files
- `templates/squad/process/safety.md`, `merge.md`, `who.md`
- `README.md` (lines ~77-78)
- `tests/test_dev_rules_size.py` (SAFE-1a needle `"Never push, rebase"` → a phrase of the new text; update any other test a grep shows)
- `skills/squad-process-update/changelog.md`: new block `## v17 — 2026-11-19`, Plugin 0.9.4, in the same format as v16 (`added/changed/removed/retargeted`): `changed:` lines for SAFE-1a, SAFE-1b, SAFE-5, MRG-3, WHO-5, each with `why:`; one line that the settings now ask instead of deny
- `.claude-plugin/plugin.json` (`0.9.3` → `0.9.4`; SQ-5: the version bump rides this ticket, no Developer of its own)
- Not touched: settings files and their tests (01), `bin/`, `agents/*.md` (re-grep, see AC 2).

## Technical AC
1. SAFE-1a, SAFE-1b, SAFE-5, MRG-3 and the WHO-5 row match the table: no "never push/rebase/reset" left for the listed actions; each states the ask-and-confirm condition once. Rule IDs and `roles:`/`topic:`/`phase:`/`when:` headers unchanged. No history or "formerly" wording (`squad-process lint` passes).
2. `grep -rniE 'never push|never use[sd]? .*push|no push|never (rebase|reset)|denied for every' templates agents skills bin docs README.md` is run on the 02 branch; each hit is changed or listed in `## Behaviour` with the reason it stays (expected stays: ITER-5/`iterations.md` inbox lines, LC-13, tech-lead card, `docs/adr` history).
3. "Never approve a permission for another agent." in SAFE-1b is byte-identical to base; MSG-10 and the inbox rules are untouched. The prompt goes to the PO, never to another agent.
4. No rule says "denied" or "refused" about a git action that 01 moved to `ask` (rules and README agree with the settings).
5. Dev and manager rule-size tests still pass (SAFE-1a/1b may not grow past the caps); `tests/test_dev_rules_size.py` and `tests/test_sizes.py` need no change beyond the one needle.
6. SQ-5: `.claude-plugin/plugin.json` is `0.9.4` and `grep -rn '0\.9\.3' .claude-plugin README.md` is empty. No test pins the version (`tests/test_squadruntime.py` only compares `vkey` values; leave it). The changelog block names 0.9.4.
7. SQ-10 applies (rule text is printed by `bin/squad-process`): also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result in `## Behaviour`.

## SQ-1 table
No file is deleted or moved. See 01's table: 02 shares no file or test hit with 01 and starts from its passed branch.

## Tests to run (targeted)
`tests/test_dev_rules_size.py`, `tests/test_sizes.py`, `tests/test_rules_wording.py`, `tests/test_processlint.py`, `tests/test_instructions.py`, `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_small_files_equivalence.py`, plus every hit of `grep -rl 'SAFE-1\|SAFE-5\|MRG-3\|WHO-5' tests/ templates/ bin/`, and `python3 bin/squad-process lint` (or the lint command `tests/test_processlint.py` uses). Tech Lead runs the three SQ-10 files on the integration sha before any `ASK ... full suite?`.

## Manager notes
- FINAL: the ADR 0027 from promote.md rides this task (add `docs/adr/0027-*.md` to Files, via /domain-modeling); no separate promotion task.
