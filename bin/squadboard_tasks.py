"""squad board: tasks reader (module M5). Every task, its stage, owner, returns and "N new".

read(sel) -> {data: {rows, scope_column}, quality, unknown}. Never raises, read-only.
Route: GET /api/tasks?scope=S|goal=G[&since=<epoch>[&detail=<id>]].

Facts per ticket, first hit wins for each (design.md s6, no merging of two sources for one field): the event store
(`squadtask.fold`, `task-events/<slug>.jsonl`), else the ledger (`squadledger.build`) of the scope with the newest
message of that ticket among every scope sharing the ticket folder, else the ticket `Status:` label (states.md s5).
Git (`squadboard_git`) gives the branch tip and `merged`. A row needs a ticket file or a plan-table row: a token like
`REV-8` is not a task.
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
import squadtask  # noqa: E402
import squadtickets  # noqa: E402
from squadboard_time import parse_iso  # noqa: E402
from squadreport_tasks import DEDUPE_S, REASON_CUT, iso  # noqa: E402

STAGES = ("todo", "in progress", "checking", "returned", "blocked", "passed", "sha changed after PASS", "merged", "wontfix")
PASSED_LIKE = ("passed", "sha changed after PASS", "merged")  # a `Blocked by:` ticket in one of these no longer blocks
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

def _names(f, only_missing=True):
    verd = f.get("verdicts") or {}
    return [QA_ROLES.get(f["roles"].get(c), c) for c in f["checkers"] if not only_missing or verd.get(c) != "PASS"]


def stage(f):
    """f: task facts -> (word, detail). One word per row, first match of states.md s2:
    merged > sha changed after PASS > passed > blocked (BLOCKED message) > returned > checking > in progress >
    blocked (open `Blocked by:`) > wontfix > todo. Facts: verdicts, checkers (slot names; `evidence` when no QA),
    qa (the team has QA rows), roles, sha, tip, merged, handin, blocked (open BLOCKED texts), blocked_by_open (ids),
    ticket_status (label, only when the ticket has no events), wontfix, active, claimed, owner, wait_s, warns."""
    verd, checkers = f.get("verdicts") or {}, f.get("checkers") or []
    passed = [c for c in checkers if verd.get(c) == "PASS"]
    tip, sha = f.get("tip"), f.get("sha")
    all_pass = bool(sha) and (verd.get("override") == "PASS" or (bool(checkers) and len(passed) == len(checkers)))
    tip_match = bool(tip and sha and (tip.startswith(sha) or sha.startswith(tip)))
    note = "; ".join(f.get("warns") or [])
    status = f.get("ticket_status") or ""
    if f.get("merged"):
        return "merged", note
    if all_pass and tip and not tip_match:
        return "sha changed after PASS", "PASS on %s, branch tip %s" % (sha[:10], tip[:10])
    if all_pass:
        return "passed", note  # the tip matches or is unknown (other scope, no branch): still passed
    if status == "done":
        return "passed", note
    if f.get("blocked"):
        return "blocked", f["blocked"][0]
    if f.get("handin"):
        if any(v == "FAIL" for v in verd.values()):
            return "returned", note
        if not f.get("qa"):
            return "in progress", note  # no QA: never `checking, 0 of 0`; W9 is in the note until the evidence check passes
        waiting = _names(f)
        word = "checking, %d of %d PASS" % (len(passed), len(checkers))
        if waiting and f.get("wait_s") is not None:
            word += ", waiting on %s, %s" % (" and ".join(waiting), age_words(f["wait_s"]))
        return word, note
    if f.get("claimed") or f.get("active") or status in ("claimed", "in progress", "handed in"):
        return "in progress", note
    if f.get("wontfix"):
        return "wontfix", ""  # waits on nobody, even with an open `Blocked by:`
    if f.get("blocked_by_open"):
        return "blocked", "waiting on ticket " + ", ".join(f["blocked_by_open"])
    if status == "blocked":
        return "blocked", ""
    return "todo", ""


def _waits_on(word, f):
    if word.startswith("checking") or word == "sha changed after PASS":
        return " and ".join(_names(f)) or ("QA" if f.get("qa") else "evidence check")
    if word == "blocked":
        if f.get("blocked") or not f.get("blocked_by_open"):
            return "Team Lead" if f.get("has_tl") else "Manager"
        return "ticket " + ", ".join(f["blocked_by_open"])
    return {"passed": "PO", "returned": f["owner"], "in progress": f["owner"], "todo": "assignment"}.get(word, "nobody")


# ---- one scope -------------------------------------------------------------

class _C:
    def __init__(self, home, name):
        self.scope_home, self.name = str(home), name


def _scope_index(squad_dir, cache):
    """{scope name: folder} of every scope of the squad, open first, then `_done`."""
    k = ("index", str(squad_dir))
    if k not in cache:
        idx = {}
        for sub in ("scopes", "scopes/_done"):
            try:
                names = sorted(p for p in (Path(squad_dir) / sub).iterdir() if p.is_dir() and not p.name.startswith("_"))
            except OSError:
                continue
            for p in names:
                idx.setdefault(p.name, p)
        cache[k] = idx
    return cache[k]


def _ledger_of(home, cache):
    """-> {recs, led: {key: ledger row}, ts: {key: newest message epoch}} of one scope folder (cached per request)."""
    k = ("ledger", str(home))
    if k not in cache:
        recs = [r for r in squadledger.read_records(Path(home) / "messages.jsonl") if isinstance(r.get("task"), str)]
        ts = {}
        for r in recs:
            t = parse_iso(r.get("ts"))
            if t is not None:
                kk = squadledger.key(r["task"])
                ts[kk] = max(ts.get(kk, 0), t)
        cache[k] = {"recs": recs, "led": {squadledger.key(x["task"]): x for x in squadledger.build(recs)}, "ts": ts}
    return cache[k]


def _checkers_of(home, cache):
    """-> (slots, has_qa, roles, has_team_lead) from the roster of `home` (the scope that built the ticket)."""
    k = ("chk", str(home))
    if k not in cache:
        chk = squadtask.checkers(home)
        roster = _roster(home)
        cache[k] = (squadtask.slots(chk), bool(chk["qa"]), {r.get("agent"): r.get("role") for r in roster if r.get("agent")},
                    any(r.get("role") == "team-lead" for r in roster))
    return cache[k]


def read_scope(squad_name, name, home, repo_root, since, now, git=None, with_detail=False, looked=None, cache=None):
    """-> (rows, unknown list, ready list) for one scope folder. `ready`: passed branches waiting for the PO."""
    unknown, home, cache = [], Path(home), ({} if cache is None else cache)
    own = _ledger_of(home, cache)
    if not (home / "messages.jsonl").exists():
        unknown.append("messages")
    root = _repo_of(home, repo_root)
    found = squadtickets.scope_tasks(home, root, name)
    by_id = {t["id"]: t for t in found["tasks"]}
    if found["source"] is None:
        unknown.append("tickets")
        if looked is not None:
            looked.extend(x for x in found["looked"] if x not in looked)
    ids = {squadledger.key(i): i for i in by_id}
    roster = _roster(home)
    squad_dir, slug = squadtask.squad_dir_of(home), squadtask.slug_of(home)
    states = squadtask.fold(squadtask.read_events(squad_dir, slug))  # a missing or bad file gives {}
    index = _scope_index(squad_dir, cache)
    siblings = {n: p for n, p in index.items() if n != name and squadtask.slug_of(p) == slug}
    owns = {}
    for r in roster:
        m = re.search(r"ticket\s*#?\s*(\d+)", r.get("owns", ""), re.I)
        if m and r.get("role") == "dev":
            owns.setdefault(squadledger.key(m.group(1)), r.get("agent"))
    refs = git
    if refs is None:
        if "refs" not in cache:
            cache["refs"] = _git_refs(root, squad_name)
        refs = cache["refs"]
    if refs is None:
        unknown.append("git")
    tips = {} if refs is None else {r["branch"]: r for r in refs[0]}
    merged = set() if refs is None else {r["branch"] for r in refs[1]}
    tickets = []
    for key, tid in sorted(ids.items(), key=lambda kv: (len(kv[1]), kv[1])):
        st = states.get(key)
        # the ledger of the scope with the newest message of this ticket (own scope wins a tie): D8
        src_name, src = name, own
        for sn, sp in siblings.items():
            cand = _ledger_of(sp, cache)
            if cand["ts"].get(key, -1) > src["ts"].get(key, -1):
                src_name, src = sn, cand
        led = src["led"].get(key) or {}
        msgs = [r for r in src["recs"] if squadledger.key(r["task"]) == key]
        status = (by_id.get(tid) or {}).get("status", "")
        if st:
            scope_of, owner, sha, verd = st["scope"] or src_name, st["owner"], st["sha"], st["verdicts"]
            branch = st["branch"] or ("squad/%s/%s/%s" % (squad_name, scope_of, owner) if sha and owner else None)
            handin_ts, returns, blocked = parse_iso(st["handin_ts"]), st["returns"], st["blocked_open"]
            claimed, warns = bool(st["claimed"] or owner), st["warns"]
            ev_ts, merged_ts = parse_iso(st["updated_ts"]), bool(st["merged_ts"])
            label = ""  # the store wins; the ticket label only fills a ticket with no events
        else:
            scope_of, sha, verd = src_name, led.get("sha"), led.get("verdicts")
            owner = owns.get(key) or led.get("handin_from")
            branch = led.get("branch") or ("squad/%s/%s/%s" % (squad_name, src_name, led["handin_from"]) if led.get("handin_from") else None)
            hts = max((parse_iso(r.get("ts")) or 0 for r in msgs if r.get("type") == "HANDIN"), default=None)
            handin_ts, returns, blocked = hts, led.get("returns") or 0, led.get("blocked")
            claimed, warns, ev_ts, merged_ts, label = False, [], None, False, status
        slots, has_qa, roles, has_tl = _checkers_of(index.get(scope_of) or home, cache)
        tip = (tips.get(branch) or {}).get("sha") if branch else None
        owner = owner or "unassigned"
        facts = {"verdicts": verd, "checkers": slots, "qa": has_qa, "roles": roles, "has_tl": has_tl, "sha": sha, "tip": tip,
                 "merged": merged_ts or bool(branch in merged and sha), "handin": bool(sha), "blocked": blocked,
                 "blocked_by_open": [], "ticket_status": label, "wontfix": status == "wontfix", "claimed": claimed,
                 "active": bool(msgs) and not st, "owner": owner, "wait_s": max(0, now - handin_ts) if handin_ts else None,
                 "warns": warns}
        tickets.append([key, tid, st, msgs, facts, branch, tip, returns, ev_ts, status])
    word_of = {t[0]: stage(t[4])[0] for t in tickets}
    rows, ready = [], []
    for key, tid, st, msgs, facts, branch, tip, returns, ev_ts, status in tickets:
        for b in squadtask.parse_blocked_by(squadtask.ticket_text(home, root, tid)):
            if word_of.get(squadledger.key(b)) not in PASSED_LIKE:
                facts["blocked_by_open"].append(b)
        word, detail = stage(facts)
        owner = facts["owner"]
        msg_ts = max((parse_iso(r.get("ts")) or 0 for r in msgs), default=None)
        last_ts = max((t for t in (msg_ts, ev_ts) if t), default=None)
        fails = [r for r in msgs if r.get("type") == "FAIL"]
        new = _count_new(msgs, since)
        row = {"id": tid, "title": (by_id.get(tid) or {}).get("title", ""), "stage": word, "owner": owner,
               "waits_on": _waits_on(word, facts), "last_active": last_ts,
               "last_active_iso": iso(last_ts) if last_ts else None, "returns": returns,
               "last_fail_line": _first_line(fails[-1].get("text")) if fails else "",
               "branch": branch, "tip": tip, "new_count": new, "detail_note": detail,
               "where": (by_id.get(tid) or {}).get("where", ""), "ticket_status": status}
        if (by_id.get(tid) or {}).get("untitled"):
            row["untitled"] = True
        if "abs" in (by_id.get(tid) or {}):
            row["abs"] = by_id[tid]["abs"]
        if with_detail:
            row["detail"] = _detail(msgs)
        rows.append(row)
        if word == "passed" and tip:
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


def _git_refs(root, squad_name):
    """One pair of git calls for every scope of the squad: a ticket built in another scope has its branch there."""
    if not root:
        return None
    prefix = "squad/%s/" % squad_name
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
        rows, unknown, looked, cache = [], [], [], {}
        for sname, shome in _scopes_of(sel):
            r, u, _ = read_scope(squad.name, sname, shome, sel.get("repo_root"), since, now,
                                 with_detail=bool(want), looked=looked, cache=cache)
            for x in r:
                if goal:
                    x["scope"] = sname
                if not want or x["id"] == want:
                    rows.append(x)
            unknown += [s for s in u if s not in unknown]
        new_by_scope = {}
        if goal:
            for x in rows:
                new_by_scope[x["scope"]] = new_by_scope.get(x["scope"], 0) + x["new_count"]
        data = {"rows": rows, "scope_column": goal, "new_by_scope": new_by_scope,
                "looked": looked, "wsl_distro": os.environ.get("WSL_DISTRO_NAME") or None}  # ticket 30: the VS Code link form
        return {"data": data, "quality": "exact" if not unknown else "approx", "unknown": unknown}
    except Exception:  # a reader never raises
        return {"data": None, "quality": "unknown", "unknown": ["tasks"]}


def ready_by_scope(sel):
    """-> {scope name: passed branches waiting for the PO} for EVERY open scope of the squad, whatever the choice.
    Never raises. (The Inbox still calls it by its old name; the count is the `passed` rows that have a branch.)"""
    try:
        out, cache = {}, {}
        for sname, shome in _scopes_of(dict(sel, kind=None, name=None)):
            out[sname] = len(read_scope(sel["squad"].name, sname, shome, sel.get("repo_root"), None,
                                        sel.get("now") or time.time(), cache=cache)[2])
        return out
    except Exception:
        return {}


ROUTE = {"name": "tasks", "path": "/api/tasks", "read": read, "selection": True}
