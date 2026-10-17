"""T2c: squad-process, processlint and squadlabel under a simulated Windows locale (cp1252 pipes, no UTF-8 mode)."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "bin"))
import squadprocess as sp  # noqa: E402
import test_squadprocess_apply as ap  # noqa: E402

TEXT = "→ 🦀 é"
WIN_ENV = {**os.environ, "PYTHONUTF8": "0", "LC_ALL": "C", "PYTHONCOERCECLOCALE": "0", "PYTHONIOENCODING": "cp1252"}


def run(*cmd):
    return subprocess.run([sys.executable, *map(str, cmd)], capture_output=True, env=WIN_ENV)


class SquadProcessWinTest(ap.Base):
    def squad_with_text(self):
        return self.squad(ap.V1.replace("a1", "a1 " + TEXT))

    def cli_win(self, *args, d):
        return run(ap.CLI, *args, "--squad-dir", d, "--plugin-root", self.plugin)

    def test_show_check_version_exit_0_and_print_utf8(self):
        d = self.squad_with_text()
        for cmd in (("show", "dev"), ("check",), ("version",)):
            extra = () if cmd[0] == "show" else ("--plugin-root", self.plugin)
            r = run(ap.CLI, *cmd, "--squad-dir", d, *extra)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn(b"\r", r.stdout)
            self.assertNotIn(b"Traceback", r.stderr)
        self.assertIn(TEXT.encode("utf-8"), run(ap.CLI, "show", "manager", "--squad-dir", d).stdout)

    def test_apply_writes_utf8_lf_bytes(self):
        d = self.squad_with_text()
        f = self.tmp / "combined.md"
        sp.compose(d, self.plugin, f, {"## A": "ours"})
        self.assertIn(TEXT, f.read_text(encoding="utf-8"))
        before_log = (d / "process-log.md").read_bytes()
        r = self.cli_win("apply", "--file", f, "--yes", d=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((d / "process.md").read_bytes(), f.read_bytes())
        log = (d / "process-log.md").read_bytes()
        self.assertNotIn(b"\r", log)
        log.decode("utf-8")
        self.assertIn(before_log.split(b"\n")[-2], log)  # the old row is intact

    def test_processlint_exit_0_on_non_ascii(self):
        f = self.tmp / "p.md"
        f.write_bytes(("# T\n\n## A\n- Send the file " + TEXT + ".\n").encode("utf-8"))
        r = run(ROOT / "bin" / "processlint.py", f)
        self.assertNotIn(b"Traceback", r.stderr)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class SquadLabelWinTest(unittest.TestCase):
    def test_label_round_trip_bytes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as home:
            code = ("import sys; sys.path.insert(0, sys.argv[1]); import squadlabel as sl; "
                    "sl.write_entry(sys.argv[2], 'a', 'manager', None, '\\U0001F980 Manager'); "
                    "e = sl.read_entry(sys.argv[2], 'a'); sys.stdout.buffer.write(e['title'].encode('utf-8'))")
            r = run("-c", code, ROOT / "bin", home)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout, "🦀 Manager".encode("utf-8"))
            raw = (Path(home) / "labels" / "a.json").read_bytes()
            self.assertIn("🦀 Manager".encode("utf-8"), raw)
            self.assertNotIn(b"\r", raw)


if __name__ == "__main__":
    unittest.main()
