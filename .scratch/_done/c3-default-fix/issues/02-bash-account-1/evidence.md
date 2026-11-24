## Behaviour
No repo code changed. No repo-owned bash startup path exports `CLAUDE_CONFIG_DIR` for 2/3 without an unset for 1 (grep and classification: the design note in `../02-bash-account-1.md`).

For the PO: if `~/.bashrc` has only cases 2 and 3, add the unset. This is the line the repo already tests (`BashrcLineTest`, passes):

    d=$("$HOME/.claude-accounts/bin/cdefault" 2>/dev/null)
    case "$d" in 2|3) export CLAUDE_CONFIG_DIR="$HOME/.claude-$d" ;; *) unset CLAUDE_CONFIG_DIR ;; esac; unset d

Use `unset`, never `export CLAUDE_CONFIG_DIR=` (empty) and never `~/.claude`. Nothing outside the repo was edited or run.
