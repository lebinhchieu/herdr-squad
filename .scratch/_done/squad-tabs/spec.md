Status: ready-for-agent

# Spec: squad-tabs, readable tabs and fewer pings

**One line:** every squad tab and every agent name on the board reads `<emoji> <Role>[ n] · <task>`; the workspace takes the scope's (or goal's) name; and only the Manager waiting on the PO, or any agent blocked, raises a desktop toast, while non-squad Claude sessions keep toasting as today. Source: the PO's TODO items 1-2 and the grill decisions D1-D15 in `decisions.md` (binding; rounds in `round1-3.html`). Business AC below cite their D-number; technical AC live in the tickets (`issues/`).

## Problem Statement

As PO I keep one squad team in one herdr workspace. Today:
- every tab is named with the agent's full address (`squad-board-dev-squad-tabs-1`), so I read a long squad name I already know and learn nothing about what the agent is doing;
- the workspace keeps whatever name it had, so it does not say which scope or goal the tabs belong to;
- every Claude turn-end in every tab can raise a desktop toast, so workers ping me all day while most stops mean nothing. I only need to hear about it when the Manager waits for me or when an agent is blocked.

## Solution

- A **display label** `<emoji> <Role>[ n] · <task>` for each tab and for each agent's name on the board: `🦀` Manager, `🤖` every other agent, `📋 Board` for the board tab. The agent's **address name** (what agents message each other with) does not change.
- The task text comes from `squad-spawn --title` and from `squad-label "<text>"` (an agent relabels itself when it takes a new ticket; the Manager may relabel anyone).
- `squad-start` renames the caller's herdr workspace to the goal or scope name.
- One notification path (D15): herdr's own toast is switched off, and one hook in the squad plugin sends every toast itself, by writing the desktop-notification sequence (OSC) to the herdr client's terminal so WezTerm shows it. `herdr notification show` cannot be used: it shows nothing when delivery is off. The hook applies the skip-active-tab and title rules itself, and the route is proven in a spike before it ships (story 16). Squad sessions toast only for the Manager stopping or an agent being blocked; non-squad Claude sessions toast on stop and on needs-input as before. A toast is skipped when its tab is the one I am looking at.

## Glossary (business terms this scope adds)

- **Address name:** an agent's unique messaging name `<squad>-<role>-<scope>[-n]`; unchanged (D1).
- **Display label:** the human-readable name shown on the herdr tab and on the board (D1, D2).
- **Task text:** the short free text after the ` · ` in a label; blank unless set (D4).
- **Toast:** the desktop notification shown through the terminal (WezTerm); under D15 the squad hook writes it, not herdr.
- **Squad session:** a Claude session started by `squad-spawn`. A **non-squad session** is any other Claude session (D8).
- **Blocked:** a permission prompt or a question waiting in the pane (round 2).

## Decision coverage

| D | Story | D | Story |
|---|---|---|---|
| D1 | 1, 8 | D8 | 10 |
| D2 | 1, 2, 8, 12 | D9 | 11 |
| D3 | 1, 3 | D10 | 12 |
| D4 | 4, 5, 12 | D11, D15 | 13, 16 |
| D5 | 6, 7 | D12 | 14 |
| D6 | 9 | D13 | 15 |
| D7 | 10 (squad rule) | D14 | 15 |

## Role names used in labels (BA decision B1)

Fixed display name per role, so the board and tabs agree: `Manager`, `BA`, `Team Lead`, `Tech Lead`, `QA Whitebox`, `QA Blackbox`, `Dev`, `Designer`, `Token Coach`. Reason: the PO's examples (`🤖 Tech Lead`, `🤖 Dev`) show title-cased full words; the closed role list is in `squad-spawn`.

## User Stories

### Tab labels

1. **As the PO, I want each squad tab labelled `<emoji> <Role> · <task>` with no squad or scope name, so I read what each agent is doing at a glance.** (D1, D2, D3)
   - **Given** the Manager spawns a Tech Lead with `--title "plan"`, **when** the tab opens, **then** its herdr tab label is `🤖 Tech Lead · plan` and its address name is unchanged. (D1, D2)
   - **Given** a Manager tab, **then** it is `🦀 Manager`, never `🤖`; **given** any other role, **then** `🤖`. (D2)
   - **Given** an agent spawned with no `--title`, **then** the label is just `🤖 Tech Lead` or `🦀 Manager`, with no ` · ` and no trailing space. (D2, D4)
   - **Given** a label longer than 32 characters (counted as characters, emoji = 1), **then** it is cut to 31 characters plus `…`, so 32 in all; for example `🤖 QA Blackbox · TAB-05 integration live check` shows as `🤖 QA Blackbox · TAB-05 integrat…`. A label of 32 or fewer is never touched. (D3; BA reading: the 32 counts the whole label)
   - **Given** any tab opened, **then** neither the squad name nor the scope name appears in its label. (D2)

2. **As the PO, I want the board tab labelled `📋 Board`.** (D2)
   - **Given** `squad-board-start` opens a board tab, **then** the tab label is exactly `📋 Board`.

3. **As the PO, I want a number when two agents of one role are live in a scope, so I can tell them apart.** (D3)
   - **Given** one live Dev in a scope, **then** its label has no number (`🤖 Dev · TAB-02 tab labels`).
   - **Given** a second Dev goes live in the same scope, **then** the two read `🤖 Dev 1 · …` and `🤖 Dev 2 · …`, the first one relabelled when the second appears. (D3; BA reading of "two live agents of one role get a number")
   - **Given** Dev 1 retires and Dev 2 stays, **then** Dev 2 keeps `Dev 2` (numbers never move under me). (BA decision B2: stable numbers; I learn a tab once)
   - **Given** the same role in two different scopes of a goal, **then** each scope numbers on its own, so both may read `🤖 Tech Lead`; the task text is what tells them apart. (D3 says "in a scope"; known limit, see below)

### Task text

4. **As the PO, I want the task text set when an agent is spawned and changed when it takes a new ticket.** (D4)
   - **Given** `squad-spawn ... --title "TAB-02 tab labels"`, **then** the label carries that text after ` · `. Default (no `--title`) is blank. (D4)
   - **Given** a Dev takes the next ticket without a respawn and runs `squad-label "TAB-03 board labels"`, **then** its own tab reads `🤖 Dev 1 · TAB-03 board labels` and its role, number and emoji are unchanged. (D4)
   - **Given** the Manager runs `squad-label` on another agent's address name, **then** that agent's tab is relabelled the same way; **given** a non-Manager agent targets another agent, **then** it is refused. (D4: "the Manager may relabel any agent"; "an agent relabels its own tab")
   - **Given** `squad-label ""` (blank), **then** the task text is cleared and the label is `🤖 Dev 1`. (BA decision B3: needed so a finished ticket does not stay on the tab)
   - **Given** a relabel, **then** the board shows the new label too (story 8). (D1, D4)

5. **As the PO, I want the roles to know this rule, so I do not have to remind them.** (D2, D3, D4; PO's TODO: "have rule to name the herdr tabs")
   - **Given** the squad process file, **then** it states the label shape, the emoji per role, the 32-character cut, the numbering rule, and who relabels whom.
   - **Given** the Manager's role instructions, **then** the Manager passes `--title` whenever the agent has a specific task (a Dev: ticket id + a few words; a QA: the ticket it checks) and leaves it blank otherwise.
   - **Given** a Dev's role instructions, **then** the Dev runs `squad-label` on its own tab when it takes the next ticket. (D4)
   - **Given** a QA (whitebox or blackbox) is pointed at a new ticket, **then** the Manager relabels it with `squad-label --agent <address name> "<text>"`, so the QA's tab shows the ticket without editing the QA role files. (D4: "the Manager may relabel any agent"; BA decision B11, agreed with the Tech Lead: only `manager.md` and `dev.md` are edited, as the PO approved.)
   - **Given** the project glossary (`CONTEXT.md`), **then** it defines "display label" and "address name".

### Surviving respawns and legacy squads

6. **As the PO, I want a respawned agent to keep its label, so my tab strip does not change under me.** (D5)
   - **Given** the Manager is respawned (`squad-respawn`), **then** its new tab reads `🦀 Manager` again, with the same task text as before, if any. (D5)
   - **Given** any other agent is respawned, **then** it comes back with the same role, number and task text it had. (BA decision B4: extension of D5; otherwise a respawned Dev loses its ticket text)

7. **As the PO, I want `squad-board-start` to find the board by its new label, in every squad.** (D5)
   - **Given** a running board tab labelled `📋 Board`, **when** `squad-board-start` runs, **then** it reuses it and prints its URL; no second board tab appears. (D5)
   - **Given** a board tab still labelled `board` from before this change, **then** `squad-board-start` reuses it (and relabels it `📋 Board`) rather than opening a second board. (BA decision B5: "finds the board tab by its new label" must not orphan a running board)
   - **Given** a squad on the legacy flat layout, **then** the labels, the board lookup and `squad-respawn` behave the same as in a per-scope squad. (D5: "every squad, legacy layout too")

### The board

8. **As the PO, I want the board to show the same display label as the tab, so one agent has one name on screen.** (D1, D2, D4)
   - **Given** a live agent, **then** its column header on the board reads its display label, not its address name. (D1)
   - **Given** a column header too narrow for the whole label, **then** the task text is cut first and the emoji, role and number always stay readable (`🤖 Dev 2 …`, `🤖 QA Whitebox`), or the header wraps or shrinks; a plain cut to `Dev …` fails, because it makes two agents look alike. The full label is in the side panel. (BA decision B14; D1, D2, D3: the PO tells agents apart at a glance)
   - **Given** a needs-you item about a blocked agent, **then** it names the agent by its display label. (D1)
   - **Given** the side panel of an agent, **then** it also shows the address name, since messages and the roster use it. (BA decision B7)
   - **Given** an agent relabelled with `squad-label`, **then** the board shows the new label without a restart; a stale board is fixed by the board's normal refresh. (D1, D4)
   - **Given** an agent with no stored label (an older squad, a replayed earlier iteration, a retired agent), **then** the board builds one by the same rules from its role: emoji, role name, number when two of one role share a scope, and no task text. It never shows an empty or raw-address header. (BA decision B8: replay and legacy must read the same way)
   - **Given** the agent's address name, **then** the roster, notes files, messages, `herdr agent` and the event log still use it unchanged. (D1)

### Workspace

9. **As the PO, I want the workspace renamed to what I am working on, so the workspace list is readable.** (D6)
   - **Given** I run `squad-start "<lone task>"` inside herdr, **then** my herdr workspace is renamed to the scope name; **given** `squad-start "goal: ..."`, **then** to the goal name. (D6)
   - **Given** I start another scope or goal from the same workspace, **then** it is renamed again: the last start wins. (D6)
   - **Given** `squad-start ... --in-goal G` (a scope inside a goal, no Manager of its own), **then** the workspace name is not changed: the goal name stays. (BA reading of D6: only a goal or a lone scope names the workspace)
   - **Given** `squad-start --resume NAME`, **then** the workspace is renamed to NAME like any start. (BA reading: "last start wins"; the resumed Manager is a start)
   - **Given** `squad-start` runs outside herdr (no `HERDR_ENV`), **then** it still creates the scope and Manager exactly as before and says nothing about the rename; the rename is skipped, never an error. (D6)
   - **Given** a rename that herdr refuses, **then** the scope still starts. (BA decision B6: naming is never a reason to stop work)

### Notifications

10. **As the PO, I want a toast only when something needs me: the Manager waiting on me, or any agent blocked.** (D7, D8)
    - **Given** a squad session that is the Manager, **when** it stops (waits on me), **then** one toast fires. (D7)
    - **Given** a squad session of any role, **when** it is blocked (permission prompt, or a question waiting), **then** one toast fires. (D7)
    - **Given** a squad worker (any non-Manager role) that finishes a turn, **then** no toast. (D7)
    - **Given** a squad Manager that stops while an agent is blocked, **then** each event gives its own toast with its own reason (story 12).
    - **Given** a non-squad Claude session (one not started by `squad-spawn`, in any workspace), **when** it stops or needs input, **then** one toast fires, the same events as today. (D8)
    - **Given** a Claude session outside herdr, **then** nothing fires and the session is not disturbed; today herdr does not toast for it either. (BA decision B9)
    - **Given** the toast script fails, herdr is slow, or no herdr client terminal can be found, **then** no toast, and the Claude session is not blocked, slowed or shown an error. (BA decision B10: a notifier must never cost me a working session; D15)

11. **As the PO, I want no toast for the tab I am already looking at.** (D9)
    - **Given** the stopping or blocked agent's tab is the active tab of the focused workspace, **then** no toast. (D9)
    - **Given** it is in another tab, or another workspace, or the workspace is not focused, **then** the toast fires. (D9)

12. **As the PO, I want the toast to say where and why.** (D10; D2, D4 for the label)
    - **Given** a toast, **then** its title is `<workspace name> · <tab label>`, for example `squad-tabs · 🦀 Manager`. (D10)
    - **Given** the Manager stops, **then** the body is `Waiting for you`; **given** a permission prompt, `Permission prompt`; **given** a question waiting, `Question waiting`. (D10)
    - **Given** a non-squad session, **then** the title is built the same way from its workspace and tab, and the body is `Done` on stop and `Needs input` on needs-input. (D10)
    - **Given** the terminal's notification sequence can carry only one line of text, **then** the toast reads `<title>: <body>`, so the PO still sees workspace, label and reason. (BA decision B12; D10, D15)
    - **Given** herdr cannot tell the hook the workspace or tab (its CLI fails), **then** the toast still fires with the title `herdr` and the right body, and the active-tab skip cannot apply; **given** the herdr CLI hangs, **then** no toast after a short cut-off (about 3 s). (BA decision B13: a Manager waiting must not be lost, so a plain title beats silence; a hang is silence by B10.)
    - **Given** the tab was relabelled, **then** the toast carries the current label. (D4, D10)

13. **As the PO, I want exactly one toast per event, from one place.** (D11, D15)
    - **Given** herdr's `[ui.toast] delivery` is `"off"` and the plugin hook is active, **then** one event gives one toast, written by the hook, never two: observed as exactly one write to the client terminal per event (QA blackbox), and as one visible toast at the PO's check-in. (D11, D15)
    - **Given** the plugin is enabled user-wide (it is, in the PO's `~/.claude/settings.json`), **then** the one hook carries both the squad rule and the non-squad rule, and does the skip-active-tab and title work itself. (D11, D15)
    - **Given** `delivery` is still `"terminal"` (before story 14), **then** herdr still toasts every turn-end as today on top of the hook, so permitted events toast twice and workers still ping; the check-in says so. (D11, D12: accepted until the flip)

14. **As the PO, I want the one herdr config line changed for me, safely, and undoable.** (D12)
    - **Given** the spike (story 16) passed, **when** the integration step runs, **then** the Developer changes `delivery = "terminal"` to `delivery = "off"` in `~/.config/herdr/config.toml` only behind a permission prompt I approve; if I decline, nothing is changed and the check-in says toasts are doubled until I do it. (D12)
    - **Given** the change, **then** a backup `~/.config/herdr/config.toml.squad-tabs.bak` exists first, and the existing `config.toml.bak` is untouched. (D12)
    - **Given** the check-in, **then** it states the exact line changed and the one command to undo (restore the backup). (D12)

15. **As the PO, I want to know what stays as it is.** (D13, D14)
    - **Given** a non-Claude agent in herdr (codex, gemini, ...), **then** it no longer toasts once `delivery` is `"off"` (only if route A ships; under fallback B nothing changes for it); the PO accepted this (all the PO's agents are Claude). The check-in lists it as a known consequence. (D13)
    - **Given** the board's browser "needs you" notification, **then** it behaves as today: same triggers, same permission setting, and no change from this scope. (D14)

16. **As the PO, I want the notification route proven before anything is switched, and a safe fallback if it fails.** (D15)
    - **Given** the hook, **then** it is first proven in the throwaway workspace `squad-tabs-test`: with `delivery = "off"` on a test herdr server, a squad Manager stop and a blocked agent each produce a notification that reaches the client terminal; nothing is changed in the PO's herdr config for the spike. (D15)
    - **Given** the spike fails, **then** fallback B applies: labels, workspace rename and board labels still ship; `~/.config/herdr/config.toml` is left as is; every hook decision (D7-D13: the squad-only toast rule, the non-squad rule, skip-active-tab, title and body, one path, the config flip, non-Claude agents going quiet) is dropped for now, and the PO keeps herdr's own toasts with herdr's own active-tab skip and text (Manager's answer, 2026-10-14). D14 and D1-D6 are unaffected. The check-in says plainly that the toast part did not ship and why. (D15)
    - **Given** the spike passes, **then** stories 10-14 ship as written.

## Out of scope

- Renaming tabs that are already open: an open tab changes only when its agent is respawned or relabelled. The board covers old agents by story 8's fallback.
- A per-pane toast mute in herdr (round 3 option C; the PO may ask herdr separately).
- Toasts for rate-limit or API-error deaths (round 1 option 2 was not chosen).

## Known limits (accepted, not gaps)

- In a goal, one workspace holds several scopes and the label has no scope name (D2), so equal roles in two scopes read the same; only the task text tells them apart. Settled by D2 + D3; no escalation.
- Agreement with QA blackbox (2026-10-14): stories 1-9 and 15 are agreed as written; observation points are in `$SCOPE_DIR/evidence/qa-b-ac.md`. Stories 10-14 and 16 (reworded after D15) are agreed with QA blackbox (observation in `qa-b-ac.md`, section "Toast AC observation"): the hook is run with Claude-style Stop/Notification input and the bytes it writes to a test pty are checked; QA cannot see the Windows desktop, never edits `~/.config/herdr` (story 14 is checked by reading the config and backup files), so the real toast and the true double-toast check are the PO's at check-in.
- A Claude Stop can fire while a background subagent is still running, so a Manager may toast `Waiting for you` a little early. Accepted: an early ping costs less than a missed one.

## BA decisions in this spec (not in D1-D14; PO may overrule through the Manager)

B1 role display names · B2 stable numbers · B3 blank `squad-label` clears the task · B4 every respawn keeps its label · B5 an old `board` tab is reused · B6 a failed rename never stops a start · B7 side panel shows the address name · B8 board builds a label when none is stored · B9 no toast outside herdr · B10 the notifier never harms the session · B11 the Manager, not the QAs, relabels QAs · B12 one-line toast reads `<title>: <body>` · B13 plain `herdr` title when workspace/tab cannot be read · B14 a narrow board header keeps emoji, role and number and cuts the task text first. None cuts scope or changes a D; each fills a corner the decisions leave open.

## For `promote.md` (one line each, business rules and terms)

- Rule: a squad tab and an agent's name on the board read `<emoji> <Role>[ n] · <task>` (`🦀` Manager, `🤖` others, `📋 Board`), cut at 32 characters; the address name never changes.
- Rule: a squad session toasts (written by the squad hook to the herdr client terminal, herdr's own toast off) only when the Manager waits on the PO or any agent is blocked; non-squad Claude sessions toast on stop and needs-input; the active tab is never toasted.
- Rule: `squad-start` names the herdr workspace after the goal or lone scope (last start wins).
- Terms: display label, address name, task text, toast, squad session.
