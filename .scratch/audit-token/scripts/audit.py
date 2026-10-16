#!/usr/bin/env python3
"""Token audit of the squad's Claude Code transcripts (AT-01). Read-only, stdlib only.

  python3 -I .scratch/audit-token/scripts/audit.py --until 2026-10-16T09:00:00Z
  python3 -I .scratch/audit-token/scripts/audit.py --selftest

Writes audit-tables.md and audit.json under .scratch/audit-token/ (refuses any other path).
Method: usage is deduped by message.id over ALL files; each token field is the max over the lines of an id
(streaming partials only grow). Cost = list price per model. The report holds ids, counts and numbers only.
"""
import argparse
import glob
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_ROOT = HERE.parent  # .scratch/audit-token
FIXTURE = HERE / "fixtures" / "session-fixture.jsonl"

# $ per million tokens. Source: vendor pricing page https://platform.claude.com/docs/en/about-claude/pricing,
# "Model pricing" table, fetched 2026-10-16 (Haiku 5.5: rows "up to 100,000 tokens" / "over 100,000 tokens").
# The `claude-api` skill's cached table (2026-10-06) says Sonnet 5.5 cache read $0.20; the vendor page says $0.10 and
# matches Claude Code's own cost-state totals, so the vendor page is used.
PRICE_DATE = "2026-10-16"
PRICES = {  # model: (in, out, cache_read, write_5m, write_1h)
    "claude-opus-5-5": (4.00, 20.00, 0.20, 5.00, 8.00),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10, 2.50, 4.00),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125, 0.20),
}
HAIKU_BIG = (0.50, 2.50, 0.05, 0.625, 1.00)  # prompts over 100K tokens
FIELDS = ("in", "cr", "cw5", "cw1", "out")
SKIP_MODELS = {"<synthetic>"}

ROLE_OF_SETTING = {"squad:manager": "manager", "squad:tech-lead": "tech-lead", "squad:ba": "ba",
                   "squad:designer": "designer", "squad:dev": "dev", "squad:qa-whitebox": "qa-whitebox",
                   "squad:qa-blackbox": "qa-blackbox", "squad:token-coach": "token-coach",
                   "squad:team-lead": "team-lead"}
PHASE_OF_ROLE = {"ba": "plan", "tech-lead": "plan", "team-lead": "plan", "designer": "plan", "dev": "build",
                 "qa-whitebox": "QA", "qa-blackbox": "QA", "token-coach": "retro", "manager": "coordination"}
ROLE_SHORT = {"mgr": "manager", "tech": "tech-lead", "ba": "ba", "qaw": "qa-whitebox", "qab": "qa-blackbox",
              "dev": "dev", "coach": "token-coach", "ux": "designer", "tl": "team-lead", "manager": "manager"}


def prices_for(model, prompt_tokens):
    if model == "claude-haiku-5-5" and prompt_tokens > 100_000:
        return HAIKU_BIG
    return PRICES.get(model)


def cost_of(model, f, prompt_tokens):
    p = prices_for(model, prompt_tokens)
    if p is None:
        return None
    return (f["in"] * p[0] + f["out"] * p[1] + f["cr"] * p[2] + f["cw5"] * p[3] + f["cw1"] * p[4]) / 1e6


def cost_parts(model, f, prompt_tokens):
    p = prices_for(model, prompt_tokens)
    if p is None:
        return None
    return {"in": f["in"] * p[0] / 1e6, "cr": f["cr"] * p[2] / 1e6, "cw5": f["cw5"] * p[3] / 1e6,
            "cw1": f["cw1"] * p[4] / 1e6, "out": f["out"] * p[1] / 1e6}


def usage_fields(u):
    cc = u.get("cache_creation") or {}
    cw5, cw1 = cc.get("ephemeral_5m_input_tokens"), cc.get("ephemeral_1h_input_tokens")
    total = u.get("cache_creation_input_tokens", 0) or 0
    if cw5 is None and cw1 is None:  # no split recorded: treat all as 5m and say so via the "unsplit" counter
        cw5, cw1 = total, 0
    return {"in": u.get("input_tokens", 0) or 0, "cr": u.get("cache_read_input_tokens", 0) or 0,
            "cw5": cw5 or 0, "cw1": cw1 or 0, "out": u.get("output_tokens", 0) or 0}


def parse_file(path, until):
    """-> dict(header, msgs{id: rec}, lines, cost_state). rec fields are the max over the lines of the id."""
    head = {"names": [], "setting": None}
    msgs, n_lines, cost_state, last_ts = {}, 0, None, None
    with open(path) as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            t = o.get("type")
            if t == "agent-name" and o.get("agentName") not in head["names"]:
                head["names"].append(o["agentName"])
            elif t == "agent-setting" and head["setting"] is None:
                head["setting"] = o.get("agentSetting")
            elif t == "cost-state":
                cost_state = o.get("totalCostUSD")
            if t != "assistant":
                continue
            ts = o.get("timestamp")
            if not ts or ts > until:
                continue
            m = o.get("message") or {}
            u = m.get("usage")
            if not u:
                continue
            last_ts = max(last_ts or ts, ts)
            n_lines += 1
            key = m.get("id") or o.get("uuid")
            f = usage_fields(u)
            th = (u.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0
            r = msgs.get(key)
            if r is None:
                msgs[key] = {"id": key, "model": m.get("model"), "ts": ts, "f": f, "think": th, "lines": 1,
                             "side": bool(o.get("isSidechain")), "speed": u.get("speed"), "effort": o.get("effort"),
                             "split": u.get("cache_creation") is not None, "naive": dict(f)}
            else:
                r["lines"] += 1
                r["ts"] = min(r["ts"], ts)
                r["side"] = r["side"] or bool(o.get("isSidechain"))
                r["think"] = max(r["think"], th)
                for k in FIELDS:
                    r["f"][k] = max(r["f"][k], f[k])
                    r["naive"][k] += f[k]
    return {"head": head, "msgs": msgs, "lines": n_lines, "cost_state": cost_state, "last_ts": last_ts}


# ---------- discovery ----------
def discover(claude_dirs):
    raw, real = 0, {}
    for cd in claude_dirs:
        for d in sorted(glob.glob(os.path.join(cd, "projects", "-home-chieule-workspace-squad*"))):
            for root, _, files in os.walk(d):
                for name in sorted(files):
                    if name.endswith(".jsonl"):
                        raw += 1
                        p = os.path.join(root, name)
                        real.setdefault(os.path.realpath(p), p)
    out = []
    for rp in sorted(real):
        parts = rp.split(os.sep)
        sub = "subagents" in parts
        session = parts[-3] if sub else Path(rp).stem
        out.append({"path": rp, "sub": sub, "session": session, "dir": parts[parts.index("projects") + 1]
                    if "projects" in parts else ""})
    return raw, out


def read_roster(path):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in Path(path).read_text().splitlines()
            if l.startswith("|")]
    if len(rows) < 3:
        return []
    h = rows[0]
    col = {k: h.index(k) for k in ("Agent", "Role", "Scope", "Session") if k in h}
    return [{k: (r[i] if len(r) > i else "") for k, i in col.items()} for r in rows[2:]]


def load_registry(squads_dir):
    """roster rows and usage-events: agent -> (squad, scope, done); session -> agent."""
    agents, roster_sess, ev_sess, scopes, ev_count = defaultdict(set), {}, {}, {}, 0
    for sq in sorted(glob.glob(os.path.join(squads_dir, "*"))):
        squad = os.path.basename(sq)
        for rp in sorted(glob.glob(os.path.join(sq, "scopes", "*", "roster.md")) +
                         glob.glob(os.path.join(sq, "scopes", "_done", "*", "roster.md")) +
                         glob.glob(os.path.join(sq, "goals", "*", "roster.md"))):
            d = os.path.dirname(rp)
            scope, done = os.path.basename(d), "/_done/" in rp
            scopes[(squad, scope)] = "closed" if done else "live"
            for r in read_roster(rp):
                agents[r["Agent"]].add((squad, scope))
                if r.get("Session"):
                    roster_sess[r["Session"]] = r["Agent"]
            ue = os.path.join(d, "usage-events.jsonl")
            if os.path.exists(ue):
                for l in open(ue):
                    try:
                        e = json.loads(l)
                    except ValueError:
                        continue
                    ev_count += 1
                    ev_sess[e["session"]] = (e["agent"], e.get("role"))
                    agents[e["agent"]].add((squad, scope))
    return {"agents": agents, "roster_sess": roster_sess, "ev_sess": ev_sess, "scopes": scopes, "events": ev_count}


def attribute(head, session, reg):
    """-> (role, squad, scope, how). how: roster | pattern | none."""
    name = head["names"][0] if head["names"] else None
    role = ROLE_OF_SETTING.get(head["setting"])
    if not name:
        return role, None, None, "none"
    hits = reg["agents"].get(name)
    if hits and len(hits) == 1:
        sq, sc = next(iter(hits))
        return role, sq, sc, "roster"
    m = re.match(r"^(?:(plugin|squad-board)-)?(mgr|tech|ba|qaw|qab|dev|coach|ux|tl|manager)-(.+?)(?:-\d+)?$", name)
    if m:
        sq0, rs, sc = m.groups()
        role = role or ROLE_SHORT.get(rs)
        cands = [k for k in reg["scopes"] if k[1] == sc and (sq0 is None or k[0] == sq0)]
        if len(cands) == 1:
            return role, cands[0][0], cands[0][1], "pattern"
    return role, None, None, "none"


# ---------- aggregation ----------
def tok_total(f):
    return sum(f[k] for k in FIELDS)


def add(acc, f):
    for k in FIELDS:
        acc[k] += f[k]


def zero():
    return {k: 0 for k in FIELDS}


def build(files, reg, until):
    parsed = []
    for fi in files:
        p = parse_file(fi["path"], until)
        p.update(fi)
        parsed.append(p)
    # parent role for subagent files
    by_session = {p["session"]: p for p in parsed if not p["sub"]}
    for p in parsed:
        src = by_session.get(p["session"], p) if p["sub"] else p
        p["attr"] = attribute(src["head"], p["session"], reg)
        p["src_head"] = src["head"]
    # cross-file dedupe: an id counts once, in the file whose copy of it has the earliest timestamp (tie: path)
    owner = {}
    for p in parsed:
        for k, r in p["msgs"].items():
            c = (r["ts"], p["path"])
            if k not in owner or c < owner[k][0]:
                owner[k] = (c, p["path"])
    rows, dup_ids, dup_cost = [], 0, 0.0
    for p in parsed:
        for k, r in sorted(p["msgs"].items(), key=lambda kv: (kv[1]["ts"], kv[0])):
            if r["model"] in SKIP_MODELS:
                continue
            if owner[k][1] != p["path"]:
                dup_ids += 1
                dup_cost += cost_of(r["model"], r["f"], tok_total(r["f"]) - r["f"]["out"]) or 0.0
                continue
            role, squad, scope, how = p["attr"]
            ctx = r["f"]["in"] + r["f"]["cr"] + r["f"]["cw5"] + r["f"]["cw1"]
            rows.append({"id": k, "session": p["session"], "name": (p["src_head"]["names"] or [None])[0], "file": p["path"], "sub": p["sub"] or r["side"],
                         "role": role or "?", "squad": squad, "scope": scope, "how": how, "model": r["model"],
                         "ts": r["ts"], "f": r["f"], "ctx": ctx, "think": r["think"], "speed": r["speed"], "effort": r["effort"],
                         "cost": cost_of(r["model"], r["f"], ctx), "parts": cost_parts(r["model"], r["f"], ctx),
                         "split": r["split"]})
    return parsed, rows, {"dup_ids": dup_ids, "dup_cost": dup_cost}


TEST_NAME = re.compile(r"livetest|inboxtest|test|probe|e2e|spike|^lt-")


def category(row):
    if row["scope"]:
        return "attributed"
    if row["name"] == "manager":
        return "unattributed: squad-level manager (no scope)"
    if row["name"] and TEST_NAME.search(row["name"]):
        return "non-squad: test/probe sessions"
    if row["role"] != "?":
        return "unattributed: squad role, scope unresolved"
    return "non-squad: no agent-name (PO or manual sessions)"


def share(x, tot):
    return f"{100 * x / tot:.1f}%" if tot else "-"


def tables(rows, parsed, reg, raw_count, until, dup, claude_dirs):
    priced = [r for r in rows if r["cost"] is not None]
    unpriced = [r for r in rows if r["cost"] is None]
    total = sum(r["cost"] for r in priced)
    out, js = [], {"until": until, "total_usd": round(total, 4)}
    P = out.append

    def table(title, head, body, note=None):
        P(f"\n### {title}\n")
        if note:
            P(note + "\n")
        P("| " + " | ".join(head) + " |")
        P("|" + "|".join("---" for _ in head) + "|")
        for b in body:
            P("| " + " | ".join(str(c) for c in b) + " |")

    # --- baseline
    sess_main = [p for p in parsed if not p["sub"]]
    sess_with_usage = [p for p in sess_main if p["msgs"]]
    ts = sorted(r["ts"] for r in rows)
    P(f"## Baseline (until {until})\n")
    P(f"- Transcript files found (raw, both config dirs): {raw_count}; distinct after realpath: {len(parsed)} "
      f"({len(sess_main)} sessions + {len(parsed) - len(sess_main)} subagent files)")
    P(f"- Sessions with at least one usage line before the cutoff: {len(sess_with_usage)}")
    P(f"- Messages (distinct ids): {len(rows)}; lines read: {sum(p['lines'] for p in parsed)}; "
      f"synthetic ids skipped: {sum(1 for p in parsed for r in p['msgs'].values() if r['model'] in SKIP_MODELS)}")
    P(f"- Date range of usage: {ts[0]} .. {ts[-1]}")
    P(f"- Ids that appear in more than one file (resumed/forked copies), counted once: {dup['dup_ids']} "
      f"(${dup['dup_cost']:.2f} that a per-file sum would add)")
    P(f"- Total spend (list price, priced models): ${total:,.2f}; unpriced messages: {len(unpriced)}")
    cs = [(p["session"], p["cost_state"]) for p in sess_main if p["cost_state"] is not None and p["last_ts"]]
    mine = {}
    for r in priced:
        if not r["sub"] or True:
            mine[r["session"]] = mine.get(r["session"], 0) + r["cost"]
    pairs = [(mine.get(s, 0), c) for s, c in cs if c]
    if pairs:
        P(f"- Cross-check against Claude Code's own `cost-state.totalCostUSD` (last record of each session, "
          f"{len(pairs)} sessions): sum ${sum(c for _, c in pairs):,.2f} vs this script ${sum(m for m, _ in pairs):,.2f}")
        js["cost_state_sum"] = round(sum(c for _, c in pairs), 4)
        js["cost_state_mine"] = round(sum(m for m, _ in pairs), 4)

    # --- prices
    table("Price table ($ per million tokens)", ["model", "input", "output", "cache read", "cache write 5m", "cache write 1h"],
          [[m, *p] for m, p in sorted(PRICES.items())] + [["claude-haiku-5-5 (prompt > 100K)", *HAIKU_BIG]],
          f"Source: vendor pricing page platform.claude.com/docs/en/about-claude/pricing, Model pricing table, fetched {PRICE_DATE}. "
          "(The `claude-api` skill's cached table lists Sonnet 5.5 cache read at $0.20; the vendor page says $0.10 and "
          "agrees with Claude Code's own cost-state totals, so the vendor page is used.) No other model appears in the data.")
    P("\nUnpriced models: " + (", ".join(sorted({str(r['model']) for r in unpriced})) or "none"))

    # --- coverage
    cats = defaultdict(lambda: [set(), 0.0])
    for r in priced:
        c = cats[category(r)]
        c[0].add(r["session"])
        c[1] += r["cost"]
    table("Attribution coverage (T6)", ["category", "sessions", "spend $", "share of total"],
          [[k, len(v[0]), f"{v[1]:,.2f}", share(v[1], total)] for k, v in sorted(cats.items())],
          "attributed = transcript `agent-name` resolved to a scope (roster or name pattern); unattributed = squad role "
          "known but no scope; non-squad = test/probe names or no `agent-name` (PO's own sessions).")
    how = defaultdict(set)
    for p in sess_with_usage:
        how[p["attr"][3]].add(p["session"])
    P("\nScope resolved by: " + ", ".join(f"{k}: {len(v)}" for k, v in sorted(how.items())))
    in_roster = sum(1 for p in sess_with_usage if p["session"] in reg["roster_sess"])
    in_ev = sum(1 for p in sess_with_usage if p["session"] in reg["ev_sess"])
    attributed = [p for p in sess_with_usage if p["attr"][2]]
    missed = sum(1 for p in attributed if p["session"] not in reg["roster_sess"])
    mism = 0
    for p in sess_with_usage:
        a = reg["roster_sess"].get(p["session"]) or (reg["ev_sess"].get(p["session"]) or (None,))[0]
        if a and p["head"]["names"] and p["head"]["names"][0] != a:
            mism += 1
    P(f"\nRoster rows give a session id for {in_roster} of {len(sess_with_usage)} sessions; usage-events for {in_ev}; "
      f"a roster-only attribution would miss {missed} of {len(attributed)} attributed sessions (respawned roles). "
      f"Transcript name vs roster/usage-events name disagreements: {mism}.")
    js["coverage"] = {"attributed_sessions": len(attributed), "sessions": len(sess_with_usage), "roster_missed": missed,
                      "name_mismatch": mism}

    # --- by role / phase / type / model
    def group(keyf, rows_):
        g = defaultdict(lambda: {"cost": 0.0, "msgs": 0, "tok": zero(), "parts": {k: 0.0 for k in FIELDS}, "sess": set()})
        for r in rows_:
            x = g[keyf(r)]
            x["cost"] += r["cost"]
            x["msgs"] += 1
            x["sess"].add(r["session"])
            add(x["tok"], r["f"])
            for k in FIELDS:
                x["parts"][k] += r["parts"][k]
        return g

    g = group(lambda r: r["role"], priced)
    table("Spend per role (denominator: total spend)", ["role", "phase", "sessions", "messages", "$", "share of total",
          "in $", "cache read $", "cache write $", "out $"],
          [[k, PHASE_OF_ROLE.get(k, "?"), len(v["sess"]), v["msgs"], f"{v['cost']:,.2f}", share(v["cost"], total),
            f"{v['parts']['in']:,.2f}", f"{v['parts']['cr']:,.2f}", f"{v['parts']['cw5'] + v['parts']['cw1']:,.2f}",
            f"{v['parts']['out']:,.2f}"] for k, v in sorted(g.items(), key=lambda kv: -kv[1]["cost"])],
          "Includes subagent messages under the parent's role (see the subagent row below). Role = `agent-setting`; "
          "`?` = no squad role.")
    js["by_role"] = {k: round(v["cost"], 4) for k, v in g.items()}
    gp = group(lambda r: PHASE_OF_ROLE.get(r["role"], "no-phase"), priced)
    table("Spend per phase (approximate: phase is derived from role)", ["phase", "$", "share of total"],
          [[k, f"{v['cost']:,.2f}", share(v["cost"], total)] for k, v in sorted(gp.items(), key=lambda kv: -kv[1]["cost"])],
          "Role-to-phase table: plan = ba, tech-lead, team-lead, designer; build = dev; QA = qa-whitebox, qa-blackbox; "
          "retro = token-coach; coordination = manager; no-phase = no squad role.")
    js["by_phase"] = {k: round(v["cost"], 4) for k, v in gp.items()}

    tt = zero()
    tp = {k: 0.0 for k in FIELDS}
    for r in priced:
        add(tt, r["f"])
        for k in FIELDS:
            tp[k] += r["parts"][k]
    names = {"in": "input (uncached)", "cr": "cache read", "cw5": "cache write 5m", "cw1": "cache write 1h", "out": "output"}
    table("Spend per token type (denominator: total spend)", ["type", "tokens", "$", "share of total"],
          [[names[k], f"{tt[k]:,}", f"{tp[k]:,.2f}", share(tp[k], total)] for k in FIELDS],
          f"Output includes thinking tokens (not added again): thinking_tokens max-folded = "
          f"{sum(r['think'] for r in priced):,} of the output tokens above.")
    js["by_type"] = {k: round(tp[k], 4) for k in FIELDS}
    js["tokens"] = tt

    gm = group(lambda r: r["model"], priced)
    table("Spend per model (denominator: total spend)", ["model", "messages", "$", "share of total", "in $", "cache read $",
          "cache write $", "out $"],
          [[k, v["msgs"], f"{v['cost']:,.2f}", share(v["cost"], total), f"{v['parts']['in']:,.2f}",
            f"{v['parts']['cr']:,.2f}", f"{v['parts']['cw5'] + v['parts']['cw1']:,.2f}", f"{v['parts']['out']:,.2f}"]
           for k, v in sorted(gm.items(), key=lambda kv: -kv[1]["cost"])])
    js["by_model"] = {k: round(v["cost"], 4) for k, v in gm.items()}
    gr = group(lambda r: (r["role"], r["model"]), priced)
    table("Role x model (denominator: total spend)", ["role", "model", "messages", "$", "share of total"],
          [[k[0], k[1], v["msgs"], f"{v['cost']:,.2f}", share(v["cost"], total)]
           for k, v in sorted(gr.items(), key=lambda kv: -kv[1]["cost"])])
    speeds = defaultdict(int)
    for r in rows:
        speeds[str(r["speed"])] += 1
    P("\nSpeed field (messages): " + ", ".join(f"{k}: {v}" for k, v in sorted(speeds.items())) +
      ". Anything other than `standard` would be flagged; `None` = older transcript lines without the field.")

    # --- subagents
    sub = [r for r in priced if r["sub"]]
    gs = group(lambda r: r["role"], sub)
    subfiles = sorted({r["file"] for r in sub})
    table("Subagents (T3; `bin/squad-usage` skips sidechain lines)", ["parent role", "messages", "$", "share of total"],
          [[k, v["msgs"], f"{v['cost']:,.2f}", share(v["cost"], total)] for k, v in sorted(gs.items())] +
          [["all", len(sub), f"{sum(r['cost'] for r in sub):,.2f}", share(sum(r['cost'] for r in sub), total)]],
          f"{len(subfiles)} subagent file(s) / sidechain lines contribute; messages tagged `subagent` in the rows.")
    js["subagent_usd"] = round(sum(r["cost"] for r in sub), 4)

    # --- scopes
    gsc = group(lambda r: (r["squad"], r["scope"]) if r["scope"] else None, [r for r in priced if r["scope"]])
    rows_sc = []
    for k, v in gsc.items():
        status = reg["scopes"].get(k, "?")
        ts_ = [r["ts"] for r in priced if (r["squad"], r["scope"]) == k]
        rows_sc.append([f"{k[0]}/{k[1]}", status, len(v["sess"]), v["msgs"], v["cost"], min(ts_)[:10], max(ts_)[:10]])
    rows_sc.sort(key=lambda r: -r[4])
    table("Spend per scope (denominator: total spend)", ["squad/scope", "status", "sessions", "messages", "$", "share of total", "first", "last"],
          [[a, b, c, d, f"{e:,.2f}", share(e, total), f, g_] for a, b, c, d, e, f, g_ in rows_sc])
    vals = [r[4] for r in rows_sc]
    cl = [r[4] for r in rows_sc if r[1] == "closed"]
    spread = lambda xs: f"min ${min(xs):,.2f} / median ${statistics.median(xs):,.2f} / max ${max(xs):,.2f} (n={len(xs)})"
    P(f"\nSpread across all scopes: {spread(vals)}.")
    if cl:
        P(f"Spread across closed scopes: {spread(cl)}.")
    js["scope_spread"] = {"all": [min(vals), statistics.median(vals), max(vals), len(vals)]}
    js["by_scope"] = {r[0]: round(r[4], 4) for r in rows_sc}
    # per scope role mix for the median closed scope
    # --- drivers (inputs to the report)
    P("\n## Driver metrics\n")
    bands = [(0, 50_000), (50_000, 120_000), (120_000, 200_000), (200_000, 10**12)]
    bt = []
    for lo, hi in bands:
        sel = [r for r in priced if lo <= r["ctx"] < hi]
        bt.append([f"{lo // 1000}k-{hi // 1000 if hi < 10**9 else 'inf'}k", len(sel), f"{sum(r['cost'] for r in sel):,.2f}",
                   share(sum(r["cost"] for r in sel), total), f"{sum(r['f']['cr'] for r in sel):,}"])
    table("Cost by message context size (context = input + cache read + cache write of that message)",
          ["context band", "messages", "$", "share of total", "cache-read tokens"], bt)
    js["bands"] = {b[0]: b[2] for b in bt}
    # cache expiry
    exp_cost = exp_extra = 0.0
    exp_n = 0
    msess = defaultdict(list)
    for r in priced:
        if not r["sub"]:
            msess[r["session"]].append(r)
    for s, lst in msess.items():
        lst.sort(key=lambda r: r["ts"])
        for a, b in zip(lst, lst[1:]):
            if (parse_ts(b["ts"]) - parse_ts(a["ts"])).total_seconds() > 3600 and b["f"]["cw5"] + b["f"]["cw1"] >= 10_000:
                exp_n += 1
                wc = b["parts"]["cw5"] + b["parts"]["cw1"]
                exp_cost += wc
                p = prices_for(b["model"], b["ctx"])
                exp_extra += wc - (b["f"]["cw5"] + b["f"]["cw1"]) * p[2] / 1e6
    P(f"\n- Cache expiries (gap > 1h and cache write >= 10k, same rule as `squad-usage`): {exp_n}; the rewrite cost "
      f"${exp_cost:,.2f} ({share(exp_cost, total)} of total), ${exp_extra:,.2f} above what a cache read of the same tokens would have cost.")
    js["expiry"] = {"n": exp_n, "usd": round(exp_cost, 4), "extra_usd": round(exp_extra, 4)}
    # startup
    first = {}
    for s, lst in msess.items():
        first[s] = lst[:10]
    sc_cost = sum(r["cost"] for lst in first.values() for r in lst)
    P(f"- First 10 messages of every session (startup reading): ${sc_cost:,.2f} ({share(sc_cost, total)} of total) over {len(first)} sessions.")
    js["startup10_usd"] = round(sc_cost, 4)
    # sessions per role-scope
    sess_rs = defaultdict(set)
    for r in priced:
        if r["scope"]:
            sess_rs[(r["squad"], r["scope"], r["role"])].add(r["session"])
    resp = defaultdict(lambda: [0, 0])
    for (sq, sc, role), ss in sess_rs.items():
        resp[role][0] += len(ss)
        resp[role][1] += 1
    table("Sessions per (scope, role) = respawn count", ["role", "sessions", "(scope, role) pairs", "avg sessions per pair"],
          [[k, v[0], v[1], f"{v[0] / v[1]:.2f}"] for k, v in sorted(resp.items())])
    # per-session spread
    ps = sorted(((sum(r["cost"] for r in lst), s) for s, lst in msess.items()), reverse=True)
    P(f"\nPer session (main threads): n={len(ps)}, min ${ps[-1][0]:,.2f} / median ${statistics.median([x for x, _ in ps]):,.2f} / "
      f"max ${ps[0][0]:,.2f}; top 5 sessions: " + ", ".join(f"{s[:8]} ${c:,.2f}" for c, s in ps[:5]) + ".")
    # naive vs deduped
    best = max((p for p in parsed if not p["sub"]), key=lambda p: (p["lines"], p["path"]))
    nl = best["lines"]
    nid = len(best["msgs"])
    naive_cost = sum(cost_of(r["model"], r["naive"], tok_total(r["naive"]) - r["naive"]["out"]) or 0 for r in best["msgs"].values()
                     if r["model"] not in SKIP_MODELS)
    ded_cost = sum(cost_of(r["model"], r["f"], tok_total(r["f"]) - r["f"]["out"]) or 0 for r in best["msgs"].values()
                   if r["model"] not in SKIP_MODELS)
    P(f"\n## Naive-sum inflation (T2)\n\nSession {best['session']} ({best['path']}): {nl} assistant usage lines, {nid} distinct message ids; "
      f"summing every line would give ${naive_cost:,.2f} vs ${ded_cost:,.2f} deduped "
      f"({naive_cost / ded_cost:.2f}x).")
    allnaive = sum(cost_of(r["model"], r["naive"], tok_total(r["naive"]) - r["naive"]["out"]) or 0
                   for p in parsed for r in p["msgs"].values() if r["model"] not in SKIP_MODELS)
    P(f"All files: naive per-line sum ${allnaive:,.2f} vs per-id max ${total + dup['dup_cost']:,.2f} before cross-file dedupe "
      f"({allnaive / (total + dup['dup_cost']):.2f}x).")
    js["naive"] = {"session": best["session"], "lines": nl, "ids": nid, "naive": round(naive_cost, 4), "dedup": round(ded_cost, 4),
                   "all_naive": round(allnaive, 4)}
    drivers(priced, msess, total, P, js)
    return "\n".join(out) + "\n", js


# Dates the existing token work went live (git log on the repo, UTC): Token Coach + usage hook (67a19b6),
# absolute 120k/100k limits (155b5db).
WINDOWS = [("before Token Coach", "", "2026-10-12T10:32:00Z"), ("Token Coach, percent rules", "2026-10-12T10:32:00Z", "2026-10-14T15:58:00Z"),
           ("absolute 120k rule", "2026-10-14T15:58:00Z", "9999")]


def drivers(priced, msess, total, P, js):
    P("\n## Driver arithmetic (inputs for audit.md)\n")
    # existing work: before / after
    rows_w = []
    for name, lo, hi in WINDOWS:
        sel = [r for r in priced if lo <= r["ts"] < hi]
        if not sel:
            continue
        c = sum(r["cost"] for r in sel)
        big = sum(r["cost"] for r in sel if r["ctx"] > 120_000)
        rows_w.append([name, len(sel), f"{c:,.2f}", f"{c / len(sel) * 1000:,.1f}", share(big, c),
                       share(sum(1 for r in sel if r["ctx"] > 120_000), len(sel))])
    P("### Existing work: context over 120k before and after (denominator: that window's spend)\n")
    P("| window | messages | $ | $ per 1000 messages | spend in messages over 120k | messages over 120k |")
    P("|---|---|---|---|---|---|")
    for r in rows_w:
        P("| " + " | ".join(str(x) for x in r) + " |")
    js["windows"] = rows_w
    # D1 excess context
    ex_by = defaultdict(lambda: [0.0, 0, 0])
    cross = defaultdict(set)
    for r in priced:
        if r["sub"]:
            continue
        if r["ctx"] > 120_000:
            p = prices_for(r["model"], r["ctx"])
            ex = min(r["f"]["cr"], r["ctx"] - 120_000) * p[2] / 1e6
            ex_by[r["role"]][0] += ex
            ex_by[r["role"]][1] += 1
            cross[r["role"]].add(r["session"])
    first = {s: lst[:10] for s, lst in msess.items()}
    sess_role = {s: lst[0]["role"] for s, lst in msess.items()}
    peak = {s: max(r["ctx"] for r in lst) for s, lst in msess.items()}
    rows_d = []
    tot_ex = tot_resp = 0.0
    for role, (ex, n, _) in sorted(ex_by.items(), key=lambda kv: -kv[1][0]):
        sess_r = [s for s in msess if sess_role[s] == role]
        avg_start = statistics.mean(sum(r["cost"] for r in first[s]) for s in sess_r)
        respawns = sum(int(peak[s] // 120_000) for s in cross[role])
        resp_cost = respawns * avg_start
        tot_ex += ex
        tot_resp += resp_cost
        rows_d.append([role, n, len(cross[role]), f"{ex:,.2f}", respawns, f"{avg_start:,.2f}", f"{resp_cost:,.2f}", f"{ex - resp_cost:,.2f}"])
    P("\n### D1: cost of context above 120k (excess cache-read tokens x read price) vs the respawns that would cut it\n")
    P("Respawns = sum over sessions of floor(peak context / 120k); respawn cost = respawns x that role's mean first-10-message cost.\n")
    P("| role | messages over 120k | sessions crossing | excess read $ | respawns needed | mean startup $ | respawn cost $ | net $ |")
    P("|---|---|---|---|---|---|---|---|")
    for r in rows_d:
        P("| " + " | ".join(str(x) for x in r) + " |")
    P(f"\nTotal: excess ${tot_ex:,.2f} ({share(tot_ex, total)} of total), respawn cost ${tot_resp:,.2f}, net ${tot_ex - tot_resp:,.2f} ({share(tot_ex - tot_resp, total)} of total).")
    js["d1"] = {"excess": round(tot_ex, 4), "respawn": round(tot_resp, 4)}
    # D2 startup by role
    g = defaultdict(lambda: [0.0, 0])
    for s, lst in first.items():
        g[sess_role[s]][0] += sum(r["cost"] for r in lst)
        g[sess_role[s]][1] += 1
    P("\n### D2: first 10 messages of each session, by role (denominator: total spend)\n")
    P("| role | sessions | $ | share of total | mean $ per session |")
    P("|---|---|---|---|---|")
    for k, (c, n) in sorted(g.items(), key=lambda kv: -kv[1][0]):
        P(f"| {k} | {n} | {c:,.2f} | {share(c, total)} | {c / n:,.2f} |")
    # D2b early retirement: a session that ended below 100k context while the same (scope, role) started another
    ses_first = {s_: lst[0]["ts"] for s_, lst in msess.items()}
    bypair = defaultdict(list)
    for s_, lst in msess.items():
        if lst[0]["scope"]:
            bypair[(lst[0]["squad"], lst[0]["scope"], lst[0]["role"])].append(s_)
    early = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for key, ss in bypair.items():
        ss.sort(key=lambda x: ses_first[x])
        for a_, b_ in zip(ss, ss[1:]):
            x = early[key[2]]
            x[0] += 1
            if peak[a_] < 100_000:
                x[1] += 1
                x[2] += sum(r["cost"] for r in first[b_])
                last = msess[a_][-1]
                x[3] += last["ctx"] * prices_for(last["model"], last["ctx"])[2] / 1e6  # one read of the carried context
    P("\n### D2b: respawns that happened while the previous session was under 100k context\n")
    P("Upper bound of what reuse could save = startup cost of the successor; the carried context would be read again each turn (one read shown).\n")
    P("| role | successor sessions | of which predecessor peak < 100k | their startup $ | one read of carried context $ |")
    P("|---|---|---|---|---|")
    for k, (n, e, c, rd) in sorted(early.items(), key=lambda kv: -kv[1][2]):
        P(f"| {k} | {n} | {e} | {c:,.2f} | {rd:,.2f} |")
    js["d2b"] = {k: [v[0], v[1], round(v[2], 4)] for k, v in early.items()}
    # D3 1h -> 5m
    w1 = sum(r["parts"]["cw1"] for r in priced)
    as5 = 0.0
    for r in priced:
        p = prices_for(r["model"], r["ctx"])
        as5 += r["f"]["cw1"] * p[3] / 1e6
    extra = 0.0
    n_gap = 0
    for s, lst in msess.items():
        for a, b in zip(lst, lst[1:]):
            gap = (parse_ts(b["ts"]) - parse_ts(a["ts"])).total_seconds()
            if 300 < gap <= 3600 and b["f"]["cr"] > 0:
                p = prices_for(b["model"], b["ctx"])
                extra += b["f"]["cr"] * (p[3] - p[2]) / 1e6
                n_gap += 1
    P("\n### D3: 1-hour cache writes\n")
    P(f"- 1h cache-write spend ${w1:,.2f} ({share(w1, total)} of total); the same tokens at the 5m write price: ${as5:,.2f}; difference ${w1 - as5:,.2f}.")
    P(f"- Messages that read cache after a gap of 5-60 min (would miss a 5m cache and rewrite those tokens): {n_gap}; extra cost ${extra:,.2f}.")
    P(f"- Net if every write were 5m: ${w1 - as5 - extra:,.2f} ({share(w1 - as5 - extra, total)} of total). Whether Claude Code lets the squad choose the TTL is not measured here.")
    js["d3"] = {"w1": round(w1, 4), "diff": round(w1 - as5, 4), "extra": round(extra, 4)}
    # D4 manager / opus repricing
    P("\n### D4: Opus messages repriced at Sonnet 5.5 (same tokens)\n")
    P("| role | opus messages | opus $ | same tokens at sonnet $ | difference $ | share of total |")
    P("|---|---|---|---|---|---|")
    go = defaultdict(lambda: [0, 0.0, 0.0])
    for r in priced:
        if r["model"] == "claude-opus-5-5":
            x = go[r["role"]]
            x[0] += 1
            x[1] += r["cost"]
            x[2] += cost_of("claude-sonnet-5-5", r["f"], r["ctx"])
    for k, (n, c, c2) in sorted(go.items(), key=lambda kv: -kv[1][1]):
        P(f"| {k} | {n} | {c:,.2f} | {c2:,.2f} | {c - c2:,.2f} | {share(c - c2, total)} |")
    js["d4"] = {k: [round(v[1], 4), round(v[2], 4)] for k, v in go.items()}
    # D5 output and thinking, effort
    P("\n### D5: output and thinking by role (denominator: total spend)\n")
    P("| role | output $ | share of total | thinking tokens | thinking $ (at output price) | share of total | effort field (messages) |")
    P("|---|---|---|---|---|---|---|")
    go = defaultdict(lambda: [0.0, 0, 0.0, defaultdict(int)])
    for r in priced:
        x = go[r["role"]]
        x[0] += r["parts"]["out"]
        x[1] += r["think"]
        p = prices_for(r["model"], r["ctx"])
        x[2] += r["think"] * p[1] / 1e6
        x[3][str(r["effort"])] += 1
    for k, (o, th, tc, ef) in sorted(go.items(), key=lambda kv: -kv[1][0]):
        P(f"| {k} | {o:,.2f} | {share(o, total)} | {th:,} | {tc:,.2f} | {share(tc, total)} | " + ", ".join(f"{a}: {b}" for a, b in sorted(ef.items())) + " |")
    js["d5"] = {k: [round(v[0], 4), v[1], round(v[2], 4)] for k, v in go.items()}
    P("\n### D5b: developer output per message by effort (same role, same model; task mix differs, so only an upper-bound hint)\n")
    P("| effort | messages | mean output tokens | mean thinking tokens |")
    P("|---|---|---|---|")
    by_e = defaultdict(lambda: [0, 0, 0])
    for r in priced:
        if r["role"] == "dev" and r["model"] == "claude-sonnet-5-5":
            x = by_e[str(r["effort"])]
            x[0] += 1
            x[1] += r["f"]["out"]
            x[2] += r["think"]
    for k, (n, o, th) in sorted(by_e.items()):
        P(f"| {k} | {n} | {o / n:,.0f} | {th / n:,.0f} |")
    js["d5b"] = {k: [v[0], round(v[1] / v[0], 1)] for k, v in by_e.items()}
    # D4b manager model by scope
    P("\n### D4b: manager messages and quality signals per scope\n")
    P("| squad/scope | manager messages opus | manager messages sonnet | scope $ |")
    P("|---|---|---|---|")
    bs = defaultdict(lambda: [0, 0, 0.0])
    for r in priced:
        if r["scope"]:
            x = bs[(r["squad"], r["scope"])]
            x[2] += r["cost"]
            if r["role"] == "manager":
                x[0 if r["model"] == "claude-opus-5-5" else 1] += 1
    for k, (o, so, c) in sorted(bs.items()):
        P(f"| {k[0]}/{k[1]} | {o} | {so} | {c:,.2f} |")


def parse_ts(s):
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def safe_out(path):
    p = Path(path).resolve()
    if OUT_ROOT.resolve() not in p.parents and p != OUT_ROOT.resolve():
        sys.exit(f"refusing to write outside {OUT_ROOT}: {p}")
    return p


# ---------- selftest ----------
SELFTEST_EXPECT = {  # fixture: id A on 3 lines (out grows 10,40,90), id B on 1 line, one sidechain id C, one synthetic
    "messages": 3, "in": 17, "cr": 600, "cw5": 150, "cw1": 200, "out": 150, "sub": 1,
}


def selftest():
    parsed = parse_file(FIXTURE, "9999-01-01T00:00:00Z")
    msgs = {k: r for k, r in parsed["msgs"].items() if r["model"] not in SKIP_MODELS}
    tot = zero()
    for r in msgs.values():
        add(tot, r["f"])
    got = {"messages": len(msgs), **tot, "sub": sum(1 for r in msgs.values() if r["side"])}
    ok = got == SELFTEST_EXPECT
    a = msgs["msg_A"]
    naive_out = a["naive"]["out"]
    c = cost_of("claude-sonnet-5-5", {"in": 1_000_000, "cr": 1_000_000, "cw5": 1_000_000, "cw1": 1_000_000, "out": 1_000_000}, 0)
    ok_cost = abs(c - (2 + 10 + 0.1 + 2.5 + 4)) < 1e-9
    ok_unpriced = cost_of("claude-unknown-9", zero(), 0) is None
    ok_lines = a["lines"] == 3 and a["f"]["out"] == 90 and naive_out == 140
    print(f"fixture {FIXTURE.name}: lines={parsed['lines']} ids={len(parsed['msgs'])} (synthetic included)")
    print(f"expected {SELFTEST_EXPECT}")
    print(f"got      {got}")
    print(f"msg_A: lines={a['lines']} max out={a['f']['out']} naive out={naive_out} (3 lines: 10+40+90)")
    print(f"price check sonnet-5-5 1M of each type = ${c:.2f} (expect $18.60): {'ok' if ok_cost else 'FAIL'}")
    print(f"unpriced model returns None: {'ok' if ok_unpriced else 'FAIL'}")
    good = ok and ok_cost and ok_unpriced and ok_lines
    print("SELFTEST PASS" if good else "SELFTEST FAIL")
    return 0 if good else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--until", help="ISO UTC cutoff, e.g. 2026-10-16T09:00:00Z; later lines are ignored")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--claude-dir", action="append", default=None, help="config dir (default: ~/.claude and ~/.claude-2)")
    ap.add_argument("--squads-dir", default="/home/chieule/workspace/squad/.claude/squads")
    ap.add_argument("--show-session", metavar="ID", help="print the deduped messages of one session (ids, tokens, $)")
    ap.add_argument("--out", default=str(OUT_ROOT / "audit-tables.md"))
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.until:
        sys.exit("--until is required")
    until = a.until if a.until.endswith("Z") else a.until
    dirs = a.claude_dir or [os.path.expanduser("~/.claude"), os.path.expanduser("~/.claude-2")]
    out_md, out_js = safe_out(a.out), safe_out(Path(a.out).with_suffix(".json"))
    raw, files = discover(dirs)
    reg = load_registry(a.squads_dir)
    parsed, rows, dup = build(files, reg, until)
    if a.show_session:
        tot = 0.0
        print(f"session {a.show_session} until {until}: columns id, ts, model, in, cr, cw5, cw1, out, ctx, $, lines-in-file")
        for r in rows:
            if r["session"] == a.show_session:
                lines = next(p["msgs"][r["id"]]["lines"] for p in parsed if r["id"] in p["msgs"] and p["path"] == r["file"])
                tot += r["cost"] or 0
                print(r["id"], r["ts"], r["model"], *(r["f"][k] for k in FIELDS), r["ctx"], f"{r['cost']:.4f}", lines,
                      "sub" if r["sub"] else "")
        print(f"total ${tot:.4f}")
        return
    md, js = tables(rows, parsed, reg, raw, until, dup, dirs)
    out_md.write_text(md)
    out_js.write_text(json.dumps(js, indent=1, sort_keys=True) + "\n")
    print(f"wrote {out_md} and {out_js}; total ${js['total_usd']:,.2f}")


if __name__ == "__main__":
    main()
