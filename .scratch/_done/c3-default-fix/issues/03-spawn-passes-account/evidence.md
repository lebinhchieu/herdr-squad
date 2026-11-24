## Behaviour
No code change (option b, see the design note in `../03-spawn-passes-account.md`). `squad-spawn` and `squad-respawn` output is byte-identical to base because the files are unchanged (`git diff 574204a -- bin/` is empty). A new pane gets its account from the shell profile (ticket 01).

For the PO: the real check is a new herdr tab in a default-1 workspace, `echo $env:CLAUDE_CONFIG_DIR` prints nothing (`windows/CHECKLIST.md`), after `install.sh --force` copies the fixed profile.
