"""BRD-17: seams between the iteration 2 branches once they are merged."""
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

import test_board_recorder as recorder
from board_fixture import Fixture
from test_board_events import Stream


class LiveKeyTest(recorder.LiveCase):
    """`/state` and the first `/events` frame carry the same `live` value, in live mode and in replay."""

    def first_frame(self, server):
        stream = Stream(server)
        self.addCleanup(stream.close)
        return stream.state(10)

    def test_live_mode_says_true_on_both_paths(self):
        self.add_agent("manager")
        srv = self.start()
        self.assertIs(srv.state()["live"], True)
        self.assertIs(self.first_frame(srv)["live"], True)

    def test_replay_says_false_on_both_paths(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([recorder.MANAGER])
        fx.iteration(1)
        fx.activity(agent="manager", status="idle")
        srv = fx.start(now="2026-10-12T12:00:00Z")
        self.assertIs(srv.state()["live"], False)
        self.assertIs(self.first_frame(srv)["live"], False)


class StderrPollTest(unittest.TestCase):
    def test_two_polls_while_the_child_writes_lose_no_line(self):
        import subprocess
        import sys
        from board_fixture import Server
        handle = tempfile.TemporaryFile()
        script = ("import sys,time\nprint('squad-board: http://127.0.0.1:1/?token=x', flush=True)\n"
                  "for i in range(40):\n    sys.stderr.write('line %d\\n' % i); sys.stderr.flush(); time.sleep(0.01)\n")
        proc = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, stderr=handle, bufsize=0)
        server = Server(proc, handle, proc.stdout.readline().decode().strip())
        try:
            while proc.poll() is None:
                server.stderr()
                time.sleep(0.003)
            proc.wait()
            lines = server.stderr().splitlines()
        finally:
            proc.kill()
            proc.wait()
            proc.stdout.close()
            handle.close()
        self.assertEqual(lines, ["line %d" % i for i in range(40)])


if __name__ == "__main__":
    unittest.main()
