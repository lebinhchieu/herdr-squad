"""Test helper: the composed rules of a role for a team, and the targeting of a rule (`squad-process who`)."""
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
    architecture. Without it the team is the converter's mapping of `size`, design and architecture
    (`squadrules.legacy_team`): a shorthand for the old S/M/L test shapes; the home always holds a `team:` line."""
    import squadcompose as sc
    import squadrules as sr
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "scopes" / "s"
        home.mkdir(parents=True)
        if team is None:
            team = sr.legacy_team(size, "yes", design, architecture)
        toks = [t.strip() for t in team.split(",")] if isinstance(team, str) else list(team)
        toks = [t for t in toks if t]
        text = f"team: {', '.join(toks) or 'none'}\nqa: {qa}\ngoal: {goal}\n"
        (home / "scope.md").write_text(text, encoding="utf-8")
        try:
            out = sc.compose(role, str(home), str(ROOT), None, role, "2026-01-01T00:00:00Z", None)
        except sc.ComposeError as e:
            raise AssertionError("\n".join(e.lines))
        return re.sub(r"\s+", " ", out)


@functools.lru_cache(maxsize=None)
def who(rule_id):
    """-> {key: (acting roles, aware roles)} from `squad-process who <ID>`: key `<key> = <value>`
    (e.g. `plan-owner = team-lead`, `ba = yes`) for a duty or presence line of the team language."""
    r = run("who", rule_id)
    assert r.returncode == 0, r.stderr
    out = {}
    for line in r.stdout.splitlines():
        m = re.match(r"([a-z][a-z-]* = \S+): acts: (.*?); aware: (.*)$", line)
        if m:
            split = lambda s: () if s.strip() == "-" else tuple(x.strip() for x in s.split(","))
            out[m.group(1)] = (split(m.group(2)), split(m.group(3)))
    out.update(_size_shapes(rule_id))
    return out


def _size_shapes(rule_id):
    """Shorthand for the old test shapes: key `S`/`M`/`L` -> (acting, aware) of the rule in the team the converter maps
    that size to (`squadrules.legacy_team`). Test convenience only; the engine has no size."""
    import squadcompose as sc
    import squadrules as sr
    e = sc.find_rule(str(ROOT), None, rule_id)
    out = {}
    for size in "SML":
        facts = sr.team_facts(sr.legacy_team(size, "yes", "no", "no"))
        facts.pop("design"); facts.pop("architecture")  # the old size lines left every other fact missing (true)
        ok = sr.matches(e.when, facts)
        out[size] = (tuple(e.roles) if ok else (), tuple(e.aware) if ok else ())
    return out


def acts(rule_id, key):
    """Acting roles of a rule at a `<key> = <value>` line."""
    return who(rule_id)[key][0]
