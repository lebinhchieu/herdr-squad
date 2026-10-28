"""claude-accounts, Windows side: runs tools/claude-accounts/windows/claude-accounts.ps1 under a real PowerShell 7
(WSL interop pwsh.exe, or a native pwsh) through one scenario script, tests/ca_win_cases.ps1, which prints one
JSON line per case; each line is a subTest here. One pwsh start for the whole file. Skips with a reason when no
pwsh is reachable (plain Linux CI). stdlib only.

Env overrides (used for the evidence runs, not needed otherwise):
  CA_WIN_PS1            path of another ps1 to run the cases against (e.g. the byte copy of the pre-port file)
  CA_WIN_PWSH_ALIAS     replaces the WindowsApps alias path in the search (point at a missing file to hide it)
Test data lives on the WSL side; nothing is written under /mnt/c and the PO's C:\\Users\\...\\.claude-accounts is
never read: USERPROFILE is pointed at a temp dir so $HOME is the test's."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PS1 = Path(os.environ.get("CA_WIN_PS1") or HERE.parent / "tools" / "claude-accounts" / "windows" / "claude-accounts.ps1")
SCENARIO = HERE / "ca_win_cases.ps1"
FIX = HERE / "fixtures" / "ca"
ALIAS = "/mnt/c/Users/84084/AppData/Local/Microsoft/WindowsApps/pwsh.exe"
BUDGET_S = 50  # "well under a minute"


def find_pwsh(path=None, alias=None):
    """A pwsh to run, or None: pwsh or pwsh.exe on PATH, else the WindowsApps alias."""
    for name in ("pwsh", "pwsh.exe"):
        found = shutil.which(name, path=path)
        if found:
            return found
    alias = alias if alias is not None else os.environ.get("CA_WIN_PWSH_ALIAS", ALIAS)
    return alias if alias and os.path.isfile(alias) else None


def winpath(p):
    """The path as pwsh.exe sees it (wslpath -w on WSL, unchanged on Windows or for a native Linux pwsh)."""
    if sys.platform == "win32" or not os.path.isfile("/proc/sys/fs/binfmt_misc/WSLInterop"):
        return str(p)
    return subprocess.run(["wslpath", "-w", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def skip_reason():
    pw = find_pwsh()
    if not pw:
        return "no pwsh (pwsh, pwsh.exe or the WindowsApps alias) reachable"
    if not (sys.platform == "win32" or os.path.isfile("/proc/sys/fs/binfmt_misc/WSLInterop") or not pw.endswith(".exe")):
        return "pwsh.exe found but WSL interop is off"
    if not PS1.is_file():
        return f"{PS1} does not exist"
    return None


def unsafe_home(p):
    """Why `p` may not be a test home (P10), or None: empty, under /mnt (a Windows disk) or the real home."""
    if not p or not str(p).strip():
        return "empty"
    real = os.path.realpath(str(p))
    if real == "/mnt" or real.startswith("/mnt/") or real == "/":
        return "under /mnt (a Windows disk)"
    for h in {os.path.realpath(os.path.expanduser("~")), os.path.realpath(os.environ.get("HOME", "/nonexistent"))}:
        if real == h or real.startswith(h + os.sep):
            return "the real home or under it"
    return None


class GuardTest(unittest.TestCase):
    def test_refuses_empty_mnt_and_the_real_home(self):
        for bad in ("", "  ", "/", "/mnt/c/Users/84084/.claude-accounts", "/mnt/c", os.path.expanduser("~"),
                    os.path.expanduser("~/.claude-accounts"), "/mnt/c/../c/Users"):
            self.assertIsNotNone(unsafe_home(bad), repr(bad))

    def test_accepts_a_wsl_temp_dir(self):
        with tempfile.TemporaryDirectory(prefix="cawin") as d:
            self.assertIsNone(unsafe_home(d))


class FinderTest(unittest.TestCase):
    """The skip logic itself: runs everywhere."""

    def test_no_pwsh_on_an_empty_path_and_a_missing_alias(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(find_pwsh(path=empty, alias="/nonexistent/pwsh.exe"))

    def test_finds_pwsh_on_path_before_the_alias(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d, "pwsh")
            exe.write_text("#!/bin/sh\n", encoding="utf-8")
            exe.chmod(0o755)
            self.assertEqual(find_pwsh(path=d, alias="/nonexistent/pwsh.exe"), str(exe))

    def test_the_alias_is_the_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            alias = Path(d, "pwsh.exe")
            alias.write_text("", encoding="utf-8")
            self.assertEqual(find_pwsh(path=d + "/none", alias=str(alias)), str(alias))

    def test_fixtures_are_the_real_captures(self):
        win = ('{"id":"cli:workspace:list","result":{"type":"workspace_list","workspaces":[{"active_tab_id":"w6:tQ",'
               '"agent_status":"done","focused":true,"label":"enemy-spritesheet","number":1,"pane_count":10,'
               '"tab_count":9,"workspace_id":"w6"}]}}')
        three = ('{"id":"cli:workspace:list","result":{"type":"workspace_list","workspaces":[{"active_tab_id":"w26:tW",'
                 '"agent_status":"done","focused":true,"label":"claude-accounts","number":1,"pane_count":3,"tab_count":3,'
                 '"workspace_id":"w26"},{"active_tab_id":"w2H:t1","agent_status":"unknown","focused":false,'
                 '"label":"squad","number":2,"pane_count":1,"tab_count":1,"workspace_id":"w2H"},'
                 '{"active_tab_id":"w2J:t1","agent_status":"idle","focused":false,"label":"wpw","number":3,'
                 '"pane_count":1,"tab_count":1,"tokens":{"account":"c3"},"workspace_id":"w2J"}]}}')
        for name, want in (("workspace-list-windows.real.json", win), ("workspace-list-3.real.json", three)):
            self.assertEqual((FIX / name).read_bytes().rstrip(b"\n").decode("utf-8"), want, name)
        self.assertTrue((FIX / "workspace-list.real.json").is_file())


@unittest.skipIf(skip_reason(), skip_reason() or "")
class WindowsPortTest(unittest.TestCase):
    cases = None
    notes = ()

    @classmethod
    def setUpClass(cls):
        tmp = Path(tempfile.mkdtemp(prefix="cawin"))
        cls.addClassCleanup(shutil.rmtree, tmp, True)
        for d in (tmp, tmp / "home"):
            why = unsafe_home(d)
            if why:
                raise AssertionError(f"refusing to run pwsh: test dir {d} is {why}")
        (tmp / "home").mkdir()
        (tmp / "data").mkdir()
        env = dict(os.environ)
        env["USERPROFILE"] = winpath(tmp / "home")
        env["WSLENV"] = ":".join(filter(None, [env.get("WSLENV", ""), "USERPROFILE"]))
        cmd = [find_pwsh(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", winpath(SCENARIO),
               "-Ps1", winpath(PS1), "-Tmp", winpath(tmp / "data"), "-Fix", winpath(FIX), "-HomeDir", winpath(tmp / "home")]
        # a cwd that is not a UNC path (pwsh.exe refuses one); reading only
        cwd = "C:\\Windows" if sys.platform == "win32" else ("/mnt/c/Windows" if os.path.isdir("/mnt/c/Windows") else "/")
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=BUDGET_S)
        cls.cases, cls.notes = [], []
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                row = json.loads(line)
                (cls.notes if row["name"].startswith("note.") else cls.cases).append(row)
        cls.stderr, cls.rc = r.stderr, r.returncode

    def test_scenario_ran_and_every_case_is_unique(self):
        names = [c["name"] for c in self.cases]
        self.assertTrue(names, f"no case lines; rc={self.rc} stderr={self.stderr[:2000]}")
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(self.rc, 0, self.stderr[:2000])

    def test_every_case_passes(self):
        for c in self.cases:
            with self.subTest(case=c["name"]):
                self.assertTrue(c["ok"], c["detail"])

    def test_recorded_not_asserted(self):
        for n in self.notes:  # the share's behaviour on a destination held open: printed with -v
            print(f"\n{n['name']}: {n['detail']}", file=sys.stderr)


if __name__ == "__main__":
    unittest.main()
