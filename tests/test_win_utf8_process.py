"""T2c: squad-process, processlint and squadlabel under a simulated Windows locale (cp1252 pipes, no UTF-8 mode)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "bin"))

TEXT = "→ 🦀 é"
WIN_ENV = {**os.environ, "PYTHONUTF8": "0", "LC_ALL": "C", "PYTHONCOERCECLOCALE": "0", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "cp1252"}


def run(*cmd):
    return subprocess.run([sys.executable, *map(str, cmd)], capture_output=True, env=WIN_ENV)


class ProcessLintWinTest(unittest.TestCase):
    tmp = Path()

    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.tmp = Path(self._d.name)
        self.addCleanup(self._d.cleanup)

    def test_composed_rule_and_who_print_lf_utf8(self):
        for cmd in (("rule", "CORE-1"), ("who", "CORE-1")):
            r = run(ROOT / "bin" / "squad-process", *cmd)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn(b"\r", r.stdout)
            self.assertNotIn(b"Traceback", r.stderr)
            r.stdout.decode("utf-8")

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
