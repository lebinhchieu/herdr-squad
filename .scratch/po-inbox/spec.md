# PO inbox

Status: ready-for-agent (PO answered Q1–Q4 as recommended on 2026-10-15; QA blackbox AGREED the AC)

**A Claude Code mod in the Manager's session that shows the PO a separate list of what the Manager needs the PO to read or answer, so none of it is buried in the working chat. The PO answers in the list; the answer reaches the Manager without the PO retyping it.** Brief: `scopes/po-inbox/scope.md`. Written by the BA, iteration 1 of scope `po-inbox`.

## The goal behind the brief

The PO talks to the Manager in one chat that also carries status, routing and tool output. A question or a "please read this" scrolls away; the PO either misses it or has to hunt for it, and the squad waits. The need is not "a list": it is **"I can always see, in one place, what waits on me, and acting on it costs one step."**

## Terms

- **Inbox**: the PO-facing list in a Manager's session. One inbox per Manager home (a scope, or a goal).
- **Item**: one thing the Manager wrote for the PO. Fields the PO sees: **id**, title, kind, body, created date, and what it blocks (or "nothing"). An answer item also has options and the Manager's recommendation (both optional).
- **Read item**: the PO must read it, nothing to decide (a check-in summary, "branch X passed, evidence here"). Kept in the inbox's own store.
- **Answer item**: the PO must decide or reply (a question with options). **Under Q3(b), every answer item is a row of `escalations.md`**, blocking or not (`Blocks` = "nothing"); an escalation and an answer item are the same thing. Only read items live in the inbox's own store.
- **States**: `open` → `done` (read, answered, or withdrawn by the Manager). An answered item not yet delivered to the Manager shows "answered, waiting for the Manager".
- **Delivered**: the answer text has entered the Manager's session. QA observes delivery; what the Manager then does is the Manager's instructions.
- **N** (timing): 5 seconds, the business target for "shows up" and "reaches an idle Manager". The Tech Lead may counter with a measured figure.

## User stories and business AC

Given/When/Then, observable in the running mod and in the files it leaves. IDs are for QA blackbox and the tickets. **Kind of check:** AC marked *(live)* depend on a live LLM Manager's behaviour; QA tests them best-effort in a sandbox and each has a deterministic partner AC.

### US1: The Manager writes an item and the chat stays clean
*As the PO I want the Manager to put what I must read or answer into the inbox, so my chat stays about the work.*

- **B-01** Given a Manager session with the mod, when the Manager writes a read item or an answer item, then it appears in the inbox within N seconds without the item's body being printed into the chat.
- **B-02** *(live)* Given the Manager wrote an item, then the chat carries at most one short pointer line ("1 new item in the inbox: <title>") and none of the body, options or recommendation.
- **B-02b** *(NOT TRIGGERED: spike S3 ended as outcome A, 2026-10-15; only if spike S3 outcome B: the tool row can be collapsed but the CLI's own stdout line still shows)* The chat carries at most two short title-only pointer lines (`→ inbox: <title>` and `1 new item in the inbox: <title>`) and none of the body, options or recommendation. B-01 and B-02 are then judged on that. Same reading as B-02a: the Manager tells the PO at the check-in.
- **B-02a** *(NOT TRIGGERED: spike S3 ended as outcome A, 2026-10-15; fallback, only if the Tech Lead's spike S3 shows this build cannot collapse the Manager's `squad-inbox add` tool row)* The Manager's own chat text carries no body, options or recommendation, only the pointer line; the tool row the Claude Code UI draws for the command may still show the body. The Manager tells the PO at the check-in that this limit applies. B-01 and B-02 are then judged on the Manager's chat text, not on the tool row.
- **B-03** Given the write command is run from a session that is not a Manager's, then it is refused with a message and nothing is written. (A Developer, QA, Tech Lead or BA that needs the PO still sends its question to the Manager: instruction level, whitebox.)
- **B-04** Given an item with a missing title, an empty body or a kind other than `read` / `answer`, when written, then it is refused with a message that names what is wrong; nothing half-written appears in the inbox. Kinds are only `read` and `answer`; there is no kind for a permission approval (see B-30).

### US2: I see what waits on me at a glance
*As the PO I want to know without asking whether anything waits, and what matters first.*

- **B-05** Given open items exist, then I see how many are open, split into "need answer" and "to read", while the Manager is idle and while it is mid-turn, without opening the inbox.
- **B-06** Given open items, when I open the inbox, then items that block work now come first (what they block is shown), then the rest, oldest first within each group.
- **B-07** Given no open items, then the inbox says so in plain words and the count shows none.
- **B-08** Given a draft typed in my prompt (text and cursor position), when a new item arrives, then the count changes, at most one signal is given for that item, and the draft is unchanged. The form of the signal is the Designer's.

### US3: I read a read item and clear it
- **B-09** Given an open read item, when I open it, then I see id, title, body, created date and what it blocks.
- **B-10** Given an open read item, when I mark it read, then it leaves the open list, the count drops by one, and it appears in the done list with "read" and the time.
- **B-11** Opening a read item alone does not clear it; only marking it read does.

### US4: I answer in the inbox and the Manager gets it
*As the PO I want to answer where I read the question, without copying anything into the chat.*

- **B-12** Given an open answer item with options, when I pick an option (optionally adding a note) or give a note alone with no option picked, then the item shows my answer and the time, and leaves the open list.
- **B-13** Given an open answer item without options, when I type a reply, then the same happens.
- **B-14** Given I answered, then the answer is delivered to the Manager without my typing it again: to an idle Manager within N seconds; to a busy Manager at its next turn, after the current one. The text arrives byte for byte, including several lines, quotes, backticks, `|` and non-ASCII.
- **B-15** An answer is never lost: until delivered, the item shows "answered, waiting for the Manager". It is written to a file first; a closed or busy Manager session does not drop it.
- **B-16** Given the answer was delivered, then the item shows "answered" with the delivery time.
- **B-17** An answered item cannot be changed or answered again from the inbox: the attempt is refused with a message and the first answer stays. If I answered wrongly, I tell the Manager in chat, and the Manager writes a new item or acts on my correction.
- **B-32** An empty answer, or an empty note with no option picked, is refused; the item stays open.
- **B-33** Every item shows a short id that both the PO and the Manager use ("answer 3: yes"), unique within the inbox's home.
- **B-34** Given the PO answers an item at the moment the Manager withdraws it (or answers twice in a row), then exactly one outcome stands and nothing is lost: the first to reach the store wins, the other is refused with a message naming the winner.

### US5: I answer in the chat instead
- **B-18** *(live)* Given an open answer item, when I answer it in the chat, then the Manager records my answer on the item and it moves to done with "answered in chat". With several open items and an answer that fits more than one, the Manager asks which before recording. The item never stays open once the PO has answered. Deterministic partner: the command that records "answered in chat" on an item (works like B-12 and B-34).

### US6: The inbox survives the Manager
*The Manager respawns after every check-in (process.md, Cost rules); the inbox must not reset with it.*

- **B-19** Given open items and the Manager respawned, then the new session's inbox shows the same open items, with their answers if any.
- **B-20** Given I answered while no Manager session was running, then the next Manager session receives that answer at its start (B-14, B-15).
- **B-21** Given the PO closes the Claude session and opens it again, the open items are still there.

### US7: Escalations are inbox items (see Q3)
- **B-22** Given a row in `escalations.md` (existing or new, written by hand or by the Manager), then within N seconds, without a restart, the inbox shows it as an answer item with its question, options, recommendation and "blocks". Options are shown as separate choices when the row's Options cell follows the format the Tech Lead sets for it; a cell that does not follow it is shown whole and answered in free text. The Manager's instructions name that format.
- **B-23** Given the PO answers it in the inbox, then the answer lands in the row's Answer column, so the check-in rule and `squad-board`'s Needs-you keep working unchanged. An answer containing `|` or a line break does not break the table or the board's parse; the PO's text is shown back unchanged in the inbox.
- **B-24** Every open answer item is a row of `escalations.md`, so Needs-you lists every one of them. There is no answer item that only the inbox knows. Read items are not in `escalations.md` and not in Needs-you.
- **B-35** Given `escalations.md` or an item file is malformed or edited by hand, then the inbox does not crash: it shows an error naming the file and row, and the other items still show.

### US8: Lifetime: open until handled, then kept
- **B-25** A read item stays open until marked read. An answer item stays open until answered or withdrawn. Nothing expires on its own: an item dated 60 days ago is still open.
- **B-26** The Manager may withdraw an item that became obsolete, with a one-line reason. It leaves the open list, shows in done as "withdrawn: <reason>", and the count drops.
- **B-27** Done items are not deleted when handled: the inbox has a done list, ordered by the time they were handled, newest first, that the PO can open to look back.
- **B-28** Done items stay in the scope's or goal's own folder; when the scope or goal closes they move with the folder to `_done/`, and a new scope starts with an empty inbox.
- **B-29** `squad-close --scope` / `--goal` refuses while answer items are open **or answered but not yet delivered to the Manager ("answered, waiting", B-15)** and names them, as `squad-close --goal` already refuses without `promoted:`; the PO may override with `--force`. (Deterministic. A Manager that tells the PO first is instruction level.) *Should-have: the Tech Lead may make it the one droppable ticket.*
- **B-36** With 50 open items, a body of many lines and a long title, the count is right and the list stays readable (scrolls or truncates with a way to open the whole item).

### US9: Safety rules still hold (see Q4)
- **B-30** The inbox offers only the kinds `read` and `answer` (B-04): it has no way to carry a permission approval for another agent. A blocked pane's prompt goes to the PO directly, as today. Role-instruction line, whitebox.
- **B-31** *(live)* Given an answer "yes, merge X" in the inbox on a sandbox repo, then no merge happens; the Manager says the merge needs the PO's explicit request in its chat (`process.md` → Safety). The Manager does not offer merge, push or deploy as answer items.

## Defaults I took (the PO may object; none change the goal)

- **D1** Both kinds exist: the brief says "read and answer".
- **D2** Only the Manager writes: the brief says "allow manager to write down".
- **D3** Urgency is the existing "blocks" field, not a new priority scale. A Manager's "batch for the check-in" rule becomes "write it as an item that blocks nothing".
- **D4** Free text and options both work for answers; the Manager's recommendation is shown but never pre-selected.
- **D5** Handled items are kept (B-27), not deleted; nothing is deleted before the scope's archive.
- **D6** The count and the signal (B-05, B-08) are required; their form (band, status line, toast) is the Designer's call.
- **D7** "Delivered" means the answer entered the Manager's session; "within N seconds" (N = 5) is the business target the Tech Lead may counter.

## PO decisions (were open questions Q1–Q4)

**Resolved 2026-10-15, logged in `iterations/1.md` → PO check-in: Q1a, Q2a, Q3b, Q4a, all as recommended; D1–D6 (and D7) accepted.** The table keeps the options and reasons.

| # | Question | Options | Decision and reason | Affects |
|---|---|---|---|---|
| Q1 | One inbox per Manager session, or one across scopes and squads? | (a) per Manager home, `squad-board` stays the cross-home view; (b) the mod also lists every scope's and squad's items | **DECIDED (a).** The mod lives in one Manager's session; an all-squads view is what Needs-you already does. (b) needs a registry of every squad on the machine | B-05–B-07, B-19, B-28, ticket count |
| Q2 | Where does the PO answer? | (a) in the inbox, and the chat also works; (b) chat only, the inbox is read-only | **DECIDED (a).** The brief asks for the PO to "answer"; a read-only list leaves the PO retyping into the chat, the cost the mod removes | US4, US5 |
| Q3 | Relation to `escalations.md`: replace, sit on top, or stay separate? | (a) **replace**: drop `escalations.md`; touches `process.md`, `manager.md`, `project.md`, `squad-board` and its tests; (b) **sit on top**: an escalation *is* an answer item, the file stays the store of those, read items are new; (c) **separate**: two lists | **DECIDED (b).** One concept, one place for the PO, the board and the check-in rule keep working at no cost. (a) is a large cross-cutting change for no PO-visible gain; (c) makes the PO look in two places, the problem we are solving | US7, B-22–B-24, ticket count |
| Q4 | Does a "yes" on an inbox item count as the PO's request to merge, push or deploy? | (a) no: those stay explicit requests in the Manager's chat; (b) yes for merge only | **DECIDED (a).** `process.md` says the PO asks in the Manager's own session and the Manager never offers a merge. A click on a list item is easier to make by accident and harder to audit | B-31 |

Q3(b) stands, so US7 and B-22–B-24, B-35 stay as written.

## Agreement with QA blackbox

QA blackbox reviewed B-01..B-31 on 2026-10-15 and asked for the rewrites and the added B-32..B-36 now in the text; B-02, B-18 and B-31 are best-effort *(live)* checks, each with a deterministic partner. **AGREED by QA blackbox on B-01..B-36**, with Q1–Q4 as the PO later decided. Conditions they stated:
- It holds only if the Tech Lead delivers N1–N4 (sandbox, terminal driver, exact keys, settable clock). Without them B-05, B-08, B-25 and the *(live)* AC are marked FAIL as "could not test".
- B-36 "readable" = count correct and nothing overlaps or cuts off without a way to open the whole item, unless the Designer's doc sets a tighter bar.
- B-02, B-18, B-31: a best-effort live run; the deterministic partner decides PASS/FAIL, and a live miss is a finding for the Manager role instructions.

## Out of scope

- A view across scopes or squads inside the mod (Q1a); `squad-board` changes beyond not breaking Needs-you.
- Other roles writing items; inboxes for anyone but the PO.
- Notifications outside the Claude session (push, email, sound).
- **Surfaces:** the mod supports Claude Code in the terminal only (PO decision 2026-10-15: the squad works in herdr, no UI). Desktop, mobile and IDE surfaces are out of scope: no AC, test or design effort for them.
- Snooze, priorities beyond "blocks", editing or reopening answered items, search.
- Permission approvals (B-30), merge/push/deploy answers (B-31).

## Design notes accepted (Tech Lead, 2026-10-15)

- Item ids: `E<n>` for an escalation row (its `#`), `R<n>` for a read item (B-33). Options cell format: `(a) text; (b) text`, at least two markers, else shown whole and answered in free text (B-22). In the cell `|` is `\|` and a newline `<br>`; the PO's exact text stays in `inbox.jsonl` and is shown back from there (B-23).
- B-31 is instruction-level plus an audit trail: an answer carries its `source`; a hand-edited Answer cell shows as "answered in the file (not through the inbox)". No token. Accepted.
- B-29 is ticket PI-06, droppable. N = 5 s kept.

## Notes for the Tech Lead and QA blackbox

- **From QA blackbox review (needs for the Tech Lead):** (N1) a sandbox: the mod runs against a scratch squad/scope folder with a stand-in Manager, never the real inbox; (N2) pane text through a terminal driver plus the path of the inbox files; (N3) the exact commands or keys for the PO to open the inbox, pick an option and type a note; (N4) a way to set the clock or age an item's date (B-25).
- **QA blackbox:** the running app here is a mod in a Claude session, not the board. The Tech Lead names how to drive it (`claude --plugin-dir`, a terminal driver) and what files make the evidence; every AC above is phrased as what the PO sees or what file results.
- **Whitebox questions that are the Tech Lead's, not business:** how the mod receives an answer into a live Manager session (B-14), whether the Manager writes items through a command or a file, where items live, how a hand-edited file is told from the PO's own answer (B-31).

## Lasting business rules and glossary (for `promote.md`)

- Glossary: **Inbox**, **Item** (read item, answer item) in `CONTEXT.md`; **Escalation** gets "is an answer item".
- Rule: the PO's "what waits on me" lives in one place; chat carries at most a pointer line.
- Rule: an answer the PO gave is never lost and never re-typed; files first.
- Rule: merge, push and deploy are never an inbox answer (if Q4a).
- ADR candidate: inbox relation to `escalations.md` (Q3), once the PO answers.
