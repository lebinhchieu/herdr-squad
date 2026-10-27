"""Test helper: the composed rules of a role at a size, and the targeting of a rule (`squad-process who`)."""
import functools
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
CLI = str(ROOT / "bin" / "squad-process")
ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "architect", "dev", "token-coach")


def _env():
    return {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}


def run(*args):
    return subprocess.run([sys.executable, "-B", CLI, *args], capture_output=True, encoding="utf-8", env=_env())


@functools.lru_cache(maxsize=None)
def composed(role, size="M", design="no", goal="no", qa="full", *, architecture="no", team=None):
    """Composed rules for `role` in a scope with these facts, whitespace folded to single spaces.

    `team` (tokens, a tuple or a comma string; "" or () = `none`) writes a `team:` line and ignores size, design and
    architecture. Without it the home has the old `size:` lines and composes through the branch-internal D1 scaffold
    (`legacy_scaffold=True`, set here and nowhere else; task 10 deletes it)."""
    import squadcompose as sc
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "scopes" / "s"
        home.mkdir(parents=True)
        if team is None:
            text = f"size: {size}\ndesign: {design}\narchitecture: {architecture}\nqa: {qa}\ngoal: {goal}\n"
        else:
            toks = [t.strip() for t in team.split(",")] if isinstance(team, str) else list(team)
            toks = [t for t in toks if t]
            text = f"team: {', '.join(toks) or 'none'}\nqa: {qa}\ngoal: {goal}\n"
        (home / "scope.md").write_text(text, encoding="utf-8")
        try:
            out = sc.compose(role, str(home), str(ROOT), None, role, "2026-01-01T00:00:00Z", None, legacy_scaffold=True)
        except sc.ComposeError as e:
            raise AssertionError("\n".join(e.lines))
        return re.sub(r"\s+", " ", out)


@functools.lru_cache(maxsize=None)
def who(rule_id):
    """-> {key: (acting roles, aware roles)} from `squad-process who <ID>`: key `S`/`M`/`L` for a size line, `<key> = <value>`
    (e.g. `plan-owner = team-lead`, `ba = yes`) for a duty or presence line of the team language."""
    r = run("who", rule_id)
    assert r.returncode == 0, r.stderr
    out = {}
    for line in r.stdout.splitlines():
        m = re.match(r"([SML]|[a-z][a-z-]* = \S+): acts: (.*?); aware: (.*)$", line)
        if m:
            split = lambda s: () if s.strip() == "-" else tuple(x.strip() for x in s.split(","))
            out[m.group(1)] = (split(m.group(2)), split(m.group(3)))
    return out


def acts(rule_id, key):
    """Acting roles of a rule at a size letter or a `<key> = <value>` line."""
    return who(rule_id)[key][0]
