# composed-process: each role gets only its rules, and plugin changes reach squads one rule at a time

Status: ready-for-agent
Decision record: `docs/adr/0016-process-composed-per-role.md` (proposed; accepted when this effort merges)
PO answers: D1–D7, 2026-10-21 (below). Also covers the 9 findings of the 2026-10-20 process review (map below).

**Outcome:**
- Every agent starts with exactly the rules for its role and its scope's size, attached to its system prompt. For a Developer that is about 3–4 KB, against 8.6 KB of sections today (24.4 KB for the whole file).
- A plugin process change reaches a squad between scopes. It never loses a squad rule, and it asks the PO only about the rules the squad itself changed.
- A pod runs on one pinned plugin version from start to close.

## PO decisions (D1-D7 2026-10-21; D8-D16 round 1, 2026-10-22)

| # | Decision |
|---|---|
| D1 | Rules are markdown blocks: `## <ID> <title>`, then `roles:` / `aware:` / `when:` / `topic:` lines |
| D2 | `squad-spawn` attaches the composed rules with `--append-system-prompt-file` and saves them as `roles/<agent>.rules.md` |
| D3 | `core.md` (task states, message types, who owns what) goes to every role, and `aware:` tags carry what a role must know without acting |
| D4 | Manager and Tech Lead get their own rules plus a one-line index of every rule; full text on demand (`squad-process rule <ID>`) |
| D5 | Squad changes live in `process.local.md` as hashed operations; `upstream: proposed` operations flow to the plugin |
| D6 | Upgrades apply between scopes; a running scope keeps its pin |
| D7 | ADR 0016 replaces ADR 0005; this spec and its tickets live here |
| D8 | Sizes: S = Manager + Developers; M = + QA whitebox, QA blackbox; L = every role (Designer only with `design: yes`) |
| D9 | S done = Developer's checks + `evidence.md` + one fresh-context Opus review subagent before HANDIN; the Manager only confirms both exist |
| D10 | In S and M the Manager plans and spawns Developers (exception to "never does a role's work"); each Developer writes its design notes in the task file |
| D11 | M: QA whitebox writes technical AC (agreed with the Developer) and keeps `promote.md`; business AC = the ticket as written, tested by QA blackbox; a business doubt moves the scope to L. S: the Developer keeps `promote.md` |
| D12 | Full suite: S the Developer, M QA whitebox, L the Tech Lead, once on the final sha; the rule (and `CLAUDE.md`) says "the size's suite owner" |
| D13 | Every risk flag forces L |
| D14 | Signals: S 1-2 tasks, nothing user-visible, no risk flag, existing tests cover it; M 1-6 tasks, user-visible, clear ticket or AC, no business question, no risk flag; L business questions, risk flag, cross-repo or ordering matters; unsure: size up |
| D15 | Built-in Opus advisor (`advisorModel: opus`) for every role, Manager included. Done 2026-10-22 in `templates/squad/settings/*.json` and the live squad's settings |
| D16 | Required advisor calls: the Developer on a task's 3rd FAIL before handing in again; anyone after 2 failed attempts at the same error or a BLOCKED unanswered for 2 rounds; the Tech Lead or Manager before an irreversible design choice. Each required call leaves a 3-line note in the task file |

## Contracts (every ticket builds on these; change one only by re-issuing the tickets that use it)

### Rule file (`templates/squad/process/<topic>.md`)

```
## REV-3 One verdict per final sha
roles: qa-whitebox, qa-blackbox
aware: dev, team-lead
when: size in M, L
topic: review

The Tech Lead names one final sha per task before QA verdicts; each QA gives one verdict on that sha.
```

| Item | Rule |
|---|---|
| ID | `^[A-Z]+-\d+[a-z]?$`. The prefix is fixed per file: `CORE` core, `FILE` files, `START` starting, `SIZE` sizes, `GOAL` goal, `PROMO` promotion, `CLOSE` closing, `MSG` messages, `WHO` who decides, `LC` lifecycle, `REV` review, `EVID` evidence, `ITER` iterations, `COST` cost, `NOTE` notes, `SAFE` safety, `SUITE` suites, `MRG` merge, `SPAWN` spawning. Unique across all files. Never reused, never renamed in place |
| Variant | Size or condition variants of one duty share a number with a letter: `DEV-7a` (`when: size = S`), `DEV-7b` (`when: size in M, L`). No "(S: …)" clause in rule text |
| Attribute lines | Directly after the heading, up to the first blank line. `roles:` (required, at least one) and `topic:` (required); `aware:` and `when:` optional |
| Role names | `manager`, `ba`, `team-lead`, `tech-lead`, `qa-whitebox`, `qa-blackbox`, `designer`, `dev`, `token-coach`, or `all` |
| `when:` | `<key> in <v>, <v>` or `<key> = <v>`, joined by ` and `. Keys: `size` (S M L), `design` (yes no), `qa` (full light), `goal` (yes no), `qa-b` (yes no, ticket 14). An unknown key or value is a lint error. No `when:` means always. A fact the home lacks (a goal Manager's home has no `size`) makes that condition true |
| Citation | Agents, skills and bin cite a rule as `[REV-3]` (brackets), so ticket ids such as `SEC-04` are never taken for rules |
| Body | The Writing rule (ADR 0006): one rule per block, actor named, at most 60 words per bullet or paragraph |
| Removed | `process/_removed.md`: `## <ID> (removed in <version>)` with `why:` and `replaced_by: <ID>, …` or `replaced_by: none` |
| `core.md` | IDs `CORE-*`, `roles: all`, at most 40 lines in total |

### Overlay (`$SQUAD_DIR/process.local.md`)

```
## replace REV-3 @7f3a9c21
why: report-ui-fix: 8 style returns
upstream: proposed
<new body; optional roles:/aware:/when:/topic: lines before it retarget the rule>

## add SQ-1 Style contract
roles: tech-lead, qa-blackbox
aware: qa-whitebox, dev
when: size in M, L
topic: review
why: report-ui-fix it.1 #2
upstream: proposed
<body>

## remove COST-6 @19be02aa
why: idle threshold does not fit this project
upstream: local-only
```

- The hash is the first 8 hex digits of the sha256 of the plugin rule's attribute lines plus body, with LF endings and trailing spaces removed.
- A local rule ID is `SQ-<n>`. `why:` and `upstream:` (`proposed | local-only | rejected`) are required on every operation.

### Composed rules (`<home>/roles/<agent>.rules.md`)

```
# Your process rules
agent: <name> · role: <role> · scope: <scope> (size M, design no, qa full, goal no)
plugin: <version> <sha> · overlay: <n> operations applied · composed: <ISO time>
rules: CORE-1 … REV-3 SQ-1 (ids in order)

## CORE-1 Task states
<body>
…
## REV-3 One verdict per final sha   [squad: replaced]
<body>
```

- Rules are ordered by file order (core first), then by order within the file. Source tags are `[squad: replaced]` and `[squad: added]`; a plugin rule has no tag.
- Manager and Tech Lead also get `## Index of other rules`: one line each, `<ID> <title> (roles)`.
- Composition is deterministic: the same inputs give byte-identical output.

### Plugin pin (`scope.md` line `plugin: <version> <sha>`)

- `squad-start` writes the pin. `squad-spawn` and `squad-respawn` compose from that version's rule files and run that version's agents and tools.
- How a pinned runtime is materialised (installed cache path, `git worktree`, or an archive) is decided by ticket 01.

### CLI (`bin/squad-process`)

| Command | Does |
|---|---|
| `compose <role> --home <dir> [--agent <name>] [--out <file>]` | Prints or writes the composed rules for the home's scope facts and pin |
| `rule <ID>` | Prints one effective rule, overlay applied |
| `who <ID>` | Prints the roles that act on and that are aware of a rule, per size |
| `lint [--squad-dir <dir>]` | Rule files: unique IDs, required attributes, known roles and keys, Writing rule. Overlay: every target exists, at most one operation per ID. Duplication: no sentence of 12 or more words appears in two rules or in a rule and an `agents/*.md` file. Pointers: every `[ID]` cited in agents, skills and bin exists |
| `upgrade --check / --apply [--yes]` | Ticket 07 |

## Review findings (2026-10-20) and where each is fixed

| # | Finding | Ticket |
|---|---|---|
| 1 | Two Coach rules logged 2026-10-19 (style contract; QA whitebox leaves presentational values to QA blackbox) are missing from the live `process.md` | 03 restores them |
| 2 | 12+ live-only Coach rules never reached the template | 03 ships them; 07 sends `upstream: proposed` operations to the plugin so drift cannot pile up again |
| 3 | Tickets and specs drafted untracked in the project root (10 of 20 iterations) | 10 |
| 4 | Contradictions and broken pointers in role cards (tech-lead.md writes `escalations.md`; manager.md "label shape" and "Retro"; ready-task duty missing; HANDIN target) | 03 (rule text), 06 (cards), 02 (lint on pointers) |
| 5 | Manager context limit and the 3-return step-in rely on wording only | 11 (usage notice), 12 (return counter) |
| 6 | The same rule copied into several files | 02 (duplication lint), 03, 06 |
| 7 | Four roles read the whole file at every start and respawn | 04, 05 |
| 8 | Retro loop loses lessons (Coach backlog unread, tool bugs in prose, blank retros) | 13 |
| 9 | No-UI scopes needed custom pods without QA blackbox | 14 |
| L1 | Role cards live from the repo, `process.md` pinned: version skew inside one pod | 01, 05 |
| L2 | Settings copied and half-migrated (v4 Team Lead permissions unapplied) | 08, 09 |

## PO requests 2026-10-21 (tickets 17–20)

- **Sizes:** S = Manager + Developers; M = + both QAs; L = every role. Duty owners in D9-D14. Ticket 17.
- **Manager model:** default Sonnet, effort high. Done 2026-10-21 in `templates/squad/settings/manager.json`; `tests/test_squad_start.py` updated.
- **Opus advisor for the whole team:** settings done (D15); required triggers (D16) and the 3rd-FAIL notice in ticket 18.
- **`squad-start` confirms the Manager's model and effort** before spawning, and on resume. Ticket 19.
- **The Manager confirms the team's model and effort** per role together with the size, and records it in `scope.md`. Ticket 20.
- **Until 19 and 20 ship, the starter and the Manager do both confirmations by hand.**

## Order and parallelism

| Ticket | Blocked by | Shares a file with |
|---|---|---|
| 01 spike | none | none |
| 02 rules + lint | none | `bin/squad-process` (04, 07, 09 come later) |
| 03 convert | 02 | none |
| 04 compose | 02 | none |
| 05 spawn + pin | 01, 04 | `bin/squad-spawn` (08 later) |
| 06 role cards | 03, 05 | `agents/token-coach.md` (13 later) |
| 07 upgrade | 03, 04 | fixtures (09 later) |
| 08 settings | 05 | |
| 09 adopt + init | 06, 07, 08 | |
| 10 root guard | 03 | `hooks/hooks.json` (11), `bin/squad-close` (13) |
| 11 Manager notice | 06, 10 | |
| 12 ledger | 03, 06 | |
| 13 retro loop | 06, 07, 10 | |
| 14 `qa-b: no` | 03, 04 | |
| 17 sizes S, M, L | 03, 04 | process rule files |
| 18 Opus advisor rules | 03, 12 | `bin/squad-log-message` (after 12) |
| 19 start confirms Manager model | none | `bin/squad-start` (20 later) |
| 20 Manager confirms team models | 03, 08, 19 | `bin/squad-spawn` (after 08) |
| 15 integration | 01–14, 17–20 | |
| 16 promotion | 15 | |

- 01 and 02 run in parallel. After 02, 03 and 04 run in parallel; they share no file.
- 10–14 each change rules in their own topic file (files, cost, messages and lifecycle, iterations, sizes and review and evidence), so they can run in parallel once they are unblocked.
- Suggested run: a goal of three scopes. A = 01–05; B = 06–09; C = 10–14. Each scope ends in its own integration task; 15 integrates the goal and 16 promotes.

## Global technical AC (every ticket)

- Existing tests touched pass; new behaviour has a test; no full suite (only the Tech Lead runs it).
- `squad-process lint` passes on the template once ticket 02 exists. Before that, `python3 bin/processlint.py` runs where `process.md` changes.
- Every file open uses `encoding="utf-8"` and `newline="\n"`; `tests/test_windows_safe.py` passes.
- Evidence follows ADR 0015: `.scratch/composed-process/issues/<NN>-<slug>/evidence.md`.
- Ticket and spec drafts go in `$SCOPE_DIR/tasks/` and ride a Developer branch, never untracked in the project root (finding 3).

## Rollback and compatibility

- Until ticket 09 runs, a squad keeps working on its `process.md` copy. `squad-spawn` composes only when the squad folder has no `process.md`, or has `process.local.md`; otherwise it keeps today's path.
- Reverting is reverting the merge. The live squad's old `process.md` is archived as `process.v6-archived.md` by 09, never deleted.

## Later (research 2026-10-21, not in this effort)

- Reviews as fresh subagents per task instead of long-lived QA sessions.
- BA, Designer and Token Coach as on-demand sessions only.
- An AC status list per ticket (JSON) that only checkers flip.
- `promptCacheTtl` per role settings, and a filter hook for targeted test output.
- Step up effort before model, and change the model only by respawn. This is one rule edit and can ride ticket 11 if the PO wants it now.

## Open points

- Does `--plugin-dir` win over an installed plugin of the same name, and does `--append-system-prompt-file` combine with `--agent`? Ticket 01 answers both before 05 builds on them.
