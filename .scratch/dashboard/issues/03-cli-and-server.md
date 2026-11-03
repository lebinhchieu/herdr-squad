# 03 cli and server
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 01
Feature: 6, G3, G4 (`tasks/features.md`)

## What the PO gets
Open the dashboard from the command line, local only, read-only, one choice at a time.

## Rules
- `squad-board [--squad NAME|PATH] [--goal G | --scope S] [--port N] [--no-open]`, plus `--help` listing every flag. Browser opens by default; `--no-open` prints the URL and starts no browser.
- Server on 127.0.0.1 only. The page reads squad files and writes only `board-ui.json`. Command text on the page is copy-only; no label implies a write to squad data (answer, park, merge).
- One squad here = that one; several and none named = refuse and list; `--squad` repeatable; a path to a squad in another repo works; other repos are never scanned. A switch between squads shows in the header only when more than one squad was given. A flat squad shows "flat squad: not supported".
- `squad-start` prints the command and does not open the board.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T03.AC1** Given one squad, when the PO runs `squad-board`, then the browser opens on 127.0.0.1 and shows the picker (or the saved choice).
- **T03.AC2** Given `--no-open`, then no browser starts and the URL is printed. Given `--port N`, then the page answers on N. Given N is busy, then a clear message and a non-zero exit, no crash.
- **T03.AC3** Given several squads and no `--squad`, then the command refuses, lists them and exits non-zero.
- **T03.AC4** Given an unknown squad, goal or scope name, then the known names are listed, the exit code is non-zero, and no process listens on the port.
- **T03.AC5** Given `--goal G --scope S` together, then the exit code is non-zero, the message names both flags, and no process listens on the port.
- **T03.AC6** Given `--squad <path in another repo>`, then that squad opens; given the fixture has other squads not named, then none of them appears (no scan).
- **T03.AC7** Given two `--squad` values, then the header has a squad switch; given one, then no switch.
- **T03.AC8** Given a flat squad, then "flat squad: not supported".
- **T03.AC9** Given `--help`, then every flag above is listed.
- **T03.AC10** Given the board runs, when a client asks on the machine's LAN address, then it gets no answer; on 127.0.0.1 it answers. Given a request with a wrong Host header, then it is refused.
- **T03.AC11** Given a session that opens, switches choice, moves and resizes panels, changes font size and opens every task, when a hash of the squad folder is compared before and after, then only `board-ui.json` changed.
- **T03.AC12** Given `squad-start` runs, then it prints the `squad-board` command and does not start the board.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M1.
- New: `bin/squad-board`, `bin/squadboard.py`.
- Edit: `bin/squad-start` (print the command only), `README.md`.
- Tests (new): `tests/test_squadboard_server.py` (400 without selection, Host check, token, file route allow-list, CSP, port busy, exit codes).
- Test harness: `tests/inproc.py`; fixture from ticket 02. Readers are discovered, not listed: `squadboard.py` loads every `bin/squadboard_*.py` that defines `ROUTE = {...}` (name, path, `read`). A later ticket adds its own file and never edits `squadboard.py` (the only exceptions: 09 for `PUT /api/ui`). This keeps parallel branches free of merge conflicts.

## Comments
