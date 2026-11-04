#!/usr/bin/env python3
"""Writes the static board fixture next to this file. Run once, commit the output; tests never run it.

    python3 tests/fixtures/board/_make_fixture.py

Squad `fix` lives in repo/, squad `other` (stands for another repo) in repo2/. The squads folder is `dot-claude/` here because git ignores `.claude/squads`; the copy helper renames it to `.claude/`. Times are fixed around
REF = 2026-11-04T10:00:00Z (tests/board_fixtures.py shifts them to "now" on request).
Placeholders {{sha:KEY}} in messages.jsonl are filled with real commit ids by tests/board_fixtures.py.
"""
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
FIX = HERE / "repo/dot-claude/squads/fix"
OTHER = HERE / "repo2/dot-claude/squads/other"


def put(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def iso(dt, ms=True):
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + (".000Z" if ms else "Z")


def ago(minutes):
    return REF - timedelta(minutes=minutes)


def scope_md(name, brief, goal="", extra=""):
    return ("# Scope: %s\n\n**%s**\n\ngoal: %s\ntouches: bin\nteam: qa-white, qa-black\nqa: full\n%s\n## Constraints\n"
            "- **Developer cap:** 3\n\n## Notes from the PO\n" % (name, brief, goal, extra))


def roster(rows):
    head = "# Roster\n| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n"
    return head + "".join("| %s | %s | %s | %s | %s | %s |\n" % r for r in rows)


# ---------------------------------------------------------------- squad fx
shutil.rmtree(HERE / "repo", ignore_errors=True)
shutil.rmtree(HERE / "repo2", ignore_errors=True)
shutil.rmtree(HERE / "claude-config", ignore_errors=True)
put(FIX / "project.md", "# Project source map\n\nFixture squad `fix` (test data, not a real squad).\n")
put(FIX / "process-log.md", "# Process log\n")

# goals: alpha has 4 scopes, beta 1, gamma 1
for g, scopes in (("alpha", ["alpha-api", "alpha-ui", "alpha-docs", "alpha-qa"]), ("beta", ["beta-core"]),
                  ("gamma", ["gamma-spike"])):
    put(FIX / "goals" / g / "goal.md",
        "# Goal: %s\n\n**Fixture goal %s.**\n\ntouches: bin\n\n## Scopes\n\n| Scope | Depends on | Status |\n|---|---|---|\n%s\n"
        "## Constraints\n- **Developer cap:** 3\n" % (g, g, "".join("| %s | - | open |\n" % s for s in scopes)))
    put(FIX / "goals" / g / "roster.md", roster([("fix-mgr-%s" % g, "manager", g, "plan", "live", "s-gm-%s" % g)]))
    put(FIX / "goals" / g / "shared/decisions.md", "# Decisions\n\n- D1: fixture decision for %s.\n" % g)
    put(FIX / "goals" / g / "escalations.md", "# Escalations\n\n| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n")
    for s in scopes:
        put(FIX / "scopes" / s / "scope.md", scope_md(s, "Scope %s of goal %s." % (s, g), g))
        put(FIX / "scopes" / s / "roster.md", roster([("fix-mgr-%s" % s, "manager", s, "plan", "live", "s-%s" % s)]))

LONG = "a-very-long-scope-name-that-keeps-going-and-going-past-the-column"
lone = {
    "checkout": "Lone scope with a task in every stage.",
    "search": "Lone scope with no messages.jsonl and no escalations.md (missing sources).",
    LONG: "Lone scope with a very long name.",
    "questions": "Lone scope with one open and one answered question.",
    "parked": "Lone scope with a parked question.",
    "broken-parked": "Lone scope whose open-questions.md cannot be parsed.",
}
for s, brief in lone.items():
    extra = "tickets: checkout-tasks\n" if s == "checkout" else ""
    put(FIX / "scopes" / s / "scope.md", scope_md(s, brief, "", extra))
    if s != "checkout":
        put(FIX / "scopes" / s / "roster.md", roster([("fix-mgr-%s" % s[:12], "manager", s, "plan", "live", "s-m-%s" % s[:8])]))

# 20 done scopes (the closed one has a report)
for i in range(1, 21):
    name = "closed-release" if i == 1 else "done-%02d" % i
    put(FIX / "scopes/_done" / name / "scope.md", scope_md(name, "Closed fixture scope %d." % i))
    put(FIX / "scopes/_done" / name / "roster.md", roster([("fix-mgr-%s" % name, "manager", name, "plan", "retired", "s-d-%d" % i)]))
put(FIX / "scopes/_done/closed-release/report/data.json",
    json.dumps({"scope": {"status": "closed"}, "generated_at": "2026-10-20T12:00:00Z"}, indent=1) + "\n")

# ---- scope checkout: tasks in every stage
CO = FIX / "scopes/checkout"
stages = [  # n, slug, ticket Status
    ("01", "todo-unassigned", "ready-for-agent"), ("02", "in-progress", "ready-for-agent"),
    ("03", "returned-3-fail", "ready-for-agent"), ("04", "blocked", "ready-for-agent"),
    ("05", "one-of-two-pass", "ready-for-agent"), ("06", "ready-for-review", "ready-for-agent"),
    ("07", "sha-changed-after-pass", "ready-for-agent"), ("08", "merged", "ready-for-agent"),
    ("09", "done", "done")]
for n, slug, st in stages:
    put(HERE / ("repo/.scratch/checkout-tasks/issues/%s-%s.md" % (n, slug)),
        "# %s %s\nStatus: %s\nIteration: 1\nBlocked by: -\n\n## Rules\n- Fixture ticket.\n" % (n, slug.replace("-", " "), st))
for n, slug in (("01", "index"), ("02", "ranking")):  # search: no tickets: line, found by scope name
    put(HERE / ("repo/.scratch/search/issues/%s-%s.md" % (n, slug)), "# %s %s\nStatus: ready-for-agent\n" % (n, slug))
put(CO / "roster.md", roster([
    ("fix-mgr-checkout", "manager", "checkout", "plan", "live", "s-mgr"),
    ("fix-dev-02", "dev", "checkout", "ticket 02", "live", "s-dev02"),
    ("fix-dev-03", "dev", "checkout", "ticket 03", "retired", "s-dev03"),
    ("fix-dev-04", "dev", "checkout", "ticket 04", "live", "s-dev04"),
    ("fix-qaw-checkout", "qa-whitebox", "checkout", "code check", "live", "s-qaw"),
    ("fix-qab-checkout", "qa-blackbox", "checkout", "behaviour check", "live", "s-qab-missing"),  # no transcript file
]))
M = []


def msg(mins, frm, to, typ, task, text):
    M.append({"ts": iso(ago(mins)), "msg_id": "m%03d" % (len(M) + 1), "from": frm, "to": to, "type": typ,
              "task": task, "text": text, "iteration": 1})


D, W, B, MG = "fix-dev-%s", "fix-qaw-checkout", "fix-qab-checkout", "fix-mgr-checkout"
msg(900, MG, D % "02", "STATUS", "02", "STATUS 02: start")
for i, (k, who) in enumerate((("03a", W), ("03b", B), ("03c", W))):
    t = 600 - i * 100
    msg(t, D % "03", W, "HANDIN", "03", "HANDIN 03: branch squad/fix/checkout/fix-dev-03, commit {{sha:%s}}, run it" % k)
    msg(t - 30, who, D % "03", "FAIL", "03", "FAIL 03: %s\nreason %d first line%s\nmore detail" % ({0: "finding", 1: "finding", 2: "finding"}[i], i + 1, " (newest)" if i == 2 else ""))
msg(300, D % "04", MG, "BLOCKED", "04", "BLOCKED 04: waiting for a PO answer on the payment provider")
msg(40, D % "05", W, "HANDIN", "05", "HANDIN 05: branch squad/fix/checkout/fix-dev-05, commit {{sha:05}}, run it")
msg(30, W, D % "05", "PASS", "05", "PASS 05: {{sha:05}} ok")
for n, passes in (("06", 2), ("07", 2), ("08", 2)):
    sha = "07a" if n == "07" else n
    msg(200, D % n, W, "HANDIN", n, "HANDIN %s: branch squad/fix/checkout/fix-dev-%s, commit {{sha:%s}}, run it" % (n, n, sha))
    msg(180, W, D % n, "PASS", n, "PASS %s: {{sha:%s}} ok" % (n, sha))
    msg(170, B, D % n, "PASS", n, "PASS %s: {{sha:%s}} ok" % (n, sha))
msg(60, MG, "board-ba", "HANDIN", "REV-8", "HANDIN features: tasks/features.md (REV-8 is a rule id, not a ticket)")
M.sort(key=lambda r: r["ts"])
put(CO / "messages.jsonl", "".join(json.dumps(r) + "\n" for r in M))
put(CO / "escalations.md", "# Escalations\n\n| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n")

# ---- scope questions: one open, one answered
Q = FIX / "scopes/questions"
rows = [
    (1, "2026-11-04", "Pick the payment provider<br>[decision] Which provider? I recommend (a).", "(a) Stripe; (b) Adyen", "(a), cheaper", "ticket 04", ""),
    (2, "2026-11-03", "Keep the old export?<br>[decision] Keep or drop?", "(a) keep; (b) drop", "(b)", "nothing", "(b) drop it"),
]
esc = "# Escalations\n\n| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n"
put(Q / "escalations.md", esc + "".join("| %d | %s | %s | %s | %s | %s | %s |\n" % r for r in rows))
import sys
sys.path.insert(0, str(HERE.parents[2] / "bin"))
sys.dont_write_bytecode = True
import squadinbox  # noqa: E402  (only to compute the real row keys)

keys = {int(r["#"]): r["key"] for r in squadinbox.project_rows((Q / "escalations.md").read_text(encoding="utf-8"))[0]}
ev = []
for r in rows:
    ev.append({"ev": "seen", "id": "E%d" % r[0], "ts": iso(ago(60 * 26), False), "key": keys[r[0]],
               "title": r[2].split("<br>")[0], "body": r[2], "options": r[3], "rec": r[4], "blocks": r[5], "date": r[1], "row_no": r[0]})
ev.append({"ev": "filled", "id": "E2", "ts": iso(ago(60 * 5), False)})
put(Q / "inbox.jsonl", "".join(json.dumps(e) + "\n" for e in ev))
put(Q / "roster.md", roster([("fix-mgr-questions", "manager", "questions", "plan", "live", "s-m-questio")]))

# ---- parked question, and a broken file
put(FIX / "scopes/parked/open-questions.md",
    "# Open questions\n\n## Q1\nStatus: parked\nParked: 2026-11-03T09:00:00Z\nShould the cart survive a login?\n"
    "Blocks: ticket 12\nFrom: E3 #2\n")
put(FIX / "scopes/broken-parked/open-questions.md",
    "# Open questions\n\n## Q1\nStatus: ???\nParked: not a time\n\n## Qx\ngarbage <<< \ufffd\nStatus parked\n## Q3\n")

# ---- transcripts (CLAUDE_CONFIG_DIR = claude-config)
PROJ = HERE / "claude-config/projects/-fixture-repo"


def rec(dt, kind, session, branch="squad/fix/checkout/x", human=False):
    base = {"timestamp": iso(dt), "cwd": "/fixture/repo", "gitBranch": branch, "isSidechain": False, "sessionId": session, "uuid": iso(dt)}
    if kind == "assistant":
        return {**base, "type": "assistant", "message": {"id": "m" + iso(dt), "model": "model-a", "content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}], "usage": {}}}
    if kind == "user":
        o = {**base, "type": "user", "message": {"role": "user", "content": "ok"}}
        if human:
            o["origin"] = {"kind": "human"}
        return o
    return {**base, "type": "system"}


def transcript(session, name, records):
    lines = [{"type": "agent-name", "agentName": name, "sessionId": session}] + records
    put(PROJ / (session + ".jsonl"), "".join(json.dumps(r) + "\n" for r in lines))


def run(start, step_min, n, session, kind_cycle=("assistant", "user")):
    return [rec(start + timedelta(minutes=step_min * i), kind_cycle[i % len(kind_cycle)], session) for i in range(n)]


u = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
# manager: a night (11.5 h gap ended by a human record = idle) and an 11.2 h gap ended by a system record (looks like work)
t_mgr = run(u(2026, 11, 2, 13, 0), 10, 13, "s-mgr")                                  # 13:00-15:00
t_mgr += [rec(u(2026, 11, 3, 2, 30), "user", "s-mgr", human=True)]                    # gap 11.5 h
t_mgr += run(u(2026, 11, 3, 2, 40), 10, 7, "s-mgr")                                   # to 03:40
t_mgr += [rec(u(2026, 11, 3, 14, 50), "system", "s-mgr")]                             # gap 11.2 h, system record
t_mgr += run(u(2026, 11, 3, 15, 0), 10, 7, "s-mgr")
transcript("s-mgr", "fix-mgr-checkout", t_mgr)
# dev-02: a 30 min gap across the US DST change (2026-11-01 06:00Z: 2:00 EDT -> 1:00 EST)
t_02 = run(u(2026, 11, 1, 5, 0), 15, 3, "s-dev02") + run(u(2026, 11, 1, 6, 15), 15, 3, "s-dev02")
transcript("s-dev02", "fix-dev-02", t_02)
transcript("s-dev03", "fix-dev-03", run(u(2026, 11, 3, 8, 0), 5, 6, "s-dev03"))
transcript("s-dev04", "fix-dev-04", run(u(2026, 11, 4, 8, 0), 5, 6, "s-dev04"))
transcript("s-qaw", "fix-qaw-checkout", run(u(2026, 11, 4, 8, 30), 5, 8, "s-qaw"))
# no transcript for s-qab-missing, on purpose

# ---- herdr recordings (shape of `herdr agent list`)
PANES = {}


def hagent(name, status, cwd="/fixture/repo"):
    n = PANES.setdefault(name, len(PANES) + 1)
    return {"agent": "claude", "agent_session": {"agent": "claude", "kind": "id", "source": "herdr:claude", "value": "00000000-0000-4000-8000-%012d" % n},
            "agent_status": status, "completion_seq": n, "cwd": cwd, "focused": False, "foreground_cwd": cwd,
            "interactive_ready": True, "name": name, "pane_id": "w1:p%d" % n, "revision": 1, "state_change_seq": n,
            "tab_id": "w1:t%d" % n, "terminal_id": "term_fixture%02d" % n, "terminal_title": name, "terminal_title_stripped": name,
            "workspace_id": "w1"}


agents = [hagent("fix-mgr-checkout", "working"), hagent("fix-dev-02", "blocked"), hagent("fix-dev-04", "idle"),
          hagent("fix-qaw-checkout", "working"), hagent("other-dev-1", "working", "/fixture/repo2")]
# fix-dev-03 (retired) and fix-qab-checkout are absent: "N retired" and an agent herdr does not know
put(HERE / "herdr/agents.json", json.dumps({"id": "cli:agent:list", "result": {"agents": agents}}, indent=1) + "\n")
put(HERE / "herdr/not-running.json", json.dumps({"id": "cli:agent:list", "error": {
    "code": "server_not_running", "message": "no herdr server is running at /tmp/nonexistent.sock; run `herdr` to start or attach it"}}) + "\n")

# ---- second squad (another repo)
put(OTHER / "project.md", "# Project source map\n\nFixture squad `other`.\n")
put(OTHER / "scopes/other-scope/scope.md", scope_md("other-scope", "The one scope of the second squad."))
put(OTHER / "scopes/other-scope/roster.md", roster([("other-dev-1", "dev", "other-scope", "ticket 01", "live", "s-o1")]))
print("fixture written under", HERE)
