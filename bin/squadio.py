"""Shared stdio setup (UTF-8 and LF on every platform; a Windows pipe is cp1252 with CRLF) and the bash picker."""
import ntpath
import os
import posixpath
import shutil
import sys


def utf8_stdio():
    for stream, kwargs in (
        (sys.stdin, {}),
        (sys.stdout, {"newline": "\n"}),
        (sys.stderr, {"newline": "\n"}),
    ):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace", **kwargs)


def pick_bash(which, exists, nt, system_root):
    """The bash that runs squad-spawn, or None. On Windows the System32 and WindowsApps hits are the WSL launcher
    and the Store stub, the wrong bash; fall back to the Git for Windows bash found from git.exe."""
    path = ntpath if nt else posixpath
    found = which("bash")
    if found:
        low = found.replace("/", "\\").lower()
        sys32 = path.join(system_root, "System32").replace("/", "\\").lower() + "\\" if system_root else None
        if not nt or not (("\\windowsapps\\" in low) or (sys32 and low.startswith(sys32))):
            return found
    git = which("git")
    if nt and git:
        root = git
        for _ in range(3):
            root = path.dirname(root)
            candidate = path.join(root, "bin", "bash.exe")
            if exists(candidate):
                return candidate
    return None


def need_bash():
    bash = pick_bash(shutil.which, os.path.exists, os.name == "nt", os.environ.get("SystemRoot", ""))
    if not bash:
        print("bash not found: squad-start runs squad-spawn through bash; install Git for Windows or add its bin folder to PATH", file=sys.stderr)
        sys.exit(1)
    return bash
