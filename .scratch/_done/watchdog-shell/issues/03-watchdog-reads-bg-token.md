# 03 watchdog reads the bg token, cap, log reason
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: bin/squadboard_agents.py, bin/squad-watchdog, tests/test_squad_watchdog.py, tests/test_squadboard_agents.py, README.md, .claude-plugin/plugin.json, skills/squad-process-update/changelog.md
Goal: `../iterations/2.md`; report `../evidence/01/01-solutions.md` (option A, section 3 design notes). Branch from repo `main` (804c29c). Ticket 02 runs in parallel (it ships the hook that writes the token); this ticket is tested on recorded herdr JSON, so it needs nothing from 02. Do not add the ticket file to `.scratch/watchdog-shell/issues/` (02's first commit adds both).

## What and why
`squad-watchdog` calls an agent that waits for a background shell (a test suite) idle, nudges the Manager at 5 and 15 minutes, may stop on "all goals done", and may suspend the PC (ADR 0022, 0028). herdr reports such an agent's shell as `tokens.bg` in `herdr agent list`. Count an agent with a bg token as working, at most `SQUAD_WATCHDOG_BG_MAX` minutes (default 60), and log why.

## Samples (REV-4), both shapes are real
`herdr agent list` 2026-11-21, raw file `$SCOPE_DIR/evidence/03/herdr-agent-list.raw.json` (copy the two rows you need into a test fixture, rename the agent):
- token present: `{"agent_status":"done","name":"plugin-tl-watchdog-shell","tokens":{"bg":"⏵ 1 shell"}, ...}`
- token absent: the key `tokens` is missing from the row (every other agent, any status). `parse_herdr` also tolerates `"tokens": null`, `[]`, `{}` and `{"bg": ""}`: none is busy.
- Texts seen in the script: `⏵ 1 shell`, `⏵ 1 shell · 1 monitor`, `⏵ 1 monitor`. Never parse them: any non-empty `bg` string counts (a monitor-only token is busy; the cap covers a forgotten one).

## Design notes (Tech Lead)
- `parse_herdr` (pure): add the key `bg` (the token string) to a row only when `tokens` is a dict and `bg` a non-empty string; otherwise no `bg` key. `status` keeps its mapping. `read`'s board rows and `banner` do not change: the `FIELDS` set in `test_squadboard_agents` stays as it is (REV-6), and `test_T08_TA1_two_recorded_samples` (exact dict equality) stays green unedited (its rows have no token).
- `snapshot` adds `snap["bg"] = {name: text}` over the whole herdr list: only rows whose herdr status is `idle` (`done` included) and that carry a `bg` token. So `working`, `blocked` and `unknown` can never turn busy. `machine_working` stays "any row is `working`" (raw herdr).
- `decide(st, snap, now, sleep_enabled, sleep_after=..., bg_max=BG_MAX_MIN * 60)` stays pure and must not mutate `st` (copy the nested dicts; the shallow `dict(st)` is not enough). After the `snap["ok"]` early return:
  - `since` = new dict of `st.get("bg_since")` entries whose name is in `snap["bg"]` (a name with no token, working, blocked or gone drops out: this resets the clock), plus `now` for each new name. A state file without `bg_since` works.
  - `busy` = names in `snap["bg"]` with `now - since[name] < bg_max`. `bg_max <= 0` leaves it empty (the switch for "off").
  - A roster agent is working when its state is `working` OR its name is in `busy`. `working` feeds the idle test, the nudges and the stop test (`decide`, "stop" branch) unchanged, so a busy agent holds the idle spell closed and holds off the stop. The machine check becomes `not snap["machine_working"] and not busy` (all names, roster or not).
  - Save `st["bg_since"] = since` and `st["bg_busy"] = sorted(busy)`. Events, for roster agents only (another squad's agent is counted, never logged here): `("bg_busy", name, text)` for a name that enters `busy` (not in the previous `st["bg_busy"]`); `("bg_cap", name, minutes)` for a roster name that was busy, is still idle with a token, and is now past the cap. Nothing else logs when an agent leaves busy (it worked, or the token cleared).
- Clock rule (decided with QA whitebox, Q5): the cap counts one stretch of "idle with a token". It starts at the first pass the agent is idle with a token and resets on any pass where it is `working`, blocked, gone, or the token is absent. After the cap, the agent stays not busy while that stretch lasts: a refreshed token does not re-arm it. So a Monitor held for hours while the agent works does not use the cap up before a later `run_suite`.
- Cap env: `bg_max_s()` like `sleep_after_s()`: `SQUAD_WATCHDOG_BG_MAX` minutes, empty, non-number or negative → default 60; `0` → the bg rule is off (nothing counts as busy). Never raises.
- `tick` copies `st["bg_busy"]` into `snap["busy"]` after `decide`; `states_text` prints `<name> busy (bg shell)` for those names, otherwise as today (every existing log-text assertion stays green). Log lines (exact text; `clean()` from the module, cap in minutes):
  - `bg busy: <name> has a background shell (<clean(text)>); counted as working for at most <N> min`
  - `bg cap: <name> counted as working for <N> min; idle check resumes`
  A busy agent never starts an idle spell, so these two lines carry the reason; one pair per busy stretch, never one per pass.
- Docs: the module docstring (a line in the idle rules and the `Env:` line) and the README watchdog row (the row of `bin/squad-watchdog`) name `SQUAD_WATCHDOG_BG_MAX`, the 60-minute default, `0` = off, and the one rule: "a herdr `bg` shell token counts as working while the agent is idle with it, for at most N minutes". Also say there: herdr-bg's token expires 1 h after the last hook event, so a `SQUAD_WATCHDOG_BG_MAX` above 60 only helps if `TTL_MS` in `hooks/herdr-bg` is raised too. README: this ticket owns all README edits of the goal, so also add one row for `hooks/herdr-bg` (a `PostToolUse` and `Stop` hook wired in `hooks/hooks.json`; needs bash, jq and herdr; no-op without them; reports `bg=⏵ N shell` to the herdr pane).
- Out of scope: the board's agent status (`squadboard_agents.read`) keeps the herdr word; the `idle`-vs-`busy` word does not appear on the board.

## Technical AC
1. Parsing (T03.1): `parse_herdr` rows carry `bg` for the real present sample and no `bg` key for the real absent sample and for `tokens` `null`, `[]`, `{}`, `{"bg": ""}`. `status` identical to today. One test in `test_squadboard_agents.py`, plus `FIELDS` and `test_T08_TA1_two_recorded_samples` unedited and green.
2. Pure decide (T03.2): a test that `decide` leaves the passed `st` (nested dicts too) equal to a deepcopy taken before; a state without `bg_since`/`bg_busy` loads.
3. Busy rule (T03.3), one test: an `idle`/`done` roster agent with a token → no `idle start`, no nudge over 30 minutes of ticks; a `blocked` agent with a token stays `blocked` in the log text and still gets the 10-minute WAKE (`wake_events` unchanged).
4. Cap (T03.4), one test with `now=`: busy at minute 59; the idle spell starts after 60 min; nudges follow 5 and 15 min after that start, as today; second case: token held 70 min with one `working` pass at minute 50 → still busy until 110. A token that goes absent for one pass then returns starts a new stretch. `SQUAD_WATCHDOG_BG_MAX` = `""`, `abc`, `-5` → 60; `0` → never busy. `bg_since` has no entry for a name without a token (no growth).
5. Machine check (T03.5), one test: sleep switch on, a roster-less agent of another squad idle with a token → no `sleep pc` at 6 minutes, `sleep pc` once past the cap.
6. No early stop (T03.6), one test: every goal `done`, a roster agent busy on a bg shell → no `all goals done; watchdog stops`, no `stop` event; after the cap the stop comes.
7. Log reason (T03.7), one tick series: the two exact lines above appear once per stretch; `idle start`/`idle end` lines show `<name> busy (bg shell)` where it applies.
8. Docs: `grep -rn SQUAD_WATCHDOG_BG_MAX bin/squad-watchdog README.md` hits both files; the README has the `hooks/herdr-bg` row.
9. SQ-10 (the diff edits `bin/` and text a `bin/` tool prints): run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result in `## Behaviour`. Also run every hit of `grep -rl 'squad-watchdog\|squadboard_agents' tests/` (today: `test_squad_start`, `test_squad_log_message`, `test_squadboard_agents`, `test_squadtask`, `test_squad_watchdog`, `test_squadboard_inbox`).
10. Tests are added to the two existing files only, no new file, no matrix; the two real samples are the herdr-json fixtures.
11. Version bump (SQ-5, rides this ticket as the last one that edits plugin files): `.claude-plugin/plugin.json` `"version": "0.9.6"`; `grep -rn "0\.9\.5" .claude-plugin/` is empty after; add a `v19` entry at the top of `skills/squad-process-update/changelog.md` ("Plugin 0.9.6. The watchdog counts an agent with a herdr background-shell token as working for up to `SQUAD_WATCHDOG_BG_MAX` minutes (default 60); the plugin ships the `herdr-bg` hook.", `added:` and `changed:` lines like v18). Leave the `0.9.5` text in the v18 entry and ADR 0028 (history). No test hardcodes the version: re-run `grep -rln '0\.9\.5' tests/` on the bump sha (empty on base).

## Dry-run on base 804c29c (SQ-15)
- `test_squad_watchdog` 71, `test_squadboard_agents` 9, `test_squad_start` 49, `test_squad_log_message` 25, `test_squadtask` 15, `test_squadboard_inbox` 12, `test_windows_safe` 14, `test_utf8_helpers` 14, `test_instructions` 16: all OK.
- `grep -rn "0\.9\.5" .claude-plugin/` → 1 hit (`plugin.json:4`, the line to change); `grep -rln '0\.9\.5' tests/` empty; `grep -rn SQUAD_WATCHDOG_BG_MAX bin README.md` empty (fails on base as it must).
- Known failing on base: none.

## Deploy plan (Tech Lead writes, Chieu runs; LC-13)
1. Merge with 02; update the plugin to 0.9.6. The change is additive: with no `bg` token anywhere (hook not installed, herdr off) the watchdog behaves as 0.9.5. State files from 0.9.5 load (new keys `bg_since`, `bg_busy` appear on the next pass).
2. A scope pinned to 0.9.5 runs its pinned runtime until it closes (README, "pinned runtime"), so it keeps the old `squad-watchdog`. This scope (`plugin: 0.9.5`) is such a scope: the effect shows in the next scope or after a re-pin.
3. Rollback: revert the merge; no data to migrate.
4. Check after deploy: start `python3 tests/run_suite.py ...` in the background from an agent of a watched home; `watchdog.log` shows `bg busy: <name> ...` and no `idle start` while it runs; after the run, the next pass is quiet and `idle start` returns only if work waits.

## Evidence
`evidence.md` next to this ticket (EVID-1), `## Behaviour` with the test output and the SQ-10 runs.
