"""squad-tree: the data of the /squads pane (design-notes section 2). Read-only. Python owns every fact, rule and
command text; the mod only draws and copies. `build(sel) -> dict` is JSON v1: squads > goals > scopes.

Reuses squadboard_list (scope_row, goal_row, the sorts) so a number here is the board's number.
"""
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import squadboard
import squadboard_list as L
import squadcommands

VERSION = 1


def find_repo(repo=None, env=None, cwd=None):
    """The active repo: --repo, else $SQUAD_DIR/../../.., else the MAIN repo root of git, else the cwd."""
    env = os.environ if env is None else env
    if repo:
        return Path(repo).resolve()
    if env.get("SQUAD_DIR"):
        return Path(env["SQUAD_DIR"]).resolve().parents[2]
    try:
        r = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=10, cwd=cwd)
        common = r.stdout.strip()
        if r.returncode == 0 and common:
            return Path(common).resolve().parent
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(cwd or os.getcwd()).resolve()


def _plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def next_step(node):
    """-> {"rule": 1..9, "text": str}. Pure: reads the node's status, facts and (goal) scopes (spec.md, rules 1-9)."""
    if node["status"] == "done":
        return {"rule": 9, "text": "Closed. Read the report."}
    f = node.get("facts") or {}
    if node["kind"] == "goal" and not [s for s in node.get("scopes", []) if s["status"] == "open"]:
        return {"rule": 8, "text": "All scopes closed: close goal"}
    unreadable = [n for n, k in (("inbox", "needs_you"), ("herdr", "agents_working")) if f.get(k) is None]
    if unreadable:
        return {"rule": 1, "text": "Cannot read %s: open board" % " and ".join(unreadable)}
    if f["needs_you"] > 0:
        text = "Answer %s" % _plural(f["needs_you"], "question")
        if node["kind"] == "goal":
            top = [s for s in node.get("scopes", []) if s["status"] == "open" and (s["facts"] or {}).get("needs_you")]
            if top:
                text += " in %s" % top[0]["name"]
        return {"rule": 2, "text": text}
    if f["stuck"] > 0:
        return {"rule": 3, "text": "%s stuck" % _plural(f["stuck"], "task")}
    total, done = f["tasks_total"], f["tasks_done"]
    if not total:
        return {"rule": 6, "text": "No tasks yet"}
    if done >= total:
        return {"rule": 4, "text": "All tasks done: close"}
    if f["agents_working"] == 0:
        return {"rule": 5, "text": "Nobody working: resume"}
    return {"rule": 7, "text": "Working. Nothing for you."}


def _facts(row):
    return {k: row[k] for k in ("needs_you", "stuck", "tasks_done", "tasks_total", "agents_working", "last_active")}


def _light(home, md):
    """A row with no facts: scope.md or goal.md (`md`), one mtime. No inbox, no git."""
    text = L._text(home / md)
    ts = L._mtime(home)
    return {"name": home.name, "brief": L._brief(text), "goal": L._field(text, "goal") or None,
            "closed_at": L._iso(ts) if ts is not None else "unknown", "facts": None, "unknown": []}


def _node(squad, kind, status, row):
    """One Goal or Scope dict (commands are added by the caller once the children are known)."""
    home = squad.path / (kind + "s") / ("_done" if status == "done" else "") / row["name"]
    n = {"name": row["name"], "kind": kind, "status": status, "name_safe": squadcommands.name_safe(row["name"]),
         "home": str(home)}
    if kind == "scope":
        n["goal"] = row["goal"]
        n["goal_label"] = row.get("goal_label") or row["goal"] or "no goal"
    n["brief"] = row["brief"]
    n["closed_at"] = row["closed_at"] if status == "done" else None
    n["facts"] = _facts(row) if "tasks_total" in row else None
    n["unknown"] = row["unknown"]
    return n


def _finish(squad, n, flat_goal=None, open_scopes=()):
    n["next_step"] = next_step(n)
    info = {"kind": n["kind"], "name": n["name"], "status": n["status"], "home": n["home"], "squad": squad.name, "squad_path": str(squad.path),
            "goal": flat_goal, "facts": n["facts"], "open_scopes": list(open_scopes), "flat": False}
    n["commands"] = squadcommands.commands_for(info)
    return n


def _squad(squad, sel):
    out = {"name": squad.name, "flat": False, "message": None, "needs_you": 0, "commands": [], "goals": [],
           "scopes": [], "done": {"goals": [], "scopes": []}}
    info = {"kind": "squad", "name": squad.name, "status": "open", "home": str(squad.path), "squad": squad.name, "squad_path": str(squad.path),
            "goal": None, "facts": None, "open_scopes": [], "flat": squad.flat}
    if squad.flat:
        out.update(flat=True, message=squadboard.FLAT_MESSAGE)
        out["commands"] = [c for c in squadcommands.commands_for(info) if c["id"] != "board"]
        return out
    out["commands"] = squadcommands.commands_for(info)
    open_goals = {p.name: p for p in L._dirs(squad.path / "goals")}
    done_goals = {p.name: p for p in L._dirs(squad.path / "goals" / "_done")}
    ctx = None
    rows = {"open": {}, "done": {}}  # status -> name -> (row, full)
    for status, base in (("open", squad.path / "scopes"), ("done", squad.path / "scopes" / "_done")):
        for home in L._dirs(base):
            light = _light(home, "scope.md")
            full = status == "open" or light["goal"] in open_goals
            if full:
                if ctx is None:
                    ctx = L._ctx(squad, sel)
                row = L.scope_row(squad, home, status, ctx)
                row["unknown"] = list(row["unknown"])
            else:
                row = light
                row["goal_label"] = light["goal"] or "no goal"
            rows[status][home.name] = row
    by_goal = {}
    lone = {"open": [], "done": []}
    for status in ("open", "done"):
        for row in rows[status].values():
            g = row["goal"]
            if g in open_goals or g in done_goals:
                by_goal.setdefault(g, []).append((status, row))
            else:
                lone[status].append(row)

    def scope_node(status, row, goal_name):
        return _node(squad, "scope", status, row)

    def goal_node(name, status):
        pairs = by_goal.get(name, [])
        scope_rows = [r for s, r in pairs]
        home = (open_goals if status == "open" else done_goals)[name]
        if status == "open":
            g = L.goal_row(squad, home, "open", scope_rows)
            g["unknown"] = list(g["unknown"])
            n = _node(squad, "goal", "open", g)
            opens = L._sort_open([r for s, r in pairs if s == "open"])
            closed = L._sort_done([r for s, r in pairs if s == "done"])
            kids = [scope_node("open", r, name) for r in opens] + [scope_node("done", r, name) for r in closed]
            n["scopes"] = [_finish(squad, k, name) for k in kids]
            return _finish(squad, n, open_scopes=[r["name"] for r in opens])
        light = _light(home, "goal.md")
        n = _node(squad, "goal", "done", light)
        n["scopes"] = [_finish(squad, scope_node("done", r, name), name) for r in L._sort_done(scope_rows)]
        return _finish(squad, n)

    for name in open_goals:
        out["goals"].append(goal_node(name, "open"))
    for name in done_goals:
        out["done"]["goals"].append(goal_node(name, "done"))
    out["goals"] = _sorted_goals(out["goals"])
    out["done"]["goals"].sort(key=lambda g: g["closed_at"] if g["closed_at"] != "unknown" else "", reverse=True)
    for row in L._sort_open(lone["open"]):
        out["scopes"].append(_finish(squad, scope_node("open", row, None)))
    for row in L._sort_done(lone["done"]):
        out["done"]["scopes"].append(_finish(squad, scope_node("done", row, None)))
    out["needs_you"] = sum((n["facts"] or {}).get("needs_you") or 0 for n in out["goals"] + out["scopes"])
    return out


def _sorted_goals(goals):
    rows = [dict(g["facts"], _n=g) for g in goals]
    L._sort_open(rows)
    return [r["_n"] for r in rows]


def _squad_order(squads):
    """Squads sort like goals: needs you (most first), stuck (most first), last active (newest first). A squad's
    numbers are the sums over its open goals and lone open scopes; a flat or unreadable squad counts 0 and 0."""
    def key(s):
        facts = [n["facts"] or {} for n in s["goals"] + s["scopes"]]
        las = [f.get("last_active") for f in facts if f.get("last_active")]
        return (-(s["needs_you"] or 0), -sum(f.get("stuck") or 0 for f in facts), "".join(chr(0x10FFFF - ord(c)) for c in (max(las) if las else "")))
    return sorted(squads, key=key)


def build(sel):
    """sel: {"repo": Path, "names": [squad names] or []}. Never raises on a bad squad file."""
    root = sel["repo"]
    squads = squadboard.squads_of(root)
    if sel.get("names"):
        squads = [s for s in squads if s.name in sel["names"]]
    lsel = {"squads": squads, "params": {}, "herdr_json": sel.get("herdr_json")}
    out = {"version": VERSION, "repo": str(root),
           "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "squads": []}
    for s in squads:
        try:
            out["squads"].append(_squad(s, lsel))
        except Exception as e:  # one bad squad never stops the run
            out["squads"].append({"name": s.name, "flat": False, "message": "cannot read: %s" % type(e).__name__,
                                  "needs_you": 0, "commands": [], "goals": [], "scopes": [],
                                  "done": {"goals": [], "scopes": []}})
    out["squads"] = _squad_order(out["squads"])
    return out
