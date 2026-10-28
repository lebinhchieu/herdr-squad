"""squad-report build: name resolution, collect -> fill -> digest -> data.json -> optional HTML, status. Pure python."""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadreport as sr  # noqa: E402
import squadreport_digest as dg  # noqa: E402
import squadreport_embed as emb  # noqa: E402
import squadreport_tasks as tasks  # noqa: E402

PLUGIN_ROOT = Path(os.path.dirname(os.path.realpath(__file__))).parent
OK, ERROR, REFUSED, STALE, MISSING, DEADLINE = 0, 1, 2, 3, 4, 5
LOCATIONS = (("scope", "scopes"), ("scope", "scopes/_done"), ("goal", "goals"), ("goal", "goals/_done"))


class Refused(Exception):
    pass


def make_parser(prog="squad-report"):
    p = argparse.ArgumentParser(prog=prog, description="Time and cost report of a scope (data.json + report.html).")
    p.add_argument("name", nargs="?", help="scope or goal name (default $SCOPE_DIR, then $GOAL_DIR)")
    p.add_argument("--squad", help="squad folder, or a squad name next to $SQUAD_DIR")
    p.add_argument("--out", help="output folder (default <home>/report)")
    p.add_argument("--no-html", action="store_true")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--final", action="store_true")
    p.add_argument("--redact", action="store_true")
    p.add_argument("--deadline", type=float, help="stop after N seconds (exit 5)")
    return p


def squad_dir(arg=None):
    env = os.environ.get("SQUAD_DIR")
    if arg:
        if os.sep in arg or "/" in arg or os.path.isdir(arg):
            d = Path(arg)
        elif env:
            d = Path(env).parent / arg
        else:
            raise Refused("--squad %s: no such squad" % arg)
    elif env:
        d = Path(env)
    else:
        raise Refused("no squad: set $SQUAD_DIR or pass --squad")
    if not d.is_dir():
        raise Refused("squad folder not found: %s" % d.name)
    return d


def resolve(sdir, name):
    """-> (kind, home). Refuses a flat squad, an unknown name, a name that is both a scope and a goal."""
    if not (sdir / "scopes").is_dir() or (sdir / "roster.md").exists():
        raise Refused("flat squad (no scopes/ layout) is not supported")
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise Refused("unknown scope or goal: %s" % name)
    found = [(k, sdir / rel / name) for k, rel in LOCATIONS if (sdir / rel / name).is_dir()]
    if not found:
        raise Refused("unknown scope or goal: %s" % name)
    kinds = {k for k, _ in found}
    if len(kinds) > 1:
        raise Refused("%s is both a scope and a goal" % name)
    return found[0]


def _target(args):
    sdir = squad_dir(args.squad)
    name = args.name
    if not name:
        for var, kind in (("SCOPE_DIR", "scope"), ("GOAL_DIR", "goal")):
            if os.environ.get(var):
                return sdir, kind, Path(os.environ[var])
        raise Refused("no scope or goal name given")
    kind, home = resolve(sdir, name)
    return sdir, kind, home


def build(home, sdir, plugin_root=PLUGIN_ROOT, final=False, redact=False, deadline=None, now=None):
    """The data dict of one scope (not written). Raises Unsupported, Deadline, Refused (messages but no transcripts)."""
    c = sr.collect(home, sdir, plugin_root, final=final, deadline=deadline)
    if c.sources["transcripts"] == 0 and c.sources["messages"] > 0:
        raise Refused("no transcripts left for %s" % c.name)
    data = sr.base_data(c)
    tasks.fill(data, c, redact=redact)
    data["digest"] = dg.digest(data)
    data["scope"]["generated_at"] = tasks.iso(int(time.time() if now is None else now))
    return data


def write_data(data, out_dir):
    path = Path(out_dir) / "data.json"
    emb.atomic_write(str(path), emb.dumps(data) + "\n")
    return path


def render_html(data, out_dir):
    """Path of report.html, or None when the renderer (ticket 05) does not exist yet."""
    try:
        import squadreport_html as html
    except ModuleNotFoundError as e:
        if e.name != "squadreport_html":
            raise
        return None
    html.render_scope(data, str(out_dir))
    p = Path(out_dir) / "report.html"
    return p if p.exists() else None


def summary(data):
    t = data["totals"]
    return ["elapsed: %s" % dg.fmt_dur(t["wall_s"]),
            "agent-time: %s" % dg.fmt_dur(t["agent_s"]),
            "est. cost: $%.2f (list price)" % t["cost_usd"],
            "returns: %d" % t["returns"],
            "attributed: %s%%" % t["attributed"]["time_pct"]]


def run(argv):
    args = make_parser().parse_args(argv)
    try:
        sdir, kind, home = _target(args)
        if kind == "goal":
            import squadreport_rollup as ro
            fwd = ["--goal", home.name, "--squad-dir", str(sdir)]
            fwd += ["--out", args.out] if args.out else []
            fwd += [f for f, on in (("--no-html", args.no_html), ("--quiet", args.quiet), ("--final", args.final),
                                    ("--redact", args.redact)) if on]
            fwd += ["--deadline", str(args.deadline)] if args.deadline is not None else []
            return ro.run(fwd)
        deadline = time.monotonic() + args.deadline if args.deadline is not None else None
        data = build(home, sdir, final=args.final, redact=args.redact, deadline=deadline)
        if deadline is not None and time.monotonic() > deadline:
            raise sr.Deadline()
        out = Path(args.out) if args.out else home / "report"
        path = write_data(data, out)
        shown = path
        if not args.no_html:
            shown = render_html(data, out) or path
    except Refused as e:
        print("squad-report: %s" % e, file=sys.stderr)
        return REFUSED
    except sr.Unsupported as e:
        print("squad-report: %s" % e, file=sys.stderr)
        return REFUSED
    except sr.Deadline:
        print("squad-report: deadline exceeded, old report left as it is", file=sys.stderr)
        return DEADLINE
    except Exception as e:  # noqa: BLE001 - any failure is exit 1 with one line
        print("squad-report: error: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return ERROR
    if not args.quiet:
        print("\n".join([str(shown)] + summary(data)))
    return OK


def stale_reason(home, data):
    """Why data.json is older than the sources, else None. Reads messages, inbox and roster only."""
    sc, src = data.get("scope", {}), data.get("sources", {})
    msgs = sr.read_messages(home / "messages.jsonl")
    last = tasks.iso(msgs[-1].ts) if msgs else None
    if len(msgs) != src.get("messages") or last != sc.get("last_message_at"):
        return "messages changed"
    now = [(e.id, tasks.iso(e.raised_at), tasks.iso(e.answered_at) if e.answered_at is not None else None)
           for e in sr.read_escalations(home / "inbox.jsonl")]
    had = [(i["id"], i["raised_at"], i["answered_at"]) for i in data.get("totals", {}).get("po_wait", {}).get("items", [])]
    if now != had:
        return "escalations changed"
    if len(sr._roster(home / "roster.md")) != src.get("agents_total"):
        return "roster changed"
    return None


def status(argv):
    p = make_parser("squad-report status")
    args = p.parse_args(argv)
    try:
        sdir, kind, home = _target(args)
    except Refused as e:
        print("squad-report: %s" % e, file=sys.stderr)
        return REFUSED
    path = (Path(args.out) if args.out else home / "report") / "data.json"
    if not path.exists():
        print("missing")
        return MISSING
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        why = None if kind == "goal" else stale_reason(home, data)
    except (ValueError, OSError, AttributeError):
        print("stale")
        return STALE
    print("stale" if why else "fresh")
    return STALE if why else OK
