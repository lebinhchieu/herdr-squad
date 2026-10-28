# 14 Remove QA blackbox Read deny; stop `rm /tmp` prompts

Status: ready-for-agent
Type: task
Blocked by: 08
Design task: PO decision E5, draft in `$SCOPE_DIR/tasks/e5-ticket-draft.md` (full text of both parts and Done-when). Tech Lead reviews the matcher syntax.

## What
Part 1: drop the code-path Read deny (`templates/squad/settings/qa-blackbox.json`, `bin/squadsettings.py` PLACEHOLDER/`expand_code_paths`/`codePaths`, `squad-init` stops asking; `*.local.json` with `codePaths` ignored or stripped, never fails). SAFE-10 stays a rule, text says it is no longer enforced by a deny.
Part 2: allow `rm`/`rmdir` of `/tmp/tmp.*` only in the dev, qa-whitebox, qa-blackbox (and manager, tech-lead, team-lead) settings templates; check exact matcher syntax against Claude Code docs and test live (`rm` of a `mktemp -d` dir no prompt, `rm -rf /tmp/other` still prompts). SAFE-11: scratch dirs come from `mktemp -d` only; one line.

## Files you touch
`templates/squad/settings/*.json`, `bin/squadsettings.py`, `SETTINGS-NOTES.md`, `templates/squad/process/safety.md` (SAFE-10, SAFE-11; ticket 08 touches this file, hence the dependency), changelog v9 (D8), tests `tests/test_squadsettings.py`, `tests/test_squadadopt.py` and every `grep -rl` hit.

## AC
Per the draft: tests that template settings parse; the allow entries exist for the listed roles; no entry allows `rm` outside `/tmp/tmp.*`; no `codePaths` failure. Global G1-G7, G2b of `$SCOPE_DIR/tasks/tech-design.md` apply. Remove this squad's interim `qa-blackbox.local.json` `codePaths` workaround is the Manager's, after merge.
Before HANDIN: `squad-process lint` (baseline G2b), `grep -rl` of touched paths and run every hit. Tech Lead names the final sha.

Added (TL, from dev 10): add `Bash(squad-team:*)` to the allow list in `templates/squad/settings/manager.json` (squad-team from ticket 10 has none); test the entry exists.

## Comments
