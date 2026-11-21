"""hooks/herdr-bg: reports the bg token of a session's background shells to herdr (stub herdr on PATH).

Skips when bash or jq is missing, unless SQUAD_REQUIRE_CLAUDE=1 (the full `--tz` run): then it fails.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import winlaunch

SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "herdr-bg"
JQ = shutil.which("jq")
BASH = winlaunch.bash()  # Git bash on Windows, never the WSL launcher (tests/test_no_bare_bash.py)


def setUpModule():
    missing = [n for n, exe in {"jq": "jq", "bash": BASH}.items() if not shutil.which(exe)]
    if missing:
        if os.environ.get("SQUAD_REQUIRE_CLAUDE") == "1":
            raise AssertionError("SQUAD_REQUIRE_CLAUDE=1 but not on PATH: " + ", ".join(missing))
        raise unittest.SkipTest("herdr-bg needs bash and jq, missing: " + ", ".join(missing))


class HerdrBgTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.tasks = self.tmp / "tasks" / "s1" / "tasks"
        self.tasks.mkdir(parents=True)
        self.log = self.tmp / "calls.log"
        stub = self.tmp / "bin" / "herdr"
        stub.parent.mkdir()
        stub.write_text('#!/bin/sh\necho "$*" >>"$HERDR_STUB_LOG"\n')
        stub.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{stub.parent}{os.pathsep}{os.environ['PATH']}",
                        HERDR_STUB_LOG=str(self.log), HERDR_ENV="1", HERDR_PANE_ID="w1:p1",
                        HERDR_BG_STATE_DIR=str(self.tmp / "state"),
                        HERDR_BG_TASKS_GLOB=str(self.tmp / "tasks" / "%s" / "tasks"))

    def fire(self, payload, env=None):
        return subprocess.run([BASH, str(SCRIPT), "hook"], input=json.dumps(payload), text=True,
                              capture_output=True, env=env or self.env, timeout=30)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def bash_payload(self, tid="b1"):
        return {"session_id": "s1", "tool_name": "Bash",
                "tool_input": {"command": "sleep 99", "run_in_background": True},
                "tool_response": {"backgroundTaskId": tid}}

    def test_a_background_bash_reports_one_shell(self):
        (self.tasks / "b1.output").write_text("")
        self.fire(self.bash_payload())
        self.assertEqual(self.calls()[-1],
                         "pane report-metadata w1:p1 --source herdr-bg --token bg=⏵ 1 shell --ttl-ms 3600000")

    def test_b_exit_marker_then_stop_clears(self):
        out = self.tasks / "b1.output"
        out.write_text("")
        self.fire(self.bash_payload())
        out.write_text("done\n[exited with code 0]\n")
        self.fire({"session_id": "s1", "hook_event_name": "Stop"})
        self.assertIn("--clear-token bg", self.calls()[-1])

    def test_c_taskstop_clears(self):
        (self.tasks / "b1.output").write_text("")
        self.fire(self.bash_payload())
        self.fire({"session_id": "s1", "tool_name": "TaskStop", "tool_input": {"task_id": "b1"}})
        self.assertIn("--clear-token bg", self.calls()[-1])

    def test_d_same_task_twice_counts_once(self):
        # Two hook lines (settings.json and the plugin) record one task twice.
        (self.tasks / "b1.output").write_text("")
        self.fire(self.bash_payload())
        self.fire(self.bash_payload())
        self.assertIn("--token bg=⏵ 1 shell ", self.calls()[-1])

    def test_e_no_herdr_env_is_silent(self):
        (self.tasks / "b1.output").write_text("")
        env = {k: v for k, v in self.env.items() if k != "HERDR_ENV"}
        r = self.fire(self.bash_payload(), env)
        self.assertEqual((r.returncode, r.stdout, r.stderr, self.calls()), (0, "", "", []))

    def test_e_no_jq_is_silent(self):
        bindir = self.tmp / "nojq"
        bindir.mkdir()
        for name in ("bash", "date", "mktemp", "grep", "awk", "sed", "mv", "touch", "mkdir",
                     "head", "cat", "id", "env"):
            real = shutil.which(name)
            if real:
                (bindir / name).symlink_to(real)
        env = dict(self.env, PATH=str(bindir))
        (self.tasks / "b1.output").write_text("")
        r = self.fire(self.bash_payload(), env)
        self.assertEqual((r.returncode, r.stdout, r.stderr, self.calls()), (0, "", "", []))


if __name__ == "__main__":
    unittest.main()
