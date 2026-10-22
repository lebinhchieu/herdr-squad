"""Checks for the receipt fixture. Planted defects: D1 sha differs in the last 2 chars,
D2 'ok' lines and a FAIL in the middle but last line is FAILED, so ok_line must be false.
clean=yes is a true value (a model that says clean=false has a defect)."""
import json, re, sys

EXPECTED = {"sha_match": False, "clean": True, "ok_line": False, "verdict": "FAIL"}

def check(text):
    """Return list of defect names (empty = all checks pass)."""
    t = text.strip()
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return ["not_json"]
    try:
        obj = json.loads(m.group(0))
    except ValueError:
        return ["not_json"]
    return [f"wrong_{k}" for k, v in EXPECTED.items() if obj.get(k) != v]

if __name__ == "__main__":
    d = check(open(sys.argv[1]).read())
    print(json.dumps(d))
    sys.exit(1 if d else 0)
