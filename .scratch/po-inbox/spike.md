# Spikes S3 and S5 (PI-04, plugin-dev-po-inbox-2, 2026-10-15, live: claude 2.1.300, haiku, terminal, herdr pane, mod loaded with --plugin-dir)

## S3: can a `ui.render` hook replace a Bash row? Outcome A.
- Setup: Manager env, `squad-inbox` stub on PATH, prompt "run exactly this command": `squad-inbox add --kind read --title "…" --blocks PI-04 --body-file - <<'EOF' … EOF`.
- **Normal view:** Bash calls are folded into a `ToolGroup` ("Ran 1 shell command"), no `ToolUse` row. A `ToolGroup` hook whose calls are all collapsed adds draws one line per call: `→ inbox: <title>`.
- **ctrl+o (expanded) view:** a `ToolUse` hook draws `→ inbox: <title>`; the heredoc body, options and recommendation appear nowhere.
- **ToolResult:** a hook that returns an empty `Box` for a matched, successful call hides the CLI's own stdout line (`1 new item in the inbox: …`). Only the pointer line is shown. An errored result stays (`isErrored` goes to `next`).
- ToolResult has no `input`, so the mod remembers `tool_use_id` of matched calls (set in the ToolUse/ToolGroup hook). After a reload the set starts empty: a result shows its line once (safe side).
- Retroactive: after a hot reload the earlier rows redraw with the new hook.

## S5: `Input` in the pane. Both good.
- Typing `b` in the note `Input` types `b` (no hotkey fires; the answer screen has no letter hotkeys anyway).
- A bracketed paste with a newline keeps it: field showed both lines; submit sent `bPASTE one\nPASTE two` on the CLI's stdin. So multi-line answers work; no "long answers go to chat" fallback needed.
- Other live facts: the pane (inline) is only about 12 rows tall, so a form below a 12-line body needs Tab to reach it; Tab moves the pane to the focused element.
