# Evidence 27: Work time filter block restyle

## Behaviour
Only the `CSS` array of `templates/board/timeline.js` changed (no hex colour, tokens only), plus one DOM move in `toolbar()`: the gap select and `Show real time` now sit in the range line (right side), as design-v7 s4 says; the `.tl-rng` error text is in `<span class="err">` (`--err`). Handlers, ids and `dataset` are the same.
- Block: `--panel2`, 1 px `--border`, radius 8 px, padding .75em, sticky, opaque.
- Chips: height 2.2em, padding .85em, `--bg` / `--border` / `--ink`, hover border `--ink`; active chip `--t-need`, `--mango`, bold.
- Row label: muted small caps in a 3.4em column; a wrapped row hangs under the chips.
- Range line: dashed `--border` rule above; `· loading` muted, `· could not load this range` `--err`.
Test: `tests/test_squadboard_timeline.py` `Safety.test_T27_filter_block_look_active_chip_sticky_opaque_no_percent` (computed style in headless Chrome). Run with test_squadboard_timeline, test_squadboard_page, test_squadreport_ui: 76 ok.

## AC table
| Item | Shown by |
|---|---|
| T27.AC1 / TA2 block bg, border, radius | timeline.js `.tl-bar` rule; the T27 test (bg = resolved --panel2, 1px, 8px) |
| T27.AC2 padding >= 8 px, text >= 6 px | T27 test (padding), chip `padding:0 .85em` |
| T27.AC3 two rows on one line, 8 px gaps | `.tl-r` `gap:.67em`, rows built in `toolbar()` (Task row, View row); one-line at 1440 and wrap at 1000 / Extra large: QA blackbox look check (open: not in my test) |
| T27.AC4 active chip, focus ring | `.tc.on` rule; T27 test (on/off colours, weight); focus ring is the page rule (unchanged) |
| T27.AC5 / TA1 tokens only | `grep -nE "#[0-9a-fA-F]{3,8}\b\|rgba?\(" templates/board/timeline.js`: no hit; T27 test resolves tokens |
| T27.AC6 / TA5 behaviour unchanged | test_squadboard_timeline (all pass, none edited) |
| T27.AC7 states | loading/error text in `toolbar()` r3; look of each state: QA blackbox |
| T27.AC8 hover, tooltips | `.tc:hover` rule; T27 test (tips Zoom out, Zoom in, Earlier, Later) |
| T27.AC9 / TA4 sticky, opaque | T27 test (position sticky, top 0, solid --panel2); scrolling behaviour not tested separately |
| T27.AC10 / TA7 no `%` | T27 test (`textContent` of the block) |
| Design s4 Real time chip in range line | timeline.js `toolbar()` `r3.appendChild(g)`; T27 test (`.tl-rng button[data-real]`) |

## Open gaps
- T27.AC3 at 1000 px / Extra large and T27.TA3 three-size test: not automated; QA blackbox checks the look.
