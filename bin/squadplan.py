"""The plan model of a home: one row per task (scope) or per scope (goal), with aim, estimate, what it waits on and its step.

Pure and read-only. `fields_of` and `duration_min` read text, `steps` is the graph rule, `build_scope` and `build_goal`
read the files of one home, `plan_line_parts` is the inbox line (ticket 05). Nothing here runs git (`scope_tasks(git=False)`)
or reads work time: `squad-inbox list --json` starts a new process on every pane refresh. The board route
(`squadboard_plan.py`) adds `spent_min` and the board stage on top.

Row: {id, title, aim, aim_bare_ids, est_min|None, deps [id], unknown_deps [text], step|None, loop, state, passed}.
A goal row also has `waits` (the outside waits in the words of goal.md, or None).
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadids  # noqa: E402
import squadledger  # noqa: E402
import squadtask  # noqa: E402
import squadtickets  # noqa: E402

NONE_WORDS = ("", "none", "-", "–", "—")
KEY_RE = re.compile(r"^\s*([A-Za-z][A-Za-z ]{0,20}):\s*(.*)$")
DURATION_RE = re.compile(r"^(?:(\d*\.?\d+)\s*h)?\s*(?:(\d+)\s*m)?$")
PASSED_WORDS = ("passed", "merged", "done", "closed", "complete", "completed", "finished")


def duration_min(text):
    """`30m`, `1h`, `.5h`, `1.5h`, `1h 30m` -> minutes; anything else (`1,5h`, `abc`, empty, None) -> None. Never raises."""
    try:
        m = DURATION_RE.match(str(text).strip().lower())
        if not m or not (m.group(1) or m.group(2)):
            return None
        return int(round(float(m.group(1) or 0) * 60 + int(m.group(2) or 0)))
    except (TypeError, ValueError, AttributeError):
        return None


def fields_of(text):
    """-> {aim, estimate, depends}: each None when absent. `depends` is a list of task numbers as written (may be empty for
    `none`). A field starts a line, or follows ` · ` in a header line such as `Size: S · Plan: step 1 · Depends on: 01, 03`."""
    got = {}
    for line in (text or "").splitlines()[:80]:
        if not KEY_RE.match(line):
            continue
        key = None
        for seg in line.split(" · "):
            m = KEY_RE.match(seg)
            if m:
                key, val = m.group(1).strip().lower(), m.group(2).strip()
                got.setdefault(key, val)
            elif key is not None and key in ("aim",) and got.get(key) is not None:
                got[key] += " · " + seg.strip()
    dep = got.get("depends on")
    return {"aim": got.get("aim") or None, "estimate": got.get("estimate") or None,
            "depends": None if dep is None else ([] if dep.strip().lower() in NONE_WORDS else re.findall(r"\d+", dep))}


def steps(deps):
    """{node: [nodes it waits on]} -> {node: step or None}. Step = 1 + the largest step of its known deps (longest path); a
    dep that is not a node is ignored. A node on a cycle, a self-loop or after one gets None. Kahn's algorithm: ends on any input."""
    wait = {n: 0 for n in deps}
    users = {n: [] for n in deps}
    for n, ds in deps.items():
        for d in set(ds):
            if d in deps:
                wait[n] += 1
                users[d].append(n)
    out, queue = {n: None for n in deps}, [n for n in deps if wait[n] == 0]
    for n in queue:
        out[n] = 1 + max([out[d] for d in set(deps[n]) if d in deps], default=0)
        for u in users[n]:
            wait[u] -= 1
            if wait[u] == 0:
                queue.append(u)
    return out


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _draft_text(home, nn):
    """`<scope>/tasks/NN.md` itself (not `NN-design-notes.md` and the like)."""
    try:
        for f in sorted((Path(str(home)) / "tasks").iterdir()):
            m = re.match(r"^(\d+)\.md$", f.name)
            if m and f.is_file() and int(m.group(1)) == int(nn):
                return _read(f)
    except OSError:
        pass
    return None


def _place(rows):
    """Add `step` and `loop` to rows (each has `id`, `deps`); rows end in plan order: by step, loop group last, then id."""
    st = steps({r["id"]: r["deps"] for r in rows})
    for r in rows:
        r["step"] = st[r["id"]]
        r["loop"] = r["step"] is None
    rows.sort(key=lambda r: (r["loop"], r["step"] or 0, len(r["id"]), r["id"]))
    return rows


def _aim_row(aim):
    return {"aim": aim, "aim_bare_ids": squadids.bare_ids(aim) if aim else []}


def build_scope(home, repo_root=None, name=None):
    """-> {kind: "scope", name, aim, rows} of one scope folder. Fields come from `tasks/NN.md`, then the ticket; `Depends on:`
    missing in both falls back to the ticket's `Blocked by:`."""
    home = Path(str(home))
    found = squadtickets.scope_tasks(home, repo_root, name, git=False)
    by_key = {squadledger.key(t["id"]): t["id"] for t in found["tasks"]}
    try:
        states = squadtask.fold(squadtask.read_events(squadtask.squad_dir_of(home), squadtask.slug_of(home)))
        chk = squadtask.checkers(home)
    except Exception:
        states, chk = {}, {"qa": []}
    rows = []
    for t in found["tasks"]:
        tid = t["id"]
        ticket = squadtask.ticket_text(home, repo_root, tid)
        fs = [fields_of(x) for x in (_draft_text(home, tid), ticket) if x]
        pick = lambda k: next((f[k] for f in fs if f[k] is not None), None)  # noqa: E731
        raw = pick("depends")
        if raw is None:
            raw = squadtask.parse_blocked_by(ticket)
        deps, unknown = [], []
        for d in raw:
            k = squadledger.key(d)
            if k in by_key:
                if by_key[k] not in deps:
                    deps.append(by_key[k])
            elif d not in unknown:
                unknown.append(d)
        state = squadtask.word(states.get(squadledger.key(tid)), chk)
        row = {"id": tid, "title": t.get("title", ""), "est_min": duration_min(pick("estimate")), "deps": deps,
               "unknown_deps": unknown, "state": state, "passed": state in ("passed", "merged")}
        row.update(_aim_row(pick("aim")))
        rows.append(row)
    top = fields_of(_read(home / "scope.md"))
    return {"kind": "scope", "name": name or home.name, "aim": top["aim"], "rows": _place(rows)}


def _column(columns, *names):
    low = [str(c).strip().lower() for c in columns]
    for n in names:
        if n in low:
            return low.index(n)
    return None


def _split_cell(cell):
    return [p.strip() for p in re.split(r",|\band\b", cell or "") if p.strip()]


def build_goal(goal_text):
    """-> {kind: "goal", aim, rows} from the `## Scopes` table of goal.md. Columns are found by name (first = the scope,
    `Depends on`, `Aim`, `Est`, `Status`); a missing column gives nothing. A name in a dependency cell that is not a scope of the
    table is an outside wait, kept in the words of the file."""
    import squadboard_list
    table = squadboard_list.goal_scopes_table(goal_text or "")
    cols = table["columns"]
    i_dep, i_aim = _column(cols, "depends on", "depends", "blocked by"), _column(cols, "aim")
    i_est, i_state = _column(cols, "est", "estimate"), _column(cols, "status", "state")
    cell = lambda r, i: (r[i].strip() if i is not None and i < len(r) else "")  # noqa: E731
    names = {r[0].strip().lower(): r[0].strip() for r in table["rows"] if r and r[0].strip()}
    rows = []
    for r in table["rows"]:
        if not r or not r[0].strip():
            continue
        deps, waits = [], []
        for part in ([] if cell(r, i_dep).lower() in NONE_WORDS else _split_cell(cell(r, i_dep))):
            if part.lower() in names:
                if names[part.lower()] not in deps:
                    deps.append(names[part.lower()])
            elif part.lower() not in NONE_WORDS:
                waits.append(part)
        words = cell(r, i_state).lower().split()
        state = words[0] if words else ""
        row = {"id": r[0].strip(), "title": "", "est_min": duration_min(cell(r, i_est)), "deps": deps, "unknown_deps": waits,
               "waits": ", ".join(waits) or None, "state": state, "passed": state in PASSED_WORDS}
        row.update(_aim_row(cell(r, i_aim) or None))
        rows.append(row)
    return {"kind": "goal", "aim": fields_of(goal_text)["aim"], "rows": _place(rows)}


def plan_line_parts(home, blocks, repo_root=None):
    """The inbox line of ticket 05: `blocks` is the first token of an item's `--blocks`. -> {pos, step, aim, next} or None
    (unknown token, no plan, any error). A goal home gives `scope N of M`, a scope home `task N of M` and `step S`."""
    try:
        home = Path(str(home))
        token = (str(blocks or "").split() or [""])[0].strip(",;:")
        if not token:
            return None
        if (home / "goal.md").is_file():
            plan, noun = build_goal(_read(home / "goal.md")), "scope"
        else:
            plan, noun = build_scope(home, repo_root), "task"
        rows = plan["rows"]
        keys = [squadledger.key(r["id"]) if noun == "task" else r["id"].lower() for r in rows]
        want = squadledger.key(token) if noun == "task" else token.lower()
        if want not in keys:
            return None
        i = keys.index(want)
        row = rows[i]
        nxt = next((r for r in rows[i + 1:] if not r["passed"]), None)
        label = (nxt["title"] or nxt["id"]) if nxt else None
        return {"pos": "%s %d of %d" % (noun, i + 1, len(rows)),
                "step": "step %d" % row["step"] if row["step"] else None, "aim": row["aim"],
                "next": "next: " + label if label else "next: nothing, last one"}
    except Exception:
        return None
