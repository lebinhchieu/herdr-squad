Status: ready-for-agent (PO chose route A, D15; the spike (AC 6) decides whether the rest is built)
Task ID: TAB-05
Blocked by: none (no code dependency on TAB-01..04)
Files touched: new `bin/squad-notify`, `hooks/hooks.json`, new `tests/test_squad_notify.py`, `tests/test_hooks_json.py` (new, if none exists)
Serves: spec stories 10, 11, 12, 13 (D7-D11, B9, B10)

# TAB-05: one hook decides and sends every toast (route A, D15)

**Done when one plugin hook turns Claude `Stop` and `Notification` events into at most one toast each, by the squad rule or the non-squad rule, never slowing or failing the session.** `herdr notification show` is disabled by `delivery = "off"` (finding: `evidence/design/toast-off-finding.md`), so the hook delivers itself: **route A, D15: it writes the OSC desktop-notification sequence to the herdr client's terminal, and WezTerm shows it.** `deliver(title, body)` stays a small seam so the decision logic is testable without a terminal.

## Delivery: route A (D15)
- **Find the client tty:** the herdr *client* is the process named exactly `herdr` (argv is just `herdr`, no `server`) that has a controlling tty; the server is `herdr server` with tty `?`. Today: pid 136143 on `/dev/pts/0`, parent `bash`. Scan `/proc/<pid>/` for `comm == herdr` and `cmdline == herdr`, take the link of fd 1 (`/proc/<pid>/fd/1 -> /dev/pts/N`), and only accept a path under `/dev/pts/`. Write to **every** client tty found (one per attached terminal window); none found -> no toast, one stderr log line.
- **Write:** open the tty `O_WRONLY|O_NOCTTY|O_NONBLOCK`, write `ESC ] 777 ; notify ; <title> ; <body> ESC \` (WezTerm accepts OSC 777 and OSC 9). Strip control characters and `;` from title and body before writing, so a tab label cannot inject escape sequences. Never touch the pane's own tty (it is not the client's).
- **Dormant unless herdr's own toast is off:** the hook acts only when `[ui.toast] delivery` in `$HERDR_CONFIG_PATH` (default `~/.config/herdr/config.toml`) reads `"off"`; any other value or an unreadable file -> no toast. This keeps the PO from getting two toasts in the window between merging the plugin and the config flip (TAB-07), and keeps fallback B harmless. A line-anchored regex is enough; no TOML library.
- **Fallback B (fail criterion in AC 6):** if the spike fails, the Dev stops, reports to the Manager, **builds none of the hook** and leaves `hooks/hooks.json` as it is; the ticket closes as "dropped, route B". D7/D8/D11/D12 are then not delivered, and TAB-07 skips its step 4.

## Design (fixed)
- `hooks/hooks.json`: `Stop` (add next to `squad-usage-hook`) and `Notification` with matcher `permission_prompt|elicitation_dialog`, both calling `"${CLAUDE_PLUGIN_ROOT}/bin/squad-notify"` with `"async": true` and a short timeout. `idle_prompt` and other notification types do not toast.
- **Decide** (a pure function over: event, `notification_type`, `SQUAD_NAME`, `SQUAD_ROLE`; testable with no herdr):
  - Not in herdr (`HERDR_ENV` != 1) -> nothing (B9).
  - Squad session (`SQUAD_NAME` set): `Stop` -> toast only when role is `manager`, body `Waiting for you`; `Notification` `permission_prompt` -> `Permission prompt`; `elicitation_dialog` -> `Question waiting`, any role (D7, D10).
  - Non-squad session: `Stop` -> `Done`; `Notification` -> `Needs input` for both types (D8, D10).
  - Subagent `Stop` events (payload has `agent_id`) do nothing.
- **Skip** (D9): when `herdr workspace get $HERDR_WORKSPACE_ID` says `focused` and its `active_tab_id` equals `$HERDR_TAB_ID`, no toast (fields verified on herdr 0.9.4: `result.workspace.{focused,active_tab_id,label}`, `result.tab.{label,focused}`).
- **Title** `<workspace label> · <tab label>` read live from herdr at the event (so a relabel is current, D10 and story 12).
- **Never harm the session** (B10): always exit 0, no stdout, all herdr calls and tty writes under a 3 s timeout (non-blocking open and write), errors to a log line on stderr only; async hook so Claude never waits.

## Technical AC
1. Decision table test: every (event, type, squad/non-squad, role) combination in the spec stories 10 and 12, including worker `Stop` = nothing, Manager `Stop` = `Waiting for you`, worker blocked = toast, subagent `Stop` = nothing, `idle_prompt` = nothing, outside herdr = nothing.
2. Skip test: focused workspace + active tab = none; other tab, other workspace, unfocused workspace = toast.
3. Title/body test with a fake `herdr`: title `squad-tabs · 🦀 Manager`; a relabelled tab gives the new label.
4. Failure test: herdr hanging or exiting non-zero, no client found, a tty that cannot be opened -> exit 0 within the timeout, nothing on stdout.
4b. Delivery tests (a pty pair from `os.openpty()` stands in for the client tty; no real herdr or WezTerm): the written bytes are exactly the OSC 777 sequence; `;` and control characters in the title or body are stripped; a fake `/proc` tree (the function takes the proc root as a parameter) finds the client (`comm=herdr`, argv `herdr`) and ignores `herdr server` and a path outside `/dev/pts/`; two clients -> two writes; config `delivery = "off"` -> toast, `"terminal"`, missing key, missing file -> none.
5. **Real samples** (`process.md`/Tech Lead rule): the Dev saves one real `Stop` payload and one real `Notification` payload (a permission prompt) captured by a recording hook in the throwaway workspace `squad-tabs-test`, in `evidence/TAB-05/`, and the parser tests use them (field names, `notification_type`, `agent_id` on a subagent stop).
6. **Spike first, before any other code (time-boxed, 1 hour of Dev time):** prove route A. A throwaway script (not committed) finds the client tty by the rule above and writes one OSC 777 toast titled `squad-tabs test`. The Dev announces it to the Manager (`ASK`), who has the PO watch the desktop; it fires from a pane in the throwaway workspace `squad-tabs-test`. **Pass:** the PO sees a WezTerm desktop notification with that title. **Fail (-> fallback B):** no client tty found, the write errors, or the PO sees nothing after two attempts (second attempt: the OSC 9 form `ESC ] 9 ; <title>: <body> ESC \`; if only OSC 9 shows, build with OSC 9 and say so in the evidence). At most those two live toasts; no other live toasts, no second channel (C is rejected). Save the script, its output and the PO's answer in `evidence/TAB-05/spike.md`.
7. Exactly one toast per event when `delivery = "off"` and the hook is active (story 13): shown by the decision tests (no code path sends two: one write per client tty per event) plus the live one-toast check in TAB-07 step 4(f).
8. Hook entries in `hooks.json` are valid JSON, keep the two existing hooks unchanged, and a test loads the file and checks the new entries' events, matcher and command.
9. Targeted tests pass; full suite once on the final sha.

## Notes
- Python or bash, your choice; keep the decision function importable for the test.
- The hook runs in every Claude session of the PO (plugin enabled user-wide), so its start must be cheap: no network, no heavy imports.
- **Known limit (Tech Lead, 2026-10-14, from dev-3's finding):** a Manager `Stop` can fire while a background subagent still runs (`background_tasks` non-empty in the real `Stop` sample), so "Waiting for you" may toast slightly early. Accepted: the failure is an extra toast, never a lost one, and a Manager rarely runs background subagents. No AC added; the hook does not read `background_tasks`. `SubagentStop` is a separate event the hook is not wired to, so the `agent_id` guard stays defensive only.
