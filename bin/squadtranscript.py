"""Claude Code transcript readers shared by squad-usage and squad-report. Pure functions, stdlib only.

Env: CLAUDE_CONFIG_DIR (default ~/.claude).
"""
import glob
import json
import os
from datetime import datetime
from pathlib import Path

CACHE_TTL_S = 3600           # the 1h cache lifetime
EXPIRY_MIN_WRITE = 10_000    # a cache write this big after a gap counts as an expiry
TOKEN_FIELDS = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")
WORKTREES = "--worktrees-"


def config_dir():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def projects_glob(pattern):
    """Transcript paths under projects/, symlinks resolved and deduped: ~/.claude-2/projects links to ~/.claude/projects."""
    return sorted({os.path.realpath(p) for p in glob.glob(str(config_dir() / "projects" / pattern))})


def find_transcript(session):
    hits = projects_glob(f"*/{session}.jsonl")
    return Path(hits[0]) if hits else None


def agent_name(path, limit=50):
    """The agentName of a transcript's `agent-name` record (written at the top), or None."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for _, line in zip(range(limit), f):
            if '"agent-name"' in line:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("type") == "agent-name":
                    return o.get("agentName")
    return None


def agent_sessions(name, roster_path):
    """Transcripts of agent `name`: only the project dirs of its roster session (and the squad's main dir) and of its worktree.
    Another squad's agent of the same bare name lives in another project dir and is never read. Returns (paths, certain)."""
    if not roster_path:
        return [], False
    base = Path(roster_path).parent.name.split(WORKTREES)[0]
    projects = config_dir() / "projects"
    dirs = {base, Path(roster_path).parent.name}
    dirs |= {d.name for d in projects.glob(base + WORKTREES + "*") if d.name.endswith("-" + name)}
    out = []
    for d in sorted(dirs):
        for p in projects_glob(f"{d}/*.jsonl"):
            if agent_name(p) == name:
                out.append(p)
    return out, True


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def is_expiry(a, b):
    return (b["ts"] - a["ts"]).total_seconds() > CACHE_TTL_S and b["write"] >= EXPIRY_MIN_WRITE


def read_lines(path):
    """The JSON objects of one transcript file; a line that is not a JSON object is skipped."""
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if isinstance(o, dict):
            yield o


def _file_records(path, side_file):
    last = None  # the real cost-state record carries no timestamp: it takes that of the record before it
    for o in read_lines(path):
        if o.get("type") == "cost-state" and "timestamp" not in o:
            if last:
                yield {**last, "kind": "other", "side": side_file, "origin": None, "msg_id": None, "model": None,
                       "usage": None, "cmds": [], "cost_state": {k: v for k, v in o.items() if k != "type"},
                       "uuid": None, "effort": None}
            continue
        try:
            dt = parse_ts(o["timestamp"])
            ts = int(dt.timestamp())
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        m = o.get("message")
        m = m if isinstance(m, dict) else {}
        kind = o.get("type")
        kind = kind if kind in ("assistant", "user", "system") else "other"
        cmds = []
        if kind == "assistant" and isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                    c = (b.get("input") or {}).get("command") if isinstance(b.get("input"), dict) else None
                    if isinstance(c, str):
                        cmds.append(c)
        cs = {k: v for k, v in o.items() if k != "type"} if o.get("type") == "cost-state" else None
        last = {"ts": ts, "dt": dt}
        yield {"ts": ts, "kind": kind, "side": side_file or bool(o.get("isSidechain")),
               "origin": o.get("origin") if isinstance(o.get("origin"), dict) else None,
               "msg_id": m.get("id") if kind == "assistant" else None,
               "model": m.get("model"), "usage": m.get("usage") if isinstance(m.get("usage"), dict) else None,
               "cmds": cmds, "cost_state": cs if isinstance(cs, dict) else None,
               # for read_session: exact time, record uuid, effort
               "dt": dt, "uuid": o.get("uuid"), "effort": o.get("effort") or m.get("effort")}


def iter_records(path):
    """Every timestamped record of a session file, then of its subagents/*.jsonl (side=True), as plain dicts.
    Unknown or malformed lines are skipped."""
    yield from _file_records(path, False)
    for sub in sorted(glob.glob(str(Path(path).with_suffix("") / "subagents" / "*.jsonl"))):
        yield from _file_records(sub, True)


def read_session(path):
    """Per-turn rows of a session and of its subagents/*.jsonl (flagged side), plus the compaction count of the session itself.
    A message spans several lines whose usage only grows: keep the max per field."""
    turns = {}
    boundaries = summaries = 0
    for o in read_lines(path):  # compaction markers may carry no timestamp, so they are counted off the raw lines
        if o.get("isCompactSummary"):
            summaries += 1
        elif o.get("type") == "system" and o.get("subtype") == "compact_boundary":
            boundaries += 1
    for r in iter_records(path):
        u = r["usage"]
        if r["kind"] != "assistant" or not u or r["model"] == "<synthetic>":
            continue
        t = turns.setdefault(r["msg_id"] or r["uuid"], {"side": r["side"], **dict.fromkeys(TOKEN_FIELDS, 0)})
        t["side"] = t["side"] and r["side"]
        for f in TOKEN_FIELDS:
            t[f] = max(t[f], u.get(f, 0))
        if "ts" not in t or r["dt"] >= t["ts"]:
            t.update(ts=r["dt"], model=r["model"], effort=r["effort"])
    for t in turns.values():
        t["ctx"] = t["input_tokens"] + t["cache_read_input_tokens"] + t["cache_creation_input_tokens"]
        t["write"], t["out"] = t["cache_creation_input_tokens"], t["output_tokens"]
    rows = sorted(turns.values(), key=lambda t: t["ts"])
    # one compaction may leave both a boundary and a summary line
    return rows, max(boundaries, summaries)
