"""Checks for the receipt2 fixture: the GOOD receipt (sha identical, clean=yes, last line OK).
Test names contain 'failure' and 'FAIL' as decoys. An always-FAIL answer scores defects here;
receipt (the bad one) catches always-PASS."""
import json, re, sys

EXPECTED = {"sha_match": True, "clean": True, "ok_line": True, "verdict": "PASS"}

def check(text):
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
