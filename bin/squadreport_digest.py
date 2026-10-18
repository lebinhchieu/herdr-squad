"""squad-report digest: up to 8 ranked signals from a filled data dict. Pure, deterministic, numbers only."""

# Message types the report knows; a test pins this list against the regex in bin/squad-log-message.
MESSAGE_TYPES = ("ASK", "BLOCKED", "HANDIN", "PASS", "FAIL", "ANSWER", "DECISION", "STATUS")
KINDS = ("top_cost_task", "top_cost_role", "scope_overhead", "idle_share", "longest_block", "po_wait", "review_wait",
         "most_returns", "rework_cost", "respawns", "parallelism", "attribution_low")
MAX_ITEMS = 8
RETURNS_FLAG = 3
ATTRIBUTED_MIN_PCT = 60


def fmt_dur(s):
    s = int(s)
    if s >= 3600:
        return "%dh%02dm" % (s // 3600, s % 3600 // 60)
    if s >= 60:
        return "%dm%02ds" % (s // 60, s % 60)
    return "%ds" % s


def _pct(x):
    return round(100.0 * x, 1)


def _item(kind, weight, text, value, unit, view, tid):
    return {"id": kind, "kind": kind, "weight": round(min(1.0, max(0.0, weight)), 4), "text": text,
            "value": value, "unit": unit, "target": {"view": view, "id": tid}}


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) // 2


def digest(data):
    t = data.get("totals", {})
    cost = t.get("cost_usd") or 0
    agent_s = t.get("agent_s") or 0
    wall = t.get("wall_s") or 0
    tasks = data.get("tasks", [])
    roles = data.get("roles", [])
    out = []

    if cost > 0:
        best = max(tasks, key=lambda x: (x["cost_usd"], [-ord(c) for c in x["id"]]), default=None)
        if best and best["cost_usd"] > 0:
            w = best["cost_usd"] / cost
            out.append(_item("top_cost_task", w, "Task %s took %s%% of cost ($%.2f)" % (best["id"], _pct(w), best["cost_usd"]),
                             _pct(w), "pct", "tasks", best["id"]))
        by_role = {}
        for r in roles:
            by_role[r["role"]] = by_role.get(r["role"], 0) + r["cost_usd"]
        if by_role:
            name = sorted(by_role, key=lambda k: (-by_role[k], k))[0]
            if by_role[name] > 0:
                w = by_role[name] / cost
                out.append(_item("top_cost_role", w, "Role %s took %s%% of cost ($%.2f)" % (name, _pct(w), by_role[name]),
                                 _pct(w), "pct", "roles", name))
        over = sum(m["cost_usd"] for m in data.get("matrix", []) if m.get("task") is None)
        if over > 0:
            w = over / cost
            out.append(_item("scope_overhead", w, "%s%% of cost ($%.2f) belongs to no task" % (_pct(w), over),
                             _pct(w), "pct", "matrix", "overhead"))
        rw = sum(x["rework_cost_usd"] for x in tasks)
        if rw > 0:
            w = rw / cost
            out.append(_item("rework_cost", w, "Rework after returns cost $%.2f (%s%% of cost)" % (rw, _pct(w)),
                             _pct(w), "pct", "returns", "rework"))
        ex = sum(r["expiry_cost_usd"] for r in roles)
        if ex > 0:
            n = sum(r["cache_expiries"] for r in roles)
            w = ex / cost
            out.append(_item("respawns", w, "%d cache expiries cost $%.2f (%s%% of cost)" % (n, ex, _pct(w)),
                             _pct(w), "pct", "roles", "expiries"))

    if agent_s > 0:
        idle = t.get("buckets_s", {}).get("idle", 0)
        if idle > 0:
            w = idle / agent_s
            out.append(_item("idle_share", w, "Agents sat idle %s of %s agent-time (%s%%)" % (fmt_dur(idle), fmt_dur(agent_s), _pct(w)),
                             _pct(w), "pct", "timeline", "idle"))
        long = None
        for a in data.get("agents", []):
            for s in a.get("segments", []):
                if s[2] == "b":
                    key = (s[1] - s[0], a["name"], -s[0])
                    if long is None or key > long[0]:
                        long = (key, a["name"], s)
        if long:
            s = long[2]
            d = s[1] - s[0]
            w = d / agent_s
            out.append(_item("longest_block", w, "%s waited %s on %s (%s%% of agent-time)" % (long[1], fmt_dur(d), s[4] or "?", _pct(w)),
                             d, "s", "timeline", long[1]))
        agents = len([r for r in roles if r.get("transcript_found")])
        if wall > 0 and agents > 0:
            p = t.get("parallelism") or 0
            out.append(_item("parallelism", p / agents, "Parallelism %.2f across %d agents" % (p, agents), p, "x", "timeline", None))

    po = t.get("po_wait") or {}
    if po.get("total_s", 0) > 0 and wall > 0:
        w = po["pct_of_elapsed"] / 100.0
        out.append(_item("po_wait", w, "PO wait %s over %d escalations (%s%% of elapsed)" % (fmt_dur(po["total_s"]), po["count"], po["pct_of_elapsed"]),
                         po["total_s"], "s", "waits", "po"))

    waits = [x["wait_s"] for k in tasks for x in k["review_waits"]]
    if waits and wall > 0:
        m = _median(waits)
        if m > 0:
            w = m / wall
            out.append(_item("review_wait", w, "Median review wait %s over %d handins (%s%% of elapsed)" % (fmt_dur(m), len(waits), _pct(w)),
                             m, "s", "tasks", None))

    total_returns = sum(x["returns"] for x in tasks)
    top = max(tasks, key=lambda x: (x["returns"], [-ord(c) for c in x["id"]]), default=None)
    if top and top["returns"] >= RETURNS_FLAG:
        w = top["returns"] / total_returns
        text = "Task %s came back %d times (%d returns in all)" % (top["id"], top["returns"], total_returns)
        quotes = ['"%s"' % (r.get("reason") if r.get("reason") is not None else "not shared")
                  for r in top.get("returns_list", []) if r.get("reason") != ""]
        if quotes:
            text += ": " + " / ".join(quotes)
        out.append(_item("most_returns", w, text,
                         top["returns"], "count", "returns", top["id"]))

    att = t.get("attributed") or {}
    if sum((att.get("layers") or {}).values()) > 0 and att.get("time_pct", 100) < ATTRIBUTED_MIN_PCT:
        out.append(_item("attribution_low", 1.0, "Only %s%% of working time is tied to a task" % att["time_pct"],
                         att["time_pct"], "pct", "matrix", "overhead"))

    out.sort(key=lambda i: (-i["weight"], KINDS.index(i["kind"])))
    return out[:MAX_ITEMS]
