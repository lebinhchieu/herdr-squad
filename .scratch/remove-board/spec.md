Status: ready-for-agent

# Spec: remove the squad board

**One line:** a squad user starts and runs a squad exactly as before, but no board exists: no tab, no URL, no `/squad:squad-board`, no recorder, and no doc, message or test that mentions one as something to use. Source: the PO's brief (`scopes/remove-board/scope.md`) and the five defaults in `iterations/1.md`, accepted by the PO 2026-10-16 (binding). Business AC below; technical AC live in the Tech Lead's task files and tickets.

## Problem

The board (live page, `board` tab, `/squad:squad-board`) is a large part of the plugin: about 20 test files, a 45 KB guide, a launcher, a recorder thread, and instructions in README, CONTEXT.md, two skills and the process template. The PO no longer wants it. A half-removal is worse than none: a `squad-start` that prints `board: null`, a README that links a deleted guide, or a test suite that still imports `squad-board`.

## What the user sees after the removal

| Before | After |
|---|---|
| `squad-start` opens a `board` herdr tab, prints a URL, tells the user to open it | `squad-start` opens the Manager tab only; no board output, no board warning |
| `/squad:squad-board` prints the URL or restarts the board | the command does not exist |
| README has a "Squad board" section, a limit about "one board per workspace", a guide link | none of them |
| CONTEXT.md has a "Squad board" glossary section | gone; the term `Home` stays (still used by the CLIs) |
| `squad-init` says "board logs are ignored" | says "message logs"; `*.jsonl` is still ignored |
| PO inbox says "the board may still list it" | says only that `escalations.md` was not updated |
| ADRs 0001-0004 describe the live board | marked superseded by ADR 0009 "board removed"; not deleted |

## What the PO loses (accepted, stated so nobody is surprised)

- The live cross-home view: bars, per-agent status, the Needs-you list, Jump to panel.
- `squad-inbox` stays: it is the PO's per-home list of what waits on them (ADR 0007). Nothing replaces the cross-home view.
- The Manager's STATUS rule still reads "logs, roster and task file"; it no longer reads a board.

## Kept (do not touch)

- `messages.jsonl` and the `squad-log-message` hook: `squad-migrate` reads it (default 3).
- `activity.jsonl` stays in `squad-migrate`'s carry list: an old squad may hold one, and a migration must not lose a user's file. Nothing writes a new one (BA decision R1).
- `*.jsonl` in the `.gitignore` that `squad-init` writes (messages and usage events hold message text).
- History: `.scratch/squad-board/`, `.scratch/squad-tabs/`, `process-log.md`, the pristine `skills/squad-process-update/history/process-v<N>.md` snapshots (BA decision R2: they exist so a squad's edits can be told from the plugin's text; Tech Lead owns whether the template change is a new version, ADR 0005).
- A board already running on a user's machine is not stopped or cleaned up; nothing in the plugin starts one again (BA decision R3, stated in ADR 0009).

## Business AC

Observable by running the real tools in a scratch squad and reading the user-visible docs; no browser (the board app is gone). IDs are stable; tickets are the Tech Lead's `issues/RB-01..RB-06` (RB-01 decouples tests and `tests/run_suite.py` from the board files and supports R-16); QA blackbox's `evidence/qa-b-plan.md` B-numbers map in the last column.

| ID | Ticket | Given / When / Then | QA-B |
|---|---|---|---|
| R-01 | RB-03 | **Given** the branch, **when** I list `bin/`, `skills/`, `docs/` and `docs/img/`, **then** there is no `squad-board`, `squad-board-start`, `squad-board.html`, `skills/squad-board/`, `docs/squad-board-guide.html` or `docs/img/squad-board-*.png`. | B1 |
| R-02 | RB-02 | **Given** a scratch squad and a stub `claude`, **when** I run `squad-start "<task>" --dry-run` and then a real start, **then** the scope folder is made and the Manager starts as on `main`; the JSON has no `board` key; stdout and stderr do not contain the word board; no `board` tab opens. | B2 |
| R-03 | RB-02 | **Given** the same scratch squad, **when** I run `squad-spawn`, `squad-label`, `squad-close`, `squad-retire`, `squad-respawn`, `squad-notify`, `squad-usage`, `squad-inbox add/list/read/answer` and `squad-process show <role>`, **then** each behaves as on `main` and no output or error text mentions a board. | B3 |
| R-04 | RB-02 | **Given** a flat legacy squad holding `messages.jsonl` (and an `activity.jsonl`), **when** I run `squad-migrate <squad> --to per-scope --scope X`, **then** it succeeds and both files arrive in the new layout. | B4 |
| R-05 | RB-02 | **Given** a `SendMessage` through the hook, **then** `messages.jsonl` gets its row as before. | B5 |
| R-06 | RB-02 | **Given** `squad-label` and `squad-spawn --title`, **then** role labels are exactly as before (`🦀 Manager`, `🤖 Tech Lead · plan`); no board label exists, and a tab titled `board` is treated as any other tab. | B6 |
| R-07 | RB-02 | **Given** an unwritable `escalations.md`, **when** I run `squad-inbox answer`, **then** the CLI says the answer was recorded but the Answer cell was not written, with no mention of a board, and `squad-inbox list --json` is byte-identical to `main`'s for the same input (QA blackbox). **And** the PO inbox mod's notice for that case reads "Answer kept. escalations.md was not updated." (QA whitebox: the mod test in `hooks/po-inbox/ui.test.ts` asserts the sentence; the TUI cannot be driven from outside, BA ruling on QA-B's ASK RB-02). | new |
| R-08 | RB-02 | **Given** `skills/squad-start/SKILL.md` and `skills/squad-init/SKILL.md`, **then** neither tells the user to open, restart or look for a board; `squad-start` skill step 7 ends after the tab and `process_update` lines. | B7 |
| R-09 | RB-02 | **Given** README.md, **then** it has no "Squad board" section, no board limit, no board guide link and no `/squad:squad-board`; the file layout table lists no board file. | B7, B9 |
| R-10 | RB-04 | **Given** CONTEXT.md, **then** it has no Squad board section and none of the terms Bar, Status (agent state), Needs-you, Recorder, Replay; **Home** is kept, minus "The board reads every home and merges them". | B7 |
| R-11 | RB-04 | **Given** `docs/adr/`, **then** ADR 0009 "board removed" exists (status accepted, written via `/domain-modeling`); ADRs 0001-0003 each carry `Status: superseded by 0009`, and 0004 carries `Status: partly superseded by 0009` (BA ruling: its per-scope layout rule still holds for the CLI tools, so plain "superseded" would be false; 0009 restates the rule); ADR 0007's lines on the board's Needs-you and `squad-board` as cross-home view are noted as no longer true in 0009's Consequences (0007's own text is not rewritten). | B7 |
| R-12 | RB-04 | **Given** every relative link and every skill name left in README.md, CONTEXT.md, `docs/adr/*.md` and `skills/*/SKILL.md`, **then** each resolves to an existing file or skill. | B9 |
| R-13 | RB-05 | **Given** `templates/squad/process.md`, **then** it has no board word; the STATUS rule reads "it reads logs, the roster and the task file first, and pings an agent only after 10 minutes of no pane activity"; `squad-process show <role>` still prints every role's sections. | B8 |
| R-14 | RB-05 | **Given** a squad whose `process.md` still says "reads the board", **when** the PO runs `/squad:squad-process-update`, **then** the change arrives only through that flow (a plain `squad-start` only warns; nothing is rewritten without the PO's yes). | B8 |
| R-15 | RB-05 | **Given** `agents/*.md`, **then** no file mentions a board; the one example in `agents/manager.md` (`TAB-04 board labels`) is replaced by a title that names no board. Other wording stays. | B7 |
| R-16 | RB-06 | **Given** the integration branch, **when** the full suite runs with `--tz` (nothing skipped), **then** it is green and no test file, fixture or helper still imports or runs a removed board file. | new |
| R-17 | RB-06 | **Given** a text search for `board` (case-insensitive, whole word) over README, CONTEXT.md, `agents/`, `skills/` (except `history/`), `templates/`, `bin/`, `hooks/` and `docs/adr/` (except 0001-0004 and 0009), **then** no hit tells a user to use, open or run a board; any hit that remains is a different word (for example `dashboard`, `keyboard`) or is listed in `evidence/` with the reason. | B7 |
| R-18 | RB-06 | **Given** audit-token has merged into the branch's base, **when** the integration branch pulls it, **then** both scopes' behaviour holds on the same tools; if audit-token has not merged, this AC is not applicable (its spec says Phase A changes no product code). | B10 |

Allowed leftovers (BA ruling on QA-B's open point 1): the word board may remain in `.scratch/squad-board/**`, `.scratch/squad-tabs/**`, `.scratch/remove-board/**`, `process-log.md`, `skills/squad-process-update/history/process-v1.md` and `process-v2.md`, ADRs 0001-0004 (plus their superseded line), ADR 0009, and the "was" half of any changelog item.

## Decisions (BA)

- **R1** `activity.jsonl` stays in `squad-migrate`'s carry list (see Kept). Reason: no data loss for old squads; one line, no behaviour for new squads.
- **R2** History snapshots are not edited. Default 5's "history copies lose board mentions" is read as: the live template and the squad's own `process.md` lose them; the snapshots stay pristine because ADR 0005 uses them to detect a squad's own edits. If the Tech Lead finds the template change needs a version bump, the changelog item says "board removed" and R-14 holds.
- **R3** A running board is left alone; ADR 0009 says so.
- **R4** The PO inbox notice and the code comments that point at `bin/squad-board` (`bin/squadinbox.py`, `bin/squad-log-message`) are in scope of RB-02: they are dead references after task 1. Behaviour and the `list --json` contract do not change (R-07).
- **R5** `.claude/squads/<squad>/project.md` rows "UI conventions" and "Running app" name the board. After the removal the running app is the CLI tools in a scratch squad and there is no UI convention. The Manager edits `project.md` at promotion; the line goes in `promote.md` (Tech Lead).

## Glossary and lasting rules for `promote.md`

- **Board removed:** the plugin has no live page; PO sees per-home items through `squad-inbox`. (ADR 0009)
- **Home** stays in CONTEXT.md as a plain term: a folder with its own roster, escalations, logs, `iterations/` and `roles/`.
- **Rule:** a removed feature leaves no instruction, only a superseded ADR and history under `.scratch/`.

## Out of scope

- A replacement view or summary of the squad's state (not asked; the PO's TODO board items stop with the board).
- Deleting `.scratch/squad-board/`, `.scratch/squad-tabs/` or the superseded ADRs.
- Changing role instructions beyond the one example in `agents/manager.md` (R-15); more needs the PO at check-in.
- Removing the now-unused TZ/browser machinery in `tests/run_suite.py` (PO decision, per the Tech Lead) and the board items in `TODO.md` (the PO's file).
- Cleaning a user's running board process, herdr tab or old `activity.jsonl`.

## Open points

None for the PO. Settled by the Tech Lead: (1) yes, `process-version: 3` with `history/process-v3.md` and a changelog item "Board removed" (RB-05); (2) the STATUS sentence is as R-13 says; no test pins it. Were: (1) whether the template change is `process-version: 3` (ADR 0005 says every template change bumps it); (2) the STATUS rule's "no pane activity" signal used to come from the board's recorder; after the removal nothing records it, so check how the Manager is meant to see pane activity and that no test pins the old wording.

## Comments
