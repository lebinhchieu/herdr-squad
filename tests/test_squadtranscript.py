"""squadtranscript.iter_records: one dict per timestamped record of a session and its subagents."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import squadtranscript as st  # noqa: E402

KEYS = {"ts", "kind", "side", "origin", "msg_id", "model", "usage", "cmds", "cost_state"}


def rec(type_, ts, **extra):
    return {"type": type_, "timestamp": ts, **extra}


def asst(ts, mid, content=(), **extra):
    return rec("assistant", ts, message={"id": mid, "model": "claude-sonnet-5-5", "content": list(content),
                                         "usage": {"input_tokens": 1, "output_tokens": 5}}, **extra)


class IterRecordsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "s1.jsonl"

    def write(self, path, lines):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join((l if isinstance(l, str) else json.dumps(l)) + "\n" for l in lines), encoding="utf-8")

    def test_every_record_kind_yields_the_documented_shape(self):
        bash = {"type": "tool_use", "name": "Bash", "input": {"command": "git status"}}
        other_tool = {"type": "tool_use", "name": "Read", "input": {"file_path": "/x"}}
        self.write(self.path, [
            rec("user", "2026-10-01T09:00:00.900Z", message={"role": "user", "content": "hi"}),
            rec("user", "2026-10-01T09:00:10Z", origin={"kind": "peer", "from": "dev-1"}, message={"content": "ASK 01: x"}),
            rec("user", "2026-10-01T09:00:20Z", message={"content": "<task-notification>done</task-notification>"}),
            rec("user", "2026-10-01T09:00:30Z", message={"content": [{"type": "tool_result", "content": "ok"}]}),
            asst("2026-10-01T09:01:00Z", "m1", [bash, other_tool]),
            asst("2026-10-01T09:01:01Z", "m1", [bash]),  # same message id, later line
            {"type": "cost-state", "sessionId": "s1", "totalCostUSD": 0.5, "modelUsage": {}},
            "{not json",
            {"type": "queue-operation", "timestamp": "2026-10-01T09:02:00Z"},
            {"type": "agent-name", "agentName": "dev-1"},  # no timestamp: skipped
            "[1, 2]",
        ])
        self.write(self.path.with_suffix("") / "subagents" / "a.jsonl", [asst("2026-10-01T09:03:00Z", "m9")])
        rows = list(st.iter_records(self.path))
        for r in rows:
            self.assertTrue(KEYS <= set(r), r)
        self.assertEqual([r["kind"] for r in rows],
                         ["user", "user", "user", "user", "assistant", "assistant", "other", "other", "assistant"])
        self.assertEqual(rows[0]["ts"], st.parse_ts("2026-10-01T09:00:00Z").timestamp())  # .900 floored
        self.assertIsInstance(rows[0]["ts"], int)
        self.assertIsNone(rows[0]["origin"])
        self.assertEqual(rows[1]["origin"], {"kind": "peer", "from": "dev-1"})
        self.assertEqual(rows[4]["cmds"], ["git status"])
        self.assertEqual([r["msg_id"] for r in rows if r["kind"] == "assistant"], ["m1", "m1", "m9"])
        self.assertEqual(rows[4]["usage"]["output_tokens"], 5)
        self.assertEqual(rows[4]["model"], "claude-sonnet-5-5")
        self.assertEqual(rows[0]["cmds"], [])
        self.assertIsNone(rows[0]["usage"])
        cost = rows[6]
        self.assertEqual(cost["cost_state"]["totalCostUSD"], 0.5)
        self.assertEqual(cost["ts"], rows[5]["ts"])  # the real record has no timestamp: takes the previous one
        self.assertEqual([r["side"] for r in rows], [False] * 8 + [True])
        self.assertEqual(rows[7]["kind"], "other")  # queue-operation

    def test_a_file_of_junk_yields_nothing(self):
        self.write(self.path, ["", "}{", "null", {"timestamp": "not a date", "type": "user"}])
        self.assertEqual(list(st.iter_records(self.path)), [])

    def test_read_session_dedupes_by_message_id_and_flags_subagents(self):
        self.write(self.path, [asst("2026-10-01T09:01:00Z", "m1"), asst("2026-10-01T09:01:05Z", "m1")])
        self.write(self.path.with_suffix("") / "subagents" / "a.jsonl", [asst("2026-10-01T09:03:00Z", "m9")])
        rows, compactions = st.read_session(self.path)
        self.assertEqual([t["side"] for t in rows], [False, True])
        self.assertEqual(compactions, 0)


if __name__ == "__main__":
    unittest.main()
