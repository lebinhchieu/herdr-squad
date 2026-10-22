Status: ready-for-agent (starts when TAB-01..04 and TAB-06 have passed QA whitebox, and TAB-05 has passed or closed as "dropped, route B")
Task ID: TAB-07
Blocked by: TAB-01, 02, 03, 04, 06, 05
Files touched: the merge of the passed branches into this branch; `~/.config/herdr/config.toml` (PO's machine, one line, only with the PO's approval); new `~/.config/herdr/config.toml.squad-tabs.bak`
Serves: spec stories 13, 14, 15 and the whole scope's integration

# TAB-07: integration, the herdr config change, and the live check

**Done when the passed branches are merged and the full suite is green, the labels and workspace name are checked live in a throwaway workspace, and (if the PO approves) herdr's toast delivery is `"off"` with a backup and the one-line undo written down.**

Read first: `process.md` → Stacked branches and Safety, spec stories 13-15, D11-D13, `evidence/design/toast-off-finding.md`, D15 in `decisions.md`.

## Build
1. Branch from the iteration's base; merge the passed `squad/squad-board/squad-tabs/*` branches into **your own** branch (order: 01, 03, 02, 04, 06, then 05). Resolve conflicts only inside the merge; no new features.
2. Run the full suite once on the final sha (`nice -n 10 python3 tests/run_suite.py --receipt <evidence dir> --tz`, under the lock `process.md` names) and save both receipts.
3. **Live check** in a throwaway workspace `squad-tabs-test` (`herdr workspace create --label squad-tabs-test`; closed at the end; never the PO's workspace): `squad-board-start` (tab `📋 Board`, then again: reused), one real `squad-spawn` of `token-coach` with `--title` (tab label, address unchanged), a second `dev`-role-numbering check using the label store without starting a second real session if possible, `squad-label` self and `--agent`, `squad-respawn` keeps the label, `herdr workspace rename`. Save each command and its output in `evidence/TAB-07/`. Close what you open (tabs, boards, browser).
4. **Toast check and config flip: only when TAB-05 passed (route A proven by its spike, D15).** If TAB-05 closed as "dropped, route B", skip this step and step 5's config lines: herdr's config stays untouched and `handover-to-po.md` says D7/D8 are not delivered. Order matters, because after the flip herdr stops toasting everything and only the hook toasts: (a) route A's spike passed (`evidence/TAB-05/spike.md`) and the merged hook passes its tests; (b) ask for the permission prompt; the PO approves it; (c) `cp -n ~/.config/herdr/config.toml ~/.config/herdr/config.toml.squad-tabs.bak` (the file `config.toml.bak` already exists and is **never** written or removed; if `config.toml.squad-tabs.bak` already exists, stop and ask); (d) change exactly the line `delivery = "terminal"` under `[ui.toast]` to `delivery = "off"` with an exact, anchored replacement (no other line changes: check with `diff` against the backup); (e) `herdr server reload-config`; (f) one marked test event through the hook in `squad-tabs-test` and the PO confirms it saw exactly one toast, and that a worker `Stop` in a squad session gives none. If (f) fails (none, or two), restore the backup at once (`cp` + `herdr server reload-config`) and report; the config is never left in `"off"` without a working hook. If the PO declines the prompt, change nothing and report "toasts are doubled until you do it".
5. Write `evidence/TAB-07/handover-to-po.md`: the exact line changed, the undo command (`cp ~/.config/herdr/config.toml.squad-tabs.bak ~/.config/herdr/config.toml && herdr server reload-config`), that the hook is dormant until `delivery = "off"` (so merging it before the flip does not double toasts); what stays as is (D13 non-Claude agents lose toasts; D14 board browser notification unchanged), and that open tabs keep their old names until respawned.

## Technical AC
1. Merge: `git log --merge`-style check that each passed branch's sha is an ancestor of the integration branch; no conflict markers; the diff against the base contains only the files named in tickets 01-06.
2. Receipts `suite-default.txt` and `suite-tz.txt` first line `sha <HEAD> clean=yes` and `Ran N tests ... OK`.
3. Live evidence exists for every item in Build 3, and the throwaway workspace and its tabs are gone at the end (`herdr workspace list` output in evidence).
4. Config: `diff config.toml.squad-tabs.bak config.toml` shows only the one `delivery` line; `config.toml.bak` has the same checksum before and after (record both); no `config.toml` write happens before the PO approved the prompt.
5. Nothing is pushed; the PO's own workspace tabs are not renamed or closed.
