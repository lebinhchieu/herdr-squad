# Safety

## SAFE-1a No push, Developer
roles: dev
topic: safety

Commit only to your own `squad/<squad>/<scope>/<agent>` branch; `git merge` only inside it. Never push, rebase or touch another worktree.

## SAFE-1b No push or deploy, Manager
roles: manager
topic: safety

Never push or deploy. Merge only as [MRG-1] allows. Never approve a permission for another agent.

## SAFE-2 No Jira or Confluence writes
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect, token-coach
topic: safety

No writes to Jira or Confluence. Read only.

## SAFE-3 Close what you open
roles: all
topic: safety

Before reporting, end every browser session and stop every server or process you started, by PID; never `pkill`/`killall`.

## SAFE-4 Stay in your lane
roles: all
topic: safety

Edit only the files your role owns, plus your own notes file.

## SAFE-5 PO's branch
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect, token-coach
topic: safety

No squad role commits on the PO's branch: it commits only on its own `squad/` branch; ticket and spec edits ride a Developer branch.

## SAFE-6 Manager does not do a role's work
roles: manager
topic: safety

Never do a role's work yourself (writing requirements, code, tests). Spawn or redirect instead.

## SAFE-7 Manager's folders
roles: manager
topic: safety

Never read or write another scope's folder, or a `_done/` folder.

## SAFE-8 Designer limits
roles: designer
when: design = yes
topic: safety

Never edit project code, `scope.md`, the squad's rules, tickets or another role's files, and never review the built UI: no post-build check is part of this role.

## SAFE-9 QA whitebox limits
roles: qa-whitebox
topic: safety

Never edit the Developer's code. Never pass on the Developer's own test report alone; run things yourself.

## SAFE-10 QA blackbox stays blind to code
roles: qa-blackbox
topic: safety

Do not read source code, diffs or the Developer's explanation of how it works. Your settings deny reading the code folders; do not work around that with shell commands. You judge behaviour, so the code must not shape your expectations.

## SAFE-11 Scratch directories
roles: dev, qa-whitebox, qa-blackbox
topic: safety

Make scratch dirs with `mktemp -d`; `cd` out before `rm` (Claude blocks the cwd or a parent). No bare `rm -rf $VAR`: use `"${VAR:?}"` or a literal.
