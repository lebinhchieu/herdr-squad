#!/usr/bin/env python3 -I
"""AT-02 A/B runner. Usage: python3 -I scripts/ab.py run <candidate> <arm-alias> <n-runs> [--tag T]
                          python3 -I scripts/ab.py report
Each run: fresh temp dir outside the repo with a byte copy of fixtures/<c>/input, the committed prompt.md on stdin,
`claude -p --model <alias>` with only Read,Grep,Glob, no settings/MCP/skills. Tokens and cost come from the run's
transcript (dedupe by message.id, max per field, subagent files included); score = fixtures/<c>/checks.py only.
Outputs: outputs/<c>/<arm>-<k>.txt, runs/<c>-<arm>-<k>.json (ids, counts, numbers; no transcript text)."""
import glob, importlib.util, json, os, shutil, subprocess, sys, tempfile, time, uuid, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.realpath(os.path.expanduser("~/.claude/projects"))  # ~/.claude-2/projects is a symlink to it
# USD per 1M tokens: (input, output, cache_read, cache_write_5m, cache_write_1h)
# Source: claude-api skill model table cached 2026-10-06 (input/output; Sonnet 5.5 cache read 0.20). Cache read = 0.1x input,
# write 5m = 1.25x, 1h = 2x are the standard multipliers, ASSUMED for models whose table row lacks them (marked).
PRICES = {
    "claude-sonnet-5-5": (2.00, 10.00, 0.20, 2.50, 4.00),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125, 0.20),
    "claude-haiku-4-5": (1.00, 5.00, 0.10, 1.25, 2.00),
    "claude-sonnet-4-6": (3.00, 15.00, 0.30, 3.75, 6.00),
}
FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "ephemeral_5m", "ephemeral_1h")

def price(model):
    for k, v in PRICES.items():
        if model.startswith(k):
            return v
    return None

def usage_of(files):
    """dedupe by message.id; each field = max over the id's lines (streaming partials only grow)."""
    ids = {}
    for f in files:
        for line in open(f):
            try: o = json.loads(line)
            except ValueError: continue
            m = o.get("message")
            if o.get("type") != "assistant" or not isinstance(m, dict) or "id" not in m: continue
            u = m.get("usage") or {}
            cc = u.get("cache_creation") or {}
            vals = {"input_tokens": u.get("input_tokens", 0), "output_tokens": u.get("output_tokens", 0),
                    "cache_read_input_tokens": u.get("cache_read_input_tokens", 0),
                    "ephemeral_5m": cc.get("ephemeral_5m_input_tokens", 0),
                    "ephemeral_1h": cc.get("ephemeral_1h_input_tokens", 0)}
            # cache_creation total without a breakdown counts as 5m
            tot = u.get("cache_creation_input_tokens", 0)
            if vals["ephemeral_5m"] + vals["ephemeral_1h"] < tot:
                vals["ephemeral_5m"] += tot - vals["ephemeral_5m"] - vals["ephemeral_1h"]
            e = ids.setdefault(m["id"], {"model": m.get("model"), **{k: 0 for k in FIELDS}})
            for k in FIELDS: e[k] = max(e[k], vals[k])
    return ids

def cost(ids):
    tot, unpriced = 0.0, set()
    for e in ids.values():
        p = price(e["model"] or "")
        if p is None: unpriced.add(e["model"]); continue
        tot += sum(e[k] * p[i] for i, k in enumerate(FIELDS)) / 1e6
    return tot, sorted(map(str, unpriced))

def load_checks(c):
    s = importlib.util.spec_from_file_location("checks_" + c, os.path.join(ROOT, "fixtures", c, "checks.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def run_one(c, alias, k, extra_model=None):
    fx = os.path.join(ROOT, "fixtures", c)
    prompt = open(os.path.join(fx, "prompt.md")).read()
    tmp = os.path.realpath(tempfile.mkdtemp(prefix="at02-"))
    try:
        shutil.copytree(os.path.join(fx, "input"), os.path.join(tmp, "work"))
        cwd = os.path.join(tmp, "work")
        sid = str(uuid.uuid4())
        cmd = ["claude", "-p", "--model", alias, "--session-id", sid, "--tools", "Read,Grep,Glob",
               "--allowedTools", "Read,Grep,Glob", "--setting-sources", "", "--strict-mcp-config",
               "--disable-slash-commands"]
        t0 = time.time()
        p = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"pid {p.pid} {c} {alias} #{k}", flush=True)
        try:
            out, err = p.communicate(prompt, timeout=420)
        except subprocess.TimeoutExpired:
            p.kill(); out, err = p.communicate()  # our own PID only
        secs = time.time() - t0
        pdir = os.path.join(PROJ, cwd.replace("/", "-").replace(".", "-"))
        files = glob.glob(os.path.join(pdir, sid + ".jsonl")) + glob.glob(os.path.join(pdir, sid, "subagents", "*.jsonl"))
        ids = usage_of(files)
        usd, unpriced = cost(ids)
        defects = load_checks(c).check(out)
        rec = {"candidate": c, "arm_alias": alias, "run": k, "date": datetime.date.today().isoformat(),
               "session": sid, "models": sorted({e["model"] for e in ids.values()}), "n_message_ids": len(ids),
               "tokens": {f: sum(e[f] for e in ids.values()) for f in FIELDS},
               "cost_usd": round(usd, 6), "unpriced": unpriced, "defects": defects, "seconds": round(secs, 1),
               "exit": p.returncode, "stderr_len": len(err), "transcript_files": len(files)}
        os.makedirs(os.path.join(ROOT, "outputs", c), exist_ok=True); os.makedirs(os.path.join(ROOT, "runs"), exist_ok=True)
        tag = alias + (("-" + extra_model) if extra_model else "")
        open(os.path.join(ROOT, "outputs", c, f"{tag}-{k}.txt"), "w").write(out)
        json.dump(rec, open(os.path.join(ROOT, "runs", f"{c}-{tag}-{k}.json"), "w"), indent=1)
        print(json.dumps(rec)); return rec
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def report():
    rows = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "runs", "*.json")))]
    print("| candidate | arm | run | model id (transcript) | in | cache_r | cache_w | out | cost USD | defects |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        t = r["tokens"]
        print(f"| {r['candidate']} | {r['arm_alias']} | {r['run']} | {','.join(r['models'])} | {t['input_tokens']} | "
              f"{t['cache_read_input_tokens']} | {t['ephemeral_5m']+t['ephemeral_1h']} | {t['output_tokens']} | {r['cost_usd']:.5f} | {','.join(r['defects']) or 'none'} |")
    print(f"\nstudy total cost USD: {sum(r['cost_usd'] for r in rows):.4f} over {len(rows)} runs")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "run":
        for k in range(1, int(a[3]) + 1): run_one(a[1], a[2], k)
    elif a and a[0] == "report": report()
    else: print(__doc__)
