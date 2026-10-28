"""squad-report collect: timeline, buckets, tokens, cost, config, partial states. Pure Python, read-only, no child process."""
import contextlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadtranscript as st  # noqa: E402


class Unsupported(Exception):
    """Legacy flat squad (no scopes/ layout)."""


class Deadline(Exception):
    """`deadline` (a time.monotonic() value) passed."""


@dataclass
class Msg:
    ts: int
    frm: str
    to: str
    type: str      # first word of the text
    token: str     # first token after it
    text: str      # kept in memory only
    iteration: "int | None" = None


@dataclass
class Escalation:
    id: str
    title: str
    raised_at: int
    answered_at: "int | None"


@dataclass
class Seg:
    start: int
    end: int
    bucket: str            # working|waiting|blocking|idle
    reason: "str | None"   # peer|po|human_input|None
    on: "str | None"       # agent name | "PO" | None
    stalled: bool = False  # additive: working gap longer than stall_s


@dataclass
class Turn:
    ts: int
    tokens: dict           # input, cache_read, cache_write, output
    cost: float
    model: str


@dataclass
class AgentTL:
    name: str
    role: str
    transcript_found: bool
    live: bool
    sessions: int
    segs: list = field(default_factory=list)
    turns: list = field(default_factory=list)
    cache_expiries: int = 0
    expiry_cost: float = 0.0   # additive: cost of the cache writes that followed an expiry
    respawn_gap: int = 0       # additive: seconds between sessions (not agent-time)
    span: tuple = None         # additive: (first, last) record ts


@dataclass
class Collected:
    scope_home: object
    squad: str
    name: str
    size: str
    window: tuple
    agents: dict
    msgs: list
    escalations: list
    roster: list
    cfg: dict
    sources: dict
    partial_reasons: list


DEDUPE_S = 120
KINDS = ("working", "waiting", "blocking", "idle")
TOKEN_KEYS = ("input", "cache_read", "cache_write", "output")
_FIRST = re.compile(r"\s*([A-Z]{2,})\b[ \t]*([^\s]*)")


def _check(deadline):
    if deadline is not None and time.monotonic() > deadline:
        raise Deadline()


def _epoch(s):
    try:
        return int(st.parse_ts(s).timestamp())
    except (TypeError, ValueError, AttributeError):
        return None


def iso(t):
    return None if t is None else datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return list(st.read_lines(p))


def read_messages(path):
    """messages.jsonl as Msg, copies of one message (same frm, type, token within 120 s) counted once, sorted by ts."""
    out, seen = [], {}
    for o in sorted(_jsonl(path), key=lambda o: _epoch(o.get("ts")) or 0):
        ts = _epoch(o.get("ts"))
        text = o.get("text") if isinstance(o.get("text"), str) else ""
        if ts is None:
            continue
        m = _FIRST.match(text)
        typ, tok = (m.group(1), m.group(2).rstrip(":,;.")) if m else ("", "")
        frm, to = str(o.get("from") or ""), str(o.get("to") or "")
        if typ:
            key = (frm, typ, tok)
            if key in seen and ts - seen[key] <= DEDUPE_S:
                continue
            seen[key] = ts
        it = o.get("iteration")
        out.append(Msg(ts, frm, to, typ, tok, text, it if isinstance(it, int) and not isinstance(it, bool) else None))
    return out


def read_escalations(inbox_path):
    """inbox.jsonl: `seen` raises an escalation, `answer` (or `withdraw`) closes it."""
    esc = {}
    for o in _jsonl(inbox_path):
        i, ts = o.get("id"), _epoch(o.get("ts"))
        if not isinstance(i, str) or ts is None:
            continue
        if o.get("ev") == "seen" and i not in esc:
            esc[i] = Escalation(i, str(o.get("title") or ""), ts, None)
        elif o.get("ev") in ("answer", "withdraw") and i in esc and esc[i].answered_at is None:
            esc[i].answered_at = ts
    return sorted(esc.values(), key=lambda e: (e.raised_at, e.id))


def load_config(plugin_root, squad_dir):
    """templates/report/config.json shallow-merged with <squad>/settings/report.json."""
    cfg = json.loads((Path(plugin_root) / "templates" / "report" / "config.json").read_text(encoding="utf-8"))
    over = Path(squad_dir) / "settings" / "report.json"
    if over.exists():
        try:
            o = json.loads(over.read_text(encoding="utf-8"))
        except ValueError:
            o = {}
        if isinstance(o, dict):
            cfg.update(o)
    return cfg


def _roster(path):
    rows = []
    p = Path(path)
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 6 or c[0] in ("Agent", "") or set(c[0]) <= set("-: "):
            continue
        rows.append({"name": c[0], "role": c[1], "scope": c[2], "owns": c[3], "status": c[4], "session": c[5]})
    return rows


def _scope_field(scope_md, key):
    p = Path(scope_md)
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*%s\s*:\s*(\S*)" % key, line, re.I)
            if m:
                return m.group(1)
    return ""


def _goal_link(scope_home):
    """-> (goal, rollup_href): goal from scope.md, href relative to <scope>/report/ only if that goal's report.html exists now."""
    goal = _scope_field(Path(scope_home) / "scope.md", "goal")
    if not goal or "/" in goal or "\\" in goal or ".." in goal or goal.startswith("."):
        return None, None
    squad_dir = next((p.parent for p in Path(scope_home).parents if p.name == "scopes"), None)
    if squad_dir is None:
        return goal, None
    for rel in ("goals", "goals/_done"):
        target = squad_dir / rel / goal / "report" / "report.html"
        if target.is_file():
            return goal, os.path.relpath(target, Path(scope_home) / "report").replace(os.sep, "/")
    return goal, None


def _price(prices, model, unpriced):
    m = re.sub(r"\[.*?\]$", "", model or "")
    if m in prices:
        return prices[m]
    best = max((k for k in prices if k != "default" and m.startswith(k)), key=len, default=None)
    if best:
        return prices[best]
    if model and model != "<synthetic>":
        unpriced.add(model)
    return prices.get("default", {})


def _turn_cost(price, u):
    w = u["cache_write"]
    w5 = min(u.get("w5", 0), w)
    w1 = w - w5
    return (u["input"] * price.get("input", 0) + u["cache_read"] * price.get("cache_read", 0)
            + w5 * price.get("cache_write_5m", price.get("cache_write", 0)) + w1 * price.get("cache_write", 0)
            + u["output"] * price.get("output", 0)) / 1e6


@contextlib.contextmanager
def _config_dir(d):
    old = os.environ.get("CLAUDE_CONFIG_DIR")
    if d:
        os.environ["CLAUDE_CONFIG_DIR"] = str(d)
    try:
        yield
    finally:
        if d:
            if old is None:
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
            else:
                os.environ["CLAUDE_CONFIG_DIR"] = old


def _find_sessions(name, session, extra_dirs):
    """Transcript paths of an agent from its roster session, over the default and any extra config dirs."""
    paths = []
    for d in [None] + list(extra_dirs):
        with _config_dir(d):
            roster_path = st.find_transcript(session) if session else None
            found, _ = st.agent_sessions(name, roster_path)
            paths += [str(p) for p in found]
    return sorted(set(paths))


def _open_intervals(escs, a, b):
    """Parts of [a, b) inside an open escalation, merged."""
    out = []
    for e in escs:
        lo, hi = max(a, e.raised_at), min(b, e.answered_at if e.answered_at is not None else b)
        if lo < hi:
            out.append([lo, hi])
    out.sort()
    merged = []
    for lo, hi in out:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return merged


def _unanswered_ask(name, msgs, at):
    """The latest ASK/BLOCKED `name` sent at or before `at` whose addressee sent nothing since, else None."""
    for m in reversed(msgs):
        if m.ts > at or m.frm != name or m.type not in ("ASK", "BLOCKED"):
            continue
        if not any(x.frm == m.to and m.ts < x.ts <= at for x in msgs):
            return m
    return None


def _classify(name, a, b, msgs, escs, cfg):
    """Segments of the gap (a, b) of one session, classified by the record b that ends it."""
    t0, t1 = a["ts"], b["ts"]
    if t1 <= t0:
        return []
    origin = (b.get("origin") or {}).get("kind")
    if b["kind"] == "user" and origin == "task-notification":
        return [Seg(t0, t1, "waiting", None, None)]
    if b["kind"] != "user" or origin is None:
        if b["kind"] == "user" and any(p in c for c in a["cmds"] for p in cfg["wait_patterns"]):
            return [Seg(t0, t1, "waiting", None, None)]
        return [Seg(t0, t1, "working", None, None, stalled=t1 - t0 > cfg["stall_s"])]
    if origin in ("human", "plugin"):
        opened = _open_intervals(escs, t0, t1)
        segs, cur = [], t0
        for lo, hi in opened:
            if cur < lo:
                segs.append(Seg(cur, lo, "idle", "human_input", None))
            segs.append(Seg(lo, hi, "blocking", "po", "PO"))
            cur = hi
        if cur < t1:
            segs.append(Seg(cur, t1, "idle", "human_input", None))
        return segs
    ask = _unanswered_ask(name, msgs, t0) if origin == "peer" else None
    if ask:
        return [Seg(t0, t1, "blocking", "peer", ask.to)]
    return [Seg(t0, t1, "idle", "peer", None)]


def _read_path(path, cfg, prices, unpriced, deadline):
    """(main records sorted, turns, cost-state totals) of one session file."""
    recs, turns, states = [], {}, {}
    for r in st.iter_records(path):
        _check(deadline)
        if not r["side"]:
            if r["cost_state"] is not None:
                sid = r["cost_state"].get("sessionId")
                try:
                    states[sid] = float(r["cost_state"].get("totalCostUSD"))
                except (TypeError, ValueError):
                    pass
            elif r["kind"] != "other":  # queue-operation, attachment...: the user record that follows ends the gap
                recs.append(r)
        u = r["usage"]
        if r["kind"] != "assistant" or not u or r["model"] == "<synthetic>":
            continue
        t = turns.setdefault(r["msg_id"] or r["uuid"] or id(r), {"model": r["model"], "ts": r["ts"],
                             "input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "w5": 0})
        for k, f in (("input", "input_tokens"), ("cache_read", "cache_read_input_tokens"),
                     ("cache_write", "cache_creation_input_tokens"), ("output", "output_tokens")):
            t[k] = max(t[k], u.get(f) or 0)
        cc = u.get("cache_creation")
        if isinstance(cc, dict):
            t["w5"] = max(t["w5"], cc.get("ephemeral_5m_input_tokens") or 0)
        t["ts"], t["model"] = max(t["ts"], r["ts"]), r["model"] or t["model"]
        t["side"] = r["side"] and t.get("side", True)
    out = []
    for t in sorted(turns.values(), key=lambda t: t["ts"]):
        c = _turn_cost(_price(prices, t["model"], unpriced), t)
        out.append((Turn(t["ts"], {k: t[k] for k in TOKEN_KEYS}, c, t["model"] or ""), t["w5"], t.get("side", False)))
    recs.sort(key=lambda r: r["ts"])
    return recs, out, states


def _expiries(turns):
    """Cache expiries among main-session turns: a gap over the cache TTL then a big cache write. Returns (count, cost)."""
    n, cost, prev = 0, 0.0, None
    for t, _, side in turns:
        if side:
            continue
        cur = {"ts": datetime.fromtimestamp(t.ts, timezone.utc), "write": t.tokens["cache_write"]}
        if prev and st.is_expiry(prev, cur):
            n += 1
            cost += t.cost
        prev = cur
    return n, cost


def collect(scope_home, squad_dir, plugin_root, final=False, deadline=None):
    scope_home, squad_dir = Path(scope_home), Path(squad_dir)
    if scope_home.resolve() == squad_dir.resolve() or (squad_dir / "roster.md").exists():
        raise Unsupported("legacy flat squad")
    cfg = load_config(plugin_root, squad_dir)
    prices = cfg.get("prices") or {}
    msgs = read_messages(scope_home / "messages.jsonl")
    escs = read_escalations(scope_home / "inbox.jsonl")
    roster = _roster(scope_home / "roster.md")
    running = not final and scope_home.parent.name != "_done"
    reasons = ["running"] if running else []
    unpriced, agents = set(), {}
    transcripts = harness = 0
    reported = computed_cov = 0.0
    any_reported = False
    all_cost = 0.0
    extra = cfg.get("claude_config_dirs") or []
    by_name = {}
    for row in roster:  # a name listed twice is one agent: keep the row that finds transcripts, else one with a session
        _check(deadline)
        paths = _find_sessions(row["name"], row["session"], extra)
        old = by_name.get(row["name"])
        if old is None or (not old[1] and paths) or (not old[1] and not old[0]["session"] and row["session"]):
            by_name[row["name"]] = (row, paths)
    roster = [r for r, _ in by_name.values()]
    for row, paths in by_name.values():
        name = row["name"]
        tl = AgentTL(name, row["role"], bool(paths), running and row["status"].startswith("live"), len(paths))
        if not paths:
            reasons.append("no_transcript:" + name)
        transcripts += len(paths)
        sessions = []
        for p in paths:
            recs, turns, states = _read_path(p, cfg, prices, unpriced, deadline)
            if recs:
                sessions.append(recs)
            tl.turns += [t for t, _, _ in turns]
            n, c = _expiries(turns)
            tl.cache_expiries += n
            tl.expiry_cost += c
            harness += any(r["origin"] for r in recs)
            if states:
                any_reported = True
                reported += sum(states.values())
                computed_cov += sum(t.cost for t, _, _ in turns)
        tl.turns.sort(key=lambda t: t.ts)
        sessions.sort(key=lambda recs: recs[0]["ts"])
        for recs in sessions:
            for a, b in zip(recs, recs[1:]):
                tl.segs += _classify(name, a, b, msgs, escs, cfg)
        tl.respawn_gap = sum(max(0, nxt[0]["ts"] - prv[-1]["ts"]) for prv, nxt in zip(sessions, sessions[1:]))
        tl.span = (sessions[0][0]["ts"], max(r[-1]["ts"] for r in sessions)) if sessions else None
        all_cost += sum(t.cost for t in tl.turns)
        agents[name] = tl
    stamps = [m.ts for m in msgs] + [e.raised_at for e in escs] + [e.answered_at for e in escs if e.answered_at]
    stamps += [x for a in agents.values() if a.span for x in a.span]
    window = (min(stamps), max(stamps)) if stamps else (None, None)
    sources = {"agents_total": len(roster), "agents_with_transcript": sum(a.transcript_found for a in agents.values()),
               "transcripts": transcripts, "messages": len(msgs), "escalations": len(escs),
               "unpriced_models": sorted(unpriced), "ticket_dir": None, "harness_origin": bool(harness),
               "_reported": (reported, computed_cov) if any_reported else None}
    return Collected(scope_home, squad_dir.name, scope_home.name, _scope_field(scope_home / "scope.md", "size") or "",
                     window, agents, msgs, escs, roster, {k: cfg[k] for k in ("stall_s", "wait_patterns", "min_segment_s", "prices") if k in cfg},
                     sources, reasons)


def _sum_segs(segs):
    b = dict.fromkeys(KINDS, 0)
    idle = {"peer": 0, "human_input": 0}
    block = {"peer": 0, "po": 0}
    stalled = 0
    for s in segs:
        d = s.end - s.start
        b[s.bucket] += d
        if s.bucket == "idle":
            idle[s.reason] += d
        elif s.bucket == "blocking":
            block[s.reason] += d
        if s.stalled:
            stalled += d
    return b, idle, block, stalled


def _tok(turns):
    t = dict.fromkeys(TOKEN_KEYS, 0)
    for x in turns:
        for k in TOKEN_KEYS:
            t[k] += x.tokens[k]
    return t


def base_data(c):
    t0, t1 = c.window
    wall = (t1 - t0) if t0 is not None else 0
    tot_b, tot_i, tot_k, stalled, gap = dict.fromkeys(KINDS, 0), {"peer": 0, "human_input": 0}, {"peer": 0, "po": 0}, 0, 0
    roles, agents, turns_all = [], [], []
    letter = {"working": "w", "waiting": "a", "blocking": "b", "idle": "i"}
    for a in c.agents.values():
        b, i, k, s = _sum_segs(a.segs)
        for d, e in ((tot_b, b), (tot_i, i), (tot_k, k)):
            for key in d:
                d[key] += e[key]
        stalled += s
        gap += a.respawn_gap
        turns_all += a.turns
        roles.append({"name": a.name, "role": a.role, "sessions": a.sessions, "respawns": max(0, a.sessions - 1),
                      "cache_expiries": a.cache_expiries, "expiry_cost_usd": round(a.expiry_cost, 4),
                      "transcript_found": a.transcript_found, "live": a.live, "buckets_s": b, "idle_s": i,
                      "tokens": _tok(a.turns), "cost_usd": round(sum(t.cost for t in a.turns), 4)})
        agents.append({"name": a.name, "role": a.role, "transcript_found": a.transcript_found, "live": a.live,
                       "segments": [[s.start - t0, s.end - t0, letter[s.bucket], None, s.on] for s in a.segs],
                       "events": []})
    agent_s = sum(tot_b.values())
    cost = sum(t.cost for t in turns_all)
    rep = c.sources.get("_reported")
    rep_usd = round(rep[0], 4) if rep else None
    delta = round((rep[1] - rep[0]) / rep[0] * 100, 1) if rep and rep[0] else None
    sources = {k: v for k, v in c.sources.items() if not k.startswith("_")}
    msgs = c.msgs
    goal, rollup_href = _goal_link(c.scope_home)
    return {"schema_version": 1, "kind": "scope",
            "scope": {"name": c.name, "squad": c.squad, "size": c.size,
                      "status": "running" if "running" in c.partial_reasons else "done",
                      "partial": bool(c.partial_reasons), "partial_reasons": list(c.partial_reasons),
                      "generated_at": None, "window": {"start": iso(t0), "end": iso(t1)},
                      "last_message_at": iso(msgs[-1].ts) if msgs else None, "iterations": [],
                      "goal": goal, "rollup_href": rollup_href},
            "config": c.cfg, "sources": sources,
            "totals": {"wall_s": wall, "agent_s": agent_s, "parallelism": round(agent_s / wall, 2) if wall else 0,
                       "buckets_s": tot_b, "stalled_s": stalled, "respawn_gap_s": gap,
                       "blocking_s": tot_k, "idle_s": tot_i, "tokens": _tok(turns_all),
                       "cost_usd": round(cost, 4), "cost_reported_usd": rep_usd, "cost_delta_pct": delta},
            "roles": roles, "agents": agents}
