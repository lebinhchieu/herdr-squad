"""Launch bin/ and tools/ scripts from a test the same way on Linux and Windows.

POSIX: argv is `[path, *args]` and env is passed untouched (bytes stay bytes), exactly what the tests did before.
Windows (nt): extensionless scripts cannot be exec'd and a bare `bash` is System32's WSL launcher, so the
interpreter comes from the script's shebang: bash/sh -> squadio.pick_bash (Git for Windows, absolute path),
python/python3 -> sys.executable. Paths become `as_posix()` strings; argv and env are all `str`.
"""
import os
import posixpath
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import squadio  # noqa: E402

NT = os.name == "nt"


def _resolve(shebang, nt, which, exists, system_root=""):
    """Interpreter argv prefix for a `#!` line, or None when the script is run directly (POSIX, no shebang)."""
    if not nt:
        return None
    words = shebang[2:].split() if shebang.startswith("#!") else []
    if words and posixpath.basename(words[0]) == "env":
        words = [w for w in words[1:] if not w.startswith("-")]
    name = posixpath.basename(words[0]) if words else ""
    if name in {"bash", "sh"}:
        picked = squadio.pick_bash(which, exists, True, system_root)
        if not picked:
            raise FileNotFoundError("Git for Windows bash not found (see tests/RUNNING-ON-WINDOWS.md)")
        return [picked]
    if name.startswith("python"):
        return [sys.executable]
    raise OSError("cannot run %r on Windows: unknown shebang %r" % (name, shebang))


def _first_line(path):
    with open(path, "rb") as f:
        return f.readline().decode("utf-8", "replace").strip()


def _text(x, nt):
    """On nt every argv word is a str: Path -> forward slashes, bytes -> decoded."""
    if not nt:
        return x
    if isinstance(x, bytes):
        return os.fsdecode(x)
    if isinstance(x, Path):
        return x.as_posix()
    return x if isinstance(x, str) else str(x)


def command(path, *args, nt=NT, which=shutil.which, exists=os.path.exists, shebang=None):
    """argv for running script `path` with `args`."""
    if not nt:
        return [path, *args]
    first = _first_line(path) if shebang is None else shebang
    prefix = _resolve(first, nt, which, exists, os.environ.get("SystemRoot", ""))
    return [*prefix, *(_text(a, nt) for a in (path, *args))]


def env_for(env, nt=NT):
    """None stays None (inherit). On nt keys and values become str, otherwise the mapping is returned as is."""
    if env is None or not nt:
        return env
    return {_text(k, nt): _text(v, nt) for k, v in env.items()}


def run_script(path, args=(), env=None, **kw):
    """subprocess.run of a bin/ or tools/ script; extra keywords go to subprocess.run."""
    return subprocess.run(command(path, *args), env=env_for(env), **kw)


def popen_script(path, args=(), env=None, **kw):
    return subprocess.Popen(command(path, *args), env=env_for(env), **kw)
