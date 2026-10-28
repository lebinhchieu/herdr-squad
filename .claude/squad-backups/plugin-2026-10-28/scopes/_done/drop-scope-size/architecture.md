# Architecture: drop-scope-size

Status: final

## Answer first

**Replace `size: S|M|L` with a team** the Manager proposes and the PO confirms. Plugin **0.6.0**, breaking.

- **Two fact layers** drive rules:
  1. **Presence facts** from `team:` in `scope.md`, one `when:` key per optional role: `ba`, `team-lead`, `tech-lead`, `qa-white`, `qa-black`, `design`, `architecture` (I3, PO-decided: `qa-b` is renamed `qa-black`, `qa-white` is new; the rest keep their names). The `team:` tokens and duty values use the same `qa-white`/`qa-black`; role and agent names stay `qa-whitebox`, `qa-blackbox`.
  2. **Duty facts**, derived by the composer from presence through **one fallback-chain table** that always ends at Manager or Developer. Every ownership rule says `when: <duty> = <owner>`. No rule is keyed on a role combination.
- **`size` disappears** from `when:`, `scope.md` and tools. Reports show an old scope's recorded `size` text only (section 5).
- **No shim, no dual support (I4, PO-decided).** No released engine reads `size:` or derives a team from it (a branch-internal build scaffold is allowed until the cutover task, constraint 1). It rejects `size:`, the `design:`, `architecture:`, `qa-b:` lines and the old `when:` keys with a pointer to the converter. **Every existing unpinned squad migrates with the converter to work**; a scope pinned below 0.6.0 stays on its pin's own tools (section 7).
- **ADR 0018** supersedes ADR 0016's Sizes and duty table and amends ADR 0017.
- **PO answered E4 (2026-10-27):** I1, I2, I5, I6, I7 as recommended; **I3 and I4 changed** (above). **Open:** I8 only (section 8).

### Notes

- **Author:** plugin-arch-drop-scope-size. Base: main 2949573 (0.5.2).
- **Amended 2026-10-27** for the PO's I3 and I4 (E4). Sections 1 to 8 and constraint numbers are stable; constraint 11 is new.
- **Inputs read:** ADR 0016, 0017, `CONTEXT.md`, `bin/squadrules.py`, `bin/squadcompose.py`, `bin/squad-spawn`, `bin/squad-log-message`, `bin/squadupgrade.py`, `templates/squad/process/*.md`, `tasks/tech-feasibility.md`.
- **BA answers** adopted (`tasks/spec.md` rules 1 to 6).
- **Tech Lead T1 check** done (`tasks/tech-t1-answer.md`, changes A to D folded in).

## 1. Components and modules touched

**Twelve areas change, no new dependency, vendor, data store or file format** beyond the `team:` line.

| Component | File(s) | Change |
|---|---|---|
| Rule language | `bin/squadrules.py` (`WHEN_KEYS`, `_conditions`, `matches`, lint) | drop `size`; rename `qa-b` to `qa-black`; add `ba`, `team-lead`, `tech-lead`, `qa-white`, `qa-black` and the duty keys with fixed value sets; `size` and `qa-b` are a lint and compose error in plugin rules and overlays, naming the rule |
| Composer | `bin/squadcompose.py` (`read_home`, `compose`, `who_lines`, header) | parse `team:`; validate; derive duty facts; **reject** old `scope.md` lines with the converter pointer (no shim); compact header; `who` prints per duty value. **Split `compose()` into load-once and a pure `choose(rules, role, facts)`**; the 128-set sweeps and `squad-team` call the pure part (about 3 ms per `effective_rules`) |
| Duty table | one table, `bin/squadrules.py` (`DUTIES`) | the chains of section 3; single source; a test renders it and compares it with the Manager's duty rule |
| Rule files | `templates/squad/process/*.md`, 201 `when:` lines in 17 files | mechanical retarget (same ID, new `when:`); collapsed twins tombstoned in `_removed.md`; changelog block; rule snapshot |
| Spawn | `bin/squad-spawn:111-118`, `bin/squad-respawn`, `bin/squad-start:367` | gate = "role is in the confirmed `team:`" for every optional role; refuse any non-Manager role while `team:` is undecided; refuse an unpinned old `scope.md` with the converter pointer; prompt text. **A scope pinned below 0.6.0 is handed off to the pin's own `$runtime/bin/squad-spawn` / `squad-respawn`** (same arguments; section 7) |
| Hooks | `bin/squad-log-message:43-69` | 3-returns routing keys on `team-lead` in team, not size |
| Report | `bin/squadreport.py:81,423,483`, `squadreport_rollup.py:88`, `templates/report/report.js:97`, `rollup.js:103,151,178` | new `team` field (display); an old scope's `size` is shown as a recorded string, never turned into a team; rollup `fSize` filter replaced by a team-role filter or removed |
| Scope template | `templates/scope/scope.md` | `team:` line replaces `size:`/`design:`/`architecture:`/`qa-b:`; "Done means" text |
| Migration | `bin/squadadopt.py`, `bin/squad-migrate:77-190`, `bin/squadupgrade.py` | `scope.md` converter (the only reader of `size:`); `squad-migrate` writes `team:`; upgrade lists stale ops and overlay ops using `size` or `qa-b` (no engine change) |
| New tool (optional) | `bin/squad-team` | `squad-team add|remove <role>`: edits `team:`, validates, composes before and after, lists roles whose text changed |
| Docs | ADR 0018 (draft in `tasks/`), `CONTEXT.md` glossary (Size removed, Team, Duty owner), README | promotion task |

## 2. The `team:` line (contract)

**`scope.md` carries one `team:` line**: `team: ba, tech-lead, team-lead, qa-white, qa-black, designer, architect` (any subset, any order, comma separated). Every subset of the seven optional roles is valid.

- **Implicit roles:** Manager, Developers and Token Coach are never listed.
- **`qa:` stays.** The `qa:` full/light line is orthogonal; the template keeps it.

| State | Meaning | Composer |
|---|---|---|
| `team:` blank | **undecided**: the Manager has not proposed or the PO has not confirmed | Manager role: all variants included, tagged `[if …]` (what an empty `size:` does today). Any other role: error, `squad-spawn` refuses |
| `team: none` | confirmed minimal team (Manager + Developers) | duty facts all end at Manager or Developer |
| `team: <roles>` | confirmed | normal |
| any of `size:`, `design:`, `architecture:`, `qa-b:` present (with or without `team:`) | old format | **error, exit 2** (`squad-spawn` exit 1): names the file and line and says to run the converter (I4). No team is derived |
| none of the four, no `team:` line | hand-made scope | treated as undecided |
| goal home | no team | all team facts missing; `matches()` keeps "missing counts as true" with `[if …]` tags, as today |

### Key names (I3, PO-decided)

| `team:` token (= duty value) | Role / agent name | `when:` key (`yes`/`no`) |
|---|---|---|
| `ba` | `ba` | `ba` |
| `team-lead` | `team-lead` | `team-lead` |
| `tech-lead` | `tech-lead` | `tech-lead` |
| `qa-white` | `qa-whitebox` | `qa-white` |
| `qa-black` | `qa-blackbox` | `qa-black` (was `qa-b`) |
| `designer` | `designer` | `design` |
| `architect` | `architect` | `architecture` |

- **Role and agent names stay** (`qa-whitebox`, `qa-blackbox`): `squad-spawn`, `squad-respawn` and the roster use them. One map `ROLE_KEY` (the two QA roles; every other role maps to itself) turns a role name into its token. Duty values (section 3) use the tokens: `behaviour-check = qa-black`.
- `qa-whitebox` or `qa-blackbox` as a `team:` token, and `qa-b` or `qa-whitebox` as a `when:` key, are rejected; the error names the new token or key.
- Term **QA** stays (the role's industry title).

**Missing-is-true applies only to goal homes and the undecided Manager.** For every other home the composer fills every team fact (never missing), so a forgotten fact cannot pull all roles' text into one file.

### Validity

**Compose refuses (exit 2, with the line to fix) only for:** unknown token, duplicate token, a token listed that is implicit (`manager`, `dev`, `token-coach`).

- **All 128 sets of the seven optional roles are valid**, as the BA's spec rule 3 and AC 10 require (P2, recommended all-valid).
- **Dropped refusal:** today's refusal of `design: yes` with `qa-b: no`. The built-UI check falls back along the chain (`ui-check`, section 3) to the Developer's screenshots confirmed by the Manager.
- **If the PO restricts shapes** (P2 alternative): `designer` requires `qa-blackbox`, and `qa-blackbox` requires `qa-whitebox` (64 sets). Nothing else in this design changes.
- **Test:** composes all valid sets × goal × qa in-process.

## 3. Duty facts and the fallback chain (the core contract)

**The first present role in each chain owns the duty.** Every chain ends at Manager or Developer, so no duty is orphaned for any valid set (tested). 13 rows.

| Fact | Values (chain, first present wins) | Replaces |
|---|---|---|
| `plan-owner` | `team-lead` > `manager` | plan, order, Developer spawning, routine messages, done-told-to, 3 returns (one chain) |
| `design-notes` | `tech-lead` > `dev` | design notes per task |
| `tech-ac` | `tech-lead` > `qa-white` > `dev` | technical AC |
| `business-ac` | `ba` > `ticket` | business AC |
| `code-check` | `qa-white` > `tech-lead` > `manager` | code and test check. Value = who signs it. `tech-lead`/`manager` mean the Developer's Sonnet review subagent (`## Review`) is the check and that role confirms it exists |
| `behaviour-check` | `qa-black` > `qa-white` > `manager` | behaviour check. `qa-white` checks the Developer's `## Behaviour` against the business AC (today's `qa-b: no`); `manager` confirms `evidence.md` `## Behaviour` exists (today's S) |
| `ui-check` | `qa-black` > `manager` | built UI against the design (only with `designer`); `manager` confirms the Developer's screenshots in `evidence.md` |
| `handin-target` | `qas` (`qa-white` or `qa-black` present) > `team-lead` > `manager` | hand-in goes to |
| `suite-owner` | `tech-lead` > `qa-white` > `dev` | full suite on final sha |
| `promote-owner` | `tech-lead` > `qa-white` > `dev` | `promote.md` (BA adds the business part by its own role rule) |
| `risk-owner` | `tech-lead` > `manager` | migration, contract change, risk flag |
| `doubt-owner` | `ba` > `manager` | business doubt, outside-decision question |
| `choice-owner` | `architect` > `tech-lead` > `manager` | irreversible design choice (architect or tech lead propose; PO decides; unchanged) |

**Principle (bounds the rewrite): one rule per (duty, acting role).**

- `when:` names only the duty value that makes *that role* act.
- A co-acting role has its own unconditional or presence-keyed rule. Examples: QA whitebox "agrees the technical AC with the owner", QA blackbox "tests the business AC", BA "adds business part to `promote.md`".
- So there are no S/M/L twin variants and no combination variants.
- Conjunctions are limited to one duty fact plus an orthogonal fact (`goal`, `qa`, `design`, `architecture`, `qa-black`). Today's `size = L and qa-b = yes` becomes `business-ac = ba and qa-black = yes`.

### Header

**`team: <list|none|undecided>` replaces `size X` in every role's header, except the Developer's.**

- **Developer header:** no `team:`. It saves bytes under 5 KiB; a Developer does not respawn on a team change, so a team line would go stale.
- **Manager, Team Lead, Tech Lead headers:** add one `duties:` line with the resolved owners (the static rule shows the chains; the header shows the result for this team).
- **Respawn diff** (section 4) ignores the `team:`, `composed:` and `agent:` header lines.
- **Rule bodies stay static text**, so hashes and lint are unchanged.

### Done (BA spec rule 4, agreed)

**Done = every checker on the team has passed.**

- `code-check` passed by its owner, AND
- `behaviour-check` passed by its owner, AND
- `ui-check` with a Designer.

With no optional role: Developer checks + `evidence.md` + `## Review` by the review subagent, and the Manager confirms both exist (today's S). Rules that say "both QAs" read "every checker on the team". The three facts sit on the same axis as `Done` in the BA's rule 3 chains, so the BA's table and this one are the same table.

### Missing facts (BA AC 11)

**An unknown `when:` key or value (including `size`) is a lint and compose error naming the rule ID; it never "matches".**

- Team facts are "missing" only for goal homes and an undecided-team Manager. There the `[if …]` tag shows the rule is conditional (as today).
- A scope home with a decided team never has a missing fact.

## 4. Manager proposes the team (replaces SIZE-1, SIZE-2, SIZE-3, SIZE-3a, SIZE-4)

**The Manager proposes each optional role from a signal; the PO confirms every role at the goal check, and `team:` records it.** New Manager rule, reusing `iterations/1.md` → Team as the template.

| Role | Propose when |
|---|---|
| BA | open business question, outside decision maker, unclear AC |
| Tech Lead | risk flag (migration, breaking contract, security, another team sees it), cross-repo |
| Team Lead | 4+ tasks, ordering matters, parallel Developers |
| QA whitebox | any code change (default yes unless the PO says no) |
| QA blackbox | something a person using the product sees (screen, CLI/hook output, exit code, generated file, message to the PO) |
| Designer | UI screens, states or flows change |
| Architect | irreversible choice likely (data model, new dependency, vendor) or a cross-cutting contract/boundary change |

- **Supersedes ADR 0017 and SIZE-3/3a** ("the Manager never proposes Designer or Architect"). The Manager now proposes them; the PO still decides.
- **S/M/L do not survive as presets** (I5).
- **SIZE-19 folds in** (today's `qa-b: no`): QA blackbox is simply not proposed.

### Mid-scope team change

**Replaces SIZE-13 to SIZE-17** (Handover kept, retitled; BA spec rule 5, agreed).

- **Add:** the Manager alone, except `designer` and `architect`, which wait for the PO (P1). `squad-team add designer|architect` refuses without `--po-ok` (a guard, not a proof). Steps:
  1. Edit `team:` (or run `squad-team add`).
  2. Write `## Handover` when any duty-fact value changes.
  3. Spawn joiners with a briefing that points at it.
  4. Respawn exactly the roles whose composed text differs. Method: before/after compose per roster role with fixed `--now`/`--agent`, comparing the `rules:` ID line, the rule bodies and, for the three index roles, the `duties:` line. Header lines `team:`, `composed:`, `agent:` are ignored, else every role is listed.
  5. Log it in the iteration file.
  6. Tell the PO at the check-in.
- **Remove:** only at an iteration boundary with the PO's OK. The duties move along the chain and the Handover names the new owners.
- **Late signals** (business doubt, risk flag, user-visible change, 4+ tasks, UI work, irreversible choice) map to roles in the BA's rule 5 list. The role that finds one sends `BLOCKED`/`ASK` to its `doubt-owner`/`risk-owner`; when that is the Manager, it adds the role.

## 5. Spawn, start, hooks, report

**Every tool that read `size` now reads the team through one parser.**

- **`squad-spawn`:** gate for `ba`, `team-lead`, `tech-lead`, `qa-whitebox`, `qa-blackbox`, `designer`, `architect` = present in `team:`. `dev`, `manager`, `token-coach` always. Non-Manager role + undecided team = exit 1. An unpinned old-format `scope.md` = exit 1 naming `squad-process adopt`. A home pinned below 0.6.0 is handed off (`exec $runtime/bin/squad-spawn`, same arguments; the pin's own gate, compose and prompts), so the new gate never reads its `size:`; if the runtime lacks the file, fall back to refusing with a warning. Bash reads `team:` through `squad-process team --home D [--has ROLE]`, the one parser; bash never re-parses.
- **`squad-start`:** prompt "size the scope" becomes "propose the team"; prints the proposed team and models for PO confirm. **No `--from-size`, no size hint:** a brief that says `size: S|M|L` is ordinary prose, the Manager still proposes from signals.
- **`squad-log-message`:** `team-lead` in team → notice to Team Lead (LC-7b), else Manager. The "S adds a budget line" branch becomes "no optional role in team". An old-format or unreadable `scope.md` (including a pinned scope's `size:`) falls to Manager (the hook already means "any problem: no notice").
- **`squad-respawn`:** unchanged (composes at respawn, so a team change shows).
- **Report:** `scope.team` string added; for an old scope the `size` text is displayed as recorded (`or ""` already tolerated), never mapped to a team; UI chip shows team initials, or the recorded size; `fSize` filter → role filter. Reading history for display is not dual support: no rule or duty depends on it.

## 6. Constraints the plan and designs must follow

**Ten constraints bind the plan and every task design.**

1. **Vocabulary first, no released shim (I4).**
   - Task 1 adds the presence and duty keys, `DUTIES`, `ROLE_KEY`, `read_home` (`team:`), validity and the old-format rejection.
   - **Branch-internal scaffold only** (Manager FINAL on the Tech Lead's D1): until the cutover task, `read_home` may fill duty facts for a home that still has `size:`, through the converter's mapping, so each task stays green while old rule files are alive. It exists only on the integration branch; the cutover task deletes it, and a **permanent test** proves no `read_home` path derives facts from `size` (the final `--tz` run on the sha the PO merges fails if it survives). No release carries it.
   - Rule-file tasks retarget by file group (disjoint files, parallel Developers) following section 3 exactly.
   - The cutover task removes `size`, `qa-b` from `WHEN_KEYS`, adds the old-format rejections and the lint (constraint 5), and deletes the scaffold.
   - Nothing ships between tasks, so there is no released half-state (I6 holds).
2. **Retarget, don't renumber.**
   - A rule whose body is unchanged and only `when:` moves keeps its ID (ADR 0016: a retarget).
   - Collapsed S/M/L twins keep the surviving ID; the others get tombstones in `_removed.md` with `replaced_by`.
   - New ID only for text that did not exist. `squad-process upgrade` already lists these.
3. **Dev 5 KiB cap stays.**
   - `test_dev_rules_size.py` iterates all 128 sets × goal × qa (in-process, no `product("SML")`), max ≤ 5120 B including the header. Worst set is "no optional role".
   - The pinned S+architecture exception is kept only if trimming cannot remove it; if kept, pin it by team set.
   - Lever: move rules to on-demand (`squad-process rule`), not raising the cap.
   - Plan a Dev-rules trim task (2 to 3 rules to `aware:`/on demand); "no optional role" is the likely worst set.
4. **No rule acts on an absent role.** Test over all 128 sets: every rule's `roles`/mentions resolve; every duty has exactly one owner present.
5. **No rule keyed on combinations.**
   - Lint rejects a `when:` with more than one key from `DUTIES` plus `{ba, team-lead, tech-lead, qa-white}`.
   - Extra facts allowed are only `goal`, `qa`, `design`, `architecture`, `qa-black` (the last three are team-derived presence keys but count as orthogonal).
   - Where a variant would need two (code check done by the Developer's review, confirmed by Tech Lead or Manager), the value encodes it (`code-check = tech-lead`).
6. **`who_lines`** prints per duty value (and per presence value for presence-keyed rules), not per size.
7. **Glossary terms in rule text:** Team, Duty owner (new in `CONTEXT.md`). "size" disappears from rule text except `_removed.md` and the changelog.
8. **Conform to ADR 0010** (Team Lead runs the pod when present) **and 0017** (Architect above the Tech Lead), except where ADR 0018 supersedes them.
9. **Tests that bind size are rewritten, not deleted.** List in `tasks/tech-feasibility.md`.
10. **Open-scope conflict (another scope's edits):** the open scope `squad-close` edits `templates/squad/process/` (closing.md etc.). Rebase before the rule-file tasks. Rule-file tasks touch disjoint file groups, so up to 3 Developers can work in parallel.

11. **Every old-format rejection names the file (and line, or rule ID) and says to run the converter** (the `size:`, `design:`, `architecture:`, `qa-b:` lines, and `size`/`qa-b` in a `when:`). Nothing is silently ignored or converted in memory.

## 7. Migration

**No shim (I4, PO-decided): every existing squad migrates with the converter to work.** The new engine and tools reject the old format with a pointer to it (constraint 11).

| Subject | What happens |
|---|---|
| **Converter** (`bin/squadadopt.py`; the Tech Lead names the command) | the **only released code that reads `size:`** (via the converter's mapping, `legacy_team`; used by nothing else). Per unpinned `scope.md`: `size` + `design`/`architecture`/`qa-b` → one `team:` line (S: `none`; M: `qa-white, qa-black` (no `qa-black` if `qa-b: no`); L: all but designer/architect; `design`/`architecture` add theirs; blank `size:` → blank `team:`). Removes the four old lines; keeps `qa:`, `goal:`, `touches:`, `model <role>:`. Dry run is the default and lists each file; the PO says yes; backup written; idempotent. First token only (`size: M (confirmed …)`, as `squad-close` parses) |
| Pinned open scopes (pin below 0.6.0) | **untouched; the converter skips them** and says so in its dry run (their pinned engine still reads `size:`). `squad-spawn`/`squad-respawn` from the PO's shell hand off to the pin's own `$runtime/bin/squad-spawn`/`squad-respawn`, so the pin's gate, compose and prompts run (Tech Lead D7). This is not a shim: the new engine never reads their `size:`. The hook and report only degrade (hook: Manager notice; report: recorded `size` text). I read the PO's I4 as about legacy squads meeting the new engine, so pinned scopes keep the 0.5.x guarantee (spec AC 20). If the PO wants them converted too, that is a new choice |
| Unpinned squads (legacy `process.md` only, e.g. `plugin-bk261023`, and composed scopes without a pin) | composed from the *running* plugin at the next respawn. That respawn **fails, exit 2, naming `squad-process adopt`** (the converter) until converted. `adopt` (process.md → overlay) and the `scope.md` conversion appear in one dry run |
| Overlays (`process.local.md`) | hashes change for every retargeted rule; `upgrade` lists the stale ops, ops on tombstoned IDs and same-topic local rules. **Every overlay `when:` using `qa-b` needs the exact rename `qa-black`; one using `size` needs a duty-fact translation.** `upgrade` lists each with the suggested text; the engine rejects both naming the rule. No auto-rewrite of PO-written text |
| `squad-migrate` | writes `team:` from the old `scopes.md` size row via the converter mapping `legacy_team` |
| Report | closed and old scopes show their recorded `size` text; no team is derived (section 5) |
| Deploy order | finish open scopes if possible; run the converter dry run on unpinned squads **before** any respawn under 0.6.0; pinned scopes keep their runtime (PO runs it) |

**Dropped with the shim:** the released `read_home` size path, the `size` fact, `team_source: "size"`, the "derived from size" header, `squad-process team --from-size`, the brief's size hint (spec AC 8), the shim-removal release, and tests that pin legacy homes to the old compose output. **Kept (not shim):** the branch-internal scaffold (constraint 1), the pin hand-off, the converter's mapping.

## 8. Irreversible and contract choices (PO decides)

**PO answered I1 to I7 (E4, 2026-10-27).** I1, I2, I5, I6, I7 accepted as recommended; **I3 and I4 changed by the PO**. I8 is the only open row. None adds a dependency or vendor.

| # | Choice | Options | Recommendation / decision |
|---|---|---|---|
| I1 | Targeting model | (a) presence facts + derived duty facts via one chain table; (b) presence facts only, authors write combinations; (c) internal presets (S/M/L renamed) | **PO: (a) accepted.** (b) is unbounded (2^7); (c) is size again and keeps the same coupling |
| I2 | `scope.md` shape | (a) one `team:` line, flags `design:`, `architecture:`, `qa-b:` removed; (b) keep the three flags plus a `team:` for the rest; (c) one line per role | **PO: (a) accepted.** one source of truth, one thing for the PO to read and confirm. (b) lets two lines say the same thing; (c) is longer for no gain |
| I3 | `when:` keys | (a) keep `design`, `architecture`, `qa-b` as keys derived from the team, add `ba`, `team-lead`, `tech-lead`, `qa-whitebox`; (b) rename all to role names; (c) role-aligned QA keys, rest unchanged | **PO decided (c), changing my (a):** `qa-b` → `qa-black`; new key `qa-white` (for `qa-whitebox`); `ba`, `team-lead`, `tech-lead`, `design`, `architecture` unchanged. Role and agent names stay; term QA stays. Cost: every rule and overlay using `qa-b` is renamed (23 `when:` lines in the rule files, more in tests; overlays listed by `upgrade`, section 7) |
| I4 | Legacy-mode squads meeting the new engine | (a) read-side shim from `size:`; (b) fail closed with a pointer to the converter; (c) converter only | **PO decided (b) + (c), changing my (a)+(c):** no shim, no dual support. The released engine rejects `size:`, the old `scope.md` lines and the old `when:` keys with a pointer to the converter; every existing squad migrates with it (sections 2, 5, 7). Cost: unpinned open squads stop composing on 0.6.0 until converted. Pinned scopes are not part of I4: they keep their pin (hand-off, section 7) |
| I5 | Do S/M/L survive as Manager presets | (a) vanish; (b) named presets the Manager picks from | **PO: (a) accepted.** a preset is a size under another name |
| I6 | Release | (a) 0.6.0 breaking, `size` rejected in `when:`; (b) 0.5.3 with `size` still accepted for overlays | **PO: (a) accepted.** a half-state would mean two targeting languages in the rules |
| I7 | `squad-team` tool | (a) add; (b) Manager edits `team:` by hand | **PO: (a) accepted.** reversible, small; the respawn list by diff is the part worth having |
| I8 | Team shapes (BA's P2) | (a) all 128 valid; (b) forbid designer without QA blackbox and QA blackbox without QA whitebox | **Open; recommend (a)**: chains cover every shape, a test covers every shape, the Manager's signals keep odd shapes rare. Cost of (a): drops today's refusal of designer without QA blackbox; `ui-check` falls to the Manager |

Advisor consulted before writing these (LC-25 note at the end).

## 9. Open questions

**Only I8 remains open.** BA answered A1, A2, A4, A5 in `tasks/spec.md` (rules 2 to 5): adopted above. A3 is now the PO's P2 = I8 here.

| # | To | Question | Status |
|---|---|---|---|
| P1 | PO (via BA, Manager) | Manager adds Designer or Architect mid-scope only after the PO says yes | BA proposes yes; adopted |
| P2 = I8 | PO | all 128 shapes valid | open, recommended (a) |
| I1 to I7 | PO | section 8 | **answered (E4)**: I1, I2, I5, I6, I7 as recommended; I3, I4 changed, recorded above |
| T1 | Tech Lead | `squad-process team`, `squad-team`, 128-set sweep | answered feasible with changes A to D, all folded in (`tasks/tech-t1-answer.md`; task shape F there is the Tech Lead's to design) |

## Advisor note (LC-25, SIZE-9a)

- **Question:** is a presence + derived-duty-fact model the right targeting, and what did I miss?
- **Advice:** keep duty facts as the backbone; add team validity edges, split missing-fact handling by home type, list legacy-mode squads as an irreversible choice (answer: I4, no shim), keep `design/architecture/qa-b` as derived facts (superseded by I3: `qa-b` → `qa-black`), compact header for the 5 KiB cap, list every tool reading `size`.
- **Done:** all folded into sections 2, 3, 5, 7, 8.

## Amendment note (2026-10-27)

- **Why:** PO answers E4 for I3 and I4. Both are PO decisions, not new recommendations, so no new advisor call.
- **Changed:** key names and `team:` tokens (I3); shim, `--from-size`, size hint removed, pinned scopes handed off to their pin, branch-internal scaffold allowed (I4, Tech Lead D1/D7); sections 1 to 8, constraint 1, 5, 11; Migration rewritten.
- **Unchanged:** section numbers, constraints 2 to 4 and 6 to 10, the chain table, the 128-set validity.
