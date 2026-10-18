import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import squadreport as sr  # noqa: E402
from report_fixtures import Fixture, PLUGIN_ROOT, T0, asst, cost_state, stamp, human, notif, peer, system, tool_result  # noqa: E402

ROLE_KEYS = {"name", "role", "sessions", "respawns", "cache_expiries", "expiry_cost_usd", "transcript_found", "live",
             "buckets_s", "idle_s", "tokens", "cost_usd"}


class Base(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)

    def run_collect(self, final=False, fx=None):
        fx = fx or self.fx
        with mock.patch.dict(os.environ, fx.env()):
            return sr.collect(fx.home, fx.squad, PLUGIN_ROOT, final=final)

    def data(self, **kw):
        d = sr.base_data(self.run_collect(**kw))
        self.check_invariants(d)
        return d

    def check_invariants(self, d):
        t = d["totals"]
        self.assertEqual(sum(t["buckets_s"].values()), t["agent_s"])
        self.assertEqual(t["blocking_s"]["peer"] + t["blocking_s"]["po"], t["buckets_s"]["blocking"])
        self.assertEqual(t["idle_s"]["peer"] + t["idle_s"]["human_input"], t["buckets_s"]["idle"])
        self.assertEqual(sum(sum(r["buckets_s"].values()) for r in d["roles"]), t["agent_s"])
        for r in d["roles"]:
            self.assertEqual(set(r), ROLE_KEYS)
            self.assertEqual(r["idle_s"]["peer"] + r["idle_s"]["human_input"], r["buckets_s"]["idle"])
        for a in d["agents"]:
            self.assertEqual(a["events"], [])
            for s in a["segments"]:
                self.assertEqual(len(s), 5)
                self.assertGreaterEqual(s[1], s[0])
                self.assertIn(s[2], "waib")
                self.assertIsNone(s[3])

    def one(self, recs, **kw):
        self.fx.session("dev1", [recs])
        return self.data(**kw)

    def buckets(self, d):
        return d["totals"]["buckets_s"]


class TimeModel(Base):
    def test_working(self):
        d = self.one([peer(0), asst(10), tool_result(25), system(30)])
        self.assertEqual(self.buckets(d), {"working": 30, "waiting": 0, "blocking": 0, "idle": 0})
        self.assertEqual(d["totals"]["agent_s"], 30)
        self.assertEqual(d["totals"]["stalled_s"], 0)

    def test_stalled(self):
        d = self.one([asst(0), asst(400), asst(410)])
        self.assertEqual(self.buckets(d)["working"], 410)
        self.assertEqual(d["totals"]["stalled_s"], 400)

    def test_task_notification_waiting(self):
        d = self.one([asst(0), notif(100)])
        self.assertEqual(self.buckets(d)["waiting"], 100)

    def test_wait_pattern_and_config_change(self):
        recs = [asst(0, cmd="python3 tests/run_suite.py --tz"), tool_result(200)]
        self.assertEqual(self.one(recs)["totals"]["buckets_s"]["waiting"], 200)
        self.fx.settings.update(wait_patterns=["nothing"], stall_s=150)
        self.fx.write_settings()
        d = self.data()
        self.assertEqual(d["totals"]["buckets_s"]["waiting"], 0)
        self.assertEqual(d["totals"]["stalled_s"], 200)
        self.assertEqual((d["config"]["stall_s"], d["config"]["wait_patterns"]), (150, ["nothing"]))

    def test_queue_operation_does_not_end_gap(self):
        # real transcripts log an `enqueue` record when a message arrives; the user record that follows ends the gap
        d = self.one([asst(0), {"type": "queue-operation", "operation": "enqueue", "timestamp": stamp(50)}, peer(51)])
        self.assertEqual((self.buckets(d)["idle"], self.buckets(d)["working"]), (51, 0))

    def test_idle_peer(self):
        d = self.one([asst(0), peer(50)])
        self.assertEqual((self.buckets(d)["idle"], d["totals"]["idle_s"]["peer"]), (50, 50))

    def test_unanswered_ask_blocks_answered_does_not(self):
        self.fx.messages([(5, "dev1", "tech", "ASK 02: question"), (99, "tech", "dev1", "ANSWER 02: reply")])
        d = self.one([asst(0), asst(10), peer(100), asst(110), peer(300)])
        # 0-10 working; 10-100 blocking on tech; 100-110 working; 110-300 idle (the old ASK is answered)
        self.assertEqual(self.buckets(d), {"working": 20, "waiting": 0, "blocking": 90, "idle": 190})
        self.assertEqual(d["totals"]["blocking_s"], {"peer": 90, "po": 0})
        self.assertEqual(d["agents"][0]["segments"][1], [10, 100, "b", None, "tech"])

    def test_ask_sent_after_gap_start_does_not_block(self):
        self.fx.messages([(50, "dev1", "tech", "BLOCKED 02: stuck")])
        d = self.one([asst(0), peer(100), asst(110), peer(200)])
        self.assertEqual(self.buckets(d)["blocking"], 90)  # only the gap that starts after the BLOCKED
        self.assertEqual(self.buckets(d)["idle"], 100)

    def test_escalation_straddles_gap(self):
        self.fx.inbox([("E1", "t", 100, 200)])
        d = self.one([asst(0), human(150), asst(160), human(300)])
        # 0-100 idle, 100-150 po; 150-160 working; 160-200 po, 200-300 idle
        self.assertEqual(self.buckets(d), {"working": 10, "waiting": 0, "blocking": 90, "idle": 200})
        self.assertEqual(d["totals"]["blocking_s"]["po"], 90)
        self.assertEqual(d["totals"]["idle_s"]["human_input"], 200)
        self.assertEqual(d["agents"][0]["segments"][0], [0, 100, "i", None, None])
        self.assertEqual(d["agents"][0]["segments"][1], [100, 150, "b", None, "PO"])

    def test_human_idle_without_escalation(self):
        d = self.one([asst(0), user_plugin(60)])
        self.assertEqual(d["totals"]["idle_s"]["human_input"], 60)

    def test_two_sessions_not_bridged(self):
        self.fx.session("dev1", [[asst(0), asst(10)], [asst(1000), asst(1010)]])
        d = self.data()
        self.assertEqual(d["totals"]["agent_s"], 20)
        self.assertEqual(d["totals"]["respawn_gap_s"], 990)
        self.assertEqual((d["roles"][0]["sessions"], d["roles"][0]["respawns"]), (2, 1))


def user_plugin(t):
    from report_fixtures import user
    return user(t, "plugin")


class Messages(Base):
    def test_copies_counted_once(self):
        self.fx.messages([(0, "dev1", "qaw", "HANDIN 02: a"), (1, "dev1", "qab", "HANDIN 02: a"), (2, "dev1", "tl", "HANDIN 02: a"),
                          (130, "dev1", "qaw", "HANDIN 02: again"), (5, "dev1", "qaw", "HANDIN 03: other"), (6, "x", "y", "plain words")])
        m = sr.read_messages(self.fx.home / "messages.jsonl")
        self.assertEqual([(x.ts - T0, x.type, x.token) for x in m],
                         [(0, "HANDIN", "02"), (5, "HANDIN", "03"), (6, "", ""), (130, "HANDIN", "02")])

    def test_escalations_seen_to_answer(self):
        self.fx.inbox([("E1", "one", 10, 40), ("E2", "two", 50, None)])
        e = sr.read_escalations(self.fx.home / "inbox.jsonl")
        self.assertEqual([(x.id, x.raised_at - T0, x.answered_at and x.answered_at - T0) for x in e],
                         [("E1", 10, 40), ("E2", 50, None)])


class Cost(Base):
    U = {"input_tokens": 1000, "cache_read_input_tokens": 2000, "cache_creation_input_tokens": 3000, "output_tokens": 500,
         "cache_creation": {"ephemeral_5m_input_tokens": 1000, "ephemeral_1h_input_tokens": 2000}}

    def test_cache_split_unknown_model_and_cost_state(self):
        part = dict(self.U, output_tokens=100)  # an earlier line of the same message: max per field wins
        recs = [asst(0, id="m1", usage=part), asst(5, id="m1", usage=self.U),
                asst(10, id="m2", model="mystery", usage={"input_tokens": 1000}), cost_state("s", 0.02)]
        d = self.one(recs)
        # m1: (1000*1 + 2000*.5 + 1000*2 + 2000*4 + 500*8)/1e6 = 0.016 ; m2 default: 1000*2/1e6 = 0.002
        self.assertEqual(d["totals"]["cost_usd"], 0.018)
        self.assertEqual(d["totals"]["tokens"], {"input": 2000, "cache_read": 2000, "cache_write": 3000, "output": 500})
        self.assertEqual(d["sources"]["unpriced_models"], ["mystery"])
        self.assertEqual((d["totals"]["cost_reported_usd"], d["totals"]["cost_delta_pct"]), (0.02, -10.0))

    def test_subagent_turn_priced_at_own_model(self):
        self.fx.session("dev1", [[asst(0, id="a", usage={"input_tokens": 1000})]],
                        subagent=[asst(1, id="b", model="model-a", usage={"input_tokens": 1000})])
        d = self.data()
        self.assertEqual(d["totals"]["cost_usd"], 0.001 + 0.001)  # both model-a at input 1/M
        self.assertEqual(d["totals"]["agent_s"], 0)  # a subagent record is not agent time

    def test_no_cost_state(self):
        d = self.one([asst(0, usage={"input_tokens": 1000})])
        self.assertIsNone(d["totals"]["cost_reported_usd"])
        self.assertIsNone(d["totals"]["cost_delta_pct"])

    def test_cache_expiry(self):
        big = {"cache_creation_input_tokens": 20000}
        d = self.one([asst(0, usage=big), asst(4000, usage=big), asst(4010, usage=big)])
        r = d["roles"][0]
        self.assertEqual(r["cache_expiries"], 1)
        self.assertEqual(r["expiry_cost_usd"], round(20000 * 4 / 1e6, 4))


class Partial(Base):
    def test_running_scope_partial_final_not(self):
        self.fx.session("dev1", [[asst(0), asst(5)]], status="live")
        d = self.data()
        self.assertEqual((d["scope"]["status"], d["scope"]["partial"], d["scope"]["partial_reasons"]), ("running", True, ["running"]))
        self.assertTrue(d["roles"][0]["live"])
        d = self.data(final=True)
        self.assertEqual((d["scope"]["status"], d["scope"]["partial"]), ("done", False))
        self.assertFalse(d["roles"][0]["live"])

    def test_done_dir_is_not_running(self):
        fx = Fixture(done=True)
        self.addCleanup(fx.close)
        fx.session("dev1", [[asst(0), asst(5)]])
        self.assertFalse(sr.base_data(self.run_collect(fx=fx))["scope"]["partial"])

    def test_missing_transcript(self):
        self.fx.session("dev1", [[asst(0), asst(5)]])
        self.fx.session("ghost", [[asst(0)]], transcript=False)
        d = self.data(final=True)
        self.assertEqual(d["scope"]["partial_reasons"], ["no_transcript:ghost"])
        self.assertTrue(d["scope"]["partial"])
        self.assertEqual([r["transcript_found"] for r in d["roles"]], [True, False])
        self.assertEqual((d["sources"]["agents_total"], d["sources"]["agents_with_transcript"]), (2, 1))

    def test_no_messages_no_tasks_builds(self):
        d = self.one([asst(0), asst(5)], final=True)
        self.assertEqual((d["sources"]["messages"], d["sources"]["escalations"]), (0, 0))
        self.assertEqual(d["totals"]["wall_s"], 5)
        self.assertEqual(d["totals"]["parallelism"], 1.0)

    def test_empty_scope(self):
        d = self.data(final=True)
        self.assertEqual((d["totals"]["wall_s"], d["totals"]["agent_s"], d["scope"]["window"]), (0, 0, {"start": None, "end": None}))

    def test_flat_squad_refused(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        (fx.squad / "roster.md").write_text("# Roster\n", encoding="utf-8")
        with self.assertRaises(sr.Unsupported):
            self.run_collect(fx=fx)

    def test_deadline(self):
        self.fx.session("dev1", [[asst(0), asst(5)]])
        with mock.patch.dict(os.environ, self.fx.env()), self.assertRaises(sr.Deadline):
            sr.collect(self.fx.home, self.fx.squad, PLUGIN_ROOT, deadline=0.0)


class Rules(Base):
    def test_deterministic_no_path_no_text_read_only(self):
        canary = "CANARY-9f3a"
        self.fx.messages([(5, "dev1", "tech", "ASK 02: " + canary)])
        self.fx.inbox([("E1", canary + " title", 100, 200)])
        self.fx.session("dev1", [[user_text(0, canary), asst(10, cmd="echo " + canary), peer(100, canary), asst(110)]])
        before = self.fx.snapshot()
        d1, d2 = self.data(), self.data()
        self.assertEqual(d1, d2)
        s = json.dumps(d1)
        self.assertNotIn(canary, s)
        self.assertNotIn(str(self.fx.root), s)
        self.assertEqual(self.fx.snapshot(), before)


def user_text(t, text):
    from report_fixtures import user
    return user(t, "human", text)


class Config(Base):
    def test_shipped_config_shape(self):
        cfg = json.loads((PLUGIN_ROOT / "templates/report/config.json").read_text(encoding="utf-8"))
        self.assertEqual((cfg["stall_s"], cfg["wait_patterns"], cfg["min_segment_s"]), (300, ["run_suite.py"], 60))
        self.assertIn("default", cfg["prices"])
        self.assertIn("_note", cfg)

    def test_override_is_shallow_merge(self):
        c = sr.load_config(PLUGIN_ROOT, self.fx.squad)
        self.assertEqual(c["stall_s"], 300)
        self.assertEqual(set(c["prices"]), {"model-a", "default"})


if __name__ == "__main__":
    unittest.main()
