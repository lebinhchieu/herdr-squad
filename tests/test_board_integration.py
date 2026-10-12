"""BRD-09: gaps found when the iteration 1 branches were merged. Seam A only.

Each test here covers a spec rule that no single ticket's tests reach, because it needs two of the
merged parts at once: the event stream and the needs-you list, or timeline, tasks, tokens and
needs-you all in one `/state`.
"""
import unittest

import test_board_events as ev
from board_fixture import Fixture

NOW = "2026-10-12T10:07:00Z"
SID = "11111111-2222-3333-4444-555555555555"

ROW_KEYS = {
    "message": {"id", "kind", "ts", "from", "to", "type", "task", "text", "msg_id"},
    "status": {"id", "kind", "ts", "agent", "status"},
    "gap": {"id", "kind", "ts", "seconds", "from_ts", "to_ts"},
}
BAR_KEYS = {"agent", "start_row", "end_row", "start_ts", "end_ts", "self_start", "open", "duration_s",
            "blocked"}
SEGMENT_KEYS = {"start_row", "end_row", "start_ts", "end_ts", "duration_s"}
TASK_KEYS = {"id", "state", "returns", "last_ts", "last_type"}
NEEDS_KEYS = {"id", "kind", "text", "agent", "since"}


def escalation_ids(state):
    return [n["id"] for n in state["needs_you"] if n["kind"] == "escalation"]


class EscalationsStreamTest(ev.EventsBase):
    """AC 13b, carried from BRD-06: `escalations.md` is one of the files the stream watches."""

    def test_new_escalation_row_raises_an_event_with_the_needs_you_item(self):
        server = self.start()
        stream = self.stream(server)
        first = stream.state(5)
        self.assertEqual(escalation_ids(first), [])
        self.fx.escalations([{"question": "Ship the board?"}])
        state = stream.state_where(lambda st: escalation_ids(st))
        self.assertIsNotNone(state, "no event with the escalation within 5 s")
        item = next(n for n in state["needs_you"] if n["kind"] == "escalation")
        self.assertEqual((item["id"], item["text"]), ("escalation:1", "Ship the board?"))

    def test_answering_the_escalation_raises_an_event_without_the_item(self):
        self.fx.escalations([{"question": "Ship the board?"}])
        server = self.start()
        stream = self.stream(server)
        self.assertEqual(escalation_ids(stream.state(5)), ["escalation:1"])
        self.fx.escalations([{"question": "Ship the board?", "answer": "yes"}])
        state = stream.state_where(lambda st: not escalation_ids(st))
        self.assertIsNotNone(state, "no event without the answered escalation within 5 s")


class MergedStateTest(unittest.TestCase):
    """One fixture that makes every part of the state non-empty; the contract holds for all of it."""

    def setUp(self):
        self.fx = fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"},
                   {"agent": "tech-board", "role": "Tech Lead"},
                   {"agent": "dev-board-1", "role": "Developer"},
                   {"agent": "qaw-board", "role": "QA whitebox"}])
        fx.scopes([{"scope": "board", "size": "S"}])
        fx.iteration(1)
        fx.escalations([{"question": "Ship the board?"}])
        fx.herdr({"dev-board-1": SID})
        fx.transcript("claude", "p", SID, [
            {"type": "assistant", "message": {"id": "r1", "model": "model-a", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 20, "cache_read_input_tokens": 30,
                "output_tokens": 5}}},
            {"type": "assistant", "message": {"id": "r2", "model": "model-b", "usage": {
                "input_tokens": 1, "cache_creation_input_tokens": 2, "cache_read_input_tokens": 3,
                "output_tokens": 4}}}])
        fx.message(ts="2026-10-12T10:00:00.000Z", type="DECISION", task="BRD-01", to="dev-board-1")
        fx.activity(ts="2026-10-12T10:00:20.000Z", agent="dev-board-1", status="blocked")
        fx.activity(ts="2026-10-12T10:00:50.000Z", agent="dev-board-1", status="working")
        fx.message(ts="2026-10-12T10:01:00.000Z", type="HANDIN", task="BRD-01",
                   **{"from": "dev-board-1", "to": "qaw-board"})
        fx.message(ts="2026-10-12T10:01:30.000Z", type="FAIL", task="BRD-01",
                   **{"from": "qaw-board", "to": "dev-board-1"})
        fx.activity(ts="2026-10-12T10:01:40.000Z", agent="dev-board-1", status="idle")
        fx.activity(ts="2026-10-12T10:01:50.000Z", agent="qaw-board", status="idle")
        fx.activity(ts="2026-10-12T10:06:00.000Z", agent="tech-board", status="blocked")
        fx.activity(ts="2026-10-12T10:06:10.000Z", agent="manager", status="idle")
        self.srv = fx.start(now=NOW)
        self.state = self.srv.state()

    def test_every_list_has_exactly_the_contract_keys(self):
        st = self.state
        kinds = set(r["kind"] for r in st["rows"])
        self.assertEqual(kinds, set(ROW_KEYS), "the fixture must show every row kind")
        for row in st["rows"]:
            expected = ROW_KEYS[row["kind"]] | ({"duration_s"} if "duration_s" in row else set())
            self.assertEqual(set(row), expected)
        self.assertTrue(any("duration_s" in r for r in st["rows"]))
        self.assertTrue(st["bars"] and any(b["blocked"] for b in st["bars"]))
        for bar in st["bars"]:
            self.assertEqual(set(bar), BAR_KEYS)
            for seg in bar["blocked"]:
                self.assertEqual(set(seg), SEGMENT_KEYS)
        self.assertTrue(st["tasks"])
        for task in st["tasks"]:
            self.assertEqual(set(task), TASK_KEYS)
        self.assertEqual(set(n["kind"] for n in st["needs_you"]), {"blocked", "escalation", "manager_idle"})
        for item in st["needs_you"]:
            self.assertEqual(set(item), NEEDS_KEYS)

    def test_one_column_carries_timeline_totals_and_tokens_together(self):
        col = next(c for c in self.state["columns"] if c["agent"] == "dev-board-1")
        self.assertEqual((col["working_s"], col["blocked_s"], col["wakes"]), (100, 30, 1))
        self.assertEqual((col["context_tokens"], col["tokens_in"], col["tokens_out"], col["model"]),
                         (6, 66, 9, "model-b"))
        self.assertEqual(col["status"], "idle")

    def test_rows_tasks_and_needs_you_agree_on_the_same_log(self):
        st = self.state
        self.assertEqual([(t["id"], t["state"], t["returns"], t["last_type"], t["last_ts"]) for t in st["tasks"]],
                         [("BRD-01", "returned", 1, "FAIL", "2026-10-12T10:01:30.000Z")])
        self.assertEqual([n["id"] for n in st["needs_you"]],
                         ["blocked:tech-board:2026-10-12T10:06:00.000Z", "escalation:1", "manager_idle:1"])
        gaps = [r for r in st["rows"] if r["kind"] == "gap"]
        self.assertEqual([g["seconds"] for g in gaps], [250])

    def test_no_token_in_state_page_or_stderr(self):
        for path in ("/", "/state"):
            status, _, body = self.srv.get(path)
            self.assertEqual(status, 200)
            self.assertNotIn(self.srv.token.encode(), body)
        self.assertEqual(self.srv.stderr(), "")


if __name__ == "__main__":
    unittest.main()
