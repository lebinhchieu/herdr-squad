"""squad-board --demo: the board on a temporary copy of the test fixture, every panel filled (ticket 37, decision D10).

    squad-board --demo [--port N] [--no-open]

Copies `tests/fixtures/board` (times shifted to now), gives the goal `alpha` and the scope `checkout` the content of the
fixture's task-rich scope, points HOME, USERPROFILE and CLAUDE_CONFIG_DIR into the copy, drops the SQUAD_* variables, then
calls `squadboard.main` with its existing flags. The copy is removed when the board stops (Ctrl-C, SIGTERM, any error).
Nothing real is read and nothing outside the copy is written. The committed fixture is never edited.
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
TESTS = BIN.parent / "tests"
GOAL, SOURCE, TARGET = "alpha", "checkout", "alpha-api"  # open on GOAL; TARGET gets the content of SOURCE
TICKETS_DIR = ("checkout-tasks", "alpha-api-tasks")
ENV_DROP = ("SQUAD_DIR", "SQUAD_NAME", "SQUAD_SCOPE", "SQUAD_ROLE")
REFUSED, ERROR = 2, 1
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
HELP_LINE = "--demo: open the board on sample data (a temporary copy of the test fixture); only --port and --no-open go with it"


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _rename(text):
    return text.replace(SOURCE, TARGET)


def _herdr_clone(agents, template, name, status, n):
    c = json.loads(json.dumps(template))
    c.update(name=name, terminal_title=name, terminal_title_stripped=name, agent_status=status,
             pane_id="w1:p%d" % n, terminal_id="term_demo%02d" % n)
    c["agent_session"] = dict(c.get("agent_session") or {}, value="00000000-0000-4000-8000-%012d" % n)
    agents.append(c)


def _roster_rows(path):
    """-> [(agent, session)] of a roster table."""
    out = []
    for line in _read(path).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[0].startswith("fix-"):
            out.append((cells[0], cells[5]))
    return out


def _transcript(config_dir, template, agent, session, old_agent="fix-qaw-checkout", old_session="s-qaw"):
    """A transcript for a roster session that has none: the template's records under this agent and session."""
    text = _read(template).replace(old_agent, agent).replace('"%s"' % old_session, '"%s"' % session)
    _write(Path(config_dir) / "projects" / "-fixture-repo" / (session + ".jsonl"), text)


def extend(fx, now=None):
    """Give the scopes of goal `alpha` and the scope `checkout` what a full page needs. Copy only; nothing real is read."""
    now = now or datetime.now(timezone.utc)
    squad, repo, cfg = Path(fx.squad), Path(fx.repo), Path(fx.config_dir)
    scopes = squad / "scopes"
    src, dst, questions = (scopes / n for n in (SOURCE, TARGET, "questions"))
    for f in ("escalations.md", "inbox.jsonl"):  # an open question (and an answered one) in both scopes
        for d in (src, dst):
            shutil.copy2(questions / f, d / f)
    seen = (now - timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%SZ")  # the fixture stamp is a fixed date: make E1 and E2 minutes old
    for d in (src, dst, questions):  # the temp copy of the `questions` scope too (the fixture file stays unedited)
        lines = [json.loads(l) for l in _read(d / "inbox.jsonl").splitlines() if l.strip()]
        for rec in lines:
            if rec.get("ts", "").startswith("2026-11-03"):
                rec["ts"] = seen
        _write(d / "inbox.jsonl", "".join(json.dumps(r) + "\n" for r in lines))
    _write(dst / "messages.jsonl", _rename(_read(src / "messages.jsonl")))
    roster = _read(src / "roster.md")
    _write(src / "roster.md", roster.replace("s-qab-missing", "s-qab"))
    _write(dst / "roster.md", _rename(roster).replace("| s-mgr |", "| s-mgr-api |").replace("| s-qaw |", "| s-qaw-api |")
           .replace("s-qab-missing", "s-qab-api"))
    _write(dst / "scope.md", _read(dst / "scope.md").replace("\n## Constraints", "tickets: %s\n\n## Constraints" % TICKETS_DIR[1], 1))
    shutil.copytree(repo / ".scratch" / TICKETS_DIR[0], repo / ".scratch" / TICKETS_DIR[1], dirs_exist_ok=True)
    for s in (SOURCE, TARGET):  # something of every kind for the Files panel
        h = scopes / s
        for rel, body in (("ui-design/design-v1.md", "# Design v1\nSample design note.\n"),
                          ("ui-design/proto-v1.html", "<!doctype html><meta charset=utf-8><title>Sample prototype</title><p>Sample prototype.</p>\n"),
                          ("promote.md", "# Promotion\nSample promotion note.\n"), ("evidence/qa-w.md", "# QA whitebox\nSample evidence.\n")):
            (h / rel).parent.mkdir(parents=True, exist_ok=True)
            _write(h / rel, body)
    _write(squad / "goals" / GOAL / "shared" / "notes.md", "# Notes\nSample shared notes of the goal.\n")
    stamp = (now - timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    for s in ("alpha-ui", "alpha-docs", "alpha-qa"):  # the other scopes of the goal: one ticket and one message each
        h, tdir = scopes / s, repo / ".scratch" / (s + "-tasks")
        shutil.copytree(repo / ".scratch" / TICKETS_DIR[0] / "issues", tdir / "issues", ignore=lambda d, names: [n for n in names if not n.startswith("02-")],
                        dirs_exist_ok=True)
        _write(h / "scope.md", _read(h / "scope.md").replace("\n## Constraints", "tickets: %s\n\n## Constraints" % tdir.name, 1))
        rec = {"ts": stamp, "msg_id": "d-" + s, "from": "fix-mgr-" + s, "to": "fix-dev-02", "type": "STATUS", "task": "02",
               "text": "STATUS 02: start", "iteration": 1}
        _write(h / "messages.jsonl", json.dumps(rec) + "\n")
    env = {**os.environ, **GIT_ENV}
    refs = subprocess.run(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/squad/fix/%s/" % SOURCE], cwd=str(repo),
                          capture_output=True, text=True, encoding="utf-8", check=True, env=env).stdout.split()
    for b in refs:  # the branches of the checkout tasks, again under the new scope (same commits: same merged state)
        subprocess.run(["git", "branch", _rename(b), b], cwd=str(repo), capture_output=True, check=True, env=env)
    path = Path(fx.herdr_json)  # herdr agents for every roster name of the goal
    obj = json.loads(_read(path))
    agents = obj["result"]["agents"]
    template = agents[0]
    for i, a in enumerate([x for x in agents if SOURCE in str(x.get("name"))]):
        _herdr_clone(agents, a, _rename(a["name"]), a.get("agent_status"), 20 + i)
    for i, (n, st) in enumerate((("fix-mgr-alpha", "working"), ("fix-mgr-alpha-ui", "working"), ("fix-mgr-alpha-docs", "idle"),
                                 ("fix-mgr-alpha-qa", "idle"))):
        _herdr_clone(agents, template, n, st, 30 + i)
    rosters = [squad / "goals" / GOAL / "roster.md"] + [scopes / s / "roster.md" for s in (SOURCE, TARGET, "alpha-ui", "alpha-docs", "alpha-qa")]
    for r in rosters:  # a live roster name herdr does not list would read "unknown": list it as idle
        for agent, _ in _roster_rows(r):
            if agent not in {x.get("name") for x in agents} and "| retired |" not in "".join(
                    l for l in _read(r).splitlines() if l.lstrip("| ").startswith(agent)):
                _herdr_clone(agents, template, agent, "idle", 40 + len(agents))
    _write(path, json.dumps(obj, indent=1) + "\n")
    proj = cfg / "projects" / "-fixture-repo"
    for old, new in (("s-mgr", "s-mgr-api"), ("s-qaw", "s-qaw-api")):  # alpha-api keeps the night gaps of checkout's manager
        agent = _read(proj / (old + ".jsonl")).split('"agentName": "', 1)[1].split('"', 1)[0]
        _transcript(cfg, proj / (old + ".jsonl"), _rename(agent), new, agent, old)
    template_t = proj / "s-qaw.jsonl"  # transcripts for sessions that have none
    for r in rosters:
        for agent, session in _roster_rows(r):
            if not (cfg / "projects" / "-fixture-repo" / (session + ".jsonl")).exists():
                _transcript(cfg, template_t, agent, session)
    for p in (cfg / "projects").rglob("*.jsonl"):  # last activity of an agent reads the file time: now
        os.utime(p, None)


def build(now=None):
    """-> the fixture copy (a board_fixtures.Fixture), extended; on any error the copy is removed."""
    if str(TESTS) not in sys.path:
        sys.path.insert(0, str(TESTS))
    import board_fixtures
    root = Path(tempfile.mkdtemp(prefix="squad-board-demo-"))
    try:
        fx = board_fixtures.copy_fixture(root, now=now or datetime.now(timezone.utc))
        extend(fx, now)
        return fx
    except BaseException:
        shutil.rmtree(str(root), ignore_errors=True)
        raise


def _parser():
    p = argparse.ArgumentParser(prog="squad-board --demo", allow_abbrev=False, add_help=False)
    p.add_argument("--demo", action="store_true")
    p.add_argument("--port", type=int)
    p.add_argument("--no-open", action="store_true")
    for k in ("--squad", "--goal", "--scope", "--herdr-json"):
        p.add_argument(k)
    return p


def _on_term(signum, frame):
    raise KeyboardInterrupt


def run(argv, main=None, stop=None, now=None):
    """The demo. `main` (default `squadboard.main`) and `stop` are for tests. Returns the exit code."""
    import squadboard
    main = main or squadboard.main
    try:
        args = _parser().parse_args(argv)
    except SystemExit:
        print("squad-board: --demo takes only --port N and --no-open", file=sys.stderr)
        return REFUSED
    refused = [k for k in ("squad", "goal", "scope", "herdr_json") if getattr(args, k)]
    if refused:
        print("squad-board: --demo has its own data; it cannot be combined with --%s" % refused[0].replace("_", "-"), file=sys.stderr)
        return REFUSED
    saved_env, saved_cwd = dict(os.environ), os.getcwd()
    old_term = None
    fx = None
    try:
        try:
            old_term = signal.signal(signal.SIGTERM, _on_term)  # `kill PID` cleans up like Ctrl-C
        except (ValueError, OSError):  # not the main thread
            old_term = None
        for k in ENV_DROP:  # before any git call of the copy step
            os.environ.pop(k, None)
        fx = build(now)
        cfg = Path(fx.config_dir)
        os.environ.update(HOME=str(fx.root), USERPROFILE=str(fx.root), CLAUDE_CONFIG_DIR=str(cfg),
                          GIT_CEILING_DIRECTORIES=str(fx.root.parent))  # git never looks above the copy
        os.chdir(str(fx.root))  # a call with no cwd lands in the copy, not in the real checkout
        print("demo: sample data in %s" % fx.root, flush=True)
        fwd = ["--squad", str(fx.squad), "--goal", GOAL, "--herdr-json", str(fx.herdr_json)]
        if args.port is not None:
            fwd += ["--port", str(args.port)]
        if args.no_open:
            fwd.append("--no-open")
        return main(fwd, stop=stop, demo=True) if stop is not None else main(fwd, demo=True)
    except KeyboardInterrupt:
        return 0
    finally:
        os.chdir(saved_cwd)
        if fx is not None:
            shutil.rmtree(str(fx.root), ignore_errors=True)
        os.environ.clear()
        os.environ.update(saved_env)
        if old_term is not None:
            signal.signal(signal.SIGTERM, old_term)


def help_text():
    import squadboard
    return squadboard.make_parser().format_help().rstrip() + "\n\n" + HELP_LINE + "\n"


def main(argv=None):
    """Entry of `bin/squad-board`: `--demo` runs the demo, `--help` adds the demo line, else the real board."""
    import squadboard
    import squadio
    squadio.utf8_stdio()
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--demo" in argv:
        return run(argv)
    if "-h" in argv or "--help" in argv:
        sys.stdout.write(help_text())
        return 0
    return squadboard.main(argv)
