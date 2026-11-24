# 08: Stripe, hover and command colours in the /squads pane (theme keys)

Status: ready-for-agent
Type: task
Blocked by: none (07 merged to main as 291f4d3)
Touches: `hooks/squads/ui.tsx`, `hooks/squads/core.ts` (COMMAND_STYLE), their tests, `.claude-plugin/plugin.json`, `skills/squad-process-update/changelog.md`, `tests/test_squadruntime.py` (version string)
Read first: `~/workspace/reply-style/hooks/core.ts` (STRIPE, line 42-43, and the "theme keys, never RGB" rule), `~/workspace/reply-style/hooks/draw.tsx` (line 89-112: how a stripe row is padded to full width), `~/workspace/claude-history/themes/mango-parrot.json` (Chieu's theme), `hooks/squads/ui.tsx`, `hooks/po-inbox/core.ts` (ACCENT, TONE)

## Why
Chieu gave three colours from his theme (Mango Parrot) and asked for them by theme key, never by hex, so the pane follows any theme. They match these keys in `mango-parrot.json`:
- `f6efe3` = `bashMessageBackgroundColor` (reply-style's STRIPE).
- `f6d0ad` = `userMessageBackgroundHover`.
- `a85a00` = `ide` (the same key reply-style uses for inline code).

## Do
- Striped rows in the list: every second row has `backgroundColor: 'bashMessageBackgroundColor'`, padded to the full pane width as reply-style does. Say in the plan what "every second row" counts (rows as drawn, groups included or not) and keep it stable while scrolling.
- Hovered row: the row under the mouse gets `backgroundColor: 'userMessageBackgroundHover'`. Check with the `plugin-authoring` skill and the mod types file what hover event or prop the pane API gives (a Button's hover state or an `onMouseEnter`-like prop). If the pane API has no hover, stop and `BLOCKED 08` with the finding; do not fake it.
- Commands in the detail screen: `COMMAND_STYLE` colour becomes `'ide'` (now `ACCENT` = `permission`). Bold is kept if it is bold now.
- Theme keys only; no hex anywhere in `hooks/squads/`.

## AC
- AC8.1 List: every second row uses `bashMessageBackgroundColor`; the others have no background. The selected row is still visible (not only by colour).
- AC8.2 List: the hovered row uses `userMessageBackgroundHover`, and drops it when the mouse leaves.
- AC8.3 Detail: command text uses `ide`.
- AC8.4 `grep -rniE '#[0-9a-f]{6}|rgb\(' hooks/squads/*.ts hooks/squads/*.tsx` has no hit. Existing tests pass; text, widths and keys of the pane are unchanged.
- AC8.5 Evidence: a dump that prints each run's text and style (as ticket 07's evidence does) for the list (stripe and hover) and the detail; if a real screenshot of the mod running is possible, add it.
- AC8.6 (SQ-5, last plugin-file ticket) Version 0.9.1 becomes 0.9.2 in plugin.json, changelog entry, and the test that names it; `grep -rl '0\.9\.1'` over those files finds no stale hit.
