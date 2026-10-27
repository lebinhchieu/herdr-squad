# Process is composed per role from ID-tagged rules; a squad keeps only an overlay

Status: accepted (composed-process, PO answers D1–D16 2026-10-21/22)

Amended by 0018 (team replaces scope size): Sizes and Duty owners sections.

Supersedes 0005. Amends 0006: the Writing rule applies per rule block; processlint checks rule files.

**Decision:** the plugin's process is a folder of rule files, `templates/squad/process/*.md`. Each rule is one `## <ID> <title>` block with `roles:`, `aware:`, `when:` and `topic:` lines. A squad never copies it. Its own changes live in `process.local.md` as `replace`, `add` and `remove` operations on rule IDs, each pinned to a hash of the plugin text it changes. At spawn and respawn, `squad-process compose` keeps the rules whose `roles` or `aware` name the role and whose `when` matches the scope (`size`, `design`, `qa`, `goal`), adds `core.md`, and writes `roles/<agent>.rules.md`; `squad-spawn` attaches that file with `--append-system-prompt-file`. Role cards (`agents/*.md`) hold identity, stance and tools only. The Manager and the Tech Lead get their own rules plus a one-line index of every rule; `squad-process rule <ID>` prints any rule in full. Each scope records a plugin pin (`plugin:` in `scope.md`) and runs on that version until it closes; an upgrade applies between scopes only.

**Why:**
- The squad's `process.md` copy drifted from the plugin. The per-section merge forced the PO to pick or retype whole sections, and two Coach rules logged on 2026-10-19 are not in the merged file.
- Role cards load live from the repo working tree while `process.md` is a pinned copy, so one pod could run two process versions. This was confirmed on 2026-10-21 with two `claude --agent squad:<role>` probes.
- Claude Code concatenates instruction layers and "may pick one arbitrarily" on a contradiction, so an override must be resolved by a tool before an agent reads it.
- A section view targets rules by where they sit, so rules were copied into role cards and wrapped in "(S: …)" clauses.

**Consequences:**
- A rule ID is never reused or renamed in place. A removed rule leaves a tombstone in `process/_removed.md` (`why:`, `replaced_by:`). The process changelog lists added, changed, removed and retargeted IDs per version.
- An upgrade (`squad-process upgrade`) applies every rule the overlay does not touch. It lists for the PO only the stale operations (target hash changed), the operations whose target was removed, and the local rules that share a `topic` with a changed plugin rule. A contradiction between a local rule and a plugin rule of another ID is not detected by hashing; the topic list and an eval run are the only guard.
- An overlay operation carries `why:` and `upstream: proposed | local-only | rejected`. A `proposed` operation is offered as a plugin change at the scope's close and deleted once the plugin ships it.
- Settings follow the same pattern: the template plus `settings/<role>.local.json`, merged per key at spawn, with list values merged.
- `process-version:`, the section view, the hard-coded role map in `bin/squadprocess.py` and `squad-process apply` are retired after the live squad is migrated. `squad-migrate` (folder layouts) is unchanged.
- A change of size inside a scope changes the composed rules. The Manager respawns the roles that stay, after the Handover.
- Tests that pin wording in `agents/*.md` or `process.md` become tests on rule IDs and their targeting.

**Alternatives rejected:**
- Keeping the copy and per-section merge (0005): it already lost rules.
- No local edits, with every rule shipped as a plugin change: it rules out same-day fixes in a running squad. An empty overlay behaves the same, so nothing is lost by having one.
- Whole-file role-card shadowing through `.claude/agents/`: plugin updates to that role would be missed silently.
- Agents reading their view with `squad-process show` at start: attaching at spawn guarantees the rules are present and puts them in the cached prefix.

## Decisions made while building (composed-process, 2026-10-22)
- **Composed mode** = `process.local.md` exists in the squad folder; `process.md` alone is **legacy mode**. Composed mode with no `plugin:` pin refuses spawn and respawn (exit 2). A legacy squad gets its role's plugin rules composed from the running plugin with no overlay and no pin (ticket 24); its local `process.md` edits apply only after `squad-process adopt`. Installing the plugin therefore changes what an open legacy scope's next respawn reads: merge and install after every open scope closes, or run `adopt` first.
- Rule hash, composed-file tags and header, the prefix→file table and the pin format: `shared/contracts/rules-and-compose.md` of the goal (kept in the plugin as the tests that pin it).
- **Pinned runtime:** `git archive <sha>` into `$SQUAD_DIR/_runtime/<version>-<sha12>/`, shared per pin; a role launches with `--plugin-dir` on it and `PATH=<runtime>/bin:$PATH`, so role cards, rules and settings template all come from the pin. `squad-close` prunes runtimes held by no open scope, goal or `plugin.pin` (orphans included, the closing scope's own pin excluded, never the runtime it runs from; failure warns only).
- `plugin.pin` is written by `squad-start` and by the PO-confirmed `upgrade --apply --yes` or `adopt`. `adopt` also adds `plugin: <version> <sha>` to every open `scope.md`/`goal.md` that lacks one, listed in its dry run.
- **Upgrade compares** the overlay's hashes with the running plugin; the old rule set is the pinned runtime. `adopt` writes operations only for verbatim matches; everything else is listed for the PO.
- **Settings** = pinned template + `settings/<role>.local.json`. A `codePaths` key in an old local file is ignored (QA blackbox has no code-path Read deny).
- **Rule on demand:** a rule attached to no role is read with `squad-process rule <ID>`; `who <ID>` lists the roles and sizes it reaches. The composed Developer rules at S stay under 5120 B (`test_dev_rules_size`); a rule every role needs but a Developer rarely does becomes `aware:` or on demand.
- Lint also checks pointers in rule bodies (an unknown `[ID]` with a table prefix is an error). Role-card text that duplicates a rule fails `lint --cards`.
- **Sizes.** S = Manager + Developers; M = + QA whitebox and QA blackbox (QA blackbox absent when `qa-b: no`); L = every role. `ba`, `team-lead`, `tech-lead` exist only at L. A risk flag or a business doubt moves the scope to L. A `design: yes` scope adds the Designer at any size.
- **Duty owners** (rule retargeting never renumbers; a duty whose owner is absent at a size gets a variant ID for the role that took it):

| Duty | S | M | L |
|---|---|---|---|
| Plan, order, Developer spawning | Manager | Manager | Team Lead |
| Design notes per task | Developer | Developer | Tech Lead |
| Technical AC | Developer | QA whitebox with the Developer | Tech Lead + QA whitebox |
| Business AC | ticket as written | ticket as written (QA blackbox tests it) | BA |
| Code and test check | Developer + Sonnet review subagent (high effort) | QA whitebox | QA whitebox |
| Behaviour check | Developer's `evidence.md` | QA blackbox | QA blackbox |
| Hand-in goes to / done told to | Manager / Manager | QAs / Manager | QAs / Team Lead |
| Full suite (once, final sha) | Developer | QA whitebox | Tech Lead |
| `promote.md` | Developer | QA whitebox | Tech Lead |
| Migration, contract change, risk flag | Manager moves scope to L | same | Tech Lead |
| Irreversible design choice | Manager after an advisor call; PO-listed items stay with the PO | same | Tech Lead after an advisor call |
| 3 returns on a task | Manager | Manager | Team Lead |

- **S Done** = the Developer's checks + `evidence.md` + `## Review` written by one fresh-context review subagent on Sonnet at high effort (PO 2026-10-22; a new agent, not a fork) before `HANDIN`; the Manager only confirms both exist. **Advisor:** the built-in advisor is on, Opus, for every role (D15, D16); per-scope advisor on/off is not in `scope.md`, it is a squad-wide `settings/<role>.local.json` edit by the Manager on the PO's answer. LC-25 (stuck: 2 failed attempts, the same `BLOCKED` twice, or a Developer's 3rd FAIL) and LC-26 (irreversible choice) require an advisor call; a required call with the advisor off is skipped and the 3-line note says so.
- **Role defaults** come from `scope.md` `model <role>: <model> <effort>` lines (ticket 20) over `settings/<role>.json` over the template; `squad-start`/`squad-spawn` show the effective value and the PO confirms it.
- **Evidence** lives at `<ticket path minus .md>/evidence.md` (images in `img/`); see ADR 0015's update. `squad-evidence check --base` accepts a changed path only as `<stem>/evidence.md` or under `<stem>/img/`.
- **Return** in the process = a handed-in sha with at least one FAIL (two FAILs on one sha are one return); the squad report counts FAIL messages. The scope summary lists returns per task by failing sha.
- **Developer retirement:** a Developer retires (no respawn) at 120k tokens with a finished ticket and mid-ticket respawns once; the Manager is not exempt from the fresh rule. Drafts go in `$SCOPE_DIR/tasks/`, never untracked in the project root; plugin proposals from a retro reach the PO as `tasks/` drafts listed in the check-in. `qa: light` is proposed when `touches:` has no UI path and no risk flag.
- Hashes of rule IDs may change between unreleased versions; no pin carries the old text, so nothing is kept for them. **Alternatives rejected** (in addition to those above): an `S:`-clause inside rule text (lint forbids it; use variant IDs), a cap raise for the Developer rules (trim instead).
