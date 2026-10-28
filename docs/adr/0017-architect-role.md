# An optional Architect role sits above the Tech Lead and proposes irreversible choices

Status: accepted (add-architecture, PO confirmed the design as written 2026-10-27)

Amended by 0018 (team replaces scope size): the Manager-never-proposes sentence and the two flags.

Amends 0016: the "Irreversible design choice" owner rows (WHO-2, WHO-2d, SIZE-22) get an `architecture: yes` variant (WHO-2e, SIZE-22a). Consistent with 0010: the Team Lead still runs the pod and the Tech Lead still owns per-task design, quality and security at L; the Architect sits above both.

**Decision:** the **Architect** is an optional role, turned on by the **architecture flag** (`architecture: yes|no` in `scope.md`, default `no`) the way the **design flag** adds the UI/UX Designer. Only the PO turns it on; the Manager never proposes it. It works at any size and writes one `$SCOPE_DIR/architecture.md` (`Status: draft|final`) before the plan. The plan waits for `final`.

**Why:** architecture choices (data model, new dependency, vendor) were decided late, inside a task's design notes, by a role built for per-task design. The PO wants one place that sets the boundaries first.

**Consequences:**
- Boundary against the Tech Lead: at L the Architect owns the architecture and the Tech Lead keeps per-task design, quality, security and the suites inside it; at S and M, with no Tech Lead, the Architect sits above the Developer's design notes.
- Irreversible choices: the Architect lists each with options and a recommendation, after an advisor call. The Manager escalates it and the PO decides, as before; this amends only who proposes it.
- Enforcement without a new checker: "conforms to `architecture.md`" joins the technical AC and the existing code checker verifies it (S the Developer's review subagent, M QA whitebox, L Tech Lead and QA whitebox). The team follows `architecture.md` or sends the Architect an `ASK`; after 2 rounds the Manager decides ([CORE-4]).
- The Architect is spawned after the goal check and before the plan, retired once final and respawned for a question. `squad-spawn architect` refuses without `architecture: yes`. ADR text is drafted in `$SCOPE_DIR/tasks/` and committed to `docs/adr/` by the promotion task.
- Rules for the Architect carry `when: architecture = yes`, so a scope with the flag `no` composes byte-identical rules and role cards (checked by test). Dev rules stay within 5 KiB except S with the flag on, an exception pinned by `test_s_architecture_exception_is_pinned`.
- Scopes pinned to an older plugin version run their pinned runtime and are unaffected. The plugin version is bumped with a changelog block and a rule snapshot (0016).

**Alternatives rejected:** the Tech Lead doing it (absent at S and M, and per-task by design); a separate Architect check of built code (the existing checkers check conformance); letting the Manager propose the flag (as for design); the Architect deciding irreversible choices (stays with the PO).
