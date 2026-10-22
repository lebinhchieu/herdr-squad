"""Per-task state read from messages.jsonl: last HANDIN, verdicts, returns, open BLOCKED, ASK rounds.

Row keys (always present, null when empty): task, sha, branch, handin_from, verdicts ({checker: PASS|FAIL} on
the current sha), returns, fail_messages, blocked (open BLOCKED texts), ask_rounds. Task IDs 3 and 03 are one row.

A return = a handed-in sha with at least one FAIL (two checkers failing one sha = one return).
"""
import json
import os
import re

SHA_RANGE = re.compile(r"\.\.([0-9a-fA-F]{6,40})")
SHA_COMMIT = re.compile(r"(?:commit|sha)[ \t:]+([0-9a-fA-F]{6,40})")
HEX = re.compile(r"\b[0-9a-f]{6,40}\b")
BRANCH = re.compile(r"branch[ \t:]+([^\s,]+)")


def home_dir(arg=None, env=None):
    env = os.environ if env is None else env
    return arg or env.get("SCOPE_DIR") or env.get("GOAL_DIR") or env.get("SQUAD_DIR")


def key(task):
    """03 and 3 are one task; other IDs compare as written."""
    if task is None:
        return None
    return task.lstrip("0") or "0" if task.isdigit() else task


def read_records(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except OSError:
        pass
    return out


def _sha(text):
    m = SHA_RANGE.search(text) or SHA_COMMIT.search(text)
    return m.group(1) if m else None


def _canon(sha, known):
    """Shas compare by prefix (HANDIN short, FAIL long): map to the known one."""
    sha = sha.lower()
    for k in known:
        if k.startswith(sha) or sha.startswith(k):
            return k
    return sha


def build(records):
    """-> list of per-task dicts, ordered by first appearance."""
    tasks = {}
    for r in records:
        t, typ = key(r.get("task")), r.get("type")
        if t is None or typ is None:
            continue
        st = tasks.setdefault(t, {"task": r["task"], "handin": None, "cur": None, "verdicts": {},
                                  "fail_shas": [], "fail_messages": 0, "blocked": [], "asks": []})
        text = r.get("text") or ""
        if typ == "HANDIN":
            sha = _sha(text)
            sha = _canon(sha, st["verdicts"]) if sha else st["cur"]
            b = BRANCH.search(text)
            st["cur"] = sha
            st["handin"] = {"sha": sha, "branch": b.group(1) if b else (st["handin"] or {}).get("branch"),
                            "from": r.get("from"), "ts": r.get("ts")}
            if sha:  # a new sha starts with no verdicts
                st["verdicts"].setdefault(sha, {})
            st["blocked"] = [b for b in st["blocked"] if b["from"] != r.get("from")]
        elif typ in ("PASS", "FAIL"):
            named = [k for w in HEX.findall(text.lower()) for k in st["verdicts"]
                     if k.startswith(w) or w.startswith(k)]
            sha = named[0] if named else st["cur"] or "?"
            st["verdicts"].setdefault(sha, {})[r.get("from")] = typ
            if typ == "FAIL":
                st["fail_messages"] += 1
                if sha not in st["fail_shas"]:
                    st["fail_shas"].append(sha)
        elif typ == "BLOCKED":
            st["blocked"].append({"from": r.get("from"), "ts": r.get("ts"), "text": text})
        elif typ == "DECISION":  # a ruling closes the blocks and the ASK thread
            st["blocked"] = []
            st["asks"] = []
        if typ == "ASK":
            st["asks"].append(frozenset((r.get("from"), r.get("to"))))
    result = []
    for st in tasks.values():
        rounds = 0
        if st["asks"]:
            last = st["asks"][-1]
            for pair in reversed(st["asks"]):
                if pair != last:
                    break
                rounds += 1
        cur, h = st["cur"], st["handin"] or {}
        v = st["verdicts"].get(cur, {}) if cur else {}
        result.append({
            "task": st["task"],
            "sha": cur,
            "branch": h.get("branch"),
            "handin_from": h.get("from"),
            "verdicts": v or None,
            "returns": len(st["fail_shas"]),
            "fail_messages": st["fail_messages"],
            "blocked": [b["text"] for b in st["blocked"]] or None,
            "ask_rounds": rounds,
        })
    return result


def table(rows):
    if not rows:
        return "no tasks in messages.jsonl"
    head = ["task", "sha", "branch", "verdicts", "returns", "blocked", "ask rounds"]
    body = []
    for r in rows:
        v = ", ".join("%s %s" % (c, x) for c, x in sorted((r["verdicts"] or {}).items())) or "-"
        body.append([str(r["task"]), r["sha"] or "-", r["branch"] or "-", v, str(r["returns"]),
                     str(len(r["blocked"] or [])), str(r["ask_rounds"])])
    widths = [max(len(x[i]) for x in [head] + body) for i in range(len(head))]
    return "\n".join("  ".join(c.ljust(w) for c, w in zip(line, widths)).rstrip() for line in [head] + body)


def run(argv):
    home, task, as_json = None, None, False
    it = iter(argv)
    for a in it:
        if a == "--home":
            home = next(it, None)
        elif a == "--task":
            task = next(it, None)
        elif a == "--json":
            as_json = True
        else:
            print("usage: squad-ledger [--home <dir>] [--task NN] [--json]")
            return 2
    home = home_dir(home)
    if not home:
        print("squad-ledger: no --home and no $SCOPE_DIR / $GOAL_DIR / $SQUAD_DIR")
        return 2
    rows = build(read_records(os.path.join(home, "messages.jsonl")))
    if task is not None:
        rows = [r for r in rows if key(r["task"]) == key(task)]
    print(json.dumps(rows, indent=2) if as_json else table(rows))
    return 0
