"""squad board M2: the picker and the goal / scope rows (ticket 04; architecture.md sections 1 and 6).

Two routes, found by `squadboard.load_routes`:
  GET /api/squads   no choice needed. Every open goal and lone scope with the six row facts, and the Done list.
                    `?check=NAME` adds `data.check` ({name, exists, kind, where}) for a saved choice (AC6).
  GET /api/scopes   `goal=G` or `scope=S` (400 without). The rows of that choice only.

A scope row has exactly these keys: name, kind, goal, goal_label, brief, status (open|done), closed_at,
closed_approx, read_only, and the six facts needs_you, stuck, tasks_done, tasks_total, agents_working,
last_active (ISO UTC or None), new. `unknown` names the sources a fact could not be read from.

Cheap sources only: messages.jsonl, escalations.md, inbox.jsonl, ticket files, the ledger, file mtimes, two git
calls per squad, one herdr call per request. No transcript is opened. Nothing is written. Never raises.
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import squadboard_git
import squadboard_time
import squadinbox
import squadledger
import squadtask
import squadtickets

NAME_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
HERDR_TIMEOUT_S = 3
FACTS = ("needs_you", "stuck", "tasks_done", "tasks_total", "agents_working", "last_active", "new")


def _text(path):
    """File text with LF endings, or None."""
    try:
        with open(str(path), encoding="utf-8", errors="replace", newline=None) as f:
            return f.read()
    except OSError:
        return None


def _mtime(path):
    try:
        return os.stat(str(path)).st_mtime
    except OSError:
        return None


def _iso(ts):
    return None if ts is None else datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _brief(text):
    for line in (text or "").splitlines():
        s = line.strip()
        if s.startswith("**"):
            return s.strip("*").strip()
    return ""


def _field(text, name):
    """`name: value` line of scope.md (first one), stripped; '' when absent."""
    for line in (text or "").splitlines():
        m = re.match(r"^%s:[ \t]*(.*)$" % re.escape(name), line)
        if m:
            return m.group(1).strip()
    return ""


def goal_scopes_table(text):
    """The goal.md `## Scopes` table as written: {columns, rows} with stripped cells."""
    rows, on = [], False
    for line in (text or "").splitlines():
        s = line.strip()
        if s.lower().startswith("## "):
            on = s[3:].strip().lower() == "scopes"
            continue
        if on and s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) or c == "" for c in cells) and any(cells):
                continue
            rows.append(cells)
    return {"columns": rows[0] if rows else [], "rows": rows[1:]}


def _roster_names(text):
    names = []
    for line in (text or "").splitlines():
        s = line.strip()
        if s.startswith("|"):
            c = [x.strip() for x in s.strip("|").split("|")]
            if c and c[0] and c[0].lower() != "agent" and not set(c[0]) <= set("-: "):
                names.append(c[0])
    return names


def _herdr_working(sel):
    """-> (set of agent names working now, None) or (set(), 'herdr'). One call per request."""
    path = sel.get("herdr_json")
    try:
        if path:
            raw = Path(path).read_text(encoding="utf-8")
        else:
            r = subprocess.run(["herdr", "agent", "list"], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=HERDR_TIMEOUT_S)
            if r.returncode != 0:
                return set(), "herdr"
            raw = r.stdout
        agents = json.loads(raw)["result"]["agents"]
        return {a["name"] for a in agents if a.get("agent_status") == "working"}, None
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return set(), "herdr"


def _git_facts(squad, sel_repo):
    """Two git calls for the squad -> (refs by scope {scope: newest ts}, merged branch set) or (None, None)."""
    prefix = "squad/%s/" % squad.name
    allr = squadboard_git.branch_refs(sel_repo, prefix)
    merged = squadboard_git.branch_refs(sel_repo, prefix, merged_into="main")
    if allr is None or merged is None:
        return None, None
    newest = {}
    for r in allr:
        parts = r["branch"].split("/")
        if len(parts) >= 3 and r["ts"] is not None:
            newest[parts[2]] = max(newest.get(parts[2], 0), r["ts"])
    return newest, {r["branch"] for r in merged}


def _ticket_status(path):
    t = _text(path)
    for line in (t or "").splitlines()[:12]:
        m = re.match(r"^Status:[ \t]*(.*)$", line)
        if m:
            return m.group(1).strip().lower()
    return ""


def _tickets(squad, scope_dir, scope_text, ledger):
    """-> {NN: status} or None when no source has a task. One rule: squadtickets.scope_tasks."""
    found = squadtickets.scope_tasks(scope_dir, squad.repo_root, scope_dir.name)
    if found["source"] is None:
        return None
    return {t["id"]: t["status"] for t in found["tasks"]}


def scope_row(squad, home, status, ctx):
    """One scope row. `ctx`: now, since, working (set), merged (set or None), newest (dict or None), herdr_unknown."""
    name = home.name
    unknown = []
    scope_text = _text(home / "scope.md")
    if scope_text is None:
        unknown.append("scope.md")
    roster_text = _text(home / "roster.md")
    if roster_text is None:
        unknown.append("roster.md")
    goal = _field(scope_text, "goal") or None
    row = {"name": name, "kind": "scope", "goal": goal, "goal_label": goal or "no goal", "brief": _brief(scope_text),
           "status": status, "closed_at": None, "closed_approx": True, "read_only": status == "done"}
    if status == "done":
        ts = _mtime(home)
        if ts is None:
            data = _text(home / "report" / "data.json")
            try:
                ts = squadboard_time.parse_iso(json.loads(data)["generated_at"])
            except (TypeError, ValueError, KeyError):
                ts = None
        row["closed_at"] = _iso(ts) if ts is not None else "unknown"
    row["closed_approx"] = status == "done"
    # messages and the ledger
    msg_path = home / "messages.jsonl"
    records = squadledger.read_records(str(msg_path)) if msg_path.exists() else None
    if records is None:
        unknown.append("messages.jsonl")
        records = []
    ledger = squadledger.build(records)
    # tickets: x of y done, stuck
    tickets = _tickets(squad, home, scope_text, ledger)
    if tickets is None:
        unknown.append("tickets")
        tickets = {}
    if ctx["merged"] is None:
        unknown.append("git")
    # task events (design s3): a ticket with events counts by its state, else by the ledger
    states = squadtask.fold(squadtask.read_events(squadtask.squad_dir_of(home), squadtask.slug_of(home)))
    done_keys = {squadledger.key(k) for k, s in tickets.items() if s.startswith("done")}
    for r in ledger:
        if ctx["merged"] and r.get("branch") in ctx["merged"]:
            done_keys.add(squadledger.key(r["task"]))
    for k, st in states.items():
        if st["merged_ts"] or (st["sha"] and ctx["merged"] and st["branch"] in ctx["merged"]):
            done_keys.add(k)
    all_keys = {squadledger.key(k) for k in tickets}
    facts = {squadledger.key(r["task"]): (r.get("blocked"), r.get("returns"), r.get("verdicts")) for r in ledger}
    facts.update({k: (st["blocked_open"], st["returns"], st["verdicts"]) for k, st in states.items()})
    stuck = 0
    for k, (blocked, returns, v) in facts.items():
        if k in done_keys:
            continue
        if blocked or (returns and not (v and all(x == "PASS" for x in v.values()))):
            stuck += 1
    # needs you: open questions and unread items of this scope (inbox files only)
    needs = None
    if (home / "escalations.md").exists() or (home / "inbox.jsonl").exists():
        try:
            c = squadinbox.snapshot(str(home), write=False)["counts"]
            needs = c["answer_open"] + c["read_open"]
        except Exception:
            unknown.append("inbox")
    else:
        unknown.append("inbox")
    # agents working now
    working = None
    if ctx["herdr_unknown"]:
        unknown.append("herdr")
    else:
        working = len(set(_roster_names(roster_text)) & ctx["working"])
    # last active: newest message, branch commit, or file mtime (no transcript is read)
    times = [squadboard_time.parse_iso(r.get("ts")) for r in records]
    times += [_mtime(home / n) for n in ("messages.jsonl", "inbox.jsonl", "escalations.md", "scope.md")]
    if ctx["newest"] and name in ctx["newest"]:
        times.append(ctx["newest"][name])
    times = [t for t in times if t is not None]
    last = max(times) if times else None
    new = None
    if ctx["since"] is not None:
        new = sum(1 for r in records if (squadboard_time.parse_iso(r.get("ts")) or 0) > ctx["since"])
    row.update(needs_you=needs, stuck=stuck, tasks_done=len(done_keys & all_keys),
               tasks_total=len(all_keys), agents_working=working, last_active=_iso(last), new=new)
    row["unknown"] = unknown
    return row


def _goal_row(squad, home, status, scope_rows):
    text = _text(home / "goal.md")
    unknown = [] if text is not None else ["goal.md"]
    row = {"name": home.name, "kind": "goal", "goal": home.name, "goal_label": "", "brief": _brief(text),
           "status": status, "closed_at": None, "closed_approx": status == "done", "read_only": status == "done",
           "scopes_count": len(scope_rows)}
    if status == "done":
        ts = _mtime(home)
        row["closed_at"] = _iso(ts) if ts is not None else "unknown"

    def total(k):
        vals = [r[k] for r in scope_rows if r[k] is not None]
        return sum(vals) if vals or not scope_rows else None
    row.update(needs_you=total("needs_you"), stuck=total("stuck"), tasks_done=total("tasks_done"),
               tasks_total=total("tasks_total"), agents_working=total("agents_working"), new=total("new"))
    las = [r["last_active"] for r in scope_rows if r["last_active"]]
    row["last_active"] = max(las) if las else None
    row["unknown"] = unknown
    return row


def _sort_open(rows):
    rows.sort(key=lambda r: r["last_active"] or "", reverse=True)  # newest first, then stable by the two counts
    rows.sort(key=lambda r: (-(r["needs_you"] or 0), -(r["stuck"] or 0)))
    return rows


def _sort_done(rows):
    rows.sort(key=lambda r: (r["closed_at"] if r["closed_at"] not in (None, "unknown") else ""), reverse=True)
    return rows


def _dirs(d):
    try:
        return sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith("_"))
    except OSError:
        return []


def _ctx(squad, sel):
    since = squadboard_time.parse_iso((sel.get("params") or {}).get("since"))
    working, herdr_unknown = _herdr_working(sel)
    newest, merged = _git_facts(squad, squad.repo_root)
    return {"since": since, "working": working, "herdr_unknown": bool(herdr_unknown), "newest": newest, "merged": merged}


def squad_rows(squad, sel, only_goal=None, only_scope=None):
    """-> {goals, scopes, done, scope_rows} for one squad. only_* limit the work to one choice."""
    ctx = _ctx(squad, sel)
    live, closed = squad.path / "scopes", squad.path / "scopes" / "_done"
    scope_rows = []  # (row)
    for status, base in (("open", live), ("done", closed)):
        for home in _dirs(base):
            if only_scope and home.name != only_scope:
                continue
            row = scope_row(squad, home, status, ctx)
            if only_goal and row["goal"] != only_goal:
                continue
            scope_rows.append(row)
    return {"ctx": ctx, "scope_rows": scope_rows}


def picker(sel):
    squads = []
    for squad in sel["squads"]:
        if squad.flat:
            squads.append({"name": squad.name, "key": squad.key, "path": str(squad.path), "flat": True,
                           "message": "flat squad: not supported", "open": [], "done": [], "goals": [], "scopes": []})
            continue
        built = squad_rows(squad, sel)
        scope_rows = built["scope_rows"]
        open_goals = _dirs(squad.path / "goals")
        closed_goals = _dirs(squad.path / "goals" / "_done")
        names = {p.name for p in open_goals}
        rows_open, rows_done = [], []
        for p in open_goals:
            rows_open.append(_goal_row(squad, p, "open", [r for r in scope_rows if r["goal"] == p.name]))
        for p in closed_goals:
            rows_done.append(_goal_row(squad, p, "done", [r for r in scope_rows if r["goal"] == p.name]))
        gone = {p.name for p in closed_goals} | names
        for r in scope_rows:
            if r["goal"] in names:
                continue  # listed under its open goal
            if r["goal"] in gone:  # scope of a closed goal: the goal row holds it
                continue
            (rows_done if r["status"] == "done" else rows_open).append(r)
        squads.append({"name": squad.name, "key": squad.key, "path": str(squad.path), "flat": False,
                       "open": _sort_open(rows_open), "done": _sort_done(rows_done),
                       "goals": [p.name for p in open_goals], "scopes": [r["name"] for r in scope_rows if r["status"] == "open"]})
    data = {"squads": squads, "multiple": len(squads) > 1, "read_only": True}
    if sel.get("demo"):
        data["demo"] = True  # ticket 37b: only in the demo; no key in a normal run
    chk = (sel.get("params") or {}).get("check")
    if chk:
        data["check"] = check(sel, chk)
    return {"data": data, "quality": "approx", "unknown": []}


def check(sel, name):
    """AC6: does a saved choice still exist? {name, exists, kind, where, message}. Looks in the live place and `_done/` only."""
    if not isinstance(name, str) or not NAME_OK.match(name):
        return {"name": name, "exists": False, "kind": None, "where": None, "message": "saved choice %s not found" % name}
    for squad in sel.get("squads") or []:
        for kind in ("goal", "scope"):
            for where, rel in (("live", kind + "s"), ("done", kind + "s/_done")):
                if (squad.path / rel / name).is_dir():
                    return {"name": name, "exists": True, "kind": kind, "where": where, "message": ""}
    return {"name": name, "exists": False, "kind": None, "where": None, "message": "saved choice %s not found" % name}


def read(sel):
    """`/api/scopes`: the rows of the chosen goal or scope. Never raises."""
    try:
        squad, kind, name = sel.get("squad"), sel.get("kind"), sel.get("name")
        if squad is None or kind not in ("goal", "scope") or not NAME_OK.match(name or ""):
            return {"data": None, "quality": "unknown", "unknown": ["selection"]}
        if kind == "scope":
            built = squad_rows(squad, sel, only_scope=name)
            rows = built["scope_rows"]
            if not rows:
                return {"data": None, "quality": "unknown", "unknown": ["scope"]}
            return {"data": {"kind": "scope", "scope": rows[0]}, "quality": "approx", "unknown": rows[0]["unknown"]}
        built = squad_rows(squad, sel, only_goal=name)
        home = squad.find("goal", name)
        status = "done" if home is not None and home.parent.name == "_done" else "open"
        rows = _sort_open([r for r in built["scope_rows"] if r["status"] == "open"]) + \
            _sort_done([r for r in built["scope_rows"] if r["status"] == "done"])
        grow = _goal_row(squad, home, status, rows) if home is not None else None
        table = goal_scopes_table(_text(home / "goal.md")) if home is not None else {"columns": [], "rows": []}
        return {"data": {"kind": "goal", "goal": grow, "scopes": rows, "scopes_table": table,
                         "empty_text": "No scopes in this goal" if not rows else ""},
                "quality": "approx", "unknown": (grow or {}).get("unknown", [])}
    except Exception:  # a reader never raises
        return {"data": None, "quality": "unknown", "unknown": ["scopes"]}


def read_picker(sel):
    try:
        return picker(sel)
    except Exception:
        return {"data": None, "quality": "unknown", "unknown": ["squads"]}


ROUTE = [{"name": "squads", "path": "/api/squads", "read": read_picker, "selection": False},
         {"name": "scopes", "path": "/api/scopes", "read": read, "selection": True}]
