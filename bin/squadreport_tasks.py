"""squad-report tasks: aliases, attribution, returns, rework, review wait, PO wait, iterations.

fill(data, c) completes data.json from a Collected. Pure python, read-only.
Free text kept: ticket/escalation titles (cut 120) and FAIL reasons (cut 200); nothing else from messages.
"""
import re
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

TOKEN_FIELDS = ("input", "cache_read", "cache_write", "output")
BUCKETS = ("working", "waiting", "blocking", "idle")
BCODE = {"working": "w", "waiting": "a", "blocking": "b", "idle": "i"}
EVENT_TYPES = ("BLOCKED", "ASK", "ANSWER", "FAIL", "HANDIN", "PASS", "DECISION")
DEDUPE_S = 120
TITLE_CUT = 120
REASON_CUT = 200
FLAG_RETURNS = 3
MIN_SEGMENT_DEFAULT = 30

_MSG_RE = re.compile(r"^\s*\S+\s+([^\s()]+)(?:\s+\(([^)\s]+)\))?")


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(row, *keys):
    for k in keys:
        if isinstance(row, dict):
            for rk in row:
                if str(rk).lower() == k:
                    return row[rk]
        elif hasattr(row, k):
            return getattr(row, k)
    return None


def _clean_tok(t):
    return (t or "").strip().strip("`*").rstrip(":,;.?!")


def _mtype(m):
    return (m.type or "").upper().rstrip(":")


def _recipients(m):
    return [x for x in re.split(r"[,\s]+", m.to or "") if x]


# ---- tickets -------------------------------------------------------------

def _find_tickets(c, raw_tokens):
    """-> ({NN: title}, relative feature dir or None)."""
    root = None
    p = Path(str(c.scope_home)).resolve()
    for _ in range(10):
        if (p / ".scratch").is_dir():
            root = p
            break
        if p.parent == p:
            break
        p = p.parent
    if root is None:
        return {}, None
    best = None
    for fdir in sorted((root / ".scratch").glob("*")):
        files = sorted((fdir / "issues").glob("*.md")) if (fdir / "issues").is_dir() else []
        files = [f for f in files if re.match(r"^\d+-", f.name)]
        if not files:
            continue
        stems = {f.stem for f in files}
        nns = {f.name.split("-", 1)[0] for f in files}
        slug = sum(1 for t in raw_tokens if t in stems)
        cover = sum(1 for t in raw_tokens if t in nns)
        score = (slug, 1 if fdir.name == c.name else 0, cover)
        if best is None or score > best[0]:
            best = (score, fdir, files)
    if best is None:
        return {}, None
    _, fdir, files = best
    out = {}
    for f in files:
        nn = f.name.split("-", 1)[0]
        title = f.stem.split("-", 1)[1] if "-" in f.stem else f.stem
        try:
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("# "):
                    title = re.sub(r"^\d+\s*[:.-]\s*", "", line[2:].strip())
                    break
        except OSError:
            pass
        out[nn] = title
    return out, str(fdir.relative_to(root)).replace("\\", "/")


# ---- message parsing -----------------------------------------------------

def _parse_subject(m):
    mt = _MSG_RE.match(m.text or "")
    if mt:
        return _clean_tok(mt.group(1)), _clean_tok(mt.group(2))
    return _clean_tok(m.token), ""


class _Resolver:
    def __init__(self, c, msgs):
        self.names = set(c.agents) | {
            str(_get(r, "agent", "name") or "") for r in (c.roster or [])}
        self.raw = {}      # msg id -> (token, alias)
        order = []
        links = []
        for m in msgs:
            tok, alias = _parse_subject(m)
            tok = tok if self.is_task(tok) else ""
            alias = alias if self.is_task(alias) else ""
            self.raw[id(m)] = (tok, alias)
            for t in (tok, alias):
                if t and t not in order:
                    order.append(t)
            if tok and alias:
                links.append((tok, alias))
        self.tickets, self.ticket_dir = _find_tickets(c, order)
        self.order = order
        self.parent = {}
        for t in order:
            self.parent[t] = t
        for t in order:
            nn = self.ticket_nn(t)
            if nn:
                self.parent.setdefault(nn, nn)
                self._union(t, nn)
        for a, b in links:
            self._union(a, b)
        comps = {}
        for t in list(self.parent):
            comps.setdefault(self._find(t), []).append(t)
        self.canon = {}
        self.aliases = {}
        for members in comps.values():
            tk = [x for x in members if x in self.tickets]
            if tk:
                cid = tk[0]
            else:
                seen = [x for x in order if x in members]
                dig = [x for x in seen if x[:1].isdigit()]
                cid = (dig or seen)[0]
            for x in members:
                self.canon[x] = cid
            self.aliases[cid] = sorted(x for x in members if x != cid and (x in order))

    def is_task(self, t):
        if not t or not re.match(r"^[A-Za-z0-9][\w.-]*$", t):
            return False
        if t.upper() == "STATUS" or t.lower().startswith("squad-") or t in self.names:
            return False
        return any(ch.isdigit() for ch in t)

    def ticket_nn(self, t):
        mt = re.match(r"^(\d+)(?:-.*)?$", t)
        if mt and mt.group(1) in getattr(self, "tickets", {}):
            return mt.group(1)
        return None

    def _find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            self.parent[rb] = ra

    def task_of(self, m):
        tok = self.raw[id(m)][0]
        return self.canon.get(tok) if tok else None

    def resolve_text(self, s):
        """Canonical id for a roster 'Owns' text naming a ticket, else None."""
        mt = re.search(r"ticket\s*#?\s*([A-Za-z0-9][\w.-]*)", s or "", re.I)
        if not mt:
            return None
        tok = _clean_tok(mt.group(1))
        if tok in self.canon:
            return self.canon[tok]
        if tok in self.tickets:
            return self.canon.get(tok, tok)
        nn = self.ticket_nn(tok)
        if nn:
            return nn
        return tok if any(ch.isdigit() for ch in tok) else None


def _dedupe(msgs, task_of):
    last = {}
    out = []
    for m in sorted(msgs, key=lambda x: x.ts):
        key = (m.frm, _mtype(m), task_of(m))
        if key in last and m.ts - last[key] <= DEDUPE_S:
            continue
        last[key] = m.ts
        out.append(m)
    return out


# ---- attribution ---------------------------------------------------------

class _Ctx:
    def __init__(self, c, res):
        self.ev = {}       # agent -> ([ts], [task])
        by = {}
        for m in c.msgs:
            t = res.task_of(m)
            if not t:
                continue
            for who in [m.frm] + _recipients(m):
                by.setdefault(who, []).append((m.ts, t))
        for who, lst in by.items():
            lst.sort(key=lambda x: x[0])
            self.ev[who] = ([x[0] for x in lst], [x[1] for x in lst])
        self.owns = {}
        for r in c.roster or []:
            nm = _get(r, "agent", "name")
            t = res.resolve_text(str(_get(r, "owns") or ""))
            if nm and t:
                self.owns[str(nm)] = t

    def at(self, agent, t):
        ts, tasks = self.ev.get(agent, ([], []))
        i = bisect_right(ts, t)
        if i:
            return tasks[i - 1], "message"
        if agent in self.owns:
            return self.owns[agent], "branch"
        return None, "overhead"

    def breaks(self, agent, s, e):
        ts = self.ev.get(agent, ([], []))[0]
        return sorted({x for x in ts if s < x < e})


def _z():
    return {"b": {k: 0 for k in BUCKETS}, "tok": {k: 0 for k in TOKEN_FIELDS}, "cost": 0.0}


def _wall(c):
    return max(0, c.window[1] - c.window[0])


def fill(data, c, redact=False):
    cfg = c.cfg or {}
    min_seg = int(cfg.get("min_segment_s", data.get("config", {}).get("min_segment_s", MIN_SEGMENT_DEFAULT)))
    w0, w1 = c.window
    if w0 is None:
        w0 = w1 = 0
    msgs_all = list(c.msgs)
    res = _Resolver(c, msgs_all)
    ctx = _Ctx(c, res)
    task_of = res.task_of
    dmsgs = _dedupe([m for m in msgs_all if task_of(m) or _mtype(m) in EVENT_TYPES], task_of)

    # -- per-second pieces and turns
    cells = {}
    layers = {"message": 0, "branch": 0, "overhead": 0}
    nonidle = attributed = 0
    pieces = {}   # agent -> [(s,e,bucket,on,task)]
    for name, tl in c.agents.items():
        out = pieces[name] = []
        for sg in tl.segs:
            if sg.end <= sg.start:
                continue
            on = sg.on if sg.bucket == "blocking" else None
            if sg.bucket == "idle":
                cell = cells.setdefault((None, name), _z())
                cell["b"]["idle"] += sg.end - sg.start
                out.append((sg.start, sg.end, "idle", None, None))
                continue
            pts = [sg.start] + ctx.breaks(name, sg.start, sg.end) + [sg.end]
            for a, b in zip(pts, pts[1:]):
                task, layer = ctx.at(name, a)
                cell = cells.setdefault((task, name), _z())
                cell["b"][sg.bucket] += b - a
                layers[layer] += b - a
                nonidle += b - a
                if task:
                    attributed += b - a
                out.append((a, b, sg.bucket, on, task))
    turn_rows = []   # (task, ts, cost)
    total_cost = 0.0
    attr_cost = 0.0
    for name, tl in c.agents.items():
        for t in tl.turns:
            task, _ = ctx.at(name, t.ts)
            cell = cells.setdefault((task, name), _z())
            cell["cost"] += t.cost
            for k in TOKEN_FIELDS:
                cell["tok"][k] += int((t.tokens or {}).get(k, 0) or 0)
            total_cost += t.cost
            if task:
                attr_cost += t.cost
            turn_rows.append((task, t.ts, t.cost))

    # -- messages per task
    by_task = {}
    for m in dmsgs:
        t = task_of(m)
        if t:
            by_task.setdefault(t, []).append(m)
    mention_ts = {}
    for m in msgs_all:
        t = task_of(m)
        if t:
            mention_ts.setdefault(t, []).append(m.ts)
    iters = {}   # task -> iteration of its earliest message
    for m in sorted(msgs_all, key=lambda x: x.ts):
        t = task_of(m)
        if t and t not in iters:
            it = getattr(m, "iteration", None)
            iters[t] = int(it) if it is not None and str(it).lstrip("-").isdigit() else None

    task_ids = set(mention_ts) | {t for (t, _a) in cells if t}
    tasks = []
    returns_total = 0
    passed = 0
    for tid in sorted(task_ids):
        ms = sorted(by_task.get(tid, []), key=lambda x: x.ts)
        handins = [m for m in ms if _mtype(m) == "HANDIN"]
        fails = [m for m in ms if _mtype(m) == "FAIL"]
        verdicts = [m for m in ms if _mtype(m) in ("PASS", "FAIL")]
        passes = [m for m in ms if _mtype(m) == "PASS"]
        rl = []
        intervals = []
        for f in fails:
            nxt = next((h.ts for h in handins if h.ts > f.ts), None)
            reason = re.sub(r"^\s*\S+\s+\S+\s*(\([^)]*\))?[:\s-]*", "", f.text or "", count=1)
            reason = re.sub(r"\s+", " ", reason).strip()[:REASON_CUT]
            rl.append({"fail_at": iso(f.ts), "fail_by": f.frm,
                       "handin_at": iso(nxt) if nxt is not None else None,
                       "reason": None if redact else reason})
            if nxt is not None:
                intervals.append((f.ts, nxt))
        intervals.sort()
        merged = []
        for a, b in intervals:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        rework_s = sum(b - a for a, b in merged)
        rework_cost = sum(cost for (t, ts, cost) in turn_rows if t == tid
                          and any(a <= ts < b for a, b in merged))
        waits = []
        for i, h in enumerate(handins):
            end = handins[i + 1].ts if i + 1 < len(handins) else None
            vs = [v for v in verdicts if v.ts >= h.ts and (end is None or v.ts < end)]
            if vs:
                v = vs[-1]
                waits.append({"handin_at": iso(h.ts), "verdict_at": iso(v.ts),
                              "verdict": _mtype(v), "wait_s": v.ts - h.ts})
            else:
                waits.append({"handin_at": iso(h.ts), "verdict_at": None, "verdict": "none",
                              "wait_s": max(0, w1 - h.ts)})
        cs = [cell for (t, _a), cell in cells.items() if t == tid]
        bs = {k: sum(x["b"][k] for x in cs) for k in BUCKETS}
        tok = {k: sum(x["tok"][k] for x in cs) for k in TOKEN_FIELDS}
        cost = sum(x["cost"] for x in cs)
        times = list(mention_ts.get(tid, []))
        first = min(times) if times else None
        last = max(times) if times else None
        dev = handins[0].frm if handins else None
        if dev is None:
            dev = next((a for a, t in ctx.owns.items() if t == tid), None)
        cyc = (max(p.ts for p in passes) - first) if passes and first is not None else None
        returns_total += len(fails)
        passed += 1 if passes else 0
        tasks.append({
            "id": tid, "aliases": res.aliases.get(tid, []),
            "title": None if redact or tid not in res.tickets else res.tickets[tid][:TITLE_CUT],
            "dev": dev, "status": "passed" if passes else "open",
            "iteration": iters.get(tid),
            "window": {"start": iso(first) if first is not None else None,
                       "end": iso(last) if last is not None else None},
            "cycle_s": cyc, "buckets_s": bs, "tokens": tok, "cost_usd": round(cost, 4),
            "returns": len(fails), "flag": len(fails) >= FLAG_RETURNS,
            "returns_list": rl, "rework_s": rework_s, "rework_cost_usd": round(rework_cost, 4),
            "review_waits": waits})
    data["tasks"] = tasks

    # -- matrix
    matrix = []
    for (t, a), cell in sorted(cells.items(), key=lambda kv: (kv[0][0] or "", kv[0][1])):
        tm = sum(cell["b"].values())
        if not tm and not cell["cost"] and not any(cell["tok"].values()):
            continue
        matrix.append({"task": t, "agent": a, "time_s": tm, "buckets_s": dict(cell["b"]),
                       "tokens": dict(cell["tok"]), "cost_usd": round(cell["cost"], 4)})
    data["matrix"] = matrix

    # -- iterations
    span = {}
    for m in msgs_all:
        it = getattr(m, "iteration", None)
        if it is not None and str(it).lstrip("-").isdigit():
            lo, hi = span.get(int(it), (m.ts, m.ts))
            span[int(it)] = (min(lo, m.ts), max(hi, m.ts))
    its = sorted(span)
    it_rows = []
    fail_ts = [m.ts for m in dmsgs if _mtype(m) == "FAIL" and task_of(m)]
    for n in its:
        s, e = span[n]
        agent_s = 0
        for lst in pieces.values():
            for (a, b, _bk, _on, _t) in lst:
                agent_s += max(0, min(b, e) - max(a, s))
        cost = sum(cs_ for (_t, ts, cs_) in turn_rows if s <= ts <= e)
        it_rows.append({"n": n, "window": {"start": iso(s), "end": iso(e)}, "agent_s": agent_s,
                        "cost_usd": round(cost, 4), "returns": sum(1 for x in fail_ts if s <= x <= e)})
    data["iterations"] = it_rows
    sc = data.setdefault("scope", {})
    sc["iterations"] = its

    # -- PO wait
    items = []
    spans = []
    for esc in c.escalations or []:
        end = esc.answered_at if esc.answered_at is not None else w1
        end = max(end, esc.raised_at)
        spans.append((esc.raised_at, end))
        items.append({"id": esc.id, "title": None if redact else (esc.title or "")[:TITLE_CUT],
                      "raised_at": iso(esc.raised_at),
                      "answered_at": iso(esc.answered_at) if esc.answered_at is not None else None,
                      "wait_s": end - esc.raised_at})
    spans.sort()
    total = 0
    cur = None
    for a, b in spans:
        if cur and a <= cur[1]:
            cur[1] = max(cur[1], b)
        else:
            if cur:
                total += cur[1] - cur[0]
            cur = [a, b]
    if cur:
        total += cur[1] - cur[0]
    wall = _wall(c)
    po_wait = {"count": len(items), "total_s": total,
               "longest_s": max((i["wait_s"] for i in items), default=0),
               "pct_of_elapsed": round(100.0 * total / wall, 1) if wall else 0.0,
               "items": items}

    # -- totals
    tot = data.setdefault("totals", {})
    tot["attributed"] = {
        "time_pct": round(100.0 * attributed / nonidle, 1) if nonidle else 0.0,
        "cost_pct": round(100.0 * attr_cost / total_cost, 1) if total_cost else 0.0,
        "layers": layers}
    tot["returns"] = returns_total
    tot["tasks_passed"] = passed
    tot["cost_per_passed_task_usd"] = round(total_cost / passed, 4) if passed else None
    tot["po_wait"] = po_wait

    # -- agents: segments + events
    by_name = {a.get("name"): a for a in data.get("agents", [])}
    agents_out = list(data.get("agents", []))
    for name, tl in c.agents.items():
        row = by_name.get(name)
        if row is None:
            row = {"name": name, "role": tl.role, "transcript_found": tl.transcript_found, "live": tl.live}
            agents_out.append(row)
        row["segments"] = _segments(pieces.get(name, []), w0, min_seg)
        evs = []
        for m in dmsgs:
            if m.frm == name and _mtype(m) in EVENT_TYPES:
                evs.append([m.ts - w0, _mtype(m), task_of(m)])
        row["events"] = evs
    data["agents"] = agents_out

    # -- legacy transcripts
    if (c.sources or {}).get("harness_origin") is False:
        reasons = sc.setdefault("partial_reasons", [])
        if "no_origin" not in reasons:
            reasons.append("no_origin")
        sc["partial"] = True


def _segments(pcs, w0, min_seg):
    segs = []
    for (a, b, bk, on, task) in pcs:
        seg = [a - w0, b - w0, BCODE[bk], task, on]
        if segs and segs[-1][1] == seg[0] and segs[-1][2:] == seg[2:]:
            segs[-1][1] = seg[1]
        else:
            segs.append(seg)
    changed = True
    while changed and len(segs) > 1:
        changed = False
        for i, s in enumerate(segs):
            if s[1] - s[0] >= min_seg:
                continue
            # absorb only into a contiguous neighbour (never across a hole such as a respawn gap) and never
            # into a blocking segment, so display blocking never exceeds the real blocking seconds
            if i > 0 and segs[i - 1][1] == s[0] and (segs[i - 1][2] != "b" or s[2] == "b"):
                segs[i - 1][1] = s[1]
            elif i + 1 < len(segs) and segs[i + 1][0] == s[1] and (segs[i + 1][2] != "b" or s[2] == "b"):
                segs[i + 1][0] = s[0]
            else:
                continue
            del segs[i]
            changed = True
            break
        out = []
        for s in segs:
            if out and out[-1][1] == s[0] and out[-1][2:] == s[2:]:
                out[-1][1] = s[1]
            else:
                out.append(s)
        segs = out
    return segs
