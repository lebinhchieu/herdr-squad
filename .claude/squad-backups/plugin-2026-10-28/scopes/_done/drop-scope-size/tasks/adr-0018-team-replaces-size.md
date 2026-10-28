# A per-scope team replaces scope size; the Manager proposes every role

Status: proposed (drop-scope-size; PO answered I1 to I7 on 2026-10-27, I8 open in `architecture.md`)

Supersedes 0016's **Sizes** and **Duty owners** sections (SIZE-1 to SIZE-4, SIZE-12 to SIZE-17, SIZE-19 to SIZE-22a, the `size` key of `when:`). Amends 0017: "the Manager never proposes the Architect" and the same rule for the Designer are reversed; the PO still confirms every role.

**Decision:** a scope has no size. `scope.md` carries one `team:` line (the optional roles `ba`, `team-lead`, `tech-lead`, `qa-whitebox`, `qa-blackbox`, `designer`, `architect`; Manager and Developers are always present). The Manager proposes each role with its signal; the PO confirms. Rules target the team through presence facts and **duty facts** derived by one fallback-chain table (first present role owns the duty, every chain ends at Manager or Developer). A rule's `when:` names one duty or presence fact plus the orthogonal facts `goal`, `qa`, `design`, `architecture`, `qa-black`; `size` is an error. The presence keys are `ba`, `team-lead`, `tech-lead`, `qa-white`, `qa-black`, `design`, `architecture`. Every subset of the seven roles is a valid team. Done = every checker on the team passed.

**Why:** size bundled seven independent role choices into three presets, and the PO wanted the Designer and Architect picked from the scope's signals like every other role. Presets forced a scope to carry a role it did not need, or to skip one it did.

**Consequences:**
- Plugin 0.6.0, breaking: rule `when:` retargets keep their ID; collapsed S/M/L twins get tombstones with `replaced_by`; every overlay op on a retargeted rule goes stale and `squad-process upgrade` lists it.
- **No shim, no dual support.** The engine rejects `size:`, the `design:`, `architecture:`, `qa-b:` lines of `scope.md` and the old `when:` keys (`size`, `qa-b`), each with a pointer to the converter. Every existing unpinned squad migrates with the converter (`squad-process adopt`) to work: it writes `team:` and removes the four lines, after a dry run and the PO's yes. A scope pinned below 0.6.0 keeps its pinned runtime: the converter skips it and `squad-spawn`/`squad-respawn` hand off to the pin's own tools. The `team:` tokens and duty values are `qa-white`/`qa-black`; role and agent names stay `qa-whitebox`/`qa-blackbox`. Overlay `when:` lines using `qa-b` are renamed `qa-black`; ones using `size` are translated to a duty fact (`upgrade` lists them).
- Adding a role mid-scope is the Manager's call (Designer and Architect: the PO first); removing one needs an iteration boundary and the PO's OK. Respawn is exactly the roles whose composed text changes.
- The Developer rules keep the 5 KiB cap, tested over all 128 teams.
- `CONTEXT.md`: remove **Size**, add **Team**, **Duty owner**, **Checker**.

**Alternatives rejected:** presence facts only (unbounded variants); presets under another name; keeping the `design:`, `architecture:`, `qa-b:` lines beside `team:` (two lines saying one thing); an accepted `size` key in overlays (two targeting languages); a read-side shim for old `scope.md` files (two formats read by one engine; PO decision I4); keeping `qa-b` beside new role-aligned keys (uneven names; PO decision I3).
