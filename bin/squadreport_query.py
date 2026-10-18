"""squad-report query: compact lines (or JSON) from a scope's data.json only. Pure python, ASCII, no ANSI.

  squad-report query <scope|data.json> <what> [--task X] [--role R] [--top N] [--json] [--refresh] [--squad S]
  what: digest totals tasks roles task role matrix blocks returns iterations
Exit 0 ok, 2 refused (unknown what, no data, bad name), 1 error.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadreport_build as bd  # noqa: E402
import squadreport_digest as dg  # noqa: E402

WHAT = ("digest", "totals", "tasks", "roles", "task", "role", "matrix", "blocks", "returns", "iterations")
BLOCKS_DEFAULT = 3


class Refused(Exception):
    pass


def _ascii(s):
    return str(s).encode("ascii", "replace").decode("ascii").replace("\n", " ").replace("\r", " ")


def _dur(s):
    return dg.fmt_dur(s or 0)


def _usd(x):
    return "$%.2f" % (x or 0)


def _bk(b):
    b = b or {}
    return " ".join("%s=%s" % (k[0], _dur(b.get(k))) for k in ("working", "waiting", "blocking", "idle"))


def locate(name, squad):
    """-> (data.json path, scope home or None, squad dir or None). A path to data.json or its folder also works."""
    p = Path(name)
    if p.is_file():
        return p, None, None
    if p.is_dir() and (p / "data.json").is_file():
        return p / "data.json", None, None
    try:
        sdir = bd.squad_dir(squad)
        kind, home = bd.resolve(sdir, name)
    except bd.Refused as e:
        raise Refused(str(e))
    if kind != "scope":
        raise Refused("%s is a goal: query needs a scope" % name)
    return home / "report" / "data.json", home, sdir


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (ValueError, OSError):
        raise Refused("cannot read %s" % path)


def stale(home, data):
    if home is None or not (home / "messages.jsonl").exists():
        return False
    try:
        return bd.stale_reason(home, data) is not None
    except Exception:  # noqa: BLE001 - staleness is advisory
        return False


def blocks(data, task=None, role=None):
    """Blocking spans [{agent, on, task, s}] longest first, from agents[].segments; each agent's (and task's) sum
    is capped at its blocking bucket, so no span is longer than the bucket it belongs to."""
    cap_a = {r["name"]: (r.get("buckets_s") or {}).get("blocking", 0) for r in data.get("roles", [])}
    cap_t = {t["id"]: (t.get("buckets_s") or {}).get("blocking", 0) for t in data.get("tasks", [])}
    out = []
    for a in data.get("agents", []):
        if role and a["name"] != role:
            continue
        for seg in a.get("segments", []):
            if seg[2] != "b":
                continue
            if task and seg[3] != task:
                continue
            s = seg[1] - seg[0]
            s = min(s, cap_a.get(a["name"], s))
            if seg[3] in cap_t:
                s = min(s, cap_t[seg[3]])
            if s > 0:
                out.append({"agent": a["name"], "on": seg[4] if len(seg) > 4 and seg[4] else "?", "task": seg[3], "s": s})
    out.sort(key=lambda b: (-b["s"], b["agent"], b["on"]))
    return out


def _by_cost(rows):
    return sorted(rows, key=lambda r: (-(r.get("cost_usd") or 0), str(r.get("id") or r.get("name"))))


def _task(data, tid):
    for t in data.get("tasks", []):
        if t["id"] == tid or tid in t.get("aliases", []):
            return t
    raise Refused("unknown task: %s" % tid)


def _top_returns_task(data):
    ts = [t for t in data.get("tasks", []) if t.get("returns")]
    return sorted(ts, key=lambda t: (-t["returns"], -(t.get("cost_usd") or 0), t["id"]))[0] if ts else None


def answer(data, what, a):
    """-> (json-able object, list of text lines)."""
    top = a.top
    if what == "digest":
        rows = data.get("digest", [])[:top]
        return rows, ["%s %s %s -> %s %s" % (d["id"], d["value"], d["unit"], d["target"]["view"], d["target"].get("id") or "-")
                      + " | " + d["text"] for d in rows]
    if what == "totals":
        t = data["totals"]
        lines = ["elapsed %s agent-time %s parallelism %s" % (_dur(t["wall_s"]), _dur(t["agent_s"]), t["parallelism"]),
                 "buckets " + _bk(t["buckets_s"]),
                 "cost %s returns %d passed %d attributed %s%%" % (_usd(t["cost_usd"]), t["returns"], t["tasks_passed"],
                                                                  t["attributed"]["time_pct"]),
                 "po-wait %d items %s" % (t["po_wait"]["count"], _dur(t["po_wait"]["total_s"]))]
        if data["scope"].get("partial"):
            lines.append("partial: " + ",".join(data["scope"].get("partial_reasons", [])))
        return t, lines
    if what == "tasks":
        rows = _by_cost(data.get("tasks", []))[:top]
        return rows, ["%s %s cost %s cycle %s returns %d%s dev %s" % (t["id"], t["status"], _usd(t["cost_usd"]),
                                                                    _dur(t["cycle_s"]), t["returns"],
                                                                    " FLAG" if t.get("flag") else "", t["dev"]) for t in rows]
    if what == "roles":
        rows = _by_cost(data.get("roles", []))[:top]
        return rows, ["%s (%s) cost %s %s respawns %d" % (r["name"], r["role"], _usd(r["cost_usd"]), _bk(r["buckets_s"]),
                                                         r["respawns"]) for r in rows]
    if what == "task":
        if not a.task:
            raise Refused("task needs --task X")
        t = _task(data, a.task)
        bl = blocks(data, task=t["id"])[:top]
        lines = ["%s %s dev %s iteration %s" % (t["id"], t["status"], t["dev"], t["iteration"]),
                 "title %s" % t["title"] if t.get("title") else "title -",
                 "cost %s cycle %s rework %s (%s)" % (_usd(t["cost_usd"]), _dur(t["cycle_s"]), _dur(t["rework_s"]),
                                                      _usd(t["rework_cost_usd"])),
                 "buckets " + _bk(t["buckets_s"]), "returns %d" % t["returns"]]
        lines += ["return %s by %s: %s" % (r["fail_at"], r["fail_by"], r.get("reason") or "-") for r in t["returns_list"][:top]]
        lines += ["review-wait %s %s %s" % (w["handin_at"], w["verdict"], _dur(w["wait_s"])) for w in t["review_waits"][:top]]
        lines += ["block %s waited on %s %s" % (b["agent"], b["on"], _dur(b["s"])) for b in bl]
        return dict(t, blocks=bl), lines
    if what == "role":
        if not a.role:
            raise Refused("role needs --role R")
        rs = [r for r in data.get("roles", []) if r["name"] == a.role or r["role"] == a.role]
        if not rs:
            raise Refused("unknown role: %s" % a.role)
        return rs, ["%s (%s) cost %s sessions %d respawns %d expiries %d (%s)" % (
            r["name"], r["role"], _usd(r["cost_usd"]), r["sessions"], r["respawns"], r["cache_expiries"],
            _usd(r["expiry_cost_usd"])) for r in rs] + ["  buckets " + _bk(r["buckets_s"]) for r in rs]
    if what == "matrix":
        rows = [m for m in data.get("matrix", []) if (not a.task or m["task"] == a.task) and (not a.role or m["agent"] == a.role)]
        rows = sorted(rows, key=lambda m: (-m["time_s"], str(m["task"]), m["agent"]))[:top]
        return rows, ["%s x %s %s cost %s" % (m["task"] or "-", m["agent"], _dur(m["time_s"]), _usd(m["cost_usd"])) for m in rows]
    if what == "blocks":
        rows = blocks(data, a.task, a.role)[:a.top_given or BLOCKS_DEFAULT]
        return rows, ["%s waited on %s %s%s" % (b["agent"], b["on"], _dur(b["s"]), " (task %s)" % b["task"] if b["task"] else "")
                      for b in rows]
    if what == "returns":
        t = _task(data, a.task) if a.task else _top_returns_task(data)
        if t is None:
            return [], []
        rows = t["returns_list"][:top]
        return {"task": t["id"], "returns": rows}, ["%s return %d: %s by %s: %s" % (t["id"], i + 1, r["fail_at"], r["fail_by"],
                                                                                 r.get("reason") or "-")
                                                   for i, r in enumerate(rows)]
    rows = data.get("iterations", [])[:top]
    return rows, ["iteration %d %s agent-time %s cost %s returns %d" % (i["n"], i["window"]["start"], _dur(i["agent_s"]),
                                                                       _usd(i["cost_usd"]), i["returns"]) for i in rows] \
        + (["note: each row covers that iteration's message window only"] if rows else [])


def make_parser():
    p = argparse.ArgumentParser(prog="squad-report query", description="Compact lines from a scope's data.json.")
    p.add_argument("name", help="scope name (or a data.json path)")
    p.add_argument("what")
    p.add_argument("--task")
    p.add_argument("--role")
    p.add_argument("--top", type=int)
    p.add_argument("--json", action="store_true")
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--squad")
    return p


def run(argv):
    try:
        a = make_parser().parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    a.top_given = a.top if a.top and a.top > 0 else None
    a.top = a.top_given or 5
    try:
        if a.what not in WHAT:
            raise Refused("unknown what: %s (one of %s)" % (a.what, " ".join(WHAT)))
        path, home, sdir = locate(a.name, a.squad)
        data = load(path)
        if a.refresh and home is not None and (data is None or stale(home, data)):
            fwd = [a.name] + (["--squad", a.squad] if a.squad else [])
            rc = bd.run(fwd + ["--quiet", "--no-html"])
            if rc != 0:
                return rc
            data = load(path)
        if data is None:
            raise Refused("no data.json for %s: run squad-report %s" % (a.name, a.name))
        if data.get("schema_version") != 1:
            raise Refused("schema_version %s not supported" % data.get("schema_version"))
        is_stale = stale(home, data)
        obj, lines = answer(data, a.what, a)
    except Refused as e:
        print("squad-report query: %s" % e, file=sys.stderr)
        return 2
    except (KeyError, TypeError) as e:
        print("squad-report query: error: data.json lacks field %s" % e, file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps({"stale": is_stale, "data": obj}, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
    else:
        out = (["stale"] if is_stale else []) + lines
        print("\n".join(_ascii(x) for x in out))
    return 0
