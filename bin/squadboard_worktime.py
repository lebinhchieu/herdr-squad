"""squad board: work time per agent for GET /api/worktime (ticket 15, architecture.md sections 4 and 6, M9).

Reuses the report model, never a second one: pieces come from `squadreport.collect` (which runs `_classify`),
task attribution from `squadreport_tasks._Ctx.at`. Private names used (listed in HANDIN): `_Resolver`, `_Ctx`,
`_dedupe` of squadreport_tasks; `_roster`, `_find_sessions`, `_scope_field`, `_sum_segs` of squadreport;
`_git` of squadboard_git.

The board draws the *unfiltered* pieces: the report's drawing step (`_segments`, 30/60 s minimum) is not applied.

    read(sel) -> {"data": {...}, "quality": "approx", "unknown": [source]}     never raises

A request the reader cannot serve (no choice, bad range) answers `{"data": None, "refused": 400, "error": ...}`.
Query (`sel["params"]`): `from`, `to` (UTC epoch seconds; default first record .. now), `gap_min` (15..240, default 60,
clamped). Piece = {start, end, bucket, on, task, worktree, branch, approx, collapsible, open}, UTC epoch seconds.
Bucket is working|waiting|blocked|idle (the report's `blocking` is renamed in BUCKET_NAME). `worktree` and `branch`
are empty until M10. `open` is false: a transcript piece always ends at a record, no time is invented up to `now`.
Read-only: nothing is written.
"""
import os
import sys
import threading
import time
from pathlib import Path

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
import squadboard_git  # noqa: E402
import squadreport  # noqa: E402
import squadtranscript  # noqa: E402
from squadreport_tasks import EVENT_TYPES, _Ctx, _Resolver, _dedupe, _mtype  # noqa: E402

GAP_DEFAULT_MIN, GAP_MIN_MIN, GAP_MAX_MIN = 60, 15, 240
BUCKET_NAME = {"working": "working", "waiting": "waiting", "blocking": "blocked", "idle": "idle"}
NEVER_COLLAPSE = ("waiting", "blocked")
MARK_KINDS = {"HANDIN": "handin", "FAIL": "fail", "PASS": "pass", "BLOCKED": "blocked", "MERGE": "merge", "MERGED": "merge"}
COMMIT_LIMIT = 2000
CACHE_MAX = 8
_CACHE = {}  # scope path -> (signature, Collected)
_PATHS = {}  # scope path -> (key, transcript paths)
_LOCK = threading.RLock()  # the server is threaded: one lock for both caches; a second cold request waits for the first


def _refuse(code, msg):
    return {"data": None, "refused": code, "error": msg, "quality": "unknown", "unknown": []}


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x and abs(x) != float("inf") else None


def hm(seconds):
    """Whole seconds -> {"seconds", "hours", "minutes", "label"}; never a percent."""
    s = max(0, int(round(seconds)))
    h, m = divmod(s // 60, 60)
    return {"seconds": s, "hours": h, "minutes": m, "label": "%d h %d min" % (h, m)}


def _stat(p):
    try:
        st = os.stat(p)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _session_paths(home):
    """Transcript paths of the roster, cached until the roster or a project dir changes (a new session file
    changes its dir's mtime; finding them opens the first lines of every file there, about 1 s for this squad)."""
    try:
        dirs = tuple(_stat(d) for d in sorted((squadtranscript.config_dir() / "projects").iterdir()) if d.is_dir())
    except OSError:
        dirs = ()
    key = (str(home), str(squadtranscript.config_dir()), _stat(home / "roster.md"), dirs)
    with _LOCK:
        hit = _PATHS.get(str(home))
        if hit and hit[0] == key:
            return hit[1]
        paths = []
        for row in squadreport._roster(home / "roster.md"):
            paths += squadreport._find_sessions(row["name"], row["session"], [])
        paths = sorted(set(paths))
        _PATHS[str(home)] = (key, paths)
        return paths


def _signature(home, squad_dir):
    """Cheap key of every file `collect` reads: stale after a transcript grows (mtime + size)."""
    sig = [_stat(home / n) for n in ("messages.jsonl", "inbox.jsonl", "roster.md", "scope.md")]
    sig.append(_stat(Path(squad_dir) / "settings" / "report.json"))
    try:
        for p in _session_paths(home):
            sig.append((p, _stat(p)))
            sub = Path(p).with_suffix("") / "subagents"
            if sub.is_dir():
                sig += [(str(q), _stat(q)) for q in sorted(sub.glob("*.jsonl"))]
    except OSError:
        pass
    return tuple(sig)


def collected(home, squad_dir):
    """squadreport.collect, cached in memory by file mtime + size. Thread-safe: the lock is held while collect runs."""
    key = str(home)
    with _LOCK:
        sig = _signature(home, squad_dir)
        hit = _CACHE.get(key)
        if hit and hit[0] == sig:
            return hit[1]
        c = squadreport.collect(home, squad_dir, BIN.parent, final=True)
        while len(_CACHE) >= CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)), None)
        _CACHE[key] = (sig, c)
        return c


def _clip(a, b, lo, hi):
    a, b = max(a, lo), min(b, hi)
    return (a, b) if a < b else None


def agent_pieces(name, tl, ctx, lo, hi, gap_s):
    """Unfiltered pieces of one agent inside [lo, hi): split where a message names a task, clipped at the edges."""
    out = []
    for sg in tl.segs:
        if sg.end <= sg.start:
            continue
        bucket = BUCKET_NAME[sg.bucket]
        collapsible = bucket not in NEVER_COLLAPSE and sg.end - sg.start > gap_s  # the whole gap decides, not the part in range
        on = sg.on if bucket == "blocked" else None
        pts = [sg.start]
        if bucket != "idle":
            pts += ctx.breaks(name, sg.start, sg.end)
        pts.append(sg.end)
        for a, b in zip(pts, pts[1:]):
            task = None if bucket == "idle" else ctx.at(name, a)[0]
            cut = _clip(a, b, lo, hi)
            if cut:
                out.append({"start": cut[0], "end": cut[1], "bucket": bucket, "on": on, "task": task,
                            "worktree": "", "branch": "", "approx": task is not None,
                            "collapsible": collapsible, "open": False})
    return out


def totals(pieces):
    """All pieces per bucket (equals the report for the same range) and what counts as work time (collapsed gaps out)."""
    all_b = dict.fromkeys(BUCKET_NAME.values(), 0)
    counted = dict.fromkeys(BUCKET_NAME.values(), 0)
    collapsed = unattributed = 0
    for p in pieces:
        d = p["end"] - p["start"]
        all_b[p["bucket"]] += d
        if p["collapsible"]:
            collapsed += d
            continue
        counted[p["bucket"]] += d
        if p["task"] is None and p["bucket"] != "idle":
            unattributed += d
    return {"buckets_s": all_b, "counted_s": counted, "collapsed_s": collapsed, "unattributed": hm(unattributed)}


def message_marks(c, res, lo, hi):
    marks = []
    for m in _dedupe([m for m in c.msgs if res.task_of(m) or _mtype(m) in EVENT_TYPES or _mtype(m) in MARK_KINDS], res.task_of):
        kind = MARK_KINDS.get(_mtype(m))
        if kind and lo <= m.ts < hi:
            marks.append({"ts": m.ts, "kind": kind, "agent": m.frm, "task": res.task_of(m)})
    return marks


def commit_marks(repo, squad, scope, lo, hi):
    """-> (marks, ok). Commits reachable from the scope's branches inside the range. ok False = git unknown."""
    refs = squadboard_git.branch_refs(repo, "squad/%s/%s/" % (squad, scope))
    if refs is None:
        return [], False
    if not refs:
        return [], True
    out = squadboard_git._git(repo, "log", "--no-merges", "--max-count=%d" % COMMIT_LIMIT,
                              "--since=@%d" % int(lo), "--until=@%d" % int(hi),
                              "--format=%ct\t%h", *[r["branch"] for r in refs], "--")
    if out is None:
        return [], False
    marks, seen = [], set()
    for line in out.splitlines():
        ts, _, sha = line.partition("\t")
        if sha and sha not in seen and ts.isdigit() and lo <= int(ts) < hi:
            seen.add(sha)
            marks.append({"ts": int(ts), "kind": "commit", "sha": sha})
    return marks, True


def build(c, lo, hi, gap_s, repo=None, squad="", scope=""):
    """Pure core: Collected -> (data, unknown). `repo` None skips the commit marks (no git asked)."""
    res = _Resolver(c, list(c.msgs))
    ctx = _Ctx(c, res)
    agents, allp = [], []
    for name, tl in c.agents.items():
        if not tl.transcript_found:
            agents.append({"agent": name, "role": tl.role, "scope": scope, "pieces": [], "note": "no transcript: " + name})
            continue
        ps = agent_pieces(name, tl, ctx, lo, hi, gap_s)
        allp += ps
        agents.append({"agent": name, "role": tl.role, "scope": scope, "pieces": ps, "respawn_gap_s": tl.respawn_gap,
                       "totals": totals(ps)})
    marks = message_marks(c, res, lo, hi)
    unknown = []
    if repo is not None:
        cm, ok = commit_marks(repo, squad, scope, lo, hi)
        marks += cm
        if not ok:
            unknown.append("git")
    marks.sort(key=lambda m: (m["ts"], m["kind"]))
    return {"agents": agents, "marks": marks, "totals": totals(allp)}, unknown


def _scopes(sel):
    """-> [(scope name, home)] of the choice. A goal pulls the scopes whose scope.md names it."""
    squad = sel["squad"]
    if sel["kind"] == "scope":
        return [(sel["name"], sel["home"])]
    out = []
    for rel in ("scopes", "scopes/_done"):
        base = squad.path / rel
        try:
            names = sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("_"))
        except OSError:
            continue
        for p in names:
            if squadreport._scope_field(p / "scope.md", "goal") == sel["name"]:
                out.append((p.name, p))
    return out


def read(sel):
    try:
        return _read(sel)
    except Exception:  # the reader contract: never raises
        return {"data": None, "quality": "unknown", "unknown": ["worktime"]}


def _read(sel):
    if not isinstance(sel, dict) or not sel.get("kind") or not sel.get("squad"):
        return _refuse(400, "selection required")
    params = sel.get("params") or {}
    now = _num(sel.get("now"))
    now = now if now is not None else time.time()
    g = _num(params.get("gap_min"))
    gap_min = GAP_DEFAULT_MIN if g is None else int(min(GAP_MAX_MIN, max(GAP_MIN_MIN, g)))
    f, t = params.get("from"), params.get("to")
    lo, hi = _num(f), _num(t)
    if (f not in (None, "") and lo is None) or (t not in (None, "") and hi is None):
        return _refuse(400, "from and to must be UTC epoch seconds")
    hi = int(now if hi is None else hi)
    lo = None if lo is None else int(lo)
    squad = sel["squad"]
    cols, unknown = [], []
    for scope, home in _scopes(sel):
        try:
            cols.append((scope, collected(home, squad.path)))
        except (OSError, ValueError, squadreport.Unsupported, squadreport.Deadline):
            unknown.append("transcript:" + scope)
    if lo is None:
        starts = [c.window[0] for _, c in cols if c.window[0] is not None]
        lo = min(starts) if starts else hi - 86400
    if lo >= hi:
        return _refuse(400, "from must be before to")
    data = {"from": lo, "to": hi, "gap_min": gap_min, "agents": [], "marks": [],
            "totals": None, "unattributed_note": "approx: time not tied to a task, hours and minutes"}
    allp = []
    for scope, c in cols:
        d, unk = build(c, lo, hi, gap_min * 60, sel.get("repo_root"), squad.name, scope)
        data["agents"] += d["agents"]
        data["marks"] += d["marks"]
        allp += [p for a in d["agents"] for p in a["pieces"]]
        unknown += unk
    data["marks"].sort(key=lambda m: (m["ts"], m["kind"]))
    data["totals"] = totals(allp)
    if any("no transcript" in a.get("note", "") for a in data["agents"]):
        unknown.append("transcript")
    return {"data": data, "quality": "approx", "unknown": sorted(set(unknown))}


ROUTE = {"name": "worktime", "path": "/api/worktime", "read": read, "selection": True}
