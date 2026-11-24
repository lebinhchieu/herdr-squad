# 07: Colours and styles in the /squads pane

Status: ready-for-agent
Type: task
Blocked by: none (03 is merged to main as b888cbb)
Touches: `.claude-plugin/plugin.json`, `skills/squad-process-update/changelog.md`, `tests/test_squadruntime.py` (version string), `hooks/squads/ui.tsx` (and `hooks/squads/core.ts` only if a state-to-tone table belongs there), its tests, `hooks/squads/pane-text` if it needs a styles output
Read first: `ui-design/squads-mod.md` (Colours line, Screens 1-2), `ui-design/squads-mod.html` (classes `.c-need .c-work .c-stuck .c-done .c-idle .c-blue .c-warn`, the `statusOf` function near line 180), `hooks/po-inbox/draw.tsx` and `hooks/po-inbox/core.ts` (TONE, ACCENT, QUIET theme keys, chips)

## Why
Chieu: the pane is boring, no styles or colours like the prototype. Cause: `hooks/squads/ui.tsx` draws each row as one plain string and uses only bold, dim, `error` and `warning`. T2.6b let tests ignore colour, `pane-text` prints plain text, so no check ever saw it.

## Do
Draw the pane with the prototype's meaning, using theme keys as po-inbox does (never hex): needs you = warning/accent, bold; stuck = error, bold; working = a calm key; done/closed = success; idle and facts = dim; command text = an accent key; "Not yet" = warning; destructive change word = error. Colour the symbol and state word, `needs N` and `stuck N`, the next step by state, and the command text. Selected row visible. Colour is never the only signal (words stay). Control characters in names still never reach the screen (AC5.5).

## AC
- AC7.1 Each row state (needs you, stuck, working, nobody working, all done, closed, unreadable) has its own tone, as in the prototype; a state shows the same tone in list and detail.
- AC7.2 Detail: state header bold with its tone; "Commands" heading bold; command text in the accent; the change word (read, writes, destructive) has a tone; "Not yet" in warning.
- AC7.3 Only theme keys, no hex. Text content, widths and keys of the pane are unchanged (existing tests pass).
- AC7.4 Evidence: a way to see the styles, not only text: a real screenshot of the pane (list and detail) from the mod running, or a dump that prints each run's style next to its text. QA blackbox compares it to the prototype state by state.
- AC7.5 (SQ-5, last plugin-file ticket) Version 0.9.0 becomes 0.9.1 in plugin.json, changelog entry, and the test that names it; `grep -rl '0\.9\.0'` over those files finds no stale hit.
