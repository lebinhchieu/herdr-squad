"""squad-report rollup: scope data.json files (or a goal's scopes) -> index.html + data.json (kind rollup).

Reads only the given files (goal form: the goal's scopes' report/data.json). No transcript, no roster, no network.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadreport_embed as emb  # noqa: E402

SCHEMA = 1
OK, ERROR, REFUSED = 0, 1, 2
INCLUDED = ("done", "running", "stale")
TOKEN_KINDS = ("input", "cache_read", "cache_write", "output")
BUCKETS = ("working", "waiting", "blocking", "idle")
TEMPLATES = Path(os.path.dirname(os.path.realpath(__file__))).parent / "templates" / "report"


class Bad(Exception):
    """A file that cannot be a row: status and reason."""

    def __init__(self, status, reason):
        Exception.__init__(self, reason)
        self.status, self.reason = status, reason


def parse_ts(s):
    try:
        return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
    except (TypeError, ValueError):
        return None


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else 0


def read_file(path):
    """-> parsed dict or raises Bad(unreadable | schema_mismatch)."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        raise Bad("unreadable", "This file could not be read (%s)." % type(e).__name__)
    try:
        d = json.loads(text)
    except ValueError:
        raise Bad("unreadable", "This file could not be read (not JSON).")
    if not isinstance(d, dict):
        raise Bad("unreadable", "This file could not be read (not a data.json object).")
    if d.get("kind") != "scope":
        raise Bad("schema_mismatch", "data.json kind is %s; this rollup reads scope files." % json.dumps(d.get("kind")))
    if d.get("schema_version") != SCHEMA:
        raise Bad("schema_mismatch", "data.json schema_version %s; this rollup reads %d." % (
            json.dumps(d.get("schema_version")), SCHEMA))
    return d


def row_from(d):
    """The rollup row of a valid scope data.json. Raises Bad(schema_mismatch) when a needed field is missing."""
    try:
        sc, t = d["scope"], d["totals"]
        name, squad = str(sc["name"]), str(sc.get("squad") or "")
        tokens = {k: int(_num(t["tokens"].get(k))) for k in TOKEN_KINDS}
        buckets = {k: int(_num(t["buckets_s"].get(k))) for k in BUCKETS}
        tasks = d.get("tasks") or []
        reasons = [r.get("reason") for x in tasks for r in (x.get("returns_list") or [])]
        redacted = bool(tasks) and all(x.get("title") is None for x in tasks) or any(
            x.get("reason") is None for x in (r for tk in tasks for r in (tk.get("returns_list") or [])))
        shown = [r for r in reasons if r]
        roles = {}
        for r in d.get("roles") or []:
            g = roles.setdefault(str(r.get("role")), {"role": str(r.get("role")), "agent_s": 0, "cost_usd": 0.0, "tokens": 0})
            g["agent_s"] += int(sum(_num(v) for v in (r.get("buckets_s") or {}).values()))
            g["cost_usd"] = round(g["cost_usd"] + _num(r.get("cost_usd")), 4)
            g["tokens"] += int(sum(_num(v) for v in (r.get("tokens") or {}).values()))
        att = (t.get("attributed") or {}).get("time_pct")
        return {
            "name": name, "squad": squad, "size": sc.get("size"), "status": "running" if sc.get("status") == "running" else "done",
            "report_href": None, "window": sc.get("window") or {"start": None, "end": None},
            "generated_at": sc.get("generated_at"), "last_message_at": sc.get("last_message_at"),
            "totals": {"wall_s": int(_num(t.get("wall_s"))), "agent_s": int(_num(t.get("agent_s"))), "buckets_s": buckets,
                       "tokens": tokens, "cost_usd": round(float(_num(t.get("cost_usd"))), 4), "tasks": len(tasks),
                       "passed": int(_num(t.get("tasks_passed"))), "flagged_tasks": sum(1 for x in tasks if x.get("flag")),
                       "returns": int(_num(t.get("returns"))),
                       "po_wait_s": int(_num((t.get("po_wait") or {}).get("total_s"))),
                       "attributed_time_pct": att if isinstance(att, (int, float)) else None},
            "roles": sorted(roles.values(), key=lambda r: r["role"]),
            "redacted": redacted, "top_reason": shown[0] if shown and not redacted else None,
            "reasons_n": len(shown) if not redacted else 0,
            "_prices": (d.get("config") or {}).get("prices"),
        }
    except (KeyError, TypeError, AttributeError, ValueError) as e:
        raise Bad("schema_mismatch", "data.json is missing a field this rollup reads (%s)." % (e,))


def collect_inputs(args):
    """Expand files and folders (a folder: *.json inside it, */data.json, */report/data.json), sorted, no duplicates."""
    out, seen = [], set()

    def add(p):
        k = os.path.realpath(p)
        if k not in seen:
            seen.add(k)
            out.append(p)
    for a in args:
        if os.path.isdir(a):
            found = sorted(str(p) for pat in ("*.json", "*/data.json", "*/report/data.json") for p in Path(a).glob(pat))
            for p in sorted(found):
                add(p)
        else:
            add(a)
    return out


def href_for(path, out_dir):
    """Relative link from the rollup folder to a report.html beside the data.json, else None."""
    rep = Path(path).resolve().parent / "report.html"
    if not rep.is_file():
        return None
    try:
        rel = os.path.relpath(str(rep), str(Path(out_dir).resolve()))
    except ValueError:
        return None
    rel = quote(rel.replace(os.sep, "/"), safe="/.-_~")
    return rel if rel.startswith(".") else "./" + rel


def source_label(path, out_dir):
    try:
        return os.path.relpath(os.path.abspath(path), str(Path(out_dir).resolve())).replace(os.sep, "/")
    except ValueError:
        return Path(path).name


def entry(path=None, bad=None, squad="", name=None, command=None, row=None):
    return {"path": path, "bad": bad, "squad": squad, "name": name, "command": command, "row": row}


def file_entries(paths):
    out = []
    for p in paths:
        try:
            out.append(entry(path=p, row=row_from(read_file(p))))
        except Bad as b:
            out.append(entry(path=p, bad=b))
    return out


def goal_entries(sdir, goal):
    """The goal's scopes (scope.md `goal: G`, in scopes/ or scopes/_done/) -> one entry each; no data.json = no_data."""
    out = []
    for rel in ("scopes", "scopes/_done"):
        base = Path(sdir) / rel
        if not base.is_dir():
            continue
        for home in sorted(p for p in base.iterdir() if p.is_dir() and p.name != "_done"):
            try:
                text = (home / "scope.md").read_text(encoding="utf-8-sig")
            except OSError:
                continue
            if not re.search(r"^goal:[ \t]*%s[ \t]*$" % re.escape(goal), text, re.M):
                continue
            f = home / "report" / "data.json"
            if f.is_file():
                out += file_entries([str(f)])
            else:
                out.append(entry(squad=Path(sdir).name, name=home.name, command="squad-report %s" % home.name))
    return out


def build_rollup(entries, title, form, out_dir, now, goal_name=None):
    """The single path of both forms: entries -> rollup dict (not written)."""
    rows, kept = [], {}
    for e in entries:
        if e["row"] is not None:
            r = e["row"]
            r["report_href"] = href_for(e["path"], out_dir)
            r["source"] = source_label(e["path"], out_dir)
            key = (r["squad"], r["name"])
            old = kept.get(key)
            if old is None or (r["generated_at"] or "") > (old["generated_at"] or ""):
                if old is not None:
                    old["_skip"] = True
                kept[key] = r
            else:
                r["_skip"] = True
            rows.append(r)
        elif e["bad"] is not None:
            rows.append({"name": os.path.basename(os.path.dirname(os.path.abspath(e["path"]))) or "file", "squad": "",
                         "status": e["bad"].status, "reason": e["bad"].reason, "size": None, "report_href": None,
                         "window": {"start": None, "end": None}, "generated_at": None, "last_message_at": None,
                         "totals": None, "roles": [], "source": source_label(e["path"], out_dir), "redacted": False,
                         "top_reason": None, "reasons_n": 0, "_prices": None})
        else:
            rows.append({"name": e["name"], "squad": e["squad"], "status": "no_data", "reason": "No data.json yet.",
                         "command": e["command"], "size": None, "report_href": None,
                         "window": {"start": None, "end": None}, "generated_at": None, "last_message_at": None,
                         "totals": None, "roles": [], "source": None, "redacted": False, "top_reason": None,
                         "reasons_n": 0, "_prices": None})
    for r in rows:
        if r.pop("_skip", False):
            r["status"] = "skipped"
            r["reason"] = "Older copy of the same squad and scope; the newer file (by generated_at) is used."
            r["totals"], r["roles"] = None, []
            continue
        if r["status"] in ("done", "running") and "reason" not in r:
            gen, last = parse_ts(r["generated_at"]), parse_ts(r["last_message_at"])
            if r["status"] == "done" and gen is not None and last is not None and gen < last:
                r["status"] = "stale"
            if r["status"] == "stale" or r["status"] == "running":
                r["age_s"] = max(0, now - gen) if gen is not None else None
    rows.sort(key=lambda r: (r["status"] not in INCLUDED, r["squad"], r["name"], r.get("source") or ""))
    inc = [r for r in rows if r["status"] in INCLUDED]
    prices = {emb.dumps(r["_prices"]) for r in inc if r["_prices"] is not None}
    for r in rows:
        r.pop("_prices", None)
    totals = sum_totals(inc, len(rows))
    totals["mixed_prices"] = len(prices) > 1
    reasons = sorted({r["status"] for r in rows if r["status"] not in INCLUDED} | ({"running"} if any(
        r["status"] == "running" for r in rows) else set()))
    totals["partial"] = bool(reasons)
    totals["partial_reasons"] = reasons
    roles = {}
    for r in inc:
        for x in r["roles"]:
            g = roles.setdefault(x["role"], {"role": x["role"], "agent_s": 0, "cost_usd": 0.0, "tokens": 0})
            g["agent_s"] += x["agent_s"]
            g["cost_usd"] = round(g["cost_usd"] + x["cost_usd"], 4)
            g["tokens"] += x["tokens"]
    return {"schema_version": SCHEMA, "kind": "rollup", "title": title, "form": form,
            "goal": {"name": goal_name, "scopes": [r["name"] for r in rows]},
            "generated_at": iso(now), "totals": totals, "scopes": rows,
            "roles": sorted(roles.values(), key=lambda r: r["role"]), "digest": digest(inc)}


def sum_totals(inc, listed):
    t = {"included": len(inc), "listed": listed, "wall_s": 0, "span_s": 0, "agent_s": 0, "parallelism": None,
         "buckets_s": {k: 0 for k in BUCKETS}, "tokens": {k: 0 for k in TOKEN_KINDS}, "cost_usd": 0.0, "tasks": 0, "passed": 0,
         "flagged_tasks": 0, "returns": 0, "po_wait_s": 0, "attributed_time_pct": None, "cost_per_passed_task_usd": None,
         "under_60": 0}
    starts = [parse_ts(r["window"].get("start")) for r in inc]
    ends = [parse_ts(r["window"].get("end")) for r in inc]
    starts, ends = [s for s in starts if s is not None], [e for e in ends if e is not None]
    if starts and ends:
        t["span_s"] = max(0, max(ends) - min(starts))
    att_w = att_s = 0
    for r in inc:
        x = r["totals"]
        for k in ("wall_s", "agent_s", "tasks", "passed", "flagged_tasks", "returns", "po_wait_s"):
            t[k] += x[k]
        t["cost_usd"] = round(t["cost_usd"] + x["cost_usd"], 4)
        for k in BUCKETS:
            t["buckets_s"][k] += x["buckets_s"][k]
        for k in TOKEN_KINDS:
            t["tokens"][k] += x["tokens"][k]
        p = x["attributed_time_pct"]
        if p is not None:
            att_w += x["agent_s"]
            att_s += x["agent_s"] * p
            t["under_60"] += 1 if p < 60 else 0
    if att_w:
        t["attributed_time_pct"] = round(att_s / att_w, 1)
    if t["span_s"]:
        t["parallelism"] = round(t["agent_s"] / t["span_s"], 2)
    if t["passed"]:
        t["cost_per_passed_task_usd"] = round(t["cost_usd"] / t["passed"], 4)
    return t


def _item(kind, weight, text, value, unit, row):
    return {"id": kind, "kind": kind, "weight": round(weight, 4), "text": text, "value": value, "unit": unit,
            "target": {"view": "scopes", "id": "%s/%s" % (row["squad"], row["name"])}}


def label(r):
    return "%s · %s" % (r["name"], r["squad"]) if r["squad"] else r["name"]


def digest(inc):
    """Scope-level signals; shown from 2 included scopes up. Text is built from numbers (and a return reason from the file)."""
    if len(inc) < 2:
        return []
    out = []
    cost = sum(r["totals"]["cost_usd"] for r in inc)
    if cost > 0:
        b = max(inc, key=lambda r: (r["totals"]["cost_usd"], r["name"]))
        w = b["totals"]["cost_usd"] / cost
        out.append(_item("top_cost_scope", w, "%s took %d%% of cost ($%.2f)" % (label(b), round(w * 100), b["totals"]["cost_usd"]),
                         round(w * 100), "pct", b))
    b = max(inc, key=lambda r: (r["totals"]["returns"], r["name"]))
    ret = sum(r["totals"]["returns"] for r in inc)
    if b["totals"]["returns"] > 0:
        why = "reasons not shared" if b["redacted"] else ('"%s"%s' % (b["top_reason"], " +%d more" % (b["reasons_n"] - 1) if b["reasons_n"] > 1 else "")
                                                         if b["top_reason"] else "")
        out.append(_item("most_returns_scope", b["totals"]["returns"] / ret, "%s had %d returns%s" % (
            label(b), b["totals"]["returns"], (": " + why) if why else ""), b["totals"]["returns"], "count", b))
    po = [(r["totals"]["po_wait_s"] / r["totals"]["wall_s"], r) for r in inc if r["totals"]["wall_s"] > 0 and r["totals"]["po_wait_s"] > 0]
    if po:
        w, b = max(po, key=lambda x: (x[0], x[1]["name"]))
        out.append(_item("top_po_wait_scope", w, "%s waited on the PO for %d%% of its elapsed time" % (label(b), round(w * 100)),
                         round(w * 100), "pct", b))
    att = [(r["totals"]["attributed_time_pct"], r) for r in inc if r["totals"]["attributed_time_pct"] is not None]
    if att:
        p, b = min(att, key=lambda x: (x[0], x[1]["name"]))
        out.append(_item("weakest_attribution_scope", 1 - p / 100.0, "%s attributes only %s%% of its agent-time to tasks" % (label(b), p),
                         p, "pct", b))
    return out


def render(data, out_dir):
    tpl, css, js = (open(str(TEMPLATES / n), encoding="utf-8", newline="").read() for n in ("rollup.html", "rollup.css", "rollup.js"))
    emb.atomic_write(str(Path(out_dir) / "index.html"), emb.assemble(tpl, css, js, data))


def make_parser():
    p = argparse.ArgumentParser(prog="squad-report rollup", description="Rollup of scope data.json files.")
    p.add_argument("files", nargs="*", help="data.json files or folders of them")
    p.add_argument("--out", help="output folder (default ./squad-rollup/; goal form: <goal>/report)")
    p.add_argument("--goal", help=argparse.SUPPRESS)
    p.add_argument("--squad-dir", help=argparse.SUPPRESS)
    for f in ("--no-html", "--quiet", "--final", "--redact"):
        p.add_argument(f, action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--deadline", type=float, help=argparse.SUPPRESS)
    return p


def run(argv, now=None):
    args = make_parser().parse_args(argv)
    now = int(time.time() if now is None else now)
    if args.goal:
        sdir = Path(args.squad_dir)
        home = next((sdir / rel / args.goal for rel in ("goals", "goals/_done") if (sdir / rel / args.goal).is_dir()), None)
        out = Path(args.out) if args.out else (home or sdir) / "report"
        entries, title, form = goal_entries(sdir, args.goal), args.goal, "goal"
    else:
        if not args.files:
            print("squad-report rollup: pass data.json files or a folder", file=sys.stderr)
            return REFUSED
        out = Path(args.out) if args.out else Path("squad-rollup")
        paths = collect_inputs(args.files)
        for a in args.files:
            if not os.path.exists(a):
                print("squad-report rollup: not found: %s" % os.path.basename(a), file=sys.stderr)
        entries, title, form = file_entries(paths), "Teammates' scopes", "files"
    try:
        data = build_rollup(entries, title, form, out, now, goal_name=args.goal)
        emb.atomic_write(str(out / "data.json"), emb.dumps(data) + "\n")
        if not args.no_html:
            render(data, out)
    except Exception as e:  # noqa: BLE001
        print("squad-report: error: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return ERROR
    t = data["totals"]
    if not args.quiet:
        print("\n".join([str(out / ("data.json" if args.no_html else "index.html")),
                         "scopes: %d of %d included%s" % (t["included"], t["listed"], " (partial)" if t["partial"] else ""),
                         "est. cost: $%.2f (sum of each file's own estimate)" % t["cost_usd"]]))
        for r in data["scopes"]:
            if r["status"] not in INCLUDED:
                print("skipped: %s: %s" % (r["source"] or label(r), r["reason"]), file=sys.stderr)
    return OK if t["included"] else REFUSED
