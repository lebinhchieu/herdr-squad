"""squad board: plan reader (ticket 04). `GET /api/plan?squad=K&scope=S|goal=G` -> the plan of one home.

read(sel) -> {data: {kind, name, aim, rows}, quality, unknown}. Never raises, writes nothing. The model is `squadplan`
(pure); this route adds what costs more: the Tasks panel's stage word (`squadboard_tasks.read_scope`, so the chip is the same)
and `spent_min` of each task from the work-time reader (approx; no data gives None, never a warning).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadledger  # noqa: E402
import squadplan  # noqa: E402


def _spent(sel):
    """-> {task key: minutes} of `working` time named for a task, or None when the work-time reader has no answer."""
    import squadboard_worktime
    r = squadboard_worktime.read(dict(sel, params={}))
    data = r.get("data")
    if not data:
        return None
    out = {}
    for a in data.get("agents") or []:
        for p in a.get("pieces") or []:
            if p.get("bucket") == "working" and p.get("task") and not p.get("collapsible"):
                k = squadledger.key(str(p["task"]))
                out[k] = out.get(k, 0) + (p["end"] - p["start"]) / 60.0
    return {k: int(round(v)) for k, v in out.items()}


def read(sel):
    try:
        return _read(sel)
    except Exception:  # a reader never raises
        return {"data": None, "quality": "unknown", "unknown": ["plan"]}


def _read(sel):
    squad, home, kind = sel.get("squad"), sel.get("home"), sel.get("kind")
    if squad is None or home is None or kind not in ("scope", "goal"):
        return {"data": None, "quality": "unknown", "unknown": ["plan"]}
    unknown = []
    if kind == "goal":
        text = squadplan._read(os.path.join(str(home), "goal.md"))
        if text is None:
            unknown.append("goal.md")
        data = squadplan.build_goal(text)
        data["name"] = sel.get("name")
        return {"data": data, "quality": "exact" if not unknown else "approx", "unknown": unknown}
    data = squadplan.build_scope(home, sel.get("repo_root"), sel.get("name"))
    try:
        import squadboard_tasks
        rows, unk, _ = squadboard_tasks.read_scope(squad.name, sel["name"], home, sel.get("repo_root"), None,
                                                   sel.get("now") or time.time())
        stage = {squadledger.key(r["id"]): r["stage"] for r in rows}
        for r in data["rows"]:
            if squadledger.key(r["id"]) in stage:
                r["state"] = stage[squadledger.key(r["id"])]
                r["passed"] = r["state"] in ("passed", "merged")
        unknown += [u for u in unk if u not in unknown]
    except Exception:
        unknown.append("stage")
    try:
        spent = _spent(sel)
    except Exception:
        spent = None
    if spent is None:
        unknown.append("worktime")
    for r in data["rows"]:
        r["spent_min"] = None if spent is None else spent.get(squadledger.key(r["id"]))
    return {"data": data, "quality": "approx", "unknown": unknown}


ROUTE = {"name": "plan", "path": "/api/plan", "read": read, "selection": True}
