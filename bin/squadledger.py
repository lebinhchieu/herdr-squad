"""Per-task state read from messages.jsonl: last HANDIN, verdicts, returns, open BLOCKED, ASK rounds.

Row keys (always present, null when empty): task, sha, branch, handin_from, verdicts ({checker: PASS|FAIL} on
the current sha), returns, fail_messages, blocked (open BLOCKED texts), ask_rounds. Task IDs 3 and 03 are one row.

A return = a handed-in sha with at least one FAIL (two checkers failing one sha = one return).

history(records, task) lists every PASS and FAIL of one task in order, from any sender, with sha, cause and the
criteria named; it is separate from build(), so the rows above stay as they are.
"""
import json
import os
import re

SHA_RANGE = re.compile(r"\.\.([0-9a-fA-F]{6,40})")
SHA_COMMIT = re.compile(r"(?:commit|sha)[ \t:]+([0-9a-fA-F]{6,40})")
HEX = re.compile(r"\b[0-9a-f]{6,40}\b")
EVIDENCE = re.compile(r"evidence[ \t]+sha", re.I)
BRANCH = re.compile(r"branch[ \t:]+([^\s,]+)")
VERDICT_HEAD = re.compile(r"\s*(?:PASS|FAIL)[ \t]+\S+?[ \t]*:")
AC_TOKEN = re.compile(r"\bAC\d+[a-z]?\b")
CAUSE_MAX = 160


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


def parse_handin(text):
    """-> {sha, branch, evidence} of a HANDIN text: the sha of `..<sha>` or `commit|sha <sha>`, the `branch <b>`
    name, and whether it is an `evidence sha` hand-in to the Tech Lead. Each is None / False when absent."""
    text = text or ""
    b = BRANCH.search(text)
    return {"sha": _sha(text), "branch": b.group(1) if b else None, "evidence": bool(EVIDENCE.search(text))}


def _canon(sha, known):
    """Shas compare by prefix (HANDIN short, FAIL long): map to the known one."""
    sha = sha.lower()
    for k in known:
        if k.startswith(sha) or sha.startswith(k):
            return k
    return sha


def _cause(text):
    """First non-empty line after `FAIL NN:` (or `PASS NN:`), up to CAUSE_MAX characters; "" when none."""
    m = VERDICT_HEAD.match(text)
    for line in (text[m.end():] if m else "").split("\n"):
        if line.strip():
            return line.strip()[:CAUSE_MAX]
    return ""


def _acs(text):
    return list(dict.fromkeys(AC_TOKEN.findall(text)))


def _scan(records):
    tasks = {}
    for r in records:
        t, typ = key(r.get("task")), r.get("type")
        if t is None or typ is None:
            continue
        st = tasks.setdefault(t, {"task": r["task"], "handin": None, "cur": None, "verdicts": {},
                                  "fail_shas": [], "fail_messages": 0, "blocked": [], "asks": [],
                                  "history": []})
        text = r.get("text") or ""
        hand = parse_handin(text) if typ == "HANDIN" else None
        if hand and hand["evidence"]:
            continue  # evidence handin to the Tech Lead: keeps the passed sha and its verdicts
        if typ == "HANDIN":
            sha = hand["sha"]
            sha = _canon(sha, st["verdicts"]) if sha else st["cur"]
            st["cur"] = sha
            st["handin"] = {"sha": sha, "branch": hand["branch"] or (st["handin"] or {}).get("branch"),
                            "from": r.get("from"), "ts": r.get("ts")}
            if sha:  # a new sha starts with no verdicts
                st["verdicts"].setdefault(sha, {})
            st["blocked"] = [b for b in st["blocked"] if b["from"] != r.get("from")]
        elif typ in ("PASS", "FAIL"):
            named = [k for w in HEX.findall(text.lower()) for k in st["verdicts"]
                     if k.startswith(w) or w.startswith(k)]
            sha = named[0] if named else st["cur"] or "?"
            st["verdicts"].setdefault(sha, {})[r.get("from")] = typ
            st["history"].append({"sha": sha, "from": r.get("from"), "verdict": typ, "cause": _cause(text),
                                  "acs": _acs(text)})
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
    return tasks


def history(records, task):
    """-> every PASS and FAIL of `task` in message order, from any sender: [{sha, from, verdict, cause, acs}]."""
    st = _scan(records).get(key(task))
    return list(st["history"]) if st else []


def build(records):
    """-> list of per-task dicts, ordered by first appearance."""
    tasks = _scan(records)
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


def history_lines(entries):
    out = []
    for e in entries:
        line = "  %s  %s  %s: %s" % (e["sha"], e["from"], e["verdict"], e["cause"] or "-")
        if e["acs"]:
            line += "  [%s]" % ", ".join(e["acs"])
        out.append(line)
    return out


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
    records = read_records(os.path.join(home, "messages.jsonl"))
    rows = build(records)
    if task is None:
        print(json.dumps(rows, indent=2) if as_json else table(rows))
        return 0
    rows = [r for r in rows if key(r["task"]) == key(task)]
    entries = history(records, task)
    if as_json:
        for r in rows:
            r["history"] = entries
        print(json.dumps(rows, indent=2))
    else:
        print("\n".join([table(rows)] + history_lines(entries)))
    return 0
