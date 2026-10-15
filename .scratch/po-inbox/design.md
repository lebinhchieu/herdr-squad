# PO inbox: design (Tech Lead)

Status: draft for QA agreement. Spec: `spec.md` (B-01..B-36). Tickets: `issues/01..08`. Plan and order: `plan.md`.

**Build a mod inside the squad plugin itself: one hooks module (`hooks/po-inbox/register.tsx`) that draws a band above the prompt (counts) and a pane (list, detail, answer), reads and writes everything through a new Python CLI `bin/squad-inbox`, and hands an answer to the Manager with `$.prompt.submit`.** Answer items stay rows of `escalations.md` (Q3b); read items live in `inbox.jsonl` in the Manager's home. The mod never parses or writes a file itself: the CLI is the single store, so Q3 can still change by replacing the CLI.

## Decisions

| # | Decision | Why |
|---|---|---|
| T1 | The mod ships in the squad plugin: `hooks/hooks.json` gets `"modules": ["./po-inbox/register.tsx"]` next to the existing command hooks (validated on this build: both coexist). | Squad Managers already load this plugin (`--plugin-dir $SQUAD_PLUGIN_DIR` or installed); nothing new to install. |
| T2 | The module is **inert unless `SQUAD_ROLE=manager`** and `SCOPE_DIR` or `GOAL_DIR` is set (read with `$.env.get`). Every other role and the PO's own sessions load it and do nothing. | The plugin loads in every squad session. |
| T3 | All store access goes through `bin/squad-inbox` (Python, logic in `bin/squadinbox.py`, the `squad-process` / `squadprocess.py` pattern), run by the mod with `$.process.run([…])`. | One parser, one writer, one lock. The JSON contract below is the seam: swap the store, the mod stays. |
| T4 | **Read items:** append-only `inbox.jsonl` in the home (`$SCOPE_DIR`, else `$GOAL_DIR`). **Answer items:** rows of `escalations.md`, unchanged table. | Q3b. The board, the check-in rule and `process.md` keep working. |
| T5 | The mod notices changes by polling `$.fs.stat` (mtime) of `inbox.jsonl` and `escalations.md` every 2 s, and runs `squad-inbox list --json` only when one changed. | `$.fs` has no watch. 2 s polling plus one CLI run is well under N = 5 s. |
| T6 | The PO's answer reaches the Manager as a prompt: `$.prompt.submit({ text })` right after the CLI recorded it; an answer recorded but not delivered is submitted again at `session.start`. | The PO is in the Manager's own session; this is "a user turn of its own once the session is idle". |
| T7 | A hand-edited Answer cell is told from the PO's inbox answer by the event log: no `answer` event, so the item shows "answered in the file (not through the inbox)". It is a flag, not a security boundary (see Provenance). | B-31 honesty. |
| T8 | The Manager writes items with `squad-inbox add` (both kinds). Its tool row is collapsed by a `ui.render` hook so the body is not in the chat. | B-01, B-02. |
| T9 | N = 5 s is kept. Measured plan: poll 2 s + CLI < 0.3 s for an item appearing; delivery to an idle Manager is immediate after the answer is recorded (no poll). | |

## Store

### Ids (B-33)
- Answer item: `E<n>`, `n` = the row's `#` cell. "Free" (for `add --kind answer` and for a row with a bad `#`) = above the maximum of every `#` cell in the file and every `E<n>` ever in the log, so the `#` in the table equals the id the pane shows. If the `#` is empty, not a number, or already used by a *different* row in the log, the CLI takes the next free number and records it in the `seen` event (the row's `#` cell is not rewritten). The PO says "E3: yes".
- Read item: `R<n>`, `n` = next free in the log.
- **Row identity** = `sha1(date + "|" + question)[:10]` of the raw cells (`\|` unescaped, whitespace-trimmed; not the board's cleaned form) (the `key`). A Manager who edits the question text changes the key: the open item becomes `removed` and a new id appears (accepted, pinned by a test); the `#` can be reused after a check-in deletes rows, the key cannot clash in practice.

### `inbox.jsonl`: one JSON object per line, written only by `squad-inbox`, under `flock` on `inbox.jsonl.lock`, appended with `O_APPEND`
| `ev` | Written by | Fields besides `id`, `ts` (ISO UTC) |
|---|---|---|
| `add` | `add --kind read` | `title`, `body`, `blocks` |
| `seen` | any `sync` (every `list`) on first sight of a row | `key`, `title`, `body`, `options` (raw cell), `rec`, `blocks`, `date`, `row_no`: the snapshot that keeps an item listable after the Manager deletes its row (B-27) |
| `read` | `read R<n>` | |
| `answer` | `answer` | `text`, `option` (key or null), `note`, `source` (`pane` or `chat`) |
| `delivered` | `delivered` (the mod) | `session` |
| `withdraw` | `withdraw` | `reason` |
| `gone` | `sync` | first sight of an open row that vanished (gives `removed` a stable `done.ts`) |
| `filled` | `sync` | first sight of a hand-written Answer cell (gives `answered-file` a stable `done.ts`); the cell text goes in `done.reason`, `answer` stays null |

State is folded from the log on every call (never stored): `open` → `answered-waiting` (answer, no `delivered`, source `pane`) → `done`. Done kinds: `read`, `answered` (via inbox or chat), `answered-file` (cell filled by hand), `withdrawn`, `removed` (row gone while open and unanswered). A row gone while `answered-waiting` stays `answered-waiting`: an answer is never lost (B-15). **First writer wins (B-34):** every write command takes the lock, folds, and refuses (exit 3, message names the winner and the time) if the item is no longer `open`.

### `escalations.md` projection
Parsed as the board does (first table; `\|` unescaped; headers lower-cased) in a small copy of `read_first_table` (the board is a script, not a module; a parity test pins both on the same fixture). Row to item: question cell → `title` = text before the first `<br>` or newline (cut at 80 chars) and `body` = the whole cell; options, recommendation, blocks (empty means "nothing"), date. A row without `#` and question is blank, skipped. A row with an Answer cell and no log event → `answered-file`. A malformed row or file goes to `errors` and never stops the rest (B-35). While a row exists its cells are the item's fields (the `seen` snapshot serves only after the row is gone). A row shorter than the header counts missing trailing cells as empty if it reaches the question cell (as the board does); otherwise, or with extra cells, it is an error. `add --kind answer` refuses a row whose key already exists (exit 3). Every `inbox.jsonl` line is validated (`ev`, id shape `^[ER][0-9]{1,6}$`); a bad line is an `errors` entry.

### Options cell format (B-22)
`(a) text; (b) text; (c) text`: markers `(a)`, `(b)`, … in letter order, the k-th marker must be the k-th letter, at the start or after whitespace or `;`. Text is trimmed and loses a trailing `;`. At least two markers → `options: [{key, text}]`, else `options: null` and the cell is shown whole and answered in free text. The recommendation cell stays free text and is never pre-selected (D4). The Manager instruction (ticket 05) names this format.

### Writing an answer into the row (B-23)
The CLI rewrites **only the Answer cell of that row**: `|` → `\|`; every line break the board's `str.splitlines()` splits on (`\r\n`, `\n`, `\r`, `\x0b`, `\x0c`, `\x1c`-`\x1e`, `\x85`, U+2028, U+2029) → one `<br>`; text otherwise as given. The cell is always written with a space before the closing pipe (`... text |`), so a text ending in `\` cannot escape it. Work in **bytes** (or `surrogateescape`): invalid UTF-8 elsewhere in the file, the line endings (CRLF or LF) and a missing final newline are preserved exactly. File rewritten to a temp file in the same folder, then `os.replace`, under the same lock; a symlinked `escalations.md` is refused (exit 1, message says so). The row is found by `key` (not by line number); the Answer column is found by its header name, not by index; a row shorter than the header is padded with empty cells to the header width (the board reads it as a valid row); no `answer` header, a row with extra cells or two rows with the same `key` → no cell written (the answer is kept, exit 0, stderr warning, flag `cell-not-written` in `list`), never guess.
**Order and recovery (the crash window):** the `answer` event is appended **first**, then the cell is written, all under the lock. If the cell write fails or the process dies between the two, the answer is not lost (it is in the log, state `answered-waiting`) and `list` (without `--no-write`) repairs it: a row whose key has an `answer` event and an empty Answer cell gets the cell filled from the event. A failed cell write at `answer` time exits 0 with a warning on stderr (as for a deleted row).
**What "reads back" means:** the board reader is used for structure (same number of rows and cells before and after); the exact text is read back from the `answer` event. The CLI keeps an item's `body` raw (cell text with `\|` unescaped and `<br>` kept), not the board's `clean_cell` form (which strips `**` and backticks). The PO's exact text is kept in the `answer` event and shown from there, so the escaping never shows. The board's `clean_cell` already unescapes `\|`. Known limit: the Manager's own Edit/Write of `escalations.md` is not under our lock; its edit fails on a changed line (Edit) or overwrites (Write). The window is milliseconds; the CLI re-reads the file right before it replaces it.

## The contract: `squad-inbox list --json` (version 1)

```json
{"version": 1, "home": "<path>", "now": "<iso>",
 "counts": {"answer_open": 1, "read_open": 2, "waiting": 0},
 "items": [{"id": "E3", "kind": "answer|read", "state": "open|answered-waiting|done",
            "title": "", "body": "", "options": [{"key": "a", "text": ""}] ,
            "recommendation": "", "blocks": "", "created": "<iso>", "created_precision": "day|second",
            "answer": {"text": "", "option": "a", "note": "", "ts": "", "source": "pane|chat", "delivered_ts": ""},
            "done": {"kind": "read|answered|answered-file|withdrawn|removed", "ts": "", "reason": ""},
            "flags": ["answer-by-hand|row-removed|cell-not-written"]}],
 "errors": [{"file": "escalations.md", "row": 4, "message": ""}]}
```
`options`, `answer`, `done`, `delivered_ts`, `recommendation` are `null` when absent. **`options_raw`** (string or `null`, added by PI-02): the Options cell as written, set only when it is non-empty and `options` is `null` (cell not in the `(a) x; (b) y` format), so the pane can show what the Manager wrote and take a free-text answer; the mod treats an absent key as `null`. **Closed sets (a CLI test asserts output uses only these):** `kind` answer|read; `state` open|answered-waiting|done; `done.kind` read|answered|answered-file|withdrawn|removed; `answer.source` pane|chat; `flags` ⊆ {`answer-by-hand`, `row-removed`}. `created` is always ISO-8601 (an escalation row's day becomes `YYYY-MM-DDT00:00:00Z`, `created_precision: "day"`). Unknown extra keys are ignored by the mod; the mod **validates** `version == 1`, `items` an array and the type of every field it reads, and on any mismatch shows the error state and keeps the last good snapshot. Order of `items`: open (blocking first, then oldest first), then `answered-waiting`, then done newest first by handled time (B-06, B-27). `counts.answer_open` + `read_open` count `state: open` only; `waiting` counts `answered-waiting`. Fixtures of this shape in `tests/fixtures/inbox/` are the mod's test input.

## CLI (`squad-inbox`)

| Command | Who | Does |
|---|---|---|
| `add --kind read\|answer --title T [--body-file F \| stdin] [--options "(a) …; (b) …"] [--rec R] [--blocks X]` | Manager | `read`: appends `add`. `answer`: appends a well-formed row to `escalations.md` (next number, today's date, cells escaped). Prints one line `1 new item in the inbox: <title>`. Refuses (exit 2, names the problem, writes nothing) on a missing title, an empty body, a body over 64 KiB, stdin that is a TTY or closed with no `--body-file` (never hangs), any other kind, or `SQUAD_ROLE` not `manager` (B-03, B-04). |
| `list [--json] [--open] [--no-write]` | anyone | Syncs `seen` events (unless `--no-write`) and prints the state. Plain form is for humans. |
| `read R<n>` | the mod | PO marks a read item read. |
| `answer E<n> [--option K] [--note N \| --text T \| stdin] --source pane\|chat` | the mod, the Manager | Records the answer and fills the Answer cell. Refuses an empty answer (B-32), an answered item (B-17), a lost race (B-34). `--source chat` is the Manager recording "answered in chat" (B-18): done at once, never `answered-waiting`. The text goes by stdin for the mod (no argv limit, no shell). |
| `withdraw E<n>\|R<n> --reason R` | Manager | Event; for an answer item also fills the Answer cell with `withdrawn: <reason>` so the board's Needs-you agrees. |
| `delivered E<n> --session S` | the mod | Event. |

Home: `--home D`, else `$SCOPE_DIR`, else `$GOAL_DIR`, else exit 2. `SQUAD_INBOX_NOW` (ISO) replaces the clock for every timestamp (tests and N4). Exit codes: 0 ok, 2 refused (bad input, wrong role), 3 lost a race or already handled. Input is validated against `^[ER][0-9]{1,6}$` and used as a dict key, never a path. No shell is ever involved.

## The mod

Files (all new unless noted): `hooks/po-inbox/register.tsx` (events, polling, delivery, command), `hooks/po-inbox/core.ts` (pure: contract types, count, ordering of the pane list, prompt text, sanitising), `hooks/po-inbox/ui.tsx` (band, pane, collapsed tool rows), `types/index.d.ts` (`PluginState['squad']`: `inbox: Snapshot | null`, `ui`), `hooks/hooks.json` and `.claude-plugin/plugin.json` (`"types"`) edited once, in the scaffold ticket.

| Event / call | Behaviour |
|---|---|
| `session.start` | Inert check (T2). Register `/inbox`. Run `list --json`, store in `$.state` (an `atom`). Redeliver every `answered-waiting` item (T6). Start `clock.every(2000)` polling. |
| poll tick | stat both files; if mtime **or size** changed run `list --json` and update the atom. New `open` ids since the last snapshot → one `$.ui.toast` per poll (naming the count, or the title if one) (B-08). Never touches the prompt box. |
| `ui.render` `AbovePrompt` | Band: counts "N to answer · M to read" and a button that opens the pane; nothing when no open items and no `answered-waiting` (B-05, B-07). Design owns the form. |
| `ui.render` `Pane` (`inbox`) | List, detail, mark read, pick option, note or free text, done list. Design owns it. Items drawn only as `Text` (no markdown): control characters (ESC, C0 and C1 except `\n` `\t`) are stripped from every item field before drawing (a body written by an agent must not drive the terminal). |
| `command.run` `inbox` | Opens the pane: placed at any width because asked (`$.ui.open` doc). |
| answer submitted in the pane | `answer … --source pane` (stdin). On exit 0: `$.prompt.submit({ text })` then `delivered`. On exit 3: the pane shows the message naming the winner. The prompt text is a header line plus the answer after a delimiter line, **verbatim** (B-14), e.g. `PO answered inbox item E3 ("<title>") in the inbox. Answer, exactly as typed:` then a blank line and the text. |
| `ui.render` `ToolUse` for a Bash call that is **exactly one** `squad-inbox add` invocation (see PI-04 AC5; any `;`, `&&`, `||`, `|`, backtick or `$(` outside a heredoc body leaves the row untouched) | Collapsed to one line `→ inbox: <title>`; the body is not drawn (B-01, B-02). **Spike S3** decides if the hook can replace a row; fallback is told to the BA (below). |

### While a turn runs
`prompt.submit` is "a turn of its own, once the session is idle". If this build rejects it mid-turn, the mod holds the text and submits on `turn.complete` (spike S1 settles which). The item stays "answered, waiting for the Manager" until `delivered` is written (B-15, B-16), and a session that ended before delivery redelivers at the next `session.start` (B-20). A duplicate delivery after a crash between submit and `delivered` is possible and harmless: the Manager reads the same answer twice.

### Titles and prompt injection
`add` collapses any line break or control character in `--title` to one space (it never forges a second line). The mod's `describePrompt` also collapses the title (a row written by hand can carry one), so the header is always one line. The answer text after the delimiter is verbatim (B-14).

### Delivery failures and timers
`$.prompt.submit` that rejects: no `delivered` is written, the item stays `answered-waiting`, one retry at the next `turn.complete` (never every tick); no second submit while one is in flight. A repeated `session.start` (resume, clear) leaves one timer and one `/inbox` registration. The mod passes the env to the CLI explicitly if `$.process.run` does not inherit it (spike S2/S4 records which).

### Provenance (B-31, T7)
Every `answer` event carries `source`. The CLI cannot prove who ran it: a Manager with a shell could run `answer --source pane`. So the safety rule is **instruction level**: the Manager file says an inbox answer is never a merge, push or deploy request and never offered as one (ticket 05), and `process.md` → Safety already says the PO asks in chat. The inbox adds the audit trail (`source`, `ts`) and shows a hand-edited cell as `answered-file`. We do not build crypto or a token: it would give a false guarantee.

## Driving the mod (QA blackbox needs N1–N4)

- **N1 sandbox:** `tests/fixtures/inbox/home/` is a scope folder (`escalations.md` with rows in the option format, one malformed row, one hand-answered row, an `inbox.jsonl`). QA copies it to a temp folder `H` and never touches a real home.
- **N2 driver:** a stand-in Manager is any `claude` session started with the env of one, in a herdr pane: `SQUAD_ROLE=manager SQUAD_DIR=<tmp> SCOPE_DIR=$H SQUAD_INBOX_NOW=<iso> claude --plugin-dir <worktree> --permission-mode default`. Read the screen with `herdr agent read <pane> --source visible`, send keys with `herdr agent send-keys` (own test pane only). Evidence files: `$H/inbox.jsonl`, `$H/escalations.md`, `squad-inbox list --json --no-write`, the session transcript under `~/.claude/projects/<cwd>/<session>.jsonl` (the delivered prompt text, byte for byte).
- **N3 keys:** open with `/inbox` (or the band's button); the rest (select, type, submit, back) are the Designer's and are copied into `ui-design/PI-04.md` under "Keys". Final text goes to QA when the design is final.
- **N4 clock:** `SQUAD_INBOX_NOW` for CLI timestamps; to age an escalation, edit its Date cell in `$H/escalations.md` (60 days ago); to age a read item run `add` with `SQUAD_INBOX_NOW` set. The mod's "age" text uses `$.clock.now()`; `claude plugin test` mocks it.
- **Deterministic partners:** `claude plugin test` (engine `mount` on the terminal surface) for the draw and keys; Python tests for the CLI. B-02, B-18, B-31 live checks are best-effort with a real model, their partners are `squad-inbox add` output (one line), `answer --source chat`, and the manager.md line pinned by a test.

## Compatibility, migration, deploy

- **Additive only.** No change to `escalations.md`'s table, to `process.md`, `squad-board`, any ADR 0001–0006 contract. A home without `inbox.jsonl` works (empty). Old squads and flat squads: the CLI needs a home; without `SCOPE_DIR`/`GOAL_DIR` the mod is inert.
- **Plugin version:** minor bump in `.claude-plugin/plugin.json` in the integration ticket.
- **Deploy (the PO does it):** merge, then `/reload-plugins` (or a new session). Managers started earlier keep running without the mod until respawned; the next Manager respawn picks it up. **Rollback:** revert the merge; `inbox.jsonl` files stay on disk unread and harmless; answers already written into `escalations.md` are ordinary Answer cells.
- **Checks after deploy:** in a Manager session run `/inbox`; `squad-inbox list --json` on the home; add one read item and see the band count change.
- **Role-instruction change:** `agents/manager.md` (ticket 05) needs the PO's approval before merge.

## Risks and spikes (first step of ticket 03; results in `.scratch/po-inbox/spike.md`, the Tech Lead reads it before UI work)

| Spike | Question | If no |
|---|---|---|
| S1 | `$.prompt.submit` while a turn runs and while idle: queued, rejected, or does it interrupt? **And with text typed in the prompt box (a draft):** kept, sent with the answer, or cleared? Same for a draft present when `session.start` redelivers (B-08). | Hold until `turn.complete`; if a draft is clobbered, hold until the box is empty or tell the Tech Lead. |
| S2 | `$.env.get('SQUAD_ROLE')` etc. readable in `session.start` in a `--plugin-dir` session started with those env vars; **and** `$.process.run` passes `SQUAD_ROLE`, `SCOPE_DIR`, `SQUAD_INBOX_NOW` to the CLI (else the mod passes env explicitly or `--home`). Also record `printenv SQUAD_ROLE SCOPE_DIR GOAL_DIR` of a real started Manager session (only `squad-spawn` sets `SQUAD_ROLE`; does `squad-start` Manager have it?): the real sample for T2. | Read them through `$.process.run(['printenv', …])`; if neither works the mod is not buildable as designed: BLOCKED to the Tech Lead. |
| S3 | A `ui.render` hook on `ToolUse` can replace a Bash row with one line. | B-01/B-02 weaken to "the body is in the Manager's tool row, one collapsed line in chat is not guaranteed". Tech Lead tells the BA; option: the Manager writes the body to a file first and `add --body-file` (the Write row still shows). |
| S4 | `$.process.run` of `${$.plugin.root}/bin/squad-inbox` with stdin works, and stat polling shows a change. | Fall back to `$.fs.read` of `list` output the CLI writes to a cache file. |

Other risks: a tiny window of a concurrent edit of `escalations.md` (above); the `claude plugin test` kit and `claude` binary are not in every environment, so the Python wrapper test skips with a named reason when `claude` is missing (the receipt must say it ran).

## Technical AC common to every ticket
Suite green by `tests/run_suite.py` (receipt rules in `CLAUDE.md`); no new dependency (Python stdlib, no npm); Python 3.9-safe (a test runs `ast.parse(src, feature_version=(3, 9))` over the new Python files and rejects `X | None` annotations and `match`), no `.pyc` left under the new folders; no shell with user data; surgical diff (only the ticket's files); `claude plugin validate` clean on the plugin for tickets touching `hooks/`.

## Known limits (TL, accepted by BA)
- An answer recorded by an outside process with `--source pane` while the Manager session runs is delivered at the next session start (B-20); the item keeps saying "answered, waiting for the Manager". Not built: it would risk a double delivery against the pane path.
- `squad-close` refuses only for `--scope S` and `--goal G` (PI-06). Plain `squad-close <squad>` (whole squad) and the legacy flat `--scope` form skip the open-answer check.
