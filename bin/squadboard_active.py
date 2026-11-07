"""squad board M7: last active of a task, a scope and a goal (ticket 08).

Last active = newest of three times: a `messages.jsonl` message, the tip commit of the branches, and the file mtime of
the live agents' transcripts (sub-agent files too). A transcript is never opened, only `stat`ed: the mtime stands in for
the last record, so a result from a transcript carries `approx: True`. Never raises, writes nothing.

    last_active(...) -> {ts, source ("messages"|"git"|"transcript"|None), approx, partial: [missing source], quiet_s}

`partial` names a source that could not be read: "messages" (no messages.jsonl), "git" (git did not answer),
"transcript" (a live agent has a session id and no transcript file). The page words it ("partial: transcript missing").
`quiet_s` (seconds, or None) is set only for an in-progress task (a live owner) silent for QUIET_S or more.
The page words the age ("quiet 1 h 30 min"; ticket 10).
"""
import json
import re
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
import squadboard_git  # noqa: E402
import squadboard_time  # noqa: E402
import squadledger  # noqa: E402
import squadreport  # noqa: E402
import squadtask  # noqa: E402
import squadtranscript  # noqa: E402

QUIET_S = 3600  # fixed: no setting, no env (T08 rules)
TASK_RE = re.compile(r"\b(\d{1,3})\b")


def roster_rows(home):
    try:
        return squadreport._roster(Path(home) / "roster.md")
    except (OSError, ValueError):
        return []


def task_of(owns):
    m = TASK_RE.search(owns or "")
    return m.group(1) if m else None


def messages(path):
    """-> [(epoch, task)] or None when the file is missing/unreadable. Bad lines are skipped."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    out = []
    for line in text.splitlines():
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if not isinstance(o, dict):
            continue
        ts = squadboard_time.parse_iso(o.get("ts"))
        if ts is not None:
            out.append((ts, str(o.get("task") or "")))
    return out


def transcript_mtime(session):
    """Newest mtime over the transcript of `session` and its sub-agent files, or None when there is no transcript."""
    if not session or not re.match(r"^[A-Za-z0-9._-]+$", session):
        return None
    try:
        files = squadtranscript.projects_glob("*/%s.jsonl" % session)
        if not files:
            return None
        files += squadtranscript.projects_glob("*/%s/subagents/*.jsonl" % session)
        best = None
        for f in files:
            try:
                m = Path(f).stat().st_mtime
            except OSError:
                continue
            best = m if best is None or m > best else best
        return best
    except OSError:
        return None


def last_active(msg_ts, commit_ts, tr_ts, partial=(), now=None, in_progress=False):
    """The newest of the three. `msg_ts`/`commit_ts`/`tr_ts` are epoch seconds or None."""
    best, src = None, None
    for t, name in ((msg_ts, "messages"), (commit_ts, "git"), (tr_ts, "transcript")):
        if t is not None and (best is None or t > best):
            best, src = t, name
    quiet = None
    if in_progress and best is not None and now is not None and now - best >= QUIET_S:
        quiet = int(now - best)
    return {"ts": best, "source": src, "approx": src == "transcript", "partial": sorted(set(partial)), "quiet_s": quiet}


def _newest(values):
    v = [x for x in values if x is not None]
    return max(v) if v else None


def _live_transcripts(rows):
    """-> (newest mtime, partial flag) over the live rows that have a session."""
    times, missing = [], False
    for r in rows:
        if r.get("status") != "live" or not r.get("session"):
            continue
        t = transcript_mtime(r["session"])
        if t is None:
            missing = True
        times.append(t)
    return _newest(times), missing


def _branch_times(sel, squad_name):
    """-> {scope: {agent: tip ts}} for every branch squad/<squad>/<scope>/<agent>, or None when git did not answer."""
    refs = squadboard_git.branch_refs(sel["repo_root"], "squad/%s/" % squad_name)
    if refs is None:
        return None
    out = {}
    for r in refs:
        parts = r["branch"].split("/")
        if len(parts) >= 4 and r["ts"] is not None:
            out.setdefault(parts[2], {})[parts[3]] = r["ts"]
    return out


def event_times(scope_home):
    """-> {key(task): (newest event epoch, task as written)} of the scope's task events (a missing or bad file gives {})."""
    out = {}
    try:
        for e in squadtask.read_events(squadtask.squad_dir_of(scope_home), squadtask.slug_of(scope_home)):
            t, k = squadboard_time.parse_iso(e.get("ts")), squadledger.key(e.get("task")) if isinstance(e.get("task"), str) else None
            if t is not None and k:
                out[k] = (max(out.get(k, (0,))[0], t), e["task"])
    except OSError:
        pass
    return out


def _scope_entry(scope_home, scope_name, branches, now, with_tasks):
    rows = roster_rows(scope_home)
    msgs = messages(Path(scope_home) / "messages.jsonl")
    partial = []
    if msgs is None:
        partial.append("messages")
    if branches is None:
        partial.append("git")
    tips = (branches or {}).get(scope_name, {})
    tr, tr_missing = _live_transcripts(rows)
    if tr_missing:
        partial.append("transcript")
    scope = last_active(_newest(t for t, _ in msgs or []), _newest(tips.values()), tr, partial, now)
    tasks = {}
    if with_tasks:
        owners = {}
        for r in rows:
            n = task_of(r["owns"]) if "ticket" in r["owns"].lower() else None
            if n:
                owners.setdefault(n, []).append(r)
        evs = event_times(scope_home)
        nums = set(owners) | {t for _, t in msgs or [] if t}
        have = {squadledger.key(n) for n in nums}
        nums |= {raw for k, (_, raw) in evs.items() if k not in have}
        for n in sorted(nums):
            own = owners.get(n, [])
            live = [r for r in own if r["status"] == "live"]
            tmsg = _newest([t for t, k in msgs or [] if k == n] + [evs.get(squadledger.key(n), (None,))[0]])
            tcommit = _newest(tips.get(r["name"]) for r in own)
            ttr, tmiss = _live_transcripts(live)
            tpart = [p for p in partial if p != "transcript"] + (["transcript"] if tmiss else [])
            tasks[n] = last_active(tmsg, tcommit, ttr, tpart, now, in_progress=bool(live))
    return scope, tasks


def read(sel):
    """ROUTE reader for /api/active: scope -> {scope, tasks{NN}}; goal -> {goal, scopes{name}}."""
    try:
        now, squad, home = sel["now"], sel["squad"], Path(sel["home"])
        branches = _branch_times(sel, squad.name)
        if sel["kind"] == "scope":
            scope, tasks = _scope_entry(home, sel["name"], branches, now, True)
            data = {"scope": scope, "tasks": tasks}
        else:
            scopes = {}
            for s in squad.names("scopes")[0] + squad.names("scopes")[1]:
                sh = squad.find("scope", s)
                if sh is not None and squadreport._scope_field(sh / "scope.md", "goal") == sel["name"]:
                    scopes[s] = _scope_entry(sh, s, branches, now, False)[0]
            own, _ = _scope_entry(home, "\0", branches, now, False)  # the goal Manager's own messages and transcript
            ts = _newest([own["ts"]] + [v["ts"] for v in scopes.values()])
            src = own["source"] if ts == own["ts"] else next(v["source"] for v in scopes.values() if v["ts"] == ts)
            part = set(own["partial"]) - {"git"}
            for v in scopes.values():
                part |= set(v["partial"])
            goal = {"ts": ts, "source": src if ts is not None else None, "approx": src == "transcript", "partial": sorted(part),
                    "quiet_s": None}
            data = {"goal": goal, "scopes": scopes}
        unknown = ["git"] if branches is None else []
        return {"data": data, "quality": "unknown" if unknown else "exact", "unknown": unknown}
    except Exception:
        return {"data": None, "quality": "unknown", "unknown": ["active"]}


ROUTE = {"name": "active", "path": "/api/active", "read": read, "selection": True}
