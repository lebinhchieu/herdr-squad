# 07 Board shows a ticket's picture

Status: ready-for-agent

Spec: `.scratch/po-clarity/spec.md`
Blocked by: none
Aim: Files panel previews a ticket, with its picture
Estimate: 3h
Depends on: none

Duties: Design and technical AC: `/home/chieule/workspace/squad/.claude/squads/plugin/scopes/po-clarity/tasks/06-design-notes.md` (the "06b" rows: Design 06b, T06-2, T06-3, T06-5, T06-8, T06-7(b), Ticket 30 reconciliation) with `/home/chieule/workspace/squad/.claude/squads/plugin/scopes/po-clarity/tasks/qaw-technical-ac.md` (as amended). UI: `/home/chieule/workspace/squad/.claude/squads/plugin/scopes/po-clarity/ui-design/07.md` (final). Build `mdBlocks`/`renderMd` (fence word, caption, image), the Preview button on ticket rows of the Files panel with its states, and the image mode of `/api/file` (`img=1&base=`). Reverse the ticket 30 header comment in `panel_files.js`, add the ADR 0020 amendment line, add the test that a row click sends no request. Run the test files the notes list; write `evidence.md` with screenshots; HANDIN to both QAs.
Files: `/home/chieule/workspace/squad/.claude/squads/plugin/scopes/po-clarity/tasks/06-design-notes.md`, `/home/chieule/workspace/squad/.claude/squads/plugin/scopes/po-clarity/ui-design/07.md`, `templates/board/panel_files.js`, `templates/board/board.css`, `bin/squadboard.py`, `docs/adr/0020-dashboard-replaces-removed-board.md`, `tests/test_squadboard_panels.py`, `tests/test_squadboard_server.py`

Design: ui-design/07.md
AC (added, LC-11): built UI matches the design: every screen and state.
No changelog and no version bump (06 owns the changelog entry; 05 owns the bump).

## Problem

The board cannot show a ticket the way it is written. `BOARD.renderMd` has no caller on the page, so a ticket's `diagram` fence, wireframe and images are only readable in VS Code. This is the board part of old ticket 06; the rule and template are ticket 06.

```text
FILES panel, ticket row                      before    after
┌──────────────────────────────┬────────┐
│ 04-plan-panel.md  [ticket]   │ [▸]    │  no Preview   Preview button
└──────────────────────────────┴────────┘
        click [▸]
┌──────────────────────────────────────┐
│ 04 Plan panel         [Open in VS Code]│
│ ┌ diagram · caption ───────────────┐ │
│ │ <pre> keeps its spacing          │ │
│ └──────────────────────────────────┘ │
│ [image from the evidence folder]     │
└──────────────────────────────────────┘
```

## Change

Design: `ui-design/07.md` (final). Technical design: `$SCOPE_DIR/tasks/06-design-notes.md`, the "06b" rows.

1. `mdBlocks`/`renderMd` (`templates/board/panel_files.js`): a fence keeps its word and caption (`{t:"code", s, lang, cap}`); a `diagram` fence gets a caption bar above its `<pre>`; a line that is only `![alt](src)` becomes an image. Text reaches the DOM through `textContent` or `setAttribute` only.
2. A Preview button on Files-panel rows of kind `ticket`; it reads the ticket with the existing `GET /api/file` in the page. A row click still opens VS Code and sends no request. States as in the design.
3. Image mode of `/api/file`: `img=1&base=<evidence folder>` (`bin/squadboard.py`); png, jpg, svg only; the file must stay under `base`, and `base` under the squad folder or `.scratch`; svg is `image/svg+xml` with CSP `sandbox`. Without `img=1` the route is unchanged.
4. Ticket 30 reversal, named: rewrite the header comment of `panel_files.js`, add one line to the ADR 0020 amendments, add `docs/adr/0020-dashboard-replaces-removed-board.md` to the Files line.

No changelog entry and no version bump here (06 writes the entry; 05 bumps).

## AC

- AC1: on the board, a ticket with a `diagram` fence shows the caption above a `<pre>` that keeps the fence's spacing; a `text` fence keeps its spacing; another fence word has no caption bar.
- AC2: `![x](img/a.png)` shows the image from the ticket's evidence folder; `![x](../../etc/passwd)`, an absolute path, a scheme and a wrong extension show the alt text only, and no request goes out.
- AC3: the image route refuses a file outside `base`, a symlink that resolves outside `base`, and a non-image extension; `.svg` in image mode is `image/svg+xml` with CSP `sandbox`; without `img=1` an `.svg` is still `text/html`.
- AC4: `<script>` in alt text or in a caption shows as text and runs nothing.
- AC5: a Files-panel row click sends no request; only the Preview button reads the ticket (ticket 30).
- AC6: built UI matches `ui-design/07.md`: every screen and state.
- AC7: `grep -rl 'renderMd\|mdBlocks' tests/` hits pass, plus `test_squadboard_panels.py` and `test_squadboard_server.py`. The page test drives the Preview on a fixture ticket with a `text` fence, a `diagram` fence with caption and an image.
- AC8: `evidence.md` has screenshots of a Preview with a captioned diagram, an image, and a refused image.

## Comments
