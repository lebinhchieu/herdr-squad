# Ticket 08: check the unverified Windows items

## Behaviour

| Item | Check | Seen | Result |
|---|---|---|---|
| 1 Hook shell | `claude -p` with a throwaway `--plugin-dir` hook: `PreToolUse` on `Bash`, command `"${CLAUDE_PLUGIN_ROOT}/bin/probe"`, no `shell:` key; the probe writes `$0`, `$SHELL`, `$BASH_VERSION`. Primary shell was PowerShell. | `0=C:/…/plug/bin/probe`, `SHELL=/bin/bash.exe`, `BASH_VERSION=5.3.15(2)-release` (file: `hook-probe-out.txt`) | cleared: hooks run under Git Bash |
| 2 Path forms | grep `[[ ]]` and `case` in `bin/squad-*` | Only `readlink -f` vs `readlink -f` (`squad-spawn:123`, `squad-respawn:36`) and `basename` (`squad-close:43`). No cross-form comparison. | cleared |
| 3 cwd case | Temp `CLAUDE_CONFIG_DIR` with `…-Workspace-p` and `…-workspace-p--worktrees-s-a-dev-1`; call `agent_sessions('dev-1', <roster transcript>)` | Both transcripts returned. `base` comes from the found transcript's dir, and the worktree glob is case-insensitive on Windows. | cleared |
| 4 Parallel start | 30 rounds × 10 parallel `bash -c true`, plus 6 loops × 60 starts running at the same time | 0 bytes of stderr, 0 non-zero exits, no `add_item` | not reproduced; no guard added |
| 5 Long paths | `git ls-files` on main | 0 files under `.claude/`; longest path 93 chars | cleared |

Only `.scratch/windows-native/findings.md` changed (W8 to W11 and a long-path line). No code change; Linux is unaffected. No test added (no behaviour changed).

Cleanup: temp plugin dir and temp config dir removed; no process left running.

## Review

A fresh sonnet reviewer checked the diff against the code. Fixes made:
- W8 pointed to an evidence file that was not committed: now committed at `.scratch/windows-native/issues/08-verify-unverified-windows-items/`.
- W10 wording: it rests on the case-insensitive glob on Windows (it would not hold on a case-sensitive filesystem), and the real case exists (`…-Workspace-Guardian---Learn` Manager next to `…-workspace-Guardian---Learn--worktrees-…`). Reviewer re-ran `projects_glob` and `Path.glob` on those real folders and got the same sets.
- W9: `readlink -f` does not fix case; a case-only difference makes the runtime guard say "different" but the next run matches, so there is no loop. Noted.
- Long paths: the check covers the cache path only, not `_runtime/` under a deep project root. Noted.
