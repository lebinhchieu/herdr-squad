#!/usr/bin/env python3
"""caproc: find a pane's claude process on native Windows, where there is no /proc and no pgrep.

Used by cautoswitch, cwake and cswitch only when os.name == "nt" (Git Bash). herdr tells which process runs in a
pane (`herdr pane process-info`: pid, argv). The process environment (SQUAD_NAME, CLAUDE_CONFIG_DIR,
HERDR_WORKSPACE_ID) is read from the process's PEB with ctypes, which Windows allows for your own processes.

    caproc.py pane-pid PANE     print the pid of the pane's claude (not `claude daemon run`); exit 1 if none
    caproc.py argv PANE         print its argv NUL-terminated, like /proc/PID/cmdline
    caproc.py shell PANE        print the pane's shell: bash, pwsh, powershell, cmd ...
"""
import json
import os
import re
import shutil
import subprocess
import sys


def herdr(*args):
    """The `result` object of a herdr command, or None."""
    try:
        r = subprocess.run(["herdr", *args], capture_output=True, text=True, encoding="utf-8", timeout=15)
        return json.loads(r.stdout)["result"] if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return None


def claude_in(info):
    """The claude TUI of a `pane process-info` result: {pid, argv, cwd}, or None. A `claude daemon run` is skipped."""
    procs = ((info or {}).get("process_info") or {}).get("foreground_processes") or []
    for p in procs:
        argv = p.get("argv") or []
        if str(p.get("name", "")).lower().startswith("claude") and argv[1:2] != ["daemon"] and p.get("pid"):
            return {"pid": int(p["pid"]), "argv": [str(a) for a in argv], "cwd": p.get("cwd")}
    return None


def pane_claude(pane):
    return claude_in(herdr("pane", "process-info", "--pane", pane))


def shell_name(pane):
    """Lower-case program name (no .exe) of the pane's shell, or None."""
    pid = (((herdr("pane", "process-info", "--pane", pane) or {}).get("process_info")) or {}).get("shell_pid")
    if not pid:
        return None
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {int(pid)}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    m = re.match(r'"([^"]+)"', out.strip())
    return re.sub(r"\.exe$", "", m.group(1).lower()) if m else None


def environ(pid):
    """Environment of a process of the same user, as a dict. Windows only; raises OSError."""
    import ctypes
    from ctypes import wintypes as w
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    nt = ctypes.WinDLL("ntdll")
    k32.OpenProcess.restype = w.HANDLE
    k32.ReadProcessMemory.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                      ctypes.POINTER(ctypes.c_size_t)]

    class PBI(ctypes.Structure):  # PROCESS_BASIC_INFORMATION
        _fields_ = [("r1", ctypes.c_void_p), ("peb", ctypes.c_void_p), ("r2", ctypes.c_void_p * 2),
                    ("pid", ctypes.c_void_p), ("r3", ctypes.c_void_p)]

    def read(h, addr, n):
        buf, got = ctypes.create_string_buffer(n), ctypes.c_size_t()
        if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)):
            raise OSError(ctypes.get_last_error(), "ReadProcessMemory failed")
        return buf.raw[:got.value]

    ptr = lambda h, addr: int.from_bytes(read(h, addr, 8), "little")
    h = k32.OpenProcess(0x0410, False, pid)  # QUERY_INFORMATION | VM_READ
    if not h:
        raise OSError(ctypes.get_last_error(), f"cannot open process {pid}")
    try:
        pbi = PBI()
        if nt.NtQueryInformationProcess(h, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None) != 0:
            raise OSError(f"NtQueryInformationProcess failed for {pid}")
        params = ptr(h, pbi.peb + 0x20)                     # PEB.ProcessParameters (64-bit layout)
        block, size = ptr(h, params + 0x80), ptr(h, params + 0x3F0)  # .Environment, .EnvironmentSize
        text = read(h, block, size).decode("utf-16-le", "replace")
        return dict(kv.split("=", 1) for kv in text.split("\0") if "=" in kv[1:])
    finally:
        k32.CloseHandle(h)


def pane_env(pane):
    """Environment of the pane's claude, or None."""
    p = pane_claude(pane)
    try:
        return environ(p["pid"]) if p else None
    except OSError:
        return None


def pane_envs():
    """The environment of every pane's live claude TUI (the same rows pgrep + /proc/PID/environ give on Linux)."""
    out = []
    for pane in (herdr("pane", "list") or {}).get("panes", []):
        if pane.get("agent") == "claude" and pane.get("pane_id"):
            env = pane_env(pane["pane_id"])
            if env:
                out.append(env)
    return out


def bash_exe():
    """Git for Windows' bash (never System32's WSL launcher), or None."""
    cands = [os.environ.get("CA_BASH")]
    git = shutil.which("git")
    if git:  # ...\Git\cmd\git.exe or ...\Git\bin\git.exe
        cands.append(os.path.join(os.path.dirname(os.path.dirname(git)), "bin", "bash.exe"))
    cands += [os.path.join(os.environ.get(v, ""), "Git", "bin", "bash.exe") for v in ("ProgramFiles", "ProgramW6432")]
    return next((c for c in cands if c and os.path.isfile(c)), None)


def norm_path(p):
    """A config dir comparable across the forms it shows up in: C:\\Users\\x\\.claude-3 and /c/Users/x/.claude-3."""
    p = re.sub(r"^/([A-Za-z])/", r"\1:/", p or "")
    return os.path.normcase(os.path.normpath(p))


def main(argv):
    if len(argv) == 3 and argv[1] == "shell":
        name = shell_name(argv[2])
        if name:
            sys.stdout.buffer.write(name.encode() + b"\n")
        return 0 if name else 1
    if len(argv) == 3 and argv[1] in ("pane-pid", "argv"):
        p = pane_claude(argv[2])
        if not p:
            return 1
        if argv[1] == "pane-pid":
            sys.stdout.buffer.write(b"%d\n" % p["pid"])  # bytes: a Windows text stdout would end the line with CRLF
        else:
            sys.stdout.buffer.write(b"".join(a.encode("utf-8") + b"\0" for a in p["argv"]))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
