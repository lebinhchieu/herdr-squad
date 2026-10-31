import os
import sys
import unittest
from pathlib import Path

import winlaunch

B = chr(92)
BASH = "C:/Program Files/Git/bin/bash.exe"


def which(found=BASH):
    return lambda name: found if name == "bash" else None


class CommandTest(unittest.TestCase):
    def test_posix_argv_and_env_are_untouched(self):
        self.assertEqual(winlaunch.command("/x/bin/squad-spawn", "a", b"b", nt=False), ["/x/bin/squad-spawn", "a", b"b"])
        env = {b"K": b"v", "S": "t"}
        self.assertIs(winlaunch.env_for(env, nt=False), env)
        self.assertIsNone(winlaunch.env_for(None, nt=False))

    def test_bash_shebangs_use_the_picked_bash_on_nt(self):
        for line in ("#!/usr/bin/env bash", "#!/bin/bash", "#!/usr/bin/env -S bash -e", "#!/bin/sh"):
            with self.subTest(line=line):
                argv = winlaunch.command(Path("C:/r/bin/squad-spawn"), Path("C:/r/x y"), "-f", nt=True, shebang=line,
                                         which=which())
                self.assertEqual(argv, [BASH, "C:/r/bin/squad-spawn", "C:/r/x y", "-f"])

    def test_python_shebangs_use_this_interpreter_on_nt(self):
        for line in ("#!/usr/bin/env python3", "#!/usr/bin/python3", "#!/usr/bin/env python"):
            with self.subTest(line=line):
                argv = winlaunch.command("C:/r/bin/squad-process", b"lint", nt=True, shebang=line, which=which())
                self.assertEqual(argv, [sys.executable, "C:/r/bin/squad-process", "lint"])

    def test_the_wsl_launcher_is_never_taken(self):
        sys32 = "C:"+B+"Windows"+B+"System32"+B+"bash.exe"
        git = "C:/Program Files/Git/cmd/git.exe"
        bash = "C:/Program Files/Git/bin/bash.exe"
        w = lambda n: {"bash": sys32, "git": git}.get(n)
        argv = winlaunch.command("C:/r/s", nt=True, shebang="#!/bin/bash", which=w, system_root="C:"+B+"Windows",
                                 exists=lambda p: p.replace(B, "/") == bash)
        self.assertEqual(argv[0].replace(B, "/"), bash)

    def test_no_git_bash_is_an_error_not_a_bare_bash(self):
        with self.assertRaises(FileNotFoundError):
            winlaunch.command("C:/r/s", nt=True, shebang="#!/bin/bash", which=lambda n: None)

    def test_unknown_shebang_is_an_error(self):
        for line in ("", "#!/usr/bin/env node", "no shebang"):
            with self.subTest(line=line), self.assertRaises(OSError):
                winlaunch.command("C:/r/s", nt=True, shebang=line, which=which())

    def test_env_is_all_str_on_nt(self):
        got = winlaunch.env_for({b"A": b"1", "B": Path("C:/x"), "C": 3}, nt=True)
        self.assertEqual(got, {"A": "1", "B": "C:/x", "C": "3"})


class RunScriptTest(unittest.TestCase):
    def test_runs_a_real_script_with_args_and_env(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            s = Path(d) / "tool"
            s.write_bytes(b'#!/usr/bin/env bash\nprintf "%s|%s" "$1" "$FOO"\n')
            s.chmod(0o755)
            r = winlaunch.run_script(s, ["a b"], env=dict(os.environ, FOO="bar"), capture_output=True)
            self.assertEqual((r.returncode, r.stdout), (0, b"a b|bar"))


if __name__ == "__main__":
    unittest.main()
