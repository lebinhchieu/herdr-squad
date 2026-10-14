# squad-tabs: PO decisions from the grill (2026-10-14)

**Tabs read `<emoji> <Role>[ n] · <task>` with no squad or scope name; the workspace takes the scope (or goal) name; only the Manager waiting on the PO or a blocked agent raises a toast, and non-squad Claude sessions keep today's toasts.** Rounds: `round1.html`, `round2.html`, `round3.html` in this folder.

## Tab and board labels
- D1 The agent's address name (`<squad>-<role>-<scope>[-n]`, herdr's `[a-z][a-z0-9_-]{0,31}`) does not change. A separate display label is used for the herdr tab and for the agent's name on the board. (R1 Q3)
- D2 Label format `<emoji> <Role> · <task>`. Manager `🦀`, every other agent `🤖`, the board tab `📋 Board`. No squad or scope name in it. With no task text: `🦀 Manager`, `🤖 Tech Lead`. (R1 Q4 + note)
- D3 Two live agents of one role in a scope get a number: `🤖 Dev 1`, `🤖 Dev 2`. Labels are cut at 32 characters with `…`. (default)
- D4 The task text comes from `squad-spawn --title "<text>"`, blank by default. An agent relabels its own tab with `squad-label "<text>"` when it takes a new ticket; the Manager may relabel any agent. (R1 Q6 + note)
- D5 A Manager respawn keeps the `🦀` label; `squad-board-start` finds the board tab by its new label. Applies to every squad, legacy layout too. (default)

## Workspace
- D6 `squad-start` renames the caller's herdr workspace: the goal name for a goal, the scope name for a lone scope. The last start wins. Skipped when not inside herdr. (R1 Q5, R2 Q8)

## Notifications
- D7 Squad sessions: a toast only when the Manager stops (waits on the PO) or any agent is blocked (permission prompt or question waiting). Worker turn-ends are silent. (R1 Q1)
- D8 Non-squad Claude sessions: a toast on stop or needs-input, as herdr does today. (R2 Q11, R3 Q11)
- D9 The toast is skipped when its tab is the active tab of the focused workspace. (R2 Q10)
- D10 Title `<workspace> · <tab label>`; body is the reason: `Waiting for you`, `Permission prompt`, `Question waiting` (non-squad: `Done`, `Needs input`). (R2 Q9)
- D11 Mechanism: herdr's `[ui.toast] delivery` becomes `"off"`; one hook in the squad plugin (enabled user-wide) sends every toast with `herdr notification show`. Fact: herdr 0.9.4 has no per-pane toast filter. (R3 Q11)
- D12 The integration Developer changes `~/.config/herdr/config.toml` on its last step, behind a permission prompt the PO approves, keeping a backup `config.toml.squad-tabs.bak` (a `config.toml.bak` of yours already exists and must not be overwritten). (R3 Q12)
- D13 Non-Claude agents in herdr losing toasts is accepted (PO runs Claude only). (R3 Q13)
- D14 The board's own browser "needs you" notification stays. (R1 Q2)
- D15 (amends D11, escalation 1, PO 2026-10-14) With `delivery = "off"`, `herdr notification show` shows nothing (TL live test, evidence/design/toast-off-finding.md). Route: **A only**: the hook writes the OSC desktop-notification sequence to the herdr client terminal so WezTerm shows it, applying D9 and D10 itself. Spike it in `squad-tabs-test` first; if A fails, **fallback B**: leave herdr config as is and drop D7-D13 for now (herdr keeps its own active-tab skip and text); D14 stays. No PowerShell toast (C rejected).
