"""Checks for the usage fixture: expected values are recomputed from input/ (no hand numbers).
Defects: wrong top role, top role cost off by > 0.02 USD, total off by > 0.02 USD, not json."""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = {"input_tokens": 3.00, "cache_read_tokens": 0.30, "output_tokens": 15.00}

def expected():
    by = {}
    for r in csv.DictReader(open(os.path.join(HERE, "input", "usage.csv"))):
        c = sum(int(r[k]) * p / 1e6 for k, p in P.items())
        by[r["role"]] = by.get(r["role"], 0) + c
    top = max(by, key=by.get)
    return top, by[top], sum(by.values()), by

def check(text):
    m = re.search(r"\{.*\}", text.strip(), re.S)
    if not m:
        return ["not_json"]
    try:
        o = json.loads(m.group(0))
        top, topc, tot, _ = expected()
        d = []
        if o.get("top_role") != top: d.append("wrong_top_role")
        if abs(float(o.get("top_role_cost_usd", -9)) - topc) > 0.02: d.append("wrong_top_role_cost")
        if abs(float(o.get("total_cost_usd", -9)) - tot) > 0.02: d.append("wrong_total")
        return d
    except (ValueError, TypeError):
        return ["not_json"]

if __name__ == "__main__":
    d = check(open(sys.argv[1]).read())
    print(json.dumps(d)); sys.exit(1 if d else 0)
