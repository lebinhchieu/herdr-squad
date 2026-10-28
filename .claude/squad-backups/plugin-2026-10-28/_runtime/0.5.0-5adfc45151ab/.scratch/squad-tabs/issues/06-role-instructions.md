Status: ready-for-agent
Task ID: TAB-06
Blocked by: TAB-01 (the `squad-label` CLI text; branch from its passed sha). Not blocked by TAB-02.
Files touched: `agents/manager.md`, `agents/dev.md`, `tests/test_instructions.py`
Serves: spec story 5 (D2, D3, D4). PO approved editing exactly these two role files (iteration 1 plan).

# TAB-06: the Manager and the Developer know the label rule

**Done when the Manager passes `--title` and relabels QAs as they change ticket, and the Developer runs `squad-label` on every new ticket.** Narrowing agreed with the BA's story 5 ask: QA whitebox and QA blackbox role files are **not** edited (the PO approved only these two files); the Manager relabels the QAs instead (it may relabel any agent, D4). Whether QAs should relabel themselves is proposed to the PO at the check-in.

## Build
- `agents/manager.md`, in "Spawning and retiring": the `squad-spawn` line gets `[--title "<text>"]`, plus one bullet: pass `--title` when the agent has a specific task (a Developer: ticket id and a few words, e.g. `TAB-04 board labels`; a QA: the ticket it checks); leave it out otherwise. One bullet on `squad-label --agent <name> "<text>"`: when you point a QA at a new ticket (HANDIN or next-ticket message) relabel it; `""` clears. Labels are display only: messages and `roster.md` use the address name. Do not restate the label shape: point at `process.md` (TAB-08 writes it there).
- `agents/dev.md`, in the start routine or "What you do": when you take a ticket run `squad-label "<ticket id> <few words>"`; when your last ticket is done and you wait, `squad-label ""`. One or two lines.
- Reuse existing wording; no new sections; no restating what `process.md` will say.

## Technical AC
1. The two files contain `--title` (manager) and `squad-label` (manager and dev) exactly where described; no other line of either file changes (diff shows only added lines in those places).
2. `tests/test_instructions.py` gets one test: manager.md mentions `--title` and `squad-label --agent`, dev.md mentions `squad-label`. Existing tests (stale-token checks) still pass.
3. Every command in the text exists with the flags shown (`squad-spawn --title` from TAB-02, `squad-label` from TAB-01); check with `--help` or the code, not memory.
4. The PO-approval fact is stated in `dev-evidence.md`: files touched are only the two approved role files and the test.
5. Targeted test passes; full suite once on the final sha.
