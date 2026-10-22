# squad 0.3.3 PO Inbox: CLI works on Windows, pane unverified, Manager misuses `escalations.md`

**Status:** needs-triage · **Plugin:** herdr-squad / squad 0.3.3 · **Found:** 2026-10-17 · **Follows:** `issue.md` (0.3.1 Windows bugs)

**Verdict:** the `squad-inbox` CLI works on native Windows. The pane (the mod the PO sees) has never been shown to run here. Two smaller findings trail.

## 1. The pane may not start `squad-inbox` on Windows (unverified)

**Risk:** `hooks/po-inbox/actions.ts` runs `bin/squad-inbox` by argv with no shell, and the script has no extension. This is the same shape as Bug 1 in `issue.md`.

- **Evidence for a bug:** `child_process.spawnSync` on the script returns `ENOENT` under Node on this machine.
- **Evidence it was never confirmed:** ADR 0011 D6 leaves it on the PO checklist, and its only support is an inference from a traceback.
- **Evidence from real data:** `scopes/scene-split/inbox.jsonl` has 4 `seen` events and no `answer --source pane` or `delivered`.
- **Not tested:** the Claude Code host's `$.process.run`. It is not Node and may behave differently.

**Check (needs the PO's hands):**

1. Open a Manager session and run `/inbox`.
2. Answer one item from the pane.
3. Look in `inbox.jsonl` for an `answer` event with `source: pane`, then a `delivered` event.

**Fix if it fails:** change the three `$.process.run` argv builds in `actions.ts` to `['python3', `${$.plugin.root}/bin/squad-inbox`, ...]`, as ADR 0011 D6 already proposes. Add an argv test.

## 2. The Manager writes READ notes as answer rows

**Problem:** rows E5–E8 in `scopes/scene-split/escalations.md` are informational notes ("READ (not blocking)…") written by hand as escalation rows.

- The inbox shows **4 to answer, 0 to read**. Nothing there needs an answer.
- **E7** says `RESOLVED` in its text but is still an open row.
- The notes should be read items: `squad-inbox add --kind read --title T` with a quoted-heredoc body.

**Fix:** tighten `agents/manager.md` so informational notes go through `squad-inbox add --kind read`, never a hand-written row. Then clear E5–E8 and E7 in this home. Clearing is the PO's call; I did not touch the file.

## 3. CRLF in `--body-file` keeps a stray `\r`

**Problem:** a body file with CRLF endings is stored as `'line one\r\nline two\r\n\r\n- bullet\r'`, and the answer row gets a trailing `<br>`. The display is cosmetic only.

**Fix:** normalise `\r\n` and lone `\r` to `\n` when reading the body, before the `<br>` conversion in `bin/squadinbox.py`.

## What works (verified on native Windows)

- **Commands:** `add`, `list`, `answer`, `read` and `delivered` all behave, with an emoji title, a path with spaces, and `|` and newlines in answer text.
- **Double answer:** the second answer to one item exits 3, as designed.
- **Locking:** 20 rounds of 8 truly parallel `add` calls (160 writes) gave 0 failures and unique ids.
- **Real home:** `list --json --no-write` on `scopes/scene-split` returns 4 open items and 0 errors.

## Test suite does not pass on Windows

The suite fails 12 times here (test_squadinbox, test_squadinbox_win, test_po_inbox_contract, test_po_inbox_mod, test_squadinbox_answer). **None is a product bug.** Causes:

- **Linux-only modules:** `termios` and `pty` (`test_squadinbox_answer`, `test_stdin_never_hangs`).
- **Privilege or mode:** symlink creation needs a privilege (`WinError 1314`), and file modes differ (`438 != 416`).
- **`os.execv` on Windows:** it returns early instead of replacing the process, so `test_concurrent_adds_on_a_barrier` reads the file too soon.
- **Simulated Windows:** the `NoFcntl` tests fake Windows on top of a real `fcntl`, so they cannot run on real Windows.
- **POSIX paths:** `/tmp/home` fixtures and `/h/scope` assertions meet `C:\...`.
- **Text-mode fixtures:** tests write files in text mode, which adds `\r`.

**Consequence:** the suite cannot gate Windows changes. Skip or port these tests, or run the suite in WSL.

## Done when

- The pane check in section 1 passes on Windows, or the `python3` argv fix lands with a test.
- A Manager session adds informational notes as read items.
- The `--body-file` CRLF case has a test.
- Windows-only test failures are skipped with a reason, or the suite has a documented way to run.

## Notes

- `python3` here is the WindowsApps launcher and reports Python 3.14.6. It works but is the Store alias, not the Python at `Program Files\Python314`.
- `squad-inbox answer` with only `--option` reads stdin and waits on an open pipe. It is the same on Linux and is by design, but a caller must pass `</dev/null`.
