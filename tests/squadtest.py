"""Shared set-up for the tests: repo paths, CLI loader, env scrub, fake herdr, squad home tree, git, plugin copy.

One place for each helper (ticket 14a). A helper that fewer than 3 files use belongs in its own test file.
Scripts are started with `winlaunch` (no bare `bash` here: tests/test_no_bare_bash.py)."""
import atexit
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "rules" / "compose"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
_AGENT_ENV = ("SQUAD", "SCOPE_DIR", "GOAL_DIR", "HERDR")


def load_cli(name):
    """The module of a `bin/` script that has no `.py` suffix (squad-label, squad-start ...)."""
    mod_name = name.replace("-", "_") + "_mod"
    loader = importlib.machinery.SourceFileLoader(mod_name, str(BIN / name))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(mod_name, loader))
    loader.exec_module(mod)
    return mod


def clean_env(**extra):
    """os.environ without the agent variables (SQUAD*, SCOPE_DIR, GOAL_DIR, HERDR*), plus `extra`. SQUAD_WATCHDOG=off: a
    squad-start run in a test starts no watchdog (a test of the watchdog passes its own value)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(_AGENT_ENV)}
    env["SQUAD_WATCHDOG"] = "off"
    env.update(extra)
    return env


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, **GIT_ENV}).stdout.strip()


def squad_home(root, process=None, scope=None):
    """`<root>/.claude/squads/t` with scopes/ and goals/; process.md and scope.md only when text is given."""
    squad = Path(root) / ".claude" / "squads" / "t"
    (squad / "scopes").mkdir(parents=True)
    (squad / "goals").mkdir()
    for name, text in (("process.md", process), ("scope.md", scope)):
        if text is not None:
            (squad / name).write_text(text, encoding="utf-8", newline="\n")
    return squad


# --- fake herdr -------------------------------------------------------------------------------------------------
# One script for every test. Behaviour comes from the environment the test sets:
#   HERDR_LOG  every call is appended (also the "agent rename" a respawn made: that agent is gone afterwards)
#   LIVE / DEAD  space-separated agent names that are (not) found; the rest follows the mode
#   FAIL_RENAME  `tab rename` fails        PANES  a table "pane tab agent" that agent get / tab close / pane close use
_FAKE_HERDR = r"""#!/usr/bin/env bash
[[ -n ${HERDR_LOG:-} ]] && echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent list") python3 -c 'import json,os; print(json.dumps({"result":{"agents":[{"name":n,"tab_id":"tab-"+n} for n in os.environ.get("LIVE","").split()]}}))' ;;
  "agent get")
    if [[ -n ${PANES:-} ]]; then
      row=$(awk -v n="$3" '$3 == n' "$PANES")
      [[ -n $row ]] || { echo '{"error":{"code":"agent_not_found"}}'; exit 1; }
      read -r pane tab _ <<<"$row"
      echo "{\"result\":{\"agent\":{\"name\":\"$3\",\"pane_id\":\"$pane\",\"tab_id\":\"$tab\"}}}"; exit 0
    fi
    up=@UP@
    [[ " ${LIVE:-} " == *" $3 "* ]] && up=1
    [[ " ${DEAD:-} " == *" $3 "* ]] && up=0
    [[ -n ${HERDR_LOG:-} ]] && grep -q "^agent rename $3 " "$HERDR_LOG" && up=0
    (( up )) || { echo '{"error":{"code":"agent_not_found"}}'; exit 1; }
    echo "{\"result\":{\"agent\":{\"name\":\"$3\",\"pane_id\":\"p-$3\",\"tab_id\":\"tab-$3\"}}}" ;;
  "tab create") echo '{"result":{"root_pane":{"pane_id":"p-new"},"tab":{"tab_id":"t-new"}}}' ;;
  "tab rename") [[ -n ${FAIL_RENAME:-} ]] && { echo boom >&2; exit 1; } ;;
  "tab close") [[ -n ${PANES:-} ]] && { awk -v t="$3" '$2 != t' "$PANES" > "$PANES.new"; mv "$PANES.new" "$PANES"; } ;;
  "pane close") [[ -n ${PANES:-} ]] && { awk -v p="$3" '$1 != p' "$PANES" > "$PANES.new"; mv "$PANES.new" "$PANES"; } ;;
esac
exit 0
"""


def fake_herdr(dir, mode="dead"):
    """Write `<dir>/herdr` and return its path. mode "dead": an agent is found only if it is in LIVE;
    mode "live": an agent is found unless it is in DEAD."""
    assert mode in ("live", "dead"), mode
    path = Path(dir) / "herdr"
    path.write_text(_FAKE_HERDR.replace("@UP@", "1" if mode == "live" else "0"), encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path


# --- plugin copy -------------------------------------------------------------------------------------------------
PluginCopy = namedtuple("PluginCopy", "path version sha")
_COPIES = {}


def _stamp_version(plugin, version):
    pj = plugin / ".claude-plugin" / "plugin.json"
    pj.write_text(re.sub(r'("version"\s*:\s*)"[^"]*"', rf'\1"{version}"', pj.read_text(encoding="utf-8")), encoding="utf-8")


def _build(fixtures):
    tmp = tempfile.TemporaryDirectory()
    atexit.register(tmp.cleanup)
    dest = Path(tmp.name) / "plugin"
    shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns(".git", ".worktrees", ".scratch", ".claude", "tests", "__pycache__"))
    # The copy stands for a release that has the team language (0.6.0): a pin below it is handed to its own engine.
    _stamp_version(dest, "0.6.0")
    if fixtures:
        pdir = dest / "templates" / "squad" / "process"
        pdir.mkdir(parents=True, exist_ok=True)
        for f in (FIXTURES / "templates" / "squad" / "process").glob("*.md"):
            shutil.copy(f, pdir / f.name)
        # the real _removed.md tombstones name REV-14a / REV-19b; the fixture review.md replaces the real one, so the copy gets stubs
        with (pdir / "review.md").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n## REV-14a Diff check\nroles: dev\ntopic: review\n\nA later commit goes to the same checkers.\n"
                     "\n## REV-19b Hand in to QA whitebox alone\nroles: dev\nwhen: qa-white = yes and qa-black = no\ntopic: review\n\n"
                     "The Developer hands in to QA whitebox alone.\n")
    git("init", "-q", cwd=dest)
    git("add", "-A", cwd=dest)
    git("commit", "-q", "-m", "fixture plugin", cwd=dest)
    version = json.loads((dest / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    return PluginCopy(dest, version, git("rev-parse", "HEAD", cwd=dest))


def plugin_copy(fixtures=True):
    """A git copy of this plugin (version 0.6.0), built once per process and removed at exit. READ-ONLY: a test that
    changes it uses plugin_clone(). fixtures=True adds the 04 fixture rule files (tests/fixtures/rules/compose)."""
    if fixtures not in _COPIES:
        _COPIES[fixtures] = _build(fixtures)
    return _COPIES[fixtures]


def plugin_clone(dest, fixtures=True, git_dir=True):
    """A writable copy of plugin_copy() at `dest` (the tests' own temp folder) -> PluginCopy. git_dir=False leaves out .git."""
    src = plugin_copy(fixtures)
    shutil.copytree(src.path, dest, ignore=None if git_dir else shutil.ignore_patterns(".git"))
    return PluginCopy(Path(dest), src.version, src.sha)
