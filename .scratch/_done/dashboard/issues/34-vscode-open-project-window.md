# 34 A file click shows the file in the VS Code window of the project
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO wish).
Design: no new screen. The status line of `ui-design/design-v7.md` s6 stays as it is (ticket 30).
Status: ready-for-agent
Iteration: 3
Blocked by: BA AC (this file); the Tech Lead's spike result (see "Spike first")
Feature: PO iteration 3, request 2 (`tasks/po-request-iter3.md`)

## What the PO gets
He clicks a file on the board and it appears as a tab in the VS Code window that has his project open, even when he has several VS Code windows. Today the click goes to the last active window, which reopens or reloads there.

## Spike first (Tech Lead)
A `vscode://` link cannot choose a window. The Tech Lead proves, before any build, which call (a server route that runs the `code` command is the plan) shows a file in the window that has the project open, in WSL (and Windows if reachable). The spike result goes into this file under `## Spike result`: the exact call, what it does with one window, with several, with none, and with VS Code not running. `code` is not on PATH in the WSL shell of the BA (checked 2026-11-04), so the spike may need a path to the Windows `code`. **If the spike fails, the Tech Lead tells the Manager with options; the AC below are not changed by a failed spike, the PO decides.**
The AC below are mechanism-neutral. `## Spike result` must also name (a) the calls of one open action (there may be more than one, for example one to bring the window forward and one to open the file), and (b) the visible way a test points the board to a stub: an environment variable the board reads before PATH (BA proposal: `SQUAD_BOARD_CODE`), because in WSL the real call may need a fixed path to the Windows `code`. Without (b) AC1 to AC9 cannot be run. They split in two layers:
- **Board side** (QA blackbox, no real VS Code): a stub `code` (pointed to as in (b)) records every call (arguments, exit code and delay set by variables) to a log file. QA reads the page's own request after a click (path, token) and replays it with changes.
- **PO live check** (`[PO live]`): needs real VS Code windows; no test browser can see them. The Developer or Tech Lead records the check on a machine with VS Code (screen recording or step list) in `evidence.md`; the PO confirms. QA blackbox marks these AC `PO live` in its report, not PASS or FAIL by itself.

## Rules
- **The project window.** "The window that has the project open" = the VS Code window whose folder is the repo that holds the clicked file (the repo of the file's path, not the repo the board was started from). In the fixture `repo/` and `repo2/` are two repos: a file of `repo2/` goes to the window of `repo2/`.
- **Several windows.** Only the project window gets the file and comes to the front. Every other window is unchanged (same folder, same tabs).
- **No window has the project open.** The file shows in the last active window, as the PO said ("just show the file in the active instance"). No new window opens and no window is reloaded. This is not an open point.
- **VS Code not running.** VS Code starts and shows the file in one window.
- **No reopen.** The target window keeps its folder and its open tabs. It does not reload, does not ask to trust a folder, does not reopen the last workspace. The file is added as a tab and is the active tab.
- **File already open** in that window: its tab is activated; no second tab.
- **Link kept.** The `href` of every file link stays the ticket-30 form (`vscode://file/<abs>` or the WSL form), for right-click copy and as the fallback. A normal left click is handled by the board first: the page asks the board server to run the open call. The status line `Sent to VS Code: <path>` and `Copy path` (T30.AC12) show as before, in the Files panel only.
- **If the call fails** (no `code` found, exits with an error, times out): the page falls back to the `href` link (what ticket 30 did). The page and its state stay as they were, no error page and no error message (T30.AC11). This is the BA's choice; the Tech Lead may propose another with a reason.
- **Security floor.** The route runs only for a path the board lists (the T14.AC3 / T30.AC7 rule); never a path with `..`; never a path outside the squad folders and `.scratch`; needs the page's token (T09.AC5); accepts requests from the local page only (T03); runs a fixed command with no shell; a path that starts with `-` is never read as an option. A refused path runs no command.
- **Read-only.** The board still writes no file but `board-ui.json` (T03.AC11). Starting VS Code is not a file write.
- **Same on every click place**: Files rows (files, folders, ticket rows), the Tasks "Where" link, any other file link (one function).
- **Only a plain left click uses the route.** Ctrl-click, middle click, Shift-click and right click do what the `href` does (as ticket 30).
- **No double open.** When the route's call worked, the page does not also follow the `vscode://` link. The link is followed only in the fallback (T34.AC9a-c).
- **Which repo.** The repo of a file = the main working tree of the git repository that holds it (a Developer worktree counts as its main repo, never as its own project). A file in no git repo (for example a squad folder of a scope with no repo) uses the main repo of the board's squad; if that has none, it goes to the last active window. A folder row (`.scratch`, the squad folder) is sent so that the project window comes to the front and keeps its folder (T34.AC15); if the spike finds no safe call for a folder, folder rows make no route call and keep the `href` (the Tech Lead says so in `## Spike result`).
- **Timeout.** The route call has a timeout of 5 s (the Tech Lead may change it with a reason); after it the page falls back within 1 s.
- **Closing.** 34 closes when both QAs pass AC1-AC9 and AC16 and the Developer's `evidence.md` holds the `PO live` record for AC10-AC15; the PO confirms the `PO live` AC later (Manager FINAL asked).

## Earlier AC: what changes (ticket 30)
| Earlier AC | Now |
|---|---|
| T30.AC1-4, AC5, AC6, AC7, AC9, AC13 | Still true: they check the `href` and the row text. |
| T30.AC10 | Still true for the `href`. A left click now also goes through the board route (T34.AC1); still no new tab, no `window.open`. |
| T30.AC11 | Changed: "the link is handed to the browser" is true only in the fallback (T34.AC9). In the normal case the board route is called first. The rest (no status line for a Where click or hidden Files; page unchanged when nothing opens) still holds. |
| T30.AC8 | Changed: "no new server route" no longer holds; the hash check (no file changed but `board-ui.json`) still holds, and T34.AC6 adds the route's limits. |
| T30.AC12 | Still true. |
Ticket 30's rule "the board does not open VS Code itself" is replaced by this ticket.

## Business AC (one Given / When / Then each; a FAIL names one id). Window: 1440 x 900, Normal text, for the one screen check (AC8).
- **T34.AC1** [board side] Given the fixture board with a stub `code`, when the PO left-clicks a markdown file row in the Files panel, then the stub log shows one open action: exactly the call(s) `## Spike result` lists, once; the browser opens no new tab and does not navigate to a `vscode://` link; and the status line `Sent to VS Code: <path>` shows (T30.AC12).
- **T34.AC2** [board side] Given a click on an HTML row, a ticket row, a folder row and the Tasks "Where" link, then each gives one open action with that row's absolute path (the folder rows with the folder path; as `## Spike result` says for folders), and the Where click shows no status line (T30.AC11).
- **T34.AC3** [board side] Given a file of `repo2/` (the second repo in the fixture) and one of `repo/`, when each is clicked, then the stub call names the folder of its own repo each time (the repo that holds the file, not the repo the board started from).
- **T34.AC4** [board side] Given a file named `my file.md` and one named `đề-bài.md`, when each is clicked, then the stub call carries the real path (spaces and non-ASCII intact, not percent-encoded), and a symlink row that points outside the squad folders has no click and no call (T30.AC7).
- **T34.AC5** [board side] Given a click on `Copy path` (T30.AC12), then no stub call happens. Given two clicks on the same file, then two open actions (VS Code activates the existing tab, T34.AC13). Given Ctrl-click, middle click or right click on a file link, then no stub call happens and the link does what its `href` does.
- **T34.AC6** [board side, security] Given requests made directly to the open route, (a) a path outside the squad folders and `.scratch`, (b) a path with `..`, (c) no page token, (d) a wrong Host or non-local origin, (e) a path whose name starts with `-`, (f) a path the board does not list, then each is refused, the stub log has no new call, and the hash of every file under the squad folder and `.scratch` is unchanged except `board-ui.json`.
- **T34.AC7** [board side] Given a session of 20 clicks over several rows, then the hash of every file under the squad folder and `.scratch` is the same before and after, except `board-ui.json` (T03.AC11).
- **T34.AC8** [board side] Given the Files panel at 1440 x 900 after a click, then the status line is where design-v7 s6 puts it, and the page layout, scroll position and choice are the same as before the click.
- **T34.AC9a** [board side] Given `code` cannot be found (the stub is not set and not on PATH), when the PO clicks a file, then the page uses the `href` link of ticket 30 (the link target equals T30.AC1/AC6), no error message and no error page appears, and the page state is unchanged.
- **T34.AC9b** [board side] Given the stub exits with an error (exit code 1), when the PO clicks a file, then the same as AC9a.
- **T34.AC9c** [board side] Given the stub waits longer than the timeout (5 s), when the PO clicks a file, then the page uses the `href` link within the timeout + 1 s, and the same as AC9a.
- **T34.AC10** [PO live] Given one VS Code window with the project open, when the PO clicks a file row, then the file shows as a tab in that window, it is the active tab, the window comes to the front, and its folder and other tabs are as before; no second window opens.
- **T34.AC11** [PO live] Given three VS Code windows (the project, another project, and an empty window) where the last active window is not the project's, when the PO clicks a file row, then the file shows in the project's window only; the other two windows have the same tabs as before.
- **T34.AC12** [PO live] Given no window has the project open and a different project's window was last active, then the file shows in that last active window; no new window opens and nothing reloads. Given VS Code is not running, then VS Code starts and shows the file in one window.
- **T34.AC13** [PO live] Given the file is already open in the project's window, when it is clicked, then that tab is activated and no second tab opens.
- **T34.AC14** [PO live] Given the click in AC10 to AC13, then the window does not reload, ask to trust a folder, or reopen the last workspace.
- **T34.AC15** [PO live] Given a click on a folder row (`.scratch`, the squad folder) with the project open in a window and other windows open, then the project window comes to the front, keeps its folder and tabs, no second window opens and nothing reloads (or, if `## Spike result` says folder rows make no call, the click does what the `href` does and no VS Code window changes its folder).
- **T34.AC16** [board side] Given a file in no git repo (a scope folder of the fixture with no repo) and a file under a Developer worktree of `repo/`, when each is clicked, then the stub call names the board's squad repo for the first and the main repo `repo/` (not the worktree folder) for the second; if there is no repo at all the call asks for the last active window.

## Agreement (REV-8)
BA: written 2026-11-04. Answers to QA blackbox M1-M7 and S1-S3 applied 2026-11-04 (`tasks/ac-review-qa-black-iter3.md`). QA blackbox: pending final confirmation (`tasks/business-ac-agreement.md`, section "Iteration 3"). QA blackbox cannot see real VS Code windows: AC10-AC15 are `PO live`.

## Fixtures
The fixture squad with two repos (`repo/`, `repo2/`), the files of ticket 30 (`my file.md`, `đề-bài.md`, the symlink outside the folders), and a stub `code` (a script that appends its arguments to a log file, optional exit code and delay by environment variable). The Developer adds the stub to the test helpers; QA blackbox puts it first on PATH.

## Touched files
Tech Lead: see `tasks/issues-tech/34.md` (the Manager's plan decides). The route is a new server route (`architecture.md` is touched: the Tech Lead tells the Architect role's owner if it changes a boundary).

## Comments
- BA 2026-11-04: window = repo of the clicked file is my reading of "the instance that has the running project open". It matters for the fixture's second repo. The PO may correct it.
- BA 2026-11-04: I wrote the no-window case from the PO's words (active instance), so it is not escalated.
