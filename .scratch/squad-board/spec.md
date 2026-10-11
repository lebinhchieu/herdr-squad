Status: ready-for-agent

# Spec: squad-board, a live board of the squad at work

## Problem Statement

As PO, I run a squad of Claude Code sessions: Manager, BA, Team Lead, Tech Lead, QA whitebox, QA blackbox and Developers. Each one runs in its own herdr tab. To know what the squad is doing, I have to click through tabs one by one.

From where I sit I can't see:
- which agent is stuck on a permission prompt and waiting for me;
- which escalations are open;
- who is talking to whom;
- how a task moved through the lifecycle (handed in, returned, passed);
- how long each agent has worked;
- how much context and how many tokens each agent has used.

Agent-to-agent messages aren't stored anywhere, so after a check-in I can't replay how an iteration unfolded. Existing Claude Code dashboards label sessions by project and branch. Several squad roles share the project root and the same branch, so those dashboards show them as identical rows, and none of them understands squad's roster, pods, scopes, iterations or typed messages.

## Solution

`squad-board` is a local dashboard that ships in the squad plugin. `/squad:squad-start` starts it alongside the Manager. It serves one page, reachable only from my own machine, that draws the squad as a **live sequence diagram** on a canvas in the Mango Parrot light palette:

- Each agent is a **column**. Columns are grouped by **pod** and follow roster order, Manager first.
- Each message between agents draws itself as an **arrow**, coloured by message type and labelled with type and task ID.
- An **activation bar** on an agent's column shows when it worked:
  - It starts where a message woke the agent, or where herdr reports the agent working.
  - It is hatched red while the agent is blocked.
  - It ends when herdr reports the agent idle or done. Its duration shows at the end marker.
  - An open bar carries a live timer.
- Each **column header** shows the agent's status, total working time (⏱), blocked time (⛔) and tokens in context.
- A **needs-you bar** at the top lists what is waiting on me: blocked panes, unanswered escalations, and an idle Manager while an iteration is open.
- A slim **task column** on the right shows each task's state, derived from the typed messages.
- Clicking an agent's header opens a **side panel** with its role, model, token counts, working and blocked totals, last messages and notes file. It also has a **Jump to pane** button that focuses the agent's herdr pane.
- The board follows live. Scrolling up pauses the follow and shows history, an iteration picker replays earlier iterations, and long quiet stretches fold into one row.
- A browser notification with a soft chime fires when something new needs me.

## User Stories

### Seeing what needs me

1. As the PO, I want a needs-you bar at the top of the board, so that I know at a glance whether anything is waiting on me.
2. As the PO, I want an agent stuck on a permission prompt to appear in the needs-you bar, so that I can unblock it before it wastes time.
3. As the PO, I want every escalation with an empty answer to appear in the needs-you bar, so that I never miss a question the Manager raised.
4. As the PO, I want an idle Manager during an open iteration to appear in the needs-you bar, so that I notice when the Manager is waiting for my reply in its tab.
5. As the PO, I want BLOCKED messages between agents kept out of the needs-you bar, so that the board doesn't teach me to step over the topic's owner.
6. As the PO, I want a count of needs-you items, so that I can judge urgency without reading every item.
7. As the PO, I want a browser notification when a new needs-you item appears, so that I hear about it while I'm working in herdr.
8. As the PO, I want a soft chime with that notification, so that I notice it even when the browser is behind other windows.
9. As the PO, I don't want repeat notifications for an item I've already been told about, so that alerts stay meaningful.

### Seeing who is doing what

10. As the PO, I want one column per live agent, so that the whole squad fits on one screen.
11. As the PO, I want columns grouped by pod with the pod name and size shown, so that I can read each scope's team as a unit.
12. As the PO, I want the Manager's column first, so that the coordinator is always in the same place.
13. As the PO, I want columns in roster order within a pod, so that positions stay stable and I learn them once.
14. As the PO, I want a newly spawned agent to appear at the end of its pod, so that existing columns don't move.
15. As the PO, I want a retired agent's column to collapse once it has no events on screen, so that the board doesn't fill with dead columns.
16. As the PO, I want each column header to show the agent's current status (working, idle, blocked), so that I can see the squad's state without reading the timeline.
17. As the PO, I want a blocked agent's header outlined in red with a pulsing marker, so that it stands out from the rest.

### Seeing the conversation

18. As the PO, I want each SendMessage between agents drawn as an arrow from sender to receiver, so that I can see who talks to whom.
19. As the PO, I want each arrow labelled with its message type (ASK, ANSWER, DECISION, BLOCKED, HANDIN, PASS, FAIL, STATUS), so that I can read the conversation without opening tabs.
20. As the PO, I want each arrow labelled with its task ID when the message names one, so that I can follow one task through the conversation.
21. As the PO, I want each message type to have its own colour, so that HANDIN → FAIL → HANDIN → PASS loops are visible from across the room.
22. As the PO, I want new arrows to draw themselves in, so that I notice fresh activity.
23. As the PO, I want one row per event, so that a burst of messages stays readable instead of collapsing into one line.
24. As the PO, I want long quiet stretches folded into a single "⋯ N min quiet" row, so that the screen isn't mostly empty.

### Seeing when agents work

25. As the PO, I want an activation bar on an agent's column from when it starts working until it goes idle, so that I can see when each agent was busy.
26. As the PO, I want a bar to start exactly where an arriving message woke the agent, so that cause and effect line up visually.
27. As the PO, I want a bar that started without a message (e.g. I prompted the Manager directly) marked with a self-start symbol, so that I know it wasn't another agent's message.
28. As the PO, I want the blocked part of a bar hatched in red, so that I can see how long an agent waited on me.
29. As the PO, I want each finished bar's duration shown at its end marker, so that I know how long each turn took.
30. As the PO, I want an open bar to carry a live timer, so that I can see how long the current turn has been running.
31. As the PO, I want each header to show total working time for the run, including blocked time, so that I can compare effort across agents.
32. As the PO, I want each header to show blocked time separately when there is any, so that I can spot roles whose permissions need fixing.

### Agent monitor

33. As the PO, I want each header to show how many tokens are in the agent's context, so that I can tell which agents are close to running out.
34. As the PO, I want context shown as a raw token count rather than a percentage, so that the board never relies on a model-to-window table that goes stale.
35. As the PO, I want the side panel to show the agent's model, so that I know which model each role is running.
36. As the PO, I want the side panel to show total tokens in (including cache) and tokens out, so that I can reason about each agent's usage.
37. As the PO, I want the side panel to show working and blocked totals, so that I can see an agent's time profile in one place.
38. As the PO, I want the side panel to show how many times the agent was woken, so that I can spot agents being pinged too often.
39. As the PO, I want token numbers to refresh when a bar ends and every 30 seconds while an agent works, so that they stay current without heavy file watching.
40. As the PO, I want a missing or unreadable transcript to show "—" instead of breaking the board, so that one bad file doesn't take everything down.

### Tasks

41. As the PO, I want a task column on the right listing tasks by state (blocked, building, checking, returned, done), so that I can see progress without a separate tracker.
42. As the PO, I want task state derived from the typed messages agents already send, so that no agent has to do extra bookkeeping.
43. As the PO, I want a FAIL to move a task to returned and count the return, so that I can see when a task is nearing the three-return limit where the Manager steps in.
44. As the PO, I want a task to appear on the board the first time a message names it, so that tasks show up without a separate "ready" step.

### Acting from the board

45. As the PO, I want to click an agent's header to open a side panel, so that I can look at an agent before deciding to jump into its tab.
46. As the PO, I want a Jump to pane button in the side panel that focuses that agent's herdr pane, so that I reach a stuck agent in one click.
47. As the PO, I want a link from the side panel to the agent's notes file, so that I can read its memory without hunting for the file.
48. As the PO, I want the side panel's last messages for that agent, so that I can see its recent conversation in one place.
49. As the PO, I don't want the board to answer escalations or prompt agents, so that the Manager stays the owner of escalations and the process isn't bypassed.

### History

50. As the PO, I want the board to follow new events live by default, so that I always see the present.
51. As the PO, I want scrolling up to pause the follow, so that I can read history without it scrolling away.
52. As the PO, I want a "↓ live" control that resumes following, so that I can get back to the present in one click.
53. As the PO, I want an iteration picker, so that after a check-in I can replay how an earlier iteration unfolded.
54. As the PO, I want history to survive the browser being closed, so that replay works even when I wasn't watching.

### Running it

55. As the PO, I want `/squad:squad-start` to start the board along with the Manager, so that recording begins with the squad and I never forget to start it.
56. As the PO, I want the board to run in its own herdr tab named `board`, so that I can see it's running and stop it.
57. As the PO, I want the board's URL printed when it starts, so that I can open it in my browser straight away.
58. As the PO, I want a `/squad:squad-board` skill that prints the URL or restarts the board, so that I can recover it without restarting the squad.
59. As the PO, I want the board on a fixed default port that falls back to the next free one, so that it works even when the port is taken.
60. As the PO, I want the board reachable only from 127.0.0.1, so that nothing about my project is exposed to the network.
61. As the PO, I want the jump action to require a random token from the page URL and accept only names in the roster, so that another local web page can't drive my herdr.
62. As the PO, I want the board to need nothing beyond Python 3, herdr, jq and git, so that installing the plugin stays as simple as it is today.
63. As the PO, I want `/squad:squad-init` to git-ignore the message log and activity log, so that they never add noise or ticket content to commits.
64. As the PO, I want everything the board shows to come from files in the squad folder plus herdr and the transcripts, so that the board can restart at any time without losing anything.

### Message recording (agents)

65. As an agent, I want my SendMessage calls recorded automatically, so that the board sees the conversation without me doing anything.
66. As a Claude Code user outside a squad, I want the plugin's message hook to do nothing, so that my normal sessions are never touched.
67. As an agent, I want the recorded message to include my squad name, the receiver, the message type and the task ID, so that the board can draw it and derive task state.
68. As the Manager, I want the process to say that BLOCKED, HANDIN, PASS, FAIL and STATUS messages name their task ID, so that task state can always be derived.

### Look

69. As the PO, I want the whole board in the Mango Parrot light palette, so that it matches my editor theme.
70. As the PO, I want "needs you" in mango, working in teal, idle in muted grey and blocked in red, so that colour carries the same meaning everywhere on the board.

## Implementation Decisions

### Modules

- **Message hook.** A plugin-level hook that runs after every SendMessage tool call. It does nothing unless the session carries a squad name, which `squad-spawn` already sets for every agent. It appends one record to the squad's message log and parses message type and task ID from the message text's leading `TYPE TASK-ID` prefix. It is a small shell command using jq, already a plugin requirement.
- **Board server** (`squad-board` command). One Python 3 file using only the standard library. Its jobs:
  - **Activity recorder:** connects to herdr's socket, subscribes to events, and appends every agent status change to the squad's activity log.
  - **Squad reader:** parses the roster, scopes, escalations and iteration files (markdown tables and sections).
  - **Derivation:** turns the logs plus squad files into the board state: columns, rows, bars, durations, task states, needs-you items and token figures.
  - **Transcript token reader:** finds each agent's transcript from the session ID in herdr's snapshot, searching every Claude config folder (`~/.claude*`), reads only newly appended lines, and keeps the model, the last reply's context tokens, and totals in and out.
  - **HTTP:** serves the page, a state snapshot, a server-sent-events stream of state updates, and the jump action.
  - **Replay mode:** reads a fixture folder instead of live herdr, so that tests and screenshots are deterministic.
- **Board page.** One static HTML file with one script, served by the server and drawing on a canvas. No framework, no build step. It renders only what the state contains; all derivation lives in the server.
- **Squad wiring.**
  - `squad-init` adds the two log files to the project's `.gitignore`.
  - `squad-start` opens the board in a herdr tab named `board` and prints the URL.
  - A new `/squad:squad-board` skill prints the URL or restarts the board.
  - The process file gains one rule: BLOCKED, HANDIN, PASS, FAIL and STATUS messages name their task ID.
  - The README documents the board.

### Data contracts

Both logs live in the squad folder, append only, one JSON object per line, never rotated.

- **Message log record:** `ts` (ISO time), `from` (squad name), `to`, `type` (one of the typed message prefixes, or null), `task` (task ID or null), `text`, `iteration`.
- **Activity log record:** `ts`, `agent` (squad name), `status` (working, idle, blocked, done), `iteration`.
- Every record is tagged with the current iteration: the highest-numbered iteration file at write time.
- herdr agent names match squad names, because `squad-spawn` labels the tab and agent with the squad name. That is the join key between herdr, the roster and both logs.

### Derivation rules

- **Bar start:** at a message row whose receiver was idle, or at a `working` status event. With no arriving message, the bar is marked self-started.
- **Bar blocked segment:** from a `blocked` event until the next `working` event.
- **Bar end:** at an `idle` or `done` event. Duration = end time − start time. A bar with no end is open, and its duration runs to now.
- **Per-agent totals:** working = sum of bar durations including blocked time; blocked = sum of blocked segments.
- **Task state from messages:**

  | Message | Task state |
  |---|---|
  | DECISION or STATUS naming it | building |
  | BLOCKED | blocked |
  | HANDIN | checking |
  | FAIL | returned (return count +1) |
  | PASS | done |

  ASK and ANSWER don't change the state, but they make a task appear as building the first time they name it. A task that is blocked returns to building at its agent's next `working` event.
- **Needs-you:**
  - any agent whose latest status is `blocked`;
  - each escalation row with an empty Answer cell;
  - the Manager idle while the current iteration's PO check-in section is still empty.
- **Rows:** one per message or status event, in time order. A gap longer than a threshold (a few minutes) between consecutive events becomes one folded row carrying the gap's length.
- **Columns:** roster order grouped by pod (the scope from `scopes.md`). The Manager comes first. Unknown agents seen in the logs join the end of their pod.

### HTTP contract

- The page is served at the root URL. The URL carries a random per-run token.
- The state snapshot is a JSON document. It is the same model the event stream pushes, and the seam tests assert on it. It holds: columns (agent, role, pod, status, working, blocked, context tokens, tokens in and out, model), rows, bars, tasks, needs-you items, iterations, and the current iteration.
- The event stream pushes a fresh state, or a delta, whenever either log grows, herdr reports a change, or the token reader refreshes.
- The jump action needs the token and an agent name that's in the roster, and runs `herdr agent focus <name>`. Anything else is refused.
- The server binds to 127.0.0.1 only. The default port is fixed, with a fallback to the next free port.

### Page behaviour

- **Layout:** the needs-you bar on top, the sequence in the centre, the task column on the right, and the side panel over the sequence when an agent is selected.
- **Header:** status dot, ⏱ working total, ⛔ blocked total when non-zero, and context tokens as a raw count.
- **Following:** the page follows live; scrolling up pauses; "↓ live" resumes; the iteration picker reloads history for that iteration.
- **Notification:** asked permission once; fires with a chime only for needs-you items it hasn't seen before.
- **Palette:** from the Mango Parrot light theme:
  - background `#FCF8F1`, panel `#F4ECDD`, border `#E7DBC8`, ink `#3E372E`, muted `#857A68`;
  - needs-you mango `#E8820E`, working teal `#0C8A80`, blocked red `#DB3B22`, idle `#A99C86`;
  - message types: ASK `#2A6DC0`, ANSWER `#4A8FE0`, DECISION `#9E7A00`, HANDIN `#9A40CF`, PASS `#368A1E`, FAIL `#CE1D6C`, STATUS `#857A68`.
- **Prototype:** the look is fixed by the round 6 grill prototype. Its activation-bar logic, trimmed to the decision, was:

  ```
  message row r (a → b):   startBar(a, r, self=true) if a idle; startBar(b, r, self=false) if b idle
  status working at r:     if bar open and last blocked segment open → close segment at r; else startBar(agent, r, self=true)
  status blocked at r:     ensure bar open; open blocked segment [r, null]
  status idle|done at r:   close bar at r; row r carries duration = t(r) − t(bar.start)
  ```

## Testing Decisions

- **Good tests check external behaviour only.** They feed inputs at a seam and assert on outputs a user or the page would see. They never assert on internal helpers, intermediate structures or drawing calls, so the internals can be rewritten freely.
- **Seam A, the main one: the board server in replay mode.**
  - Input: a fixture folder with squad markdown files, a message log, an activity log and sample transcripts. Tests start the server against it and read the state snapshot over HTTP.
  - Covered through this one seam:
    - parsing roster, scopes, escalations and iterations;
    - column order and pod grouping;
    - row ordering and folded gaps;
    - bar start, blocked and end, including the self-start case;
    - durations, and working and blocked totals;
    - task state transitions and return counts;
    - needs-you rules, including that a BLOCKED message between agents is not a needs-you item;
    - token figures from transcripts, and "—" for a missing or bad transcript;
    - iteration tagging and the iteration filter.
  - Also on this seam: the jump action refuses a missing or wrong token and a name not in the roster.
  - Tests are written first (red, then green), with Python's standard unittest.
- **Seam B: the message hook command.** Feed a sample hook payload on standard input, with and without a squad name in the environment. Assert on the line appended to the message log (type and task parsed from the text), and that nothing is written outside a squad.
- **Not covered by automated tests:**
  - **herdr's live socket:** proven by a throwaway test before the build (subscribe and see working and idle events) and by one live S-size squad run.
  - **The SendMessage hook actually firing in Claude Code:** proven by a throwaway test before the build, with two named sessions exchanging one message.
  - **The canvas drawing:** checked by Playwright screenshots in replay mode at desktop widths and reviewed by eye, not asserted.
- **Prior art:** the repo has no tests yet. The nearest precedent is `squad-spawn`'s dry-run mode, which prints what it would run without touching herdr. Replay mode follows the same idea: a deterministic mode that bypasses live herdr.

## Out of Scope

- Answering escalations, prompting agents, spawning or retiring agents from the board.
- Cost in dollars, price tables, and context as a percentage of a model's window.
- Access from other devices, other users, authentication, or binding beyond 127.0.0.1.
- A separate message-feed panel; the sequence is the feed.
- A "ready" task column or a task state field in task files.
- Rotating or trimming the log files.
- Committing the logs to git.
- Dark themes or other palettes.
- Recording what the PO types to the Manager (it isn't a SendMessage); such work appears only as self-started bars.
- Support for terminal multiplexers other than herdr.

## Further Notes

- **Biggest risk:** whether a PostToolUse hook fires for SendMessage, and what its input fields are called, is unverified. It's the first throwaway test. If it fails, the fallback is for the server to read SendMessage tool calls from each agent's transcript; the message log record stays the same.
- **Already checked during design:**
  - herdr publishes `pane_agent_status_changed` with statuses idle / working / blocked / done / unknown through `events.subscribe` on its socket.
  - herdr's snapshot gives each agent's session ID.
  - Transcripts carry `message.usage` and `model` on every reply.
  - The Claude config folder varies per account (e.g. `~/.claude-2`), so the server searches all of them.
- Transcripts are Claude Code's private format. The reader uses only `usage` and `model` and tolerates anything else.
- The design history (grill rounds 1–6, prototypes and the confirmed summary) lives outside the repo in the user's chat folder (`~/workspace/chat`, `squad-board-*.html`).
