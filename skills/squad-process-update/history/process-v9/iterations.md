# Iterations

## ITER-1 Iteration steps
roles: manager
topic: iterations

Each iteration has `iterations/<n>.md`.
1. **Goal check:** the Manager and PO agree the goal in the iteration file; the PO confirms the team.
2. **Plan:** the roles on the team talk freely; requirements, AC and tasks land in files.
3. **Build and verify:** event-driven; Developers build, QA checks, gaps go to owners.
4. **Retro:** the Manager writes the friction (loops, blocked panes, returns, unclear ownership) into the iteration file.
5. **Check-in:** the Manager shows the PO what is done, open escalations and proposed role-instruction changes; each answered escalation's outcome goes into the iteration file and its row leaves `escalations.md`.

## ITER-2 Escalating to the PO
roles: manager
topic: iterations

Escalate only what the rules say always goes to the PO ([WHO-1a], [WHO-1b], [WHO-2]), or what you and the owners cannot settle. Write it to the inbox (question, options, your recommendation); the line the command prints is the telling.

## ITER-3 Pod summary
roles: team-lead
topic: iterations

Write `iterations/<n>.summary.md` at iteration end: tasks done with a link to each ticket's `evidence.md`, each task's final passed sha, the checkers that passed it and the returns per task (all three from `squad-ledger`), friction, open items, at most 40 lines. It carries one line naming the residual risk "the cap is a rule, not a lock".

## ITER-3b Pod summary, Manager
roles: manager
when: team-lead = no and qa-black = yes
topic: iterations

When you own the plan (the Team Lead is not on the team), write `iterations/<n>.summary.md` at iteration end, at most 40 lines: tasks done with each ticket's `evidence.md` link, final passed sha and returns (`squad-ledger`), friction, open items.

## ITER-4 Inbox
roles: manager
topic: iterations

- Anything the PO must read or answer goes in the inbox, never in chat: `squad-inbox add --kind answer|read --title "<title>" [--options "(a) text; (b) text"] [--rec "<recommendation>"] [--blocks "<what it blocks>"]`.
- The body goes in a quoted heredoc, `squad-inbox add ... <<'EOF' … EOF`; no pipe and no unquoted heredoc (the body would show in chat).
- One `squad-inbox add` per Bash call, never two. After an add, also after a failed one (fix and retry), your reply is the printed line and nothing else: no body, options or recommendation.
- A question that blocks nothing takes `--blocks ""` and waits for the check-in.
- A note with nothing to decide goes through `squad-inbox add --kind read`, never a hand-written row in `escalations.md`; only `--kind answer` makes a row, and the command writes it.
- A resolved question is withdrawn (`squad-inbox withdraw E<n> --reason "<why>"`), not left open. A chat reply to the PO never lists steps for the PO: the steps go in the inbox item, and the reply is the printed line (or one line pointing at it).

## ITER-5 PO answers
roles: manager
topic: iterations

- A PO answer in chat to an open item: record it with `squad-inbox answer E<n> --source chat <<'EOF' … EOF`, the PO's words verbatim inside the quoted heredoc. Run `squad-inbox list` first; never answer from memory of what is open.
- With several open items and an unclear answer, ask which one first. A prompt that arrives from the inbox is the PO's answer to the id it names.
- The inbox carries only `read` and `answer` items. Never offer a merge, push or deploy as an item (the check-in item may name the passed sha with the words "to merge, ask in chat").
- Never treat an inbox answer as a request to merge, push or deploy: that stays the PO's explicit request in this chat. Never put a permission approval for another agent in the inbox.

## ITER-6 Token Coach spawn
roles: manager
topic: iterations

Spawn the Token Coach with `squad-spawn token-coach <squad>-coach-<scope> --scope <scope> --prompt "<text>"` (`--goal <goal>` at goal close; run it at every goal close). Without `--prompt` it starts idle. The prompt names the scope and folder, the team, the exact output file (`iterations/<n>.coach.md`, or `coach/<goal>.coach.md`), "read `squad-usage`, `usage-events.jsonl`, earlier backlogs", and "message the Manager with the file and the proposal count".

## ITER-6c Wait for the Token Coach
roles: manager
topic: iterations

After the spawn, do other work or end the turn and wait for the Coach's message; never loop, sleep or poll for the file. Run `herdr agent list` on its pane only when no message came after the 10-minute health-check idle window ([MSG-8a]).

## ITER-6a Token Coach, no checkers
roles: manager
when: handin-target = manager
topic: iterations

At the close of a scope with no QA and no Team Lead, spawn the Token Coach only when the PO asks.

## ITER-6b Token Coach, with checkers
roles: manager
when: handin-target in qas, team-lead
topic: iterations

At the close of every scope with a QA or a Team Lead, spawn the Token Coach.

## ITER-7 Token Coach reads and writes
roles: token-coach
topic: iterations

Read `squad-usage`, `usage-events.jsonl` of the folder the Manager names, and earlier backlogs ([ITER-13]). Write `iterations/<n>.coach.md` (scope; n = last iteration) or `coach/<goal>.coach.md` in the goal folder: proposals ranked by saving, then an empty `## Backlog` heading. Tell the Manager in one short message: the file and the proposal count.

## ITER-8 Token Coach proposals
roles: token-coach
topic: iterations

- Find waste in the table: cache expiries, peak context over the rule thresholds, compactions, a role on a bigger model or effort than its default, many turns for little output.
- Each proposal has a title, the evidence (the table row by agent name, or the `usage-events.jsonl` line by `ts`), the exact rule change (rule ID and new wording), and the expected saving (tokens or percent, with how you got it). Tune the rule values (120k, 1h, 100k) if the evidence says they are wrong.

## ITER-9 Token Coach limits
roles: token-coach
topic: iterations

- Propose changes to the rules as overlay operations ([ITER-14]); a finding about a tool or a role card goes under `## Plugin proposals`, never as a rule change. Never edit any file except your proposals file.
- Never read raw transcripts: the table, the events and earlier backlogs are your only evidence. Never propose without an evidence row.

## ITER-10 Accepting proposals
roles: manager
topic: iterations

The Manager accepts at most the top 3 proposals into the squad's rules, logs each in `process-log.md`, moves the rest under the proposals file's `## Backlog`, and retires the Coach.

## ITER-11 Check-in item
roles: manager
topic: iterations

- Send the check-in at the end of each iteration as ONE `squad-inbox add` item (`--kind read`; `--kind answer` when it asks the PO to choose), never as a chat report. Unless a question blocks the squad now, bring it to the next check-in.
- It lists each step the PO must take (clean-up, checklist, close confirmation, open choices) next to: what is done, what is next, any task at 3 returns (one budget line), open escalations, proposed role-instruction changes.
- What is done carries evidence links: per ticket, the link to its `evidence.md` (a path in the repo or on the Dev branch, not a folder), the Dev branch and the evidence sha.
- Then copy each answered escalation's outcome into the iteration file and delete its row from `escalations.md`.

## ITER-12 Reset after a check-in
roles: manager
topic: iterations

Reset after each check-in when the scope goes on. Once the PO's decisions are in the iteration file, update your notes and run `squad-respawn $SQUAD_NAME`. The new session opens in a new tab; tell the PO to continue there.

## ITER-13 Coach reads earlier backlogs
roles: token-coach
topic: iterations

Read every `## Backlog` in the squad's earlier `*.coach.md` (`scopes/_done/**`, `goals/_done/**`). An item that appears in 2 or more scopes becomes a proposal of its own; cite both coach files.

## ITER-14 Coach proposal form
roles: token-coach
topic: iterations

- Write each process proposal as an overlay operation in `process.local.md` syntax with `upstream: proposed`, so the Manager can paste it.
- List tool and role-card findings (a bug in a `bin/` tool, a wrong role card) under `## Plugin proposals`, one item each with its evidence.

## ITER-15 Plugin proposals leave the retro
roles: manager
topic: iterations

At the check-in, each Coach `## Plugin proposals` item and each retro "Plugin follow-ups" item becomes one draft in `$SCOPE_DIR/tasks/` ([FILE-11], never the project root). Where `project.md` names the plugin's tracker, file it there instead. List the draft paths (or tracker links) in the check-in item; with neither, the list itself is the item.

## ITER-16 Blank retro
roles: manager
topic: iterations

`squad-close --scope` refuses while the last iteration file's `Went well`, `Friction` or `Process changes made` has no text ("none" counts). Fill them. `--force` overrides it and logs the override in that file.
