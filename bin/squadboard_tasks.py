"""squad board: tasks reader (module M5). Every task, its stage, owner, returns and "N new".

read(sel) -> {data: {rows, ready_for_review, scope_column}, quality, unknown}. Never raises, read-only.
Route: GET /api/tasks?scope=S|goal=G[&since=<epoch>[&detail=<id>]].

Stages come from the ledger (`squadledger.build`, imported, not copied), `messages.jsonl`, the ticket `Status:`
line and git (`squadboard_git`). A row needs a ticket file or a plan-table row: a token like `REV-8` is not a task.
Free text kept: ticket titles and the first line of the newest FAIL reason (cut `REASON_CUT`); nothing else.
"""
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadboard_git  # noqa: E402
import squadledger  # noqa: E402
import squadtickets  # noqa: E402
from squadboard_time import parse_iso  # noqa: E402
from squadreport_tasks import DEDUPE_S, REASON_CUT, iso  # noqa: E402

STAGES = ("todo", "in progress", "returned", "blocked", "done", "ready for review", "sha changed after PASS", "merged")
NEW_TYPES = ("HANDIN", "FAIL", "PASS", "BLOCKED", "DECISION")
QA_ROLES = {"qa-whitebox": "QA whitebox", "qa-blackbox": "QA blackbox"}


# ---- small parsers --------------------------------------------------------

def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _table(text):
    """First markdown table of `text` -> [{lowercase header: cell}]."""
    rows, head = [], None
    for line in (text or "").splitlines():
        if not line.strip().startswith("|"):
            if head and rows:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if head is None:
            head = [c.lower() for c in cells]
        elif not all(re.match(r"^:?-+:?$", c) for c in cells if c):
            rows.append(dict(zip(head, cells)))
    return rows


def _field(text, name):
    m = re.search(r"^\s*" + name + r"\s*:\s*(.*?)\s*$", text or "", re.I | re.M)
    return m.group(1) if m else None


def _roster(home):
    return _table(_read(Path(home) / "roster.md"))


def _first_line(text):
    """Reason line of a FAIL: header `FAIL NN:` removed; a bare one-word header (`finding`) gives the next line."""
    lines = [x.strip() for x in (text or "").splitlines() if x.strip()]
    if not lines:
        return ""
    head = re.sub(r"^\S+\s+\S+\s*(\([^)]*\))?[:\s-]*", "", lines[0], count=1)
    if (not head or re.match(r"^\w+$", head)) and len(lines) > 1:
        head = lines[1]
    return head[:REASON_CUT]


def age_words(seconds):
    s = max(0, int(seconds))
    if s < 60:
        return "<1 min"
    if s < 3600:
        return "%d min" % (s // 60)
    if s < 86400:
        return "%d h" % (s // 3600)
    return "%d d" % (s // 86400)


# ---- stage (pure) ----------------------------------------------------------

def stage(f):
    """f: task facts -> (word, detail). Words are exact (ticket 07)."""
    verd, checkers = f.get("verdicts") or {}, f.get("checkers") or []
    passed = [c for c in checkers if verd.get(c) == "PASS"]
    all_pass = bool(checkers) and len(passed) == len(checkers)
    tip, sha = f.get("tip"), f.get("sha")
    tip_match = bool(tip and sha and (tip.startswith(sha) or sha.startswith(tip)))
    if f.get("merged") and f.get("handin"):
        return "merged", ""
    if all_pass and tip and tip_match:
        return "ready for review", ""
    if all_pass and tip and not tip_match:
        return "sha changed after PASS", "PASS on %s, branch tip %s" % (sha[:10], tip[:10])
    if f.get("ticket_status") == "done":
        return "done", ""
    if f.get("ticket_status") == "blocked" and not f.get("blocked"):
        return "blocked", ""
    if f.get("blocked"):
        return "blocked", f["blocked"][0]
    if f.get("handin"):
        if any(v == "FAIL" for v in verd.values()):
            return "returned", ""
        waiting = [QA_ROLES.get(f["roles"].get(c), c) for c in checkers if verd.get(c) != "PASS"]
        word = "checking, %d of %d PASS" % (len(passed), len(checkers))
        if waiting and f.get("wait_s") is not None and not all_pass:
            word += ", waiting on %s, %s" % (" and ".join(waiting), age_words(f["wait_s"]))
        return word, ""
    if f.get("active") or f.get("ticket_status") in ("in progress", "handed in"):
        return "in progress", ""
    return "todo", ""


def _waits_on(word, f):
    if word.startswith("checking") or word == "sha changed after PASS":
        verd = f.get("verdicts") or {}
        w = [QA_ROLES.get(f["roles"].get(c), c) for c in f["checkers"] if verd.get(c) != "PASS"]
        return " and ".join(w) or "QA"
    return {"ready for review": "PO", "returned": f["owner"], "blocked": "Manager", "in progress": f["owner"],
            "todo": "assignment", "done": "nobody", "merged": "nobody"}.get(word, "nobody")


# ---- one scope -------------------------------------------------------------

class _C:
    def __init__(self, home, name):
        self.scope_home, self.name = str(home), name


def read_scope(squad_name, name, home, repo_root, since, now, git=None, with_detail=False, looked=None):
    """-> (rows, unknown list, ready list) for one scope folder."""
    unknown, home = [], Path(home)
    recs = squadledger.read_records(home / "messages.jsonl")
    if not (home / "messages.jsonl").exists():
        unknown.append("messages")
    ledger = {squadledger.key(r["task"]): r for r in squadledger.build(recs)}
    tokens = sorted({str(r.get("task")) for r in recs if r.get("task")})
    scope_md = _read(home / "scope.md") or ""
    root = _repo_of(home, repo_root)
    found = squadtickets.scope_tasks(home, root, name)
    by_id = {t["id"]: t for t in found["tasks"]}
    if found["source"] is None:
        unknown.append("tickets")
        if looked is not None:
            looked.extend(x for x in found["looked"] if x not in looked)
    ids = {squadledger.key(i): i for i in by_id}
    roster = _roster(home)
    roles = {r.get("agent"): r.get("role") for r in roster if r.get("agent")}
    live = [a for a, r in roles.items() if r in QA_ROLES]
    live = [a for a in live if next((x.get("status") for x in roster if x.get("agent") == a), "") != "retired"]
    checkers = live or [a for a in roles if roles[a] in QA_ROLES] or []
    owns = {}
    for r in roster:
        m = re.search(r"ticket\s*#?\s*(\d+)", r.get("owns", ""), re.I)
        if m and r.get("role") == "dev":
            owns.setdefault(squadledger.key(m.group(1)), r.get("agent"))
    refs = git
    if refs is None:
        refs = _git_refs(root, squad_name, name)
    if refs is None:
        unknown.append("git")
    tips = {} if refs is None else {r["branch"]: r for r in refs[0]}
    merged = set() if refs is None else {r["branch"] for r in refs[1]}
    rows, ready = [], []
    for key, tid in sorted(ids.items(), key=lambda kv: (len(kv[1]), kv[1])):
        led = ledger.get(key) or {}
        msgs = [r for r in recs if squadledger.key(r.get("task")) == key]
        owner = owns.get(key) or led.get("handin_from") or "unassigned"
        branch = "squad/%s/%s/%s" % (squad_name, name, led["handin_from"]) if led.get("handin_from") else None
        tip = (tips.get(branch) or {}).get("sha") if branch else None
        facts = {"verdicts": led.get("verdicts"), "checkers": checkers, "roles": roles, "sha": led.get("sha"),
                 "tip": tip, "merged": branch in merged, "handin": bool(led.get("handin_from")),
                 "ticket_status": (by_id.get(tid) or {}).get("status", ""), "blocked": led.get("blocked"),
                 "active": bool(msgs), "owner": owner, "wait_s": None}
        if led.get("handin_from"):
            hts = max((parse_iso(r.get("ts")) or 0 for r in msgs if r.get("type") == "HANDIN"), default=None)
            facts["wait_s"] = max(0, now - hts) if hts else None
        word, detail = stage(facts)
        last_ts = max((parse_iso(r.get("ts")) or 0 for r in msgs), default=None)
        fails = [r for r in msgs if r.get("type") == "FAIL"]
        new = _count_new(msgs, since)
        row = {"id": tid, "title": (by_id.get(tid) or {}).get("title", ""), "stage": word, "owner": owner,
               "waits_on": _waits_on(word, {**facts, "owner": owner}), "last_active": last_ts,
               "last_active_iso": iso(last_ts) if last_ts else None, "returns": led.get("returns") or 0,
               "last_fail_line": _first_line(fails[-1].get("text")) if fails else "",
               "branch": branch, "tip": tip, "new_count": new, "detail_note": detail,
               "where": (by_id.get(tid) or {}).get("where", ""), "ticket_status": facts["ticket_status"]}
        if (by_id.get(tid) or {}).get("untitled"):
            row["untitled"] = True
        if "abs" in (by_id.get(tid) or {}):
            row["abs"] = by_id[tid]["abs"]
        if with_detail:
            row["detail"] = _detail(msgs)
        rows.append(row)
        if word == "ready for review":
            ready.append({"task": tid, "branch": branch, "tip": tip})
    return rows, unknown, ready


def _repo_of(home, repo_root):
    if repo_root:
        return Path(repo_root)
    p = Path(home).resolve()
    for a in p.parents:
        if a.name == ".claude":
            return a.parent
    return None


def _git_refs(root, squad_name, name):
    if not root:
        return None
    prefix = "squad/%s/%s/" % (squad_name, name)
    allr = squadboard_git.branch_refs(root, prefix)
    mer = squadboard_git.branch_refs(root, prefix, merged_into="main")
    return None if allr is None or mer is None else (allr, mer)


def _count_new(msgs, since):
    """HANDIN/FAIL/PASS/BLOCKED/DECISION newer than `since`; copies of one message within DEDUPE_S count once."""
    if since is None:
        return 0
    last, n = {}, 0
    for r in sorted(msgs, key=lambda x: parse_iso(x.get("ts")) or 0):
        t = parse_iso(r.get("ts"))
        if t is None or r.get("type") not in NEW_TYPES:
            continue
        k = (r.get("from"), r.get("type"))
        if k in last and t - last[k] <= DEDUPE_S:
            continue
        last[k] = t
        if t > since:
            n += 1
    return n


def _detail(msgs):
    """Agents and steps in time order; the only free text is a FAIL reason line."""
    steps = []
    for r in sorted(msgs, key=lambda x: parse_iso(x.get("ts")) or 0):
        t = parse_iso(r.get("ts"))
        step = {"ts": t, "iso": iso(t) if t else None, "agent": r.get("from"), "type": r.get("type")}
        if r.get("type") == "FAIL":
            step["reason"] = _first_line(r.get("text"))
        steps.append(step)
    agents = []
    for s in steps:
        if s["agent"] and s["agent"] not in agents:
            agents.append(s["agent"])
    return {"agents": agents, "steps": steps}


# ---- selection -------------------------------------------------------------

def _scopes_of(sel):
    """-> [(scope name, folder)] of the selection (a goal's scopes, or the one scope)."""
    squad = sel.get("squad")
    if sel.get("kind") == "scope":
        return [(sel["name"], Path(sel["home"]))]
    out, every = [], sel.get("kind") is None
    for kind_dir in ("scopes", "scopes/_done"):
        base = Path(squad.path) / kind_dir
        try:
            names = sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("_"))
        except OSError:
            continue
        for p in names:
            if (every and kind_dir == "scopes") or (_field(_read(p / "scope.md") or "", "goal") or "") == sel.get("name"):
                out.append((p.name, p))
    return out


def _since(sel):
    try:
        return float(sel.get("params", {}).get("since"))
    except (TypeError, ValueError):
        return None


def read(sel):
    try:
        squad, home = sel.get("squad"), sel.get("home")
        if squad is None or home is None:
            return {"data": None, "quality": "unknown", "unknown": ["tasks"]}
        goal = sel.get("kind") == "goal"
        now = sel.get("now") or time.time()
        since = _since(sel)
        want = sel.get("params", {}).get("detail")
        rows, unknown, ready, looked = [], [], [], []
        for sname, shome in _scopes_of(sel):
            r, u, rd = read_scope(squad.name, sname, shome, sel.get("repo_root"), since, now,
                                  with_detail=bool(want), looked=looked)
            for x in r:
                if goal:
                    x["scope"] = sname
                if not want or x["id"] == want:
                    rows.append(x)
            unknown += [s for s in u if s not in unknown]
            ready += [dict(x, scope=sname) if goal else x for x in rd]
        new_by_scope = {}
        if goal:
            for x in rows:
                new_by_scope[x["scope"]] = new_by_scope.get(x["scope"], 0) + x["new_count"]
        data = {"rows": rows, "ready_for_review": ready, "scope_column": goal, "new_by_scope": new_by_scope,
                "looked": looked}
        return {"data": data, "quality": "exact" if not unknown else "approx", "unknown": unknown}
    except Exception:  # a reader never raises
        return {"data": None, "quality": "unknown", "unknown": ["tasks"]}


def ready_by_scope(sel):
    """-> {scope name: ready-for-review count} for EVERY open scope of the squad, whatever the choice. Never raises."""
    try:
        out = {}
        for sname, shome in _scopes_of(dict(sel, kind=None, name=None)):
            out[sname] = len(read_scope(sel["squad"].name, sname, shome, sel.get("repo_root"), None,
                                        sel.get("now") or time.time())[2])
        return out
    except Exception:
        return {}


ROUTE = {"name": "tasks", "path": "/api/tasks", "read": read, "selection": True}
