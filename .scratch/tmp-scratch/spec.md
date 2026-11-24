# Scratch without permission prompts

Status: ready-for-agent

## Problem
Squad agents hit permission prompts when they work in `/tmp`, although every role allows `/tmp` (`additionalDirectories`, `Read`/`Edit`/`Write(//tmp/**)`, `rm /tmp/*`). Transcripts from 2026-11-15 to 2026-11-25 show two causes that allow rules cannot reach:

| Cause | Hits | Example |
|---|---|---|
| Claude Code's built-in dangerous-rm check | 45 | `rm -rf $(cat /tmp/qaw_dir)` |
| `rtk hook claude` rewrites a command after auto mode reviewed it ("no verdict") | 332 (25 on /tmp) | `cd /tmp/x && grep ...` |

SAFE-11/11b ("literal path, run rm alone") has been tightened three times and is still broken; `safety.md` even recommends `rm -rf "$D"`, which the check blocks.

## Design
```diagram
squad-spawn: squad-tmp make <agent>
▼
pane env: TMPDIR=SQUAD_TMP=/tmp/squad-<uid>/<agent>
▼
CLAUDE_CODE_TMPDIR pinned (task dir stays)
▼
agent: mktemp -d lands in its scratch dir
▼
agent never runs rm on scratch
▼
squad-retire: squad-tmp clean <agent>
```

- Claude Code moves its own task dir to `$TMPDIR/claude-<uid>` when `TMPDIR` is set (checked 2026-11-25 on 2.1.331); `CLAUDE_CODE_TMPDIR` pins it back, so `hooks/herdr-bg` keeps working.
- A respawn keeps the dir (same agent name); a retire or close deletes it.

## Tickets
01 scratch dir per agent; 02 tools delete it; 03 SAFE-11 rewrite; 04 `squad-tmp rm`; 05 no rtk hook in role settings.
