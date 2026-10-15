"""The po-inbox mod: `claude plugin validate` and `claude plugin test` on this repo, from Python.

Skips when `claude` is not installed, unless SQUAD_REQUIRE_CLAUDE=1 (the full `--tz` run sets it): then it fails.
"""
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOD_DIR = REPO / "hooks" / "po-inbox"
CLAUDE = shutil.which("claude")
AGENT_ENV = ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "SQUAD_NAME", "SQUAD_ROLE", "SQUAD_SCOPE")


def claude(*args):
    env = {k: v for k, v in os.environ.items() if k not in AGENT_ENV}
    done = subprocess.run([CLAUDE, "plugin", *args, str(REPO)], env=env, cwd=str(REPO),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    return done.returncode, done.stdout.decode("utf-8", "replace")


class PoInboxModTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if CLAUDE is None:
            if os.environ.get("SQUAD_REQUIRE_CLAUDE") == "1":
                raise AssertionError("SQUAD_REQUIRE_CLAUDE=1 but `claude` is not on PATH")
            raise unittest.SkipTest("claude not installed")

    def test_validate_lists_what_the_mod_hooks_and_calls(self):
        code, out = claude("validate")
        self.assertEqual(code, 0, out)
        hooks = next(line for line in out.splitlines() if "register.tsx hooks:" in line)
        for event in ("session.start", "command.run{command=inbox}", "turn.complete"):
            self.assertIn(event, hooks)
        self.assertIn("ui.render", hooks)
        self.assertRegex(out, r"env reads: .*GOAL_DIR")
        for name in ("SQUAD_ROLE", "SCOPE_DIR", "GOAL_DIR"):
            self.assertIn(name, next(line for line in out.splitlines() if "env reads:" in line))
        calls = next(line for line in out.splitlines() if "register.tsx calls:" in line)
        self.assertIn("$.process.run", calls)
        self.assertIn("$.fs.stat", calls)
        self.assertNotIn("$.fs.read", calls)
        self.assertNotIn("$.fs.write", calls)

    def test_plugin_test_passes(self):
        code, out = claude("test")
        self.assertEqual(code, 0, out)
        passed = re.search(r"^\s*(\d+) pass$", out, re.M)
        failed = re.search(r"^\s*(\d+) fail$", out, re.M)
        self.assertIsNotNone(passed, out)
        self.assertEqual(failed.group(1), "0", out)
        declared = sum(len(re.findall(r"^\s*test\(", p.read_text(), re.M)) for p in MOD_DIR.glob("*.test.ts"))
        self.assertGreaterEqual(int(passed.group(1)), declared)
        print("claude plugin test: %s pass, %s fail (not skipped)" % (passed.group(1), failed.group(1)))


if __name__ == "__main__":
    unittest.main()
