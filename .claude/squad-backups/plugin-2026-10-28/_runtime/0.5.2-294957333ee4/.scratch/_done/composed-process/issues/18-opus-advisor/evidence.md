# Evidence 18: rules for the Opus advisor

Branch `squad/plugin/sizes-and-models/plugin-dev-sm-18`.

## Behaviour
1. **AC5, advisor tool present with Haiku.** `claude -p --settings '{"model":"haiku","advisorModel":"opus"}' "Is a tool named advisor present? Reply with one word: yes or no."` → `yes`.
2. **Off value** (QA whitebox probe, same command): `"advisorModel":""` → `no`, settings load; `null` → settings file refused ("Expected string, but received null"). The overlay test uses `""`.
3. **Rules.** `who`: LC-25 = all roles incl. dev (3rd FAIL for the Developer); LC-26 = manager, tech-lead (S, M, L). COST-11 replaced. LC-25 defines the 2 rounds (same `BLOCKED` twice, no `ANSWER`) and the advisor-off case.
4. **Notice.** 3rd failing sha → "...consult the advisor before the next HANDIN; note it in the task file [LC-25]" (`test_squad_ledger` pins the full text).

5. **Dev rules cap (5120 B, ticket 22) kept.** LC-24 merged into LC-25 (Tech Lead DECISION 18); NOTE-1 no longer targets dev (still one `squad-process rule NOTE-1` away, added to `test_lost_rules_are_one_command_away`); COST-5's "ticket touching at most 2 files goes first to a live Developer…" sentence dropped (duplicate of COST-6a/6b, which dev does not act on). Worst combo now fits.

## Commands
`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_advisor_rules test_model_effort_settings test_squad_log_message test_squad_ledger test_processlint test_dev_rules_size test_team_lead_role`; `squad-process lint`.

## QA whitebox review

### QA whitebox, ticket 18 — PASS @ 61d35ac

Bar: ticket 18 Technical AC + `tasks/tech-ac.md` "18 (additions)" + Tech Lead DECISION 18 (per the Developer: LC-24 merged into LC-25).

History: 08c7907 FAIL (overlay test used `advisorModel: null`, which Claude Code rejects; no evidence; decision-7 wording; weak notice test). 61d35ac re-checked.

Checked at 61d35ac:
- `test_advisor_rules test_model_effort_settings test_squad_log_message test_squad_ledger test_processlint test_dev_rules_size test_team_lead_role`: 92 OK; `squad-process lint` rc 0.
- Overlay test uses `""`; I probed `""` earlier: advisor off and settings load; `null`: whole settings file refused.
- LC-25 text: 2 failed attempts at one error, same BLOCKED twice with no ANSWER, Developer's 3rd FAIL, 3-line note, "Advisor off: skip and say so". LC-26 (manager, tech-lead) points at the LC-25 note. `who LC-25` = all roles, `who LC-26` = manager, tech-lead.
- 3-return notice: AC wording, cites `[LC-25]`; test resolves it with `squad-process rule LC-25`; `test_squad_ledger` pins the full emitted text.
- COST-11 replaced. `evidence.md` has both probes, `## Behaviour`.

Out-of-list touches (Tech Lead to accept, none wrong): `cost.md` COST-5 sentence dropped (duplicated at cost.md:44 and :51, which Developers do not act on); `notes.md` NOTE-1 no longer targets dev (still `squad-process rule NOTE-1`; added to the lost-rules test); `tests/test_dev_rules_size.py`, `tests/test_squad_ledger.py`. Done to keep Developer rules under the 5 KiB cap after LC-25.

Note for Tech Lead: the ticket-18 AC "3rd FAIL → dev" is now carried by a clause inside LC-25 (all roles), so `who` cannot show it as dev-only.

## QA blackbox review

### QA blackbox, ticket 18 @ 08c7907 — PASS

Method: scratch squad /tmp/qab19/r (stub `claude`/`herdr`), CLI from the Developer's worktree; code not read.

| AC | Did | Saw | Result |
|---|---|---|---|
| Three required triggers are separate rules with IDs; `who` shows acting roles | `squad-process who LC-24 / LC-25 / LC-26`, `rule <ID>` | LC-24 3rd FAIL: dev (S, M, L). LC-25 stuck (2 failed attempts at same error, or BLOCKED unanswered 2 rounds): manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, dev. LC-26 irreversible choice: manager, tech-lead | PASS |
| Each required call leaves a 3-line note (question, advice, done) | `rule LC-24/25/26` | all three name the note in the task file | PASS |
| "Outside these, the model decides" | `rule LC-26` | "Outside [LC-24], [LC-25] and this rule, you decide when to consult it." | PASS |
| Step-up replaced | `rule COST-11` | "consult the advisor first ([LC-25]). Effort may step up for that task only; a model never changes in a live session, only by respawn." | PASS |
| 3-return notice tells Developer to consult the advisor | piped PostToolUse SendMessage JSON to `squad-log-message`: HANDIN+FAIL on 4 shas, task 05 | silent on returns 1, 2; on the 3rd failing sha: `task 05 has 3 returns: also send BLOCKED 05: 3 returns to Team Lead [LC-7b]; tell the Developer to consult the advisor before the next HANDIN and note it in the task file [LC-24]`; silent on the 4th | PASS |
| advisorModel opus in every role template | grep settings/*.json | present in all 9 | PASS |
| Squad can turn advisor off per role (overlay, composed squad) | `settings/qa-blackbox.local.json` `{"advisorModel": ""}` (+codePaths), spawn qa-blackbox | spawn settings file has `"advisorModel": ""`; a role without overlay (ba) keeps `opus` | PASS (value merges; whether Claude Code treats "" as off I did not verify) |
| Haiku + advisor opus probe | `claude -p --model haiku --advisor opus "Do you have a tool named advisor? yes or no"` | `Yes.` | PASS |

#### Observations (not fails)
- Business AC A4 (define "BLOCKED unanswered for 2 rounds") and A5 (required call skipped with a note when advisor is off/unavailable) were proposals to the Tech Lead; LC-25 still has no definition and no off-case text.
- COST-11 `who` omits dev; the old step-up rule's reach is unchanged by me checking only wording.

---
### Re-check @ 61d35ac — PASS

| Check | Saw | Result |
|---|---|---|
| Triggers after merge | LC-24 gone (`no such rule`). LC-25 (all roles incl. dev): "after 2 failed attempts at one error, the same BLOCKED sent twice with no ANSWER, or (Developer) a 3rd FAIL" + 3-line note + "Advisor off: skip and say so." LC-26 (manager, tech-lead): irreversible choice, uses the [LC-25] note | PASS (A4, A5 now covered) |
| COST-11 | unchanged: advisor first, effort may step up, model only by respawn | PASS |
| 3-return notice | silent on returns 1, 2, 4; on the 3rd failing sha: `...tell the Developer to consult the advisor before the next HANDIN; note it in the task file [LC-25]` | PASS |
| Overlay off | `"advisorModel": ""` reaches the spawn settings; `null` also spawns here (Dev says null breaks Claude's settings load; not checked) | PASS |
| NOTE-1 | `who` lists no dev; text unchanged otherwise | observation: dev no longer reads the notes-file rule |

Observation: "each trigger one rule" (ticket AC4) now holds for two rules; the 3rd-FAIL trigger lives inside LC-25, so `who` cannot show "dev only" for it; the text says "(Developer)".
