"""Copies the committed board fixture (tests/fixtures/board) to a temp dir and returns its paths.

    fx = board_fixtures.copy_fixture()            # fx.squad, fx.repo, fx.herdr_json, fx.herdr_down, fx.config_dir, fx.other_squad
    fx = board_fixtures.copy_fixture(now=dt)      # message and inbox times shifted so that REF maps to `now`
    board_fixtures.cleanup(fx)                    # the caller removes the copy (tearDown / atexit)
    python3 tests/board_fixtures.py [--now] [--dir D]          # for QA: print the paths of a fresh copy
    python3 tests/board_fixtures.py append-message DIR --scope checkout --type FAIL --task 03 --sender fix-qaw-checkout --text "FAIL 03: x"

No board logic here. Git branches (the fixture folder cannot hold a .git) are built in the copy: they give
`passed`, `sha changed after PASS` and `merged` their real commit ids, put into {{sha:KEY}} in messages.jsonl.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "board"
REF = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)  # the fixture clock: age words are measured against it
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
# branch -> keys of its commits (the key is the {{sha:KEY}} placeholder); merged = merged into main
BRANCHES = {"fix-dev-03": (["03a", "03b", "03c"], False), "fix-dev-05": (["05"], False), "fix-dev-06": (["06"], False),
            "fix-dev-07": (["07a", "07"], False), "fix-dev-08": (["08"], True)}
Fixture = namedtuple("Fixture", "root repo squad scope other_squad config_dir herdr_json herdr_down steps shas")
_TS = re.compile(r'("ts"\s*:\s*")([^"]+)(")')


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, **GIT_ENV}).stdout.strip()


def _parse(ts):
    return datetime.strptime(ts.replace(".000Z", "Z"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _shift_file(path, delta):
    text = path.read_text(encoding="utf-8")
    def fix(m):
        t = _parse(m.group(2)) + delta
        return m.group(1) + t.strftime("%Y-%m-%dT%H:%M:%S") + (".000Z" if ".000Z" in m.group(2) else "Z") + m.group(3)
    path.write_text(_TS.sub(fix, text), encoding="utf-8", newline="\n")


def _build_git(repo, squad_scope):
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture base")
    shas = {}
    for name, (keys, _) in BRANCHES.items():
        _git(repo, "checkout", "-q", "-b", "squad/fix/checkout/" + name, "main")
        for k in keys:
            (repo / ("work-%s.txt" % k)).write_text(k + "\n", encoding="utf-8", newline="\n")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "work " + k)
            shas[k] = _git(repo, "rev-parse", "--short=10", "HEAD")
        _git(repo, "checkout", "-q", "main")
    for name, (_, merged) in BRANCHES.items():
        if merged:
            _git(repo, "merge", "-q", "--no-ff", "-m", "merge " + name, "squad/fix/checkout/" + name)
    path = squad_scope / "messages.jsonl"
    text = path.read_text(encoding="utf-8")
    path.write_text(re.sub(r"\{\{sha:(\w+)\}\}", lambda m: shas[m.group(1)], text), encoding="utf-8", newline="\n")
    return shas


def copy_fixture(dest=None, now=None, git=True):
    """Copy the fixture to `dest` (a new temp dir by default); `now` (aware datetime) shifts message and inbox times."""
    root = Path(dest) if dest else Path(tempfile.mkdtemp(prefix="board-fixture-"))
    for item in FIXTURE.iterdir():
        if item.name.startswith("_"):
            continue
        target = root / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    for r in ("repo", "repo2"):  # git ignores .claude/squads, so the fixture stores it as dot-claude/
        if (root / r / "dot-claude").exists():
            (root / r / "dot-claude").rename(root / r / ".claude")
    repo = root / "repo"
    squad = repo / ".claude" / "squads" / "fix"
    scope = squad / "scopes" / "checkout"
    crlf = squad / "scopes" / "_done" / "done-02" / "scope.md"  # CRLF on purpose (ADR 0011); a tracked CRLF file is refused by test_windows_safe
    crlf.write_bytes(crlf.read_bytes().replace(b"\n", b"\r\n"))
    if now is not None:
        delta = now - REF
        for p in squad.rglob("*.jsonl"):
            _shift_file(p, delta)
    # folder mtimes stand for the close dates: done-NN closed NN days before REF
    for i in range(1, 21):
        d = squad / "scopes" / "_done" / ("closed-release" if i == 1 else "done-%02d" % i)
        t = (REF - timedelta(days=i)).timestamp()
        os.utime(d, (t, t))
    shas = _build_git(repo, scope) if git else {}
    return Fixture(root, repo, squad, scope, root / "repo2" / ".claude" / "squads" / "other", root / "claude-config",
                   root / "herdr" / "agents.json", root / "herdr" / "not-running.json", FIXTURE / "FIXTURE-STEPS.md", shas)


def cleanup(fx):
    shutil.rmtree(str(fx.root), ignore_errors=True)


def append_message(scope_dir, typ, task, sender, text, to="fix-mgr-checkout", when=None):
    """Append one record to a scope's messages.jsonl (the log the page watches for new events)."""
    when = when or datetime.now(timezone.utc)
    rec = {"ts": when.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "msg_id": "m-%d" % when.timestamp(), "from": sender, "to": to,
           "type": typ, "task": task, "text": text, "iteration": 1}
    with open(Path(scope_dir) / "messages.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    ap.add_argument("--now", action="store_true", help="shift times so that the fixture clock is the real now")
    ap.add_argument("--dir", help="copy into this empty folder instead of a temp dir")
    a = sub.add_parser("append-message")
    a.add_argument("scope_dir")
    for k in ("type", "task", "sender", "text"):
        a.add_argument("--" + k, required=True)
    args = ap.parse_args(argv)
    if args.cmd == "append-message":
        append_message(args.scope_dir, args.type, args.task, args.sender, args.text)
        return 0
    fx = copy_fixture(args.dir, datetime.now(timezone.utc) if args.now else None)
    for k, v in fx._asdict().items():
        if k != "shas":
            print("%-12s %s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
