# 30 A file click opens it in VS Code
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO, E10).
Design: `ui-design/design-v7.md` s6 (final): the click target changes, plus a status line after a click and the "cannot be opened" row text.
Status: ready-for-agent
Iteration: 2
Blocked by: 29 (folder rows and ticket rows must exist), 28 (the "Where" link); the PO's yes on O1 for AC6 only, and on O2 (ticket 29) for the folder-row link AC3
Feature: 8 (`tasks/features.md`, ticket 14); PO iteration 2, request 2

## What the PO gets
Clicking a file (or a folder) on the board opens it in VS Code, where he works, not in a new browser tab.

## Rules
- Every file or folder link on the board uses the form `vscode://file/<absolute path>` (the PO's words). It replaces "opens a new tab" of T14.AC2 for the Files panel, and applies to: Files rows (files and the two folder rows of ticket 29), the "Where" link in Tasks (ticket 28), and any other place that links a file today. No link opens a browser tab (`target=_blank` removed).
- The path is the real absolute path of the file on the machine where the board server runs (the `path` of the row). The page builds a link only for a path the board lists; a path outside the squad folder and `.scratch` never gets a link (T14.AC3 stays true).
- The board does not open VS Code itself: the click hands the link to the browser, which hands it to the system. The board stays read-only.
- Spaces and special characters in a path are percent-encoded in the link; `/` stays.
- **After a click** (design-v7 s6, replaces my earlier "tooltip only, no copy button"; the Designer added it): a status line at the top of the Files panel body, `Sent to VS Code: <path>`, with a `Copy path` button; it stays 8 s, then goes away (`role=status`). If nothing opens VS Code (not installed, blocked by the browser), nothing else appears: no error page, no error message, and the page and its state stay as they were. The tooltip on every file link shows the full absolute path and `opens in VS Code`. The "Where" column shows the path as text (folder part muted, file name bold).
- Any row of the Files panel (file, folder, ticket row; markdown and HTML rows too) is the link; the browser reader of v5 is no longer used from the page.
- **Places that link a file today** (checked in the code at 584720f): only the Files panel rows (`panel_files.js`: a link with `target=_blank`, plus a click handler that opens a new window and draws markdown). Both go. New places: the folder rows (29) and the Tasks "Where" link (28). Inbox, parked questions and task detail show no file link today; if the Dev finds another, it takes the same link function.
- **Open point O1 (WSL).** This board runs in WSL (WSL_DISTRO_NAME=Debian here). A browser on Windows given `vscode://file//home/...` looks for that path on Windows and may not find it. VS Code opens WSL files with `vscode://vscode-remote/wsl+<distro>/<abs path>`. **BA proposal:** when the server runs in WSL (the variable is set) the link uses the `vscode-remote/wsl+<distro>` form; otherwise `vscode://file/<abs>`. Needs the PO's yes through the Manager (this is a change of his wording). Until answered, build the `vscode://file/<abs>` form behind one function so the form is one line to change. AC T30.AC6 depends on the answer.
- `/api/file` (the browser view of a file) stays in the server for now; the page no longer links to it. T14.AC6 (sandboxed HTML) stays true for the route.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T30.AC1** Given a markdown file row in Files, then its link target equals what the board's one link function gives for the row's absolute path (AC6: `vscode://file/<path>` when the board does not run in WSL; the WSL form when it does and the PO agreed), and a click opens no new browser tab (the number of tabs does not change). QA blackbox runs the board twice, with `WSL_DISTRO_NAME` unset and set, and checks both forms.
- **T30.AC2** Given an HTML file row (a prototype or report) in Files, then the same link rule (AC1), no tab, and the old new-window markdown view does not open.
- **T30.AC3** Given a folder row (`.scratch`, squad folder), then its link is what the link function gives for the absolute folder path (AC1 rule).
- **T30.AC4** Given the "Where" link of a task in the Tasks panel, then the link is what the link function gives for that task file's absolute path (AC1 rule), no tab.
- **T30.AC5** Given a file named `my file.md` and one named `đề-bài.md`, then each link carries the path UTF-8 percent-encoded per segment (`my%20file.md`, `%C4%91%E1%BB%81-b%C3%A0i.md`), `/` stays, and decoding the link gives the row's path back.
- **T30.AC6** Given the board runs in WSL — **pending the PO's answer to O1** — then the link is `vscode://vscode-remote/wsl+<distro>/<absolute path>`; given it does not run in WSL, then `vscode://file/<abs>`.
- **T30.AC7** Given a symlink inside the squad folder that points to a file outside the squad folder and `.scratch`, then its row has no link, is muted plain text, and its What cell reads `cannot be opened: outside the squad folders` (design-v7 s6; T14.AC3); and the link function is never given a path with `..`.
- **T30.AC8** Given a session of clicks on file links, then the hash of every file under the squad folder and `.scratch` is the same before and after, except `board-ui.json` (T03.AC11); (no new server route: QA whitebox).
- **T30.AC9** Given the mouse is over a file link, then the tooltip shows the full absolute path and `opens in VS Code`.
- **T30.AC10** Given every page, panel and state of the board, then no link and no script opens a new tab for a file (no `target="_blank"` file link, no `window.open` for a file), and every file or folder link is in the form of AC1.
- **T30.AC11** Given a click on the Tasks "Where" link (AC4), or a click when the Files panel is hidden, then the link is handed to the browser as in AC1 and no status line shows anywhere (the tooltip is the hint there); given a click that opens nothing (VS Code not installed), then the board page and its state (panel layout, scroll, choice) are unchanged, no error page or error message appears, and the only addition is the status line of AC12.
- **T30.AC12** The status line shows in the Files panel only (design-v7 s6). Given a click on a file, folder or ticket row of the Files panel, then a status line `Sent to VS Code: <the row's absolute path>` with a `Copy path` button appears at the top of the Files panel body, has `role=status`, and is gone after 8 s (within 1 s); given a second click within 8 s, the line shows the new path. Given a click on `Copy path`, then the clipboard holds that absolute path.
- **T30.AC13** Given a folder row, then the File cell shows the folder name as a link and, under it, the full absolute path in small muted text (visible when the other columns are hidden: T29.AC7); given the Tasks "Where" cell, then it shows the repo-relative path as text and the link (underline) opens the absolute path.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: agreed (PASS AC 25-30, 2026-11-04; T30.AC6 waits on the PO's O1; `tasks/business-ac-agreement.md`). T30.AC6 pending O1. QA blackbox cannot launch VS Code in a test browser: it checks the link target and "no new tab".

## Fixtures
In the fixture squad: `my file.md`, `đề-bài.md` in the scope folder, and a symlink in the squad folder pointing to a file outside the squad folder and `.scratch`. The board started twice, with `WSL_DISTRO_NAME` unset and set.

## Touched files
Tech Lead (`tasks/issues-tech/30.md`): `templates/board/panel_files.js`, `bin/squadboard_files.py` (each row gets `abs`; the data gets `wsl_distro`); not `board.js`; runs after 29. One link function (the WSL form is one line to change); tests in `tests/test_squadboard_panels.py` (link target, no `target=_blank`, status line).

## Comments
- BA 2026-11-04: T14.AC2 (new tab, markdown readable) and the "opens in a new tab" Rule of ticket 14 are replaced by this ticket. The BA marks ticket 14 with a pointer.
