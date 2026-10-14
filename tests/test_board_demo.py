"""BRD-08: the committed demo squad replays through the real server and `/state` matches the
snapshots reviewed by hand. Seam A only: the real command, HTTP, no imports of the server.

The expected files are inputs, never outputs: nothing here writes them. When the fixture or the
server changes on purpose, regenerate by hand and review every value against the fixture again.
"""
import json
import re
import shutil
import unittest
from pathlib import Path

from board_fixture import Fixture

DEMO = Path(__file__).resolve().parent / "fixtures" / "board" / "demo"
NOW = "2026-03-02T10:30:00Z"
MAX_FIXTURE_BYTES = 100 * 1024
# a real path, an e-mail address, an API key, or a credential assignment
REAL_DATA = re.compile(r"/home/|/Users/|@[a-z]+\.(com|net|org)|sk-[A-Za-z0-9]|\btoken\b")


def expected(name):
    path = DEMO / name
    if not path.is_file():
        raise AssertionError("missing %s: the test never writes it, review and commit it" % path)
    return json.loads(path.read_text(encoding="utf-8"))


def message_rows(state):
    return [(r["type"], r["task"], r["from"], r["to"]) for r in state["rows"] if r["kind"] == "message"]


class DemoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = Fixture()
        shutil.copytree(str(DEMO), str(cls.fx.root), dirs_exist_ok=True)
        try:
            cls.server = cls.fx.start(now=NOW)
            cls.current = cls.server.state()
            cls.first = cls.server.state(1)
        except BaseException:
            cls.fx.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.fx.close()

    def column(self, agent):
        return next(c for c in self.current["columns"] if c["agent"] == agent)

    def bars(self, state, agent):
        return [b for b in state["bars"] if b["agent"] == agent]

    # --- the reviewed snapshots ------------------------------------------------------------

    def test_state_equals_the_reviewed_snapshot(self):
        self.assertEqual(self.current, expected("expected-state.json"))

    def test_iteration_1_equals_the_reviewed_snapshot(self):
        self.assertEqual(self.first, expected("expected-state-iteration-1.json"))

    # --- every behaviour the demo has to show -----------------------------------------------

    def test_handin_fail_handin_pass_loop_is_one_task_with_one_return(self):
        loop = [m for m in message_rows(self.first) if m[1] == "BRD-01"]
        self.assertEqual([m[0] for m in loop], ["DECISION", "DECISION", "HANDIN", "FAIL", "HANDIN", "PASS"])
        task = next(t for t in self.current["tasks"] if t["id"] == "BRD-01")
        self.assertEqual((task["state"], task["returns"], task["last_type"]), ("done", 1, "PASS"))

    def test_bars_that_start_themselves_and_bars_that_are_woken(self):
        manager = self.bars(self.first, "manager")
        self.assertEqual([b["self_start"] for b in manager], [True, True])
        woken = [b for b in self.first["bars"] if b["agent"] == "qaw-board"]
        self.assertEqual([b["self_start"] for b in woken], [False, False, False])
        self.assertEqual((self.column("manager")["wakes"], self.column("qaw-board")["wakes"]), (0, 3))

    def test_a_closed_and_an_open_blocked_segment(self):
        closed = self.bars(self.first, "dev-board-2")[0]
        self.assertEqual([(s["start_row"], s["end_row"], s["duration_s"]) for s in closed["blocked"]],
                         [(6, 9, 42)])
        live = self.bars(self.current, "dev-board-1")[0]
        self.assertEqual([(s["start_row"], s["end_row"], s["duration_s"]) for s in live["blocked"]],
                         [(12, None, 1080)])
        self.assertEqual((self.column("dev-board-1")["blocked_s"], self.column("dev-board-2")["blocked_s"]),
                         (1080, 42))

    def test_a_gap_over_180_s_folds_and_exactly_180_s_does_not(self):
        gaps = [(r["id"], r["seconds"]) for r in self.first["rows"] if r["kind"] == "gap"]
        self.assertEqual(gaps, [(18, 420)])
        rows = {r["id"]: r for r in self.first["rows"]}
        self.assertEqual((rows[22]["ts"], rows[23]["ts"]), ("2026-03-02T09:22:00.000Z", "2026-03-02T09:25:00.000Z"))
        self.assertEqual([r["seconds"] for r in self.current["rows"] if r["kind"] == "gap"], [445, 400, 330])

    def test_open_bars_run_to_now(self):
        open_bars = {b["agent"]: b["duration_s"] for b in self.current["bars"] if b["open"]}
        self.assertEqual(open_bars, {"dev-board-1": 1740, "dev-shop-1": 1730})
        self.assertTrue(all(b["end_row"] is None and b["end_ts"] is None
                            for b in self.current["bars"] if b["open"]))
        self.assertEqual((self.column("dev-board-1")["status"], self.column("dev-shop-1")["status"]),
                         ("blocked", "working"))

    def test_two_iterations_each_show_only_their_own_rows(self):
        self.assertEqual((self.current["iterations"], self.current["iteration"],
                          self.current["selected_iteration"], self.first["selected_iteration"]),
                         ([1, 2], 2, 2, 1))
        self.assertTrue(all(r["ts"] < "2026-03-02T10" for r in self.first["rows"]))
        self.assertTrue(all(r["ts"] >= "2026-03-02T10" for r in self.current["rows"]))
        self.assertEqual([t["id"] for t in self.first["tasks"]], ["BRD-01", "BRD-02"])
        self.assertEqual([t["id"] for t in self.current["tasks"]], ["BRD-01", "BRD-02", "BRD-03", "SHP-01"])

    def test_needs_you_has_a_blocked_agent_an_unanswered_escalation_and_the_idle_manager(self):
        self.assertEqual([(n["kind"], n["id"]) for n in self.current["needs_you"]],
                         [("blocked", "blocked:dev-board-1:2026-03-02T10:12:00.000Z"),
                          ("escalation", "escalation:2"), ("manager_idle", "manager_idle:2")])
        self.assertEqual(self.first["needs_you"], self.current["needs_you"])

    def test_one_agent_has_a_transcript_and_one_has_a_missing_one(self):
        with_transcript = self.column("dev-board-1")
        self.assertEqual((with_transcript["context_tokens"], with_transcript["tokens_in"],
                          with_transcript["tokens_out"], with_transcript["model"]),
                         (3400, 9450, 1170, "demo-model-small"))
        missing = self.column("dev-shop-1")
        self.assertEqual((missing["context_tokens"], missing["tokens_in"], missing["tokens_out"], missing["model"]),
                         (None, None, None, None))

    def test_pods_in_order_with_sizes_and_a_retired_developer(self):
        self.assertEqual([(p["name"], p["size"]) for p in self.current["pods"]],
                         [("all", None), ("board", "S + QA whitebox"), ("shop", "M")])
        self.assertEqual([c["agent"] for c in self.current["columns"] if c["retired"]], ["dev-board-2"])

    def test_serving_the_demo_is_quiet(self):
        self.assertEqual(self.server.stderr(), "")

    # --- the fixture itself -----------------------------------------------------------------

    def test_fixture_holds_no_real_data_and_stays_small(self):
        files = [p for p in DEMO.rglob("*") if p.is_file()]
        self.assertTrue(files)
        self.assertLess(sum(p.stat().st_size for p in files), MAX_FIXTURE_BYTES)
        for path in files:
            self.assertIsNone(REAL_DATA.search(path.read_text(encoding="utf-8")), str(path))


if __name__ == "__main__":
    unittest.main()
