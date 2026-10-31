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


def _utf8(x):
    return str(x).encode("utf-8", "surrogateescape")


def command(path, *args, nt=NT, which=shutil.which, exists=os.path.exists, shebang=None, system_root=None, utf8=False):
    """argv for running `path` with `args`.

    POSIX: `[path, *args]` untouched, or with utf8=True every word as UTF-8 bytes (the parent may run under an ASCII
    locale). nt: str words; a file that starts with `#!` becomes its interpreter + file, a binary or bare command name
    is used as is."""
    if not nt:
        return [_utf8(w) for w in (path, *args)] if utf8 else [path, *args]
    if shebang is None:
        try:
            first = _first_line(path)
        except OSError:  # a bare command name or an unreadable file
            first = None
        if first is None or not first.startswith("#!"):
            return [_text(w, nt) for w in (path, *args)]
    else:
        first = shebang
    if system_root is None:
        system_root = os.environ.get("SystemRoot", "")
    prefix = _resolve(first, nt, which, exists, system_root)
    return [*prefix, *(_text(a, nt) for a in (path, *args))]


def env_for(env, nt=NT, utf8=False):
    """None stays None (inherit). nt: keys and values become str. POSIX: the mapping as is, or with utf8=True as bytes."""
    if env is None:
        return env
    if nt:
        return {_text(k, nt): _text(v, nt) for k, v in env.items()}
    return {_utf8(k): _utf8(v) for k, v in env.items()} if utf8 else env


def run_script(path, args=(), env=None, utf8=False, **kw):
    """The one runner: subprocess.run of a bin/ or tools/ script (or `[bash, script]` words); extra keywords go to
    subprocess.run. utf8=True makes POSIX argv and env UTF-8 bytes; on nt both are str either way."""
    return subprocess.run(command(path, *args, utf8=utf8), env=env_for(env, utf8=utf8), **kw)


def bash(nt=NT, which=shutil.which, exists=os.path.exists, system_root=None):
    """The bash for `[bash, script]`: the literal "bash" on POSIX (argv unchanged), Git's bash on nt."""
    if not nt:
        return "bash"
    return _resolve("#!/bin/bash", nt, which, exists, os.environ.get("SystemRoot", "") if system_root is None else system_root)[0]


def python(nt=NT):
    """The python3 for `[python, script]`: PATH's python3 on POSIX (as the tests did), this interpreter on nt."""
    return sys.executable if nt else shutil.which("python3")


def no_flock_env(env, tmp):
    """env whose PATH has no flock, so the hooks take their mkdir-lock branch (Windows has none; Linux gets a symlink farm)."""
    if not shutil.which("flock", path=env.get("PATH")):
        return env
    farm = Path(tmp) / "noflock-bin"
    farm.mkdir(exist_ok=True)
    for tool in ("bash", "jq", "date", "dirname", "readlink", "cat", "basename", "python3", "sleep", "mkdir",
                 "rmdir", "env", "uname", "sed", "grep", "tr", "head", "sort", "wc", "id"):
        found = shutil.which(tool)
        if found and not (farm / tool).exists():
            (farm / tool).symlink_to(found)
    return {**env, "PATH": str(farm)}
