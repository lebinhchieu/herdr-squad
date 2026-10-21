# Process is composed per role from ID-tagged rules; a squad keeps only an overlay

Status: proposed (composed-process, PO answers D1–D7 2026-10-21)

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
