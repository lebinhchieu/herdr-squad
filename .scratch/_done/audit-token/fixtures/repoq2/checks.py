"""Checks for repoq2. Known answer: callers = src/client.py (config.load) and src/jobs.py (import alias).
Decoys: reload() in cache.py, load() only in report.py docstring, download( in util.py, scripts/ and tests/ callers
(outside src/). timeout_s = 45 (docs/notes.md holds stale 30 and 60)."""
import json, re, sys
CALLERS = {"src/client.py", "src/jobs.py"}

def check(text):
    m = re.search(r"\{.*\}", text.strip(), re.S)
    if not m:
        return ["not_json"]
    try:
        o = json.loads(m.group(0))
        got = set(o.get("callers", []))
        d = []
        if got - CALLERS: d.append("false_caller")
        if CALLERS - got: d.append("missed_caller")
        if o.get("timeout_s") != 45: d.append("wrong_timeout")
        return d
    except (ValueError, TypeError):
        return ["not_json"]

if __name__ == "__main__":
    d = check(open(sys.argv[1]).read())
    print(json.dumps(d)); sys.exit(1 if d else 0)
