import os
import sys
import unittest
from pathlib import Path

import winlaunch

B = chr(92)
POSIX_BASH = "bash"  # the guard flags a literal bash argv
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


class ChildTest(unittest.TestCase):
    def test_posix_child_argv_is_utf8_bytes_and_bash_python_are_the_old_names(self):
        self.assertEqual(winlaunch.child_argv([POSIX_BASH, "/x/s", "é"], nt=False), [b"bash", b"/x/s", "é".encode("utf-8")])
        self.assertEqual(winlaunch.bash(nt=False), "bash")
        self.assertEqual(winlaunch.python(nt=False), __import__("shutil").which("python3"))

    def test_nt_child_argv_is_str_and_a_binary_first_word_is_kept(self):
        exe = Path(sys.executable)
        self.assertEqual(winlaunch.child_argv([exe, Path("C:/r/s"), b"a"], nt=True), [exe.as_posix(), "C:/r/s", "a"])
        self.assertEqual(winlaunch.python(nt=True), sys.executable)

    def test_nt_bash_is_the_picked_one(self):
        self.assertEqual(winlaunch.bash(nt=True, which=which(), system_root="C:"+B+"Windows"), BASH)

    def test_run_child_runs_and_encodes_env(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            s = Path(d) / "tool"
            s.write_bytes(b'#!/usr/bin/env bash\nprintf "%s|%s" "$1" "$FOO"\n')
            s.chmod(0o755)
            r = winlaunch.run_child([s, "é"], dict(os.environ, FOO="bär"), capture_output=True)
            self.assertEqual(r.stdout.decode("utf-8"), "é|bär")


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
