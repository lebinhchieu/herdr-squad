"""squad task state: ONE writer for the events of a ticket (design: task-claim-gates tasks/design.md s2-s4).

State is not written into the ticket file. Events are appended to `<squad dir>/task-events/<slug>.jsonl`, one file
per ticket folder (slug = the scope's `tickets:` folder, else the scope name). Words are derived at read time
(`fold`, `word`); the store holds facts only: claim, handin, pass, fail, blocked, decision, merged.

Gates warn, never block: `record` always writes the event and returns the warnings W1-W8 (also saved in the event
as `warn`). Nothing here raises to a hook. Stdlib only; `fcntl` is optional (mkdir lock when it is missing).
"""
import contextlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None

import squadledger
import squadrules
import squadtickets

EVENTS = ("claim", "handin", "pass", "fail", "blocked", "decision", "merged")
QA_ROLES = ("qa-whitebox", "qa-blackbox")
CONFIRM_ROLES = ("manager", "team-lead")
# The ticket `Status:` label table (states.md s5): read for a ticket with no events, never written.
LABELS = {"needs-triage": "todo", "needs-info": "todo", "ready-for-agent": "todo", "ready-for-human": "todo",
          "claimed": "in progress", "done": "passed", "wontfix": "wontfix"}
TICKET_FILE = re.compile(r"^(?:ticket-)?(\d+)(?:-.*)?\.md$")
HEX = re.compile(r"\b[0-9a-f]{6,40}\b")


# ---- where things are ----------------------------------------------------------------------------------------

def slug_of(scope_home):
    """The ticket folder slug: `tickets:` line of scope.md, else the scope (or squad) folder name. Same rule as the board."""
    return squadtickets.declared_folder(scope_home) or Path(str(scope_home)).name


def squad_dir_of(scope_home):
    p = Path(str(scope_home))
    return p.parent.parent if p.parent.name in ("scopes", "goals") else p


def store_path(squad_dir, slug):
    return Path(str(squad_dir)) / "task-events" / (slug + ".jsonl")


def read_events(squad_dir, slug):
    return squadledger.read_records(store_path(squad_dir, slug))


def _now():
    t = datetime.now(timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (t.microsecond // 1000)


def _same_sha(a, b):
    a, b = (a or "").lower(), (b or "").lower()
    return len(a) >= 6 and len(b) >= 6 and (a.startswith(b) or b.startswith(a))


# ---- checkers (D7) -------------------------------------------------------------------------------------------

def _roster_rows(scope_home):
    """-> [(agent, role, status)] of roster.md table rows."""
    try:
        text = (Path(str(scope_home)) / "roster.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and len(cells) >= 5 and cells[0] not in ("Agent", "---") \
                and not set(cells[0]) <= set("-: "):
            rows.append((cells[0], cells[1], cells[4].lower()))
    return rows


def _team_tokens(scope_home):
    try:
        text = (Path(str(scope_home)) / "scope.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        m = re.match(r"^team:[ \t]*(.*?)[ \t]*(?:\([^)]*\))?[ \t]*$", line)
        if m:
            try:
                return squadrules.parse_team(m.group(1))
            except ValueError:
                return None
    return None


def role_of(scope_home, name):
    """Role of the message sender: the roster row of `name`; else $SQUAD_ROLE when `name` is this process's agent;
    else "" (unknown). The hook runs in the sender's pane, but a manual `from-message` run must not borrow its role."""
    for agent, role, _ in _roster_rows(scope_home):
        if agent == name:
            return role
    return os.environ.get("SQUAD_ROLE", "") if name and name == os.environ.get("SQUAD_NAME") else ""


def checkers(scope_home):
    """-> {"qa": [agent...], "confirmer": "Manager" | "Team Lead"}. M = len(qa) + 1, never 0."""
    rows = [r for r in _roster_rows(scope_home) if not r[2].startswith("retired")]
    qa = [a for a, role, _ in rows if role in QA_ROLES]
    team = _team_tokens(scope_home)
    lead = ("team-lead" in team) if team is not None else any(role == "team-lead" for _, role, _ in rows)
    return {"qa": qa, "confirmer": "Team Lead" if lead else "Manager"}


def slots(chk):
    """The verdict slots of M: each QA agent and `confirmer`."""
    return list(chk["qa"]) + ["confirmer"]


def is_passed(state, chk):
    v = (state or {}).get("verdicts") or {}
    return bool(state) and state.get("sha") is not None and all(v.get(s) == "PASS" for s in slots(chk))


# ---- fold (pure) ---------------------------------------------------------------------------------------------

def fold(events):
    """-> {key(task): State}. Same rules as squadledger.build, so old and new data agree."""
    acc = {}
    for e in events:
        t = squadledger.key(e.get("task"))
        if t is None or e.get("ev") not in EVENTS:
            continue
        a = acc.setdefault(t, {"task": e["task"], "owner": None, "claimed": False, "scope": None, "branch": None,
                               "cur": None, "verdicts": {}, "fail_shas": [], "blocked": [], "handin_ts": None,
                               "claim_ts": None, "merged_ts": None, "merged_sha": None, "updated_ts": None,
                               "warns": []})
        ev, ts, by = e["ev"], e.get("ts"), e.get("by")
        if ts and (a["updated_ts"] is None or ts > a["updated_ts"]):
            a["updated_ts"] = ts
        if e.get("scope") and ev in ("claim", "handin"):
            a["scope"] = e["scope"]
        if e.get("branch") and ev in ("claim", "handin"):
            a["branch"] = e["branch"]
        if ev == "claim":
            a["owner"], a["claimed"], a["claim_ts"] = by, True, ts
        elif ev == "handin":
            if a["owner"] is None:
                a["owner"] = by
            sha = e.get("sha")
            if sha:
                known = list(a["verdicts"])
                a["cur"] = next((k for k in known if _same_sha(k, sha)), sha.lower())
                a["verdicts"].setdefault(a["cur"], {})
            a["handin_ts"] = ts
            a["blocked"] = [b for b in a["blocked"] if b["by"] != by]
            a["warns"] = []
        elif ev in ("pass", "fail"):
            sha = e.get("sha")
            sha = next((k for k in a["verdicts"] if sha and _same_sha(k, sha)), None) or a["cur"] or "?"
            a["verdicts"].setdefault(sha, {})[e.get("slot") or by] = ev.upper()
            if ev == "fail" and sha not in a["fail_shas"]:
                a["fail_shas"].append(sha)
        elif ev == "blocked":
            a["blocked"].append({"by": by, "text": e.get("why") or ""})
        elif ev == "decision":
            a["blocked"] = []
        elif ev == "merged":
            a["merged_ts"], a["merged_sha"] = ts, e.get("sha")
            if e.get("branch"):
                a["branch"] = e["branch"]
        for w in e.get("warn") or []:
            if w not in a["warns"]:
                a["warns"].append(w)
    out = {}
    for t, a in acc.items():
        cur = a["cur"]
        out[t] = {"task": a["task"], "owner": a["owner"], "claimed": a["claimed"], "scope": a["scope"],
                  "branch": a["branch"], "sha": cur, "verdicts": dict(a["verdicts"].get(cur, {})) if cur else {},
                  "returns": len(a["fail_shas"]), "blocked_open": [b["text"] for b in a["blocked"]],
                  "handin_ts": a["handin_ts"], "claim_ts": a["claim_ts"], "merged_ts": a["merged_ts"],
                  "merged_sha": a["merged_sha"], "updated_ts": a["updated_ts"], "warns": a["warns"][:3]}
    return out


def word(state, chk, blocked_by_open=(), ticket_status=""):
    """Board word of one ticket (states.md s2 precedence, first match). No git here: `sha changed after PASS` and
    `ready for review` need the branch tip and stay with the board reader."""
    if not state:
        if ticket_status == "wontfix":
            return "wontfix"
        if ticket_status in ("claimed", "done"):
            return LABELS[ticket_status]
        return "blocked" if blocked_by_open else "todo"
    if state["merged_ts"]:
        return "merged"
    if is_passed(state, chk):
        return "passed"
    if state["blocked_open"]:
        return "blocked"
    v = state["verdicts"]
    if state["sha"] and any(x == "FAIL" for x in v.values()):
        return "returned"
    if state["sha"]:
        n = sum(1 for s in slots(chk) if v.get(s) == "PASS")
        return "checking, %d of %d PASS" % (n, len(slots(chk)))
    if state["claimed"] or state["owner"]:
        return "in progress"
    return "blocked" if blocked_by_open else "todo"


# ---- the ticket file: Blocked by, Status -----------------------------------------------------------------------

def ticket_text(scope_home, repo_root, nn):
    """Text of ticket NN: the merged file in `.scratch/<slug>/issues/`, else a draft in `<scope>/tasks/`."""
    home = Path(str(scope_home))
    if not str(nn).isdigit():
        return None
    root = repo_root or squadtickets._repo_of(home)
    dirs = []
    if root:
        dirs.append(Path(str(root)) / ".scratch" / slug_of(home) / "issues")
    dirs += [home / "tasks", home / "tasks" / "issues"]
    for d in dirs:
        try:
            files = sorted(d.iterdir())
        except OSError:
            continue
        for f in files:
            m = TICKET_FILE.match(f.name)
            if m and f.is_file() and int(m.group(1)) == int(nn) and not squadtickets.NOT_TASK.search(f.name):
                text = squadtickets._text(f)
                if text is not None:
                    return text
    return None


def parse_blocked_by(text):
    for line in (text or "").splitlines()[:30]:
        m = re.match(r"^Blocked by:[ \t]*(.*)$", line, re.I)
        if m:
            return re.findall(r"\d+", m.group(1))
    return []


def blocked_by(scope_home, repo_root, nn):
    return parse_blocked_by(ticket_text(scope_home, repo_root, nn))


def open_blockers(ids, states, checkers_by_id):
    """The ids that are neither passed nor merged. `checkers_by_id`: {id: checkers dict}."""
    out = []
    for i in ids:
        st = (states or {}).get(squadledger.key(i))
        if not (st and (st["merged_ts"] or is_passed(st, checkers_by_id[i]))):
            out.append(i)
    return out


# ---- warnings (pure) -------------------------------------------------------------------------------------------

def check(event, before, ctx):
    """-> [warning]. `before`: the folded state of the task (None when no events). ctx: checkers (dict),
    open_blockers (ids), ticket_status (str)."""
    ev, w = event["ev"], []
    before = before or {}
    chk = ctx.get("checkers") or {"qa": [], "confirmer": "Manager"}
    v = before.get("verdicts") or {}
    if ev == "claim":
        for i in ctx.get("open_blockers") or []:
            w.append("W1 started while ticket %s is not yet passed" % i)
        if before.get("owner") and before["owner"] != event.get("by"):
            w.append("W2 already owned by %s" % before["owner"])
        if ctx.get("ticket_status") == "wontfix":
            w.append("W8 ticket is wontfix")
    elif ev == "handin" and not before.get("claimed"):
        w.append("W3 handed in without a claim; owner taken from sender")
    elif ev == "pass":
        if event.get("slot") is None:
            w.append("W4 not a checker; not counted")
        else:
            sha = event.get("sha")
            if not before.get("sha") or (sha and not _same_sha(sha, before["sha"])):
                w.append("W5 PASS on a sha that is not the current hand-in")
            if event["slot"] == "confirmer":
                got = sum(1 for s in chk["qa"] if v.get(s) == "PASS")
                if got < len(chk["qa"]):
                    w.append("W6 confirmed early; %d of %d checkers PASS" % (got, len(chk["qa"])))
    elif ev == "merged" and not (before.get("merged_ts") or is_passed(before, chk)):
        w.append("W7 merged without every checker PASS")
    return w


# ---- write -----------------------------------------------------------------------------------------------------

@contextlib.contextmanager
def _locked(path):
    path = Path(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = str(path) + ".lock"
    if fcntl is not None:
        with open(lock, "a", encoding="utf-8", newline="\n") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        return
    held = False
    for _ in range(250):  # 5 s; a lock left by a killed writer is then broken (ADR 0011 D3b)
        try:
            os.mkdir(lock + ".d")
            held = True
            break
        except OSError:
            time.sleep(0.02)
    if not held:
        with contextlib.suppress(OSError):
            os.rmdir(lock + ".d")
    try:
        yield
    finally:
        if held:
            with contextlib.suppress(OSError):
                os.rmdir(lock + ".d")


def _event(scope_home, nn, ev, fields):
    f = {k: v for k, v in fields.items() if v is not None}
    return {"v": 1, "ts": f.get("ts") or _now(), "task": nn, "ev": ev, "by": f.get("by") or os.environ.get("SQUAD_NAME") or "manual",
            "role": f.get("role") if f.get("role") is not None else os.environ.get("SQUAD_ROLE", ""),
            "scope": f.get("scope") or Path(str(scope_home)).name, "sha": f.get("sha"), "branch": f.get("branch"),
            "slot": f.get("slot"), "why": (f["why"].splitlines() or [""])[0][:200] if f.get("why") else None,
            "warn": [], "msg_id": f.get("msg_id")}


def record(scope_home, nn, ev, **fields):
    """Lock, check, append. -> (event or None, [warning]). Never raises; a write error goes to stderr."""
    try:
        return _record(scope_home, nn, ev, fields)
    except Exception as exc:  # a hook must never fail
        print("squad-task: not recorded: %s" % exc, file=sys.stderr)
        return None, []


def _record(scope_home, nn, ev, fields):
    sd, slug = squad_dir_of(scope_home), slug_of(scope_home)
    path = store_path(sd, slug)
    event = _event(scope_home, nn, ev, fields)
    if ev == "pass" and event["slot"] is None:
        return None, check(event, None, {})  # W4: not counted, nothing written, no store touched
    with _locked(path):
        states = fold(read_events(sd, slug))
        before = states.get(squadledger.key(nn))
        chk = checkers(scope_home)
        if ev == "merged" and not (event["sha"] or event["branch"]):
            event["branch"] = (before or {}).get("branch")
        ctx = {"checkers": chk, "ticket_status": ""}
        if ev == "claim":
            text = ticket_text(scope_home, None, nn)
            ctx["ticket_status"] = squadtickets.status_of(text)
            ids = parse_blocked_by(text)
            ctx["open_blockers"] = open_blockers(ids, states, {i: chk for i in ids})
        warns = check(event, before, ctx)
        event["warn"] = warns
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event, warns


# ---- the hook entry --------------------------------------------------------------------------------------------

def _named_sha(text, events):
    """The hand-in sha a verdict text names (shas compare by prefix), else None (= the current one)."""
    known = [e["sha"] for e in events if e.get("ev") == "handin" and e.get("sha")]
    for w in HEX.findall((text or "").lower()):
        for k in known:
            if _same_sha(k, w):
                return k
    for w in HEX.findall((text or "").lower()):  # a sha no hand-in has: check() warns W5
        if re.search(r"\d", w):
            return w
    return None


def from_message(scope_home, rec, role=None):
    """One messages.jsonl record -> events (design 4.1). -> [warning]. ASK, ANSWER, STATUS, evidence hand-ins and
    records with no task id write nothing."""
    typ, nn, text = rec.get("type"), rec.get("task"), rec.get("text") or ""
    if not isinstance(nn, str) or not isinstance(text, str):
        return []
    if not nn or typ not in ("HANDIN", "PASS", "FAIL", "BLOCKED", "DECISION"):
        return []
    role = role_of(scope_home, rec.get("from")) if role is None else role
    base = {"by": rec.get("from"), "role": role, "ts": rec.get("ts"), "msg_id": rec.get("msg_id")}
    if typ == "HANDIN":
        h = squadledger.parse_handin(text)
        if h["evidence"] or not h["sha"]:
            return []
        return record(scope_home, nn, "handin", sha=h["sha"], branch=h["branch"], **base)[1]
    if typ == "DECISION":
        return record(scope_home, nn, "decision", **base)[1]
    if typ == "BLOCKED":
        return record(scope_home, nn, "blocked", why=text, **base)[1]
    slot = rec.get("from") if role in QA_ROLES else "confirmer" if role in CONFIRM_ROLES else None
    if typ == "FAIL" and slot is None:
        return []
    sd = squad_dir_of(scope_home)
    sha = _named_sha(text, read_events(sd, slug_of(scope_home)))
    return record(scope_home, nn, typ.lower(), sha=sha, slot=slot, **base)[1]


def hook_output(warnings):
    """The PostToolUse JSON for squad-log-message, or '' when there is nothing to say."""
    if not warnings:
        return ""
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                              "additionalContext": "task state warning: " + "; ".join(warnings)}})


# ---- CLI -------------------------------------------------------------------------------------------------------

USAGE = """usage: squad-task claim   NN --owner AGENT [--branch B]
       squad-task handin  NN --sha S [--branch B] [--by AGENT]
       squad-task pass|passed|fail NN [--sha S] [--slot SLOT]
       squad-task blocked NN [--why TEXT]
       squad-task merged  NN [--sha S] [--branch B]
       squad-task show    [NN] [--json]
       squad-task from-message            (one messages.jsonl record on stdin)
all take [--scope-home DIR] (default $SCOPE_DIR). Exit 0 ok or warning, 2 usage error."""
OPTS = {"--owner": "owner", "--branch": "branch", "--sha": "sha", "--by": "by", "--slot": "slot", "--why": "why",
        "--scope-home": "scope_home"}


def _parse(argv):
    args, opts, flags = [], {}, set()
    it = iter(argv)
    for a in it:
        if a in OPTS:
            v = next(it, None)
            if v is None:
                raise ValueError("%s needs a value" % a)
            opts[OPTS[a]] = v
        elif a == "--json":
            flags.add("json")
        elif a.startswith("--"):
            raise ValueError("unknown option %s" % a)
        else:
            args.append(a)
    return args, opts, flags


def _show(scope_home, nn, as_json):
    sd, slug = squad_dir_of(scope_home), slug_of(scope_home)
    states, chk = fold(read_events(sd, slug)), checkers(scope_home)
    keys = [squadledger.key(nn)] if nn else list(states)
    rows = []
    for k in keys:
        st = states.get(k)
        text = ticket_text(scope_home, None, nn or (st or {}).get("task") or k)
        ids = parse_blocked_by(text)
        rows.append({"task": (st or {}).get("task") or nn or k, "word": word(
            st, chk, open_blockers(ids, states, {i: chk for i in ids}), squadtickets.status_of(text)),
            "state": st})
    if as_json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            st = r["state"] or {}
            print("%s  %s  owner %s  sha %s  returns %s  %s" % (
                r["task"], r["word"], st.get("owner") or "-", st.get("sha") or "-", st.get("returns", 0),
                "; ".join(st.get("warns") or [])))
    return 0


def run(argv):
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    try:
        args, opts, flags = _parse(rest)
        if cmd not in ("claim", "handin", "pass", "passed", "fail", "blocked", "merged", "show", "from-message"):
            raise ValueError("unknown command %r" % cmd)
        home = opts.get("scope_home") or os.environ.get("SCOPE_DIR")
        if not home:
            raise ValueError("no --scope-home and no $SCOPE_DIR")
        if cmd == "from-message":
            try:
                rec = json.loads(sys.stdin.read())
            except ValueError:
                return 0  # a hook entry never fails
            out = hook_output(from_message(home, rec) if isinstance(rec, dict) else [])
            if out:
                print(out)
            return 0
        if cmd == "show":
            if len(args) > 1:
                raise ValueError("show takes at most one task")
            return _show(home, args[0] if args else None, "json" in flags)
        if len(args) != 1 or not args[0].isdigit():
            raise ValueError("%s needs one ticket number (digits), got %r" % (cmd, " ".join(args)))
        nn = args[0]
        if cmd == "claim" and not opts.get("owner"):
            raise ValueError("claim needs --owner")
        if cmd == "handin" and not opts.get("sha"):
            raise ValueError("handin needs --sha")
        ev = {"passed": "pass"}.get(cmd, cmd)
        if ev == "claim":
            opts["by"] = opts.pop("owner")
        if ev == "pass" and "slot" not in opts:  # a manual PASS counts as the sender's own role would
            role = os.environ.get("SQUAD_ROLE", "")
            opts["slot"] = (opts.get("by") or os.environ.get("SQUAD_NAME") or "manual") if role in QA_ROLES else \
                "confirmer" if role in CONFIRM_ROLES or not role else None
        elif ev == "fail":
            opts.setdefault("slot", "confirmer")
        if ev == "merged" and not (opts.get("sha") or opts.get("branch")) and not (
                fold(read_events(squad_dir_of(home), slug_of(home))).get(squadledger.key(nn)) or {}).get("branch"):
            raise ValueError("merged needs --sha or --branch (no branch on record)")
        opts.pop("scope_home", None)
        event, warns = record(home, nn, ev, **opts)
    except ValueError as exc:
        print("squad-task: %s\n%s" % (exc, USAGE), file=sys.stderr)
        return 2
    if event is None and not warns:
        return 1
    print(("recorded %s %s" % (ev, nn)) if event else "not recorded")
    for w in warns:
        print("warning: " + w)
    return 0
