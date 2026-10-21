"""Test helper: the composed rules of a role at a size, and the targeting of a rule (`squad-process who`)."""
import functools
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = str(ROOT / "bin" / "squad-process")
ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "dev", "token-coach")


def _env():
    return {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}


def run(*args):
    return subprocess.run([sys.executable, CLI, *args], capture_output=True, encoding="utf-8", env=_env())


@functools.lru_cache(maxsize=None)
def composed(role, size="M", design="no", goal="no", qa="full"):
    """Composed rules for `role` in a scope with these facts, whitespace folded to single spaces."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "scopes" / "s"
        home.mkdir(parents=True)
        (home / "scope.md").write_text(f"size: {size}\ndesign: {design}\nqa: {qa}\ngoal: {goal}\n", encoding="utf-8")
        out = Path(tmp) / "rules.md"
        r = run("compose", role, "--home", str(home), "--out", str(out))
        assert r.returncode == 0, r.stderr
        return re.sub(r"\s+", " ", out.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def who(rule_id):
    """-> {size: (acting roles, aware roles)} from `squad-process who <ID>`."""
    r = run("who", rule_id)
    assert r.returncode == 0, r.stderr
    out = {}
    for line in r.stdout.splitlines():
        m = re.match(r"([SML]): acts: (.*?); aware: (.*)$", line)
        if m:
            split = lambda s: () if s.strip() == "-" else tuple(x.strip() for x in s.split(","))
            out[m.group(1)] = (split(m.group(2)), split(m.group(3)))
    return out


def acts(rule_id, size):
    return who(rule_id)[size][0]
