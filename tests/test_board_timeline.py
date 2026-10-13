"""Seam A, BRD-02: rows, folded gaps, activation bars, durations and totals in GET /state."""
import json
import time
import unittest
from datetime import datetime, timedelta, timezone

from board_fixture import Fixture

BASE = datetime(2026, 10, 12, 10, 0, 0, tzinfo=timezone.utc)
MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}
TECH = {"agent": "tech-board", "role": "Tech Lead"}
DEV = {"agent": "dev-board-3", "role": "Developer"}


def ts(seconds):
    """ISO timestamp `seconds` after BASE, with milliseconds like the hook writes."""
    t = BASE + timedelta(seconds=seconds)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (t.microsecond // 1000)


class TimelineCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([MANAGER, TECH, DEV])

    def msg(self, t, frm="manager", to="tech-board", iteration=1, **kw):
        return self.fx.message(ts=ts(t), **{"from": frm, "to": to, "iteration": iteration}, **kw)

    def act(self, t, agent, status, iteration=1):
        return self.fx.activity(ts=ts(t), agent=agent, status=status, iteration=iteration)

    def state(self, iteration=None, now=300):
        return self.fx.start(now=ts(now)).state(iteration)

    def bars_of(self, st, agent):
        return [b for b in st["bars"] if b["agent"] == agent]

    def column(self, st, agent):
        return next(c for c in st["columns"] if c["agent"] == agent)


class RowOrderTest(TimelineCase):
    def test_messages_and_status_events_interleave_by_ts(self):
        self.msg(1)
        self.act(2, "dev-board-3", "working")
        self.msg(3, frm="tech-board", to="manager")
        self.act(4, "tech-board", "idle")
        rows = self.state()["rows"]
        self.assertEqual([(r["id"], r["kind"], r["ts"]) for r in rows],
                         [(0, "message", ts(1)), (1, "status", ts(2)), (2, "message", ts(3)),
                          (3, "status", ts(4))])

    def test_tie_puts_message_before_status(self):
        self.act(5, "dev-board-3", "working")
        self.msg(5)
        kinds = [r["kind"] for r in self.state()["rows"]]
        self.assertEqual(kinds, ["message", "status"])

    def test_message_row_carries_its_fields(self):
        self.msg(1, type="HANDIN", task="BRD-02", text="HANDIN BRD-02: x", msg_id="abc")
        row = self.state()["rows"][0]
        self.assertEqual(row, {"id": 0, "kind": "message", "ts": ts(1), "from": "manager",
                               "to": "tech-board", "type": "HANDIN", "task": "BRD-02",
                               "text": "HANDIN BRD-02: x", "msg_id": "abc"})

    def test_status_row_carries_agent_and_status(self):
        self.act(1, "dev-board-3", "working")
        self.assertEqual(self.state()["rows"],
                         [{"id": 0, "kind": "status", "ts": ts(1), "agent": "dev-board-3",
                           "status": "working"}])


class BarStartTest(TimelineCase):
    def test_message_starts_receiver_bar_and_sender_bar(self):
        self.msg(1)
        st = self.state()
        tb, mgr = self.bars_of(st, "tech-board")[0], self.bars_of(st, "manager")[0]
        self.assertEqual((tb["start_row"], tb["start_ts"], tb["self_start"], tb["open"]),
                         (0, ts(1), False, True))
        self.assertEqual((mgr["start_row"], mgr["self_start"], mgr["open"]), (0, True, True))
        self.assertEqual(len(st["bars"]), 2)

    def test_open_bar_is_not_restarted_by_another_message(self):
        self.msg(1)
        self.msg(5)
        st = self.state()
        self.assertEqual([(b["agent"], b["start_row"]) for b in st["bars"]],
                         [("manager", 0), ("tech-board", 0)])

    def test_open_sender_bar_stays_and_idle_receiver_gets_a_woken_bar(self):
        self.act(0, "tech-board", "working")
        self.msg(10, frm="tech-board", to="dev-board-3")
        st = self.state()
        tb = self.bars_of(st, "tech-board")
        self.assertEqual([(b["start_row"], b["self_start"]) for b in tb], [(0, True)])
        dev = self.bars_of(st, "dev-board-3")
        self.assertEqual([(b["start_row"], b["self_start"]) for b in dev], [(1, False)])

    def test_working_without_message_is_a_self_start_with_a_status_row(self):
        self.act(1, "dev-board-3", "working")
        st = self.state()
        self.assertEqual([r["kind"] for r in st["rows"]], ["status"])
        (bar,) = st["bars"]
        self.assertEqual((bar["agent"], bar["start_row"], bar["self_start"], bar["open"]),
                         ("dev-board-3", 0, True, True))


class WakeWindowTest(TimelineCase):
    def test_working_one_second_before_a_message_is_woken_by_it(self):
        self.act(9, "tech-board", "working")
        self.msg(10)
        st = self.state()
        self.assertEqual([r["kind"] for r in st["rows"]], ["message"])
        (bar,) = self.bars_of(st, "tech-board")
        self.assertEqual((bar["start_row"], bar["start_ts"], bar["self_start"]), (0, ts(10), False))

    def test_working_exactly_two_seconds_before_still_counts(self):
        self.act(8, "tech-board", "working")
        self.msg(10)
        st = self.state()
        self.assertEqual([r["kind"] for r in st["rows"]], ["message"])
        self.assertFalse(self.bars_of(st, "tech-board")[0]["self_start"])

    def test_working_three_seconds_before_is_a_self_start(self):
        self.act(7, "tech-board", "working")
        self.msg(10)
        st = self.state()
        self.assertEqual([r["kind"] for r in st["rows"]], ["status", "message"])
        (bar,) = self.bars_of(st, "tech-board")
        self.assertEqual((bar["start_row"], bar["start_ts"], bar["self_start"]), (0, ts(7), True))

    def test_working_one_second_after_the_message_adds_no_row_and_no_bar(self):
        self.msg(10)
        self.act(11, "tech-board", "working")
        st = self.state()
        self.assertEqual([r["kind"] for r in st["rows"]], ["message"])
        (bar,) = self.bars_of(st, "tech-board")
        self.assertEqual((bar["start_row"], bar["self_start"]), (0, False))

    def test_only_a_message_to_that_agent_counts(self):
        self.act(9, "dev-board-3", "working")
        self.msg(10)
        st = self.state()
        self.assertEqual([r["kind"] for r in st["rows"]], ["status", "message"])
        self.assertTrue(self.bars_of(st, "dev-board-3")[0]["self_start"])


class BlockedTest(TimelineCase):
    def test_blocked_without_a_bar_starts_one_and_opens_a_segment(self):
        self.act(10, "dev-board-3", "blocked")
        st = self.state()
        self.assertEqual([(r["kind"], r["status"]) for r in st["rows"]], [("status", "blocked")])
        (bar,) = st["bars"]
        self.assertTrue(bar["self_start"])
        self.assertEqual(bar["blocked"], [{"start_row": 0, "end_row": None, "start_ts": ts(10),
                                           "end_ts": None, "duration_s": 290}])

    def test_working_closes_the_segment_and_emits_a_row(self):
        self.act(0, "dev-board-3", "working")
        self.act(10, "dev-board-3", "blocked")
        self.act(25, "dev-board-3", "working")
        st = self.state()
        self.assertEqual([r["status"] for r in st["rows"]], ["working", "blocked", "working"])
        (bar,) = st["bars"]
        self.assertEqual(bar["blocked"], [{"start_row": 1, "end_row": 2, "start_ts": ts(10),
                                           "end_ts": ts(25), "duration_s": 15}])

    def test_working_with_an_open_bar_and_no_segment_emits_no_row(self):
        self.act(0, "dev-board-3", "working")
        self.act(10, "dev-board-3", "working")
        st = self.state()
        self.assertEqual(len(st["rows"]), 1)
        self.assertEqual(len(st["bars"]), 1)

    def test_a_second_blocked_event_in_an_open_segment_adds_nothing(self):
        self.act(0, "dev-board-3", "blocked")
        self.act(10, "dev-board-3", "blocked")
        st = self.state()
        self.assertEqual(len(st["rows"]), 1)
        self.assertEqual(len(st["bars"][0]["blocked"]), 1)

    def test_idle_closes_an_open_segment_too(self):
        self.act(0, "dev-board-3", "blocked")
        self.act(20, "dev-board-3", "idle")
        (bar,) = self.state()["bars"]
        self.assertEqual((bar["blocked"][0]["end_row"], bar["blocked"][0]["duration_s"]), (1, 20))


class EndTest(TimelineCase):
    def test_idle_and_done_both_close_the_bar_with_a_duration_on_the_row(self):
        self.act(0, "dev-board-3", "working")
        self.act(40, "dev-board-3", "idle")
        self.act(50, "tech-board", "working")
        self.act(75, "tech-board", "done")
        st = self.state()
        self.assertEqual([r.get("duration_s") for r in st["rows"]], [None, 40, None, 25])
        dev = self.bars_of(st, "dev-board-3")[0]
        self.assertEqual((dev["end_row"], dev["end_ts"], dev["open"], dev["duration_s"]),
                         (1, ts(40), False, 40))
        tb = self.bars_of(st, "tech-board")[0]
        self.assertEqual((tb["end_row"], tb["end_ts"], tb["open"], tb["duration_s"]),
                         (3, ts(75), False, 25))

    def test_open_bar_runs_to_now(self):
        self.act(100, "dev-board-3", "working")
        (bar,) = self.state(now=160)["bars"]
        self.assertEqual((bar["open"], bar["end_row"], bar["end_ts"], bar["duration_s"]),
                         (True, None, None, 60))

    def test_idle_without_an_open_bar_emits_nothing(self):
        self.act(1, "dev-board-3", "idle")
        self.act(2, "tech-board", "done")
        st = self.state()
        self.assertEqual((st["rows"], st["bars"]), ([], []))

    def test_unknown_status_and_other_values_are_ignored(self):
        self.act(0, "dev-board-3", "working")
        self.act(5, "dev-board-3", "unknown")
        self.act(6, "dev-board-3", "sleeping")
        self.act(7, "tech-board", "unknown")
        st = self.state()
        self.assertEqual(len(st["rows"]), 1)
        self.assertEqual([b["agent"] for b in st["bars"]], ["dev-board-3"])
        self.assertTrue(st["bars"][0]["open"])

    def test_a_bar_can_start_again_after_it_ended(self):
        self.act(0, "dev-board-3", "working")
        self.act(10, "dev-board-3", "idle")
        self.act(20, "dev-board-3", "working")
        bars = self.bars_of(self.state(), "dev-board-3")
        self.assertEqual([(b["start_row"], b["end_row"]) for b in bars], [(0, 1), (2, None)])


class TotalsTest(TimelineCase):
    def test_two_bars_and_one_blocked_segment_give_exact_totals(self):
        self.act(0, "tech-board", "working")
        self.act(10, "tech-board", "blocked")
        self.act(25, "tech-board", "working")
        self.act(60, "tech-board", "idle")
        self.msg(100)
        self.act(130, "tech-board", "done")
        st = self.state(now=200)
        tb = self.column(st, "tech-board")
        self.assertEqual((tb["working_s"], tb["blocked_s"], tb["wakes"]), (90, 15, 1))
        mgr = self.column(st, "manager")
        self.assertEqual((mgr["working_s"], mgr["blocked_s"], mgr["wakes"]), (100, 0, 0))
        dev = self.column(st, "dev-board-3")
        self.assertEqual((dev["working_s"], dev["blocked_s"], dev["wakes"]), (0, 0, 0))

    def test_working_total_includes_blocked_time_of_an_open_segment(self):
        self.act(0, "dev-board-3", "working")
        self.act(40, "dev-board-3", "blocked")
        col = self.column(self.state(now=100), "dev-board-3")
        self.assertEqual((col["working_s"], col["blocked_s"]), (100, 60))

    def test_durations_floor_per_bar_and_totals_sum_the_integers(self):
        self.act(0, "tech-board", "working")
        self.act(1.999, "tech-board", "idle")
        self.act(10, "tech-board", "working")
        self.act(11.999, "tech-board", "idle")
        st = self.state()
        self.assertEqual([b["duration_s"] for b in self.bars_of(st, "tech-board")], [1, 1])
        self.assertEqual(self.column(st, "tech-board")["working_s"], 2)

    def test_duration_crossing_a_second_boundary_by_a_millisecond(self):
        self.act(0.999, "dev-board-3", "working")
        self.act(2.0, "dev-board-3", "idle")
        self.assertEqual(self.state()["rows"][1]["duration_s"], 1)

    def test_blocked_segment_duration_floors(self):
        self.act(0, "dev-board-3", "working")
        self.act(1, "dev-board-3", "blocked")
        self.act(3.999, "dev-board-3", "working")
        seg = self.state()["bars"][0]["blocked"][0]
        self.assertEqual(seg["duration_s"], 2)

    def test_now_before_the_bar_start_gives_zero_not_negative(self):
        self.act(10, "dev-board-3", "working")
        st = self.state(now=5)
        self.assertEqual(st["bars"][0]["duration_s"], 0)
        self.assertEqual(self.column(st, "dev-board-3")["working_s"], 0)

    def test_open_blocked_segment_before_now_is_zero(self):
        self.act(10, "dev-board-3", "blocked")
        seg = self.state(now=5)["bars"][0]["blocked"][0]
        self.assertEqual(seg["duration_s"], 0)


class FoldTest(TimelineCase):
    def test_gap_of_180_seconds_is_not_folded(self):
        self.act(0, "dev-board-3", "working")
        self.act(180, "dev-board-3", "idle")
        self.assertEqual([r["kind"] for r in self.state()["rows"]], ["status", "status"])

    def test_gap_of_181_seconds_becomes_one_gap_row(self):
        self.act(0, "dev-board-3", "working")
        self.act(181, "dev-board-3", "idle")
        rows = self.state()["rows"]
        self.assertEqual([r["kind"] for r in rows], ["status", "gap", "status"])
        self.assertEqual(rows[1], {"id": 1, "kind": "gap", "ts": ts(0), "seconds": 181,
                                   "from_ts": ts(0), "to_ts": ts(181)})
        self.assertEqual(rows[2]["id"], 2)

    def test_bar_rows_point_past_the_gap_row(self):
        self.act(0, "dev-board-3", "working")
        self.act(500, "dev-board-3", "idle")
        (bar,) = self.state()["bars"]
        self.assertEqual((bar["start_row"], bar["end_row"]), (0, 2))

    def test_gap_seconds_floor(self):
        self.act(0, "dev-board-3", "working")
        self.act(180.999, "dev-board-3", "idle")
        gap = self.state()["rows"][1]
        self.assertEqual((gap["kind"], gap["seconds"]), ("gap", 180))

    def test_no_gap_row_before_the_first_or_after_the_last_row(self):
        self.act(1000, "dev-board-3", "working")
        st = self.state(now=5000)
        self.assertEqual([r["kind"] for r in st["rows"]], ["status"])

    def test_each_long_gap_gets_its_own_row(self):
        self.act(0, "dev-board-3", "working")
        self.act(300, "dev-board-3", "idle")
        self.act(700, "dev-board-3", "working")
        kinds = [r["kind"] for r in self.state()["rows"]]
        self.assertEqual(kinds, ["status", "gap", "status", "gap", "status"])


class IterationFilterTest(TimelineCase):
    def setUp(self):
        super().setUp()
        self.fx.iteration(1)
        self.fx.iteration(2)

    def two_iterations(self):
        self.msg(0)                                      # manager and tech-board bars start (1)
        self.act(10, "tech-board", "idle")               # tech-board bar ends (1)
        self.act(20, "dev-board-3", "working")           # dev bar starts (1)
        self.msg(30, iteration=2)                        # tech-board woken again (2)
        self.act(40, "dev-board-3", "idle", iteration=2)  # dev bar ends in 2
        self.act(50, "tech-board", "done", iteration=2)

    def test_each_iteration_shows_only_its_own_rows_and_bars(self):
        self.two_iterations()
        srv = self.fx.start(now=ts(100))
        one, two = srv.state(1), srv.state(2)
        self.assertEqual([r["ts"] for r in one["rows"]], [ts(0), ts(10), ts(20)])
        self.assertEqual([r["ts"] for r in two["rows"]], [ts(30), ts(40), ts(50)])
        self.assertEqual([(b["agent"], b["start_row"]) for b in one["bars"]],
                         [("manager", 0), ("tech-board", 0), ("dev-board-3", 2)])
        self.assertEqual([(b["agent"], b["start_row"]) for b in two["bars"]],
                         [("tech-board", 0)])

    def test_default_iteration_is_the_highest(self):
        self.two_iterations()
        st = self.fx.start(now=ts(100)).state()
        self.assertEqual(st["selected_iteration"], 2)
        self.assertEqual(len(st["rows"]), 3)

    def test_totals_do_not_change_between_the_two_queries(self):
        self.two_iterations()
        srv = self.fx.start(now=ts(100))
        one, two = srv.state(1), srv.state(2)
        self.assertEqual(one["columns"], two["columns"])
        tb = self.column(one, "tech-board")
        self.assertEqual((tb["working_s"], tb["wakes"]), (10 + 20, 2))
        dev = self.column(one, "dev-board-3")
        self.assertEqual(dev["working_s"], 20)

    def test_bar_closing_in_the_next_iteration_has_no_end_row_in_its_own_view(self):
        self.two_iterations()
        one = self.fx.start(now=ts(100)).state(1)
        (dev,) = [b for b in one["bars"] if b["agent"] == "dev-board-3"]
        self.assertEqual((dev["end_row"], dev["end_ts"], dev["open"], dev["duration_s"]),
                         (None, ts(40), False, 20))

    def test_closing_row_stays_in_the_iteration_it_happens_in(self):
        self.two_iterations()
        two = self.fx.start(now=ts(100)).state(2)
        self.assertEqual(two["rows"][1]["duration_s"], 20)
        self.assertEqual([b["agent"] for b in two["bars"]], ["tech-board"])

    def test_every_row_reference_points_at_a_visible_row(self):
        self.two_iterations()
        srv = self.fx.start(now=ts(100))
        for n in (1, 2):
            st = srv.state(n)
            ids = set(r["id"] for r in st["rows"])
            for bar in st["bars"]:
                self.assertIn(bar["start_row"], ids)
                self.assertIn(bar["end_row"], ids | {None})

    def test_blocked_segment_crossing_the_boundary_keeps_real_times(self):
        self.act(0, "dev-board-3", "working")
        self.act(10, "dev-board-3", "blocked")
        self.act(20, "dev-board-3", "working", iteration=2)
        self.act(30, "dev-board-3", "idle", iteration=2)
        one = self.fx.start(now=ts(100)).state(1)
        (bar,) = one["bars"]
        self.assertEqual((bar["start_row"], bar["end_row"], bar["end_ts"], bar["open"]),
                         (0, None, ts(30), False))
        self.assertEqual(bar["blocked"], [{"start_row": 1, "end_row": None, "start_ts": ts(10),
                                           "end_ts": ts(20), "duration_s": 10}])

    def test_blocked_segment_starting_in_the_next_iteration_has_no_start_row(self):
        self.act(0, "dev-board-3", "working")
        self.act(10, "dev-board-3", "blocked", iteration=2)
        self.act(20, "dev-board-3", "idle", iteration=2)
        one = self.fx.start(now=ts(100)).state(1)
        seg = one["bars"][0]["blocked"][0]
        self.assertEqual((seg["start_row"], seg["start_ts"], seg["end_row"], seg["end_ts"]),
                         (None, ts(10), None, ts(20)))

    def test_open_bar_started_in_an_earlier_iteration_is_still_open_in_its_own_view(self):
        self.act(0, "dev-board-3", "working")
        self.act(50, "tech-board", "working", iteration=2)
        srv = self.fx.start(now=ts(100))
        (dev,) = srv.state(1)["bars"]
        self.assertEqual((dev["open"], dev["end_row"], dev["end_ts"], dev["duration_s"]),
                         (True, None, None, 100))
        self.assertEqual([b["agent"] for b in srv.state(2)["bars"]], ["tech-board"])

    def test_gap_across_the_iteration_boundary_shows_in_neither_view(self):
        self.act(0, "dev-board-3", "working")
        self.act(1000, "dev-board-3", "idle", iteration=2)
        srv = self.fx.start(now=ts(1100))
        for n in (1, 2):
            self.assertEqual([r["kind"] for r in srv.state(n)["rows"]], ["status"])

    def test_gaps_are_computed_over_the_visible_rows_only(self):
        self.act(0, "dev-board-3", "working")
        self.act(100, "tech-board", "working", iteration=2)   # hidden in view 1
        self.act(200, "dev-board-3", "idle")
        srv = self.fx.start(now=ts(300))
        self.assertEqual([r["kind"] for r in srv.state(1)["rows"]], ["status", "gap", "status"])
        self.assertEqual(len(srv.state(2)["rows"]), 1)

    def test_null_iteration_counts_as_the_lowest(self):
        self.fx.message(ts=ts(0), **{"from": "manager", "to": "tech-board", "iteration": None})
        self.fx.activity(ts=ts(10), agent="tech-board", status="idle", iteration=None)
        self.act(20, "dev-board-3", "working", iteration=2)
        srv = self.fx.start(now=ts(100))
        self.assertEqual([r["ts"] for r in srv.state(1)["rows"]], [ts(0), ts(10)])
        self.assertEqual([r["ts"] for r in srv.state(2)["rows"]], [ts(20)])

    def test_without_iteration_files_nothing_is_filtered(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, DEV])
        fx.activity(ts=ts(0), agent="dev-board-3", status="working", iteration=7)
        fx.activity(ts=ts(10), agent="dev-board-3", status="idle", iteration=None)
        st = fx.start(now=ts(100)).state()
        self.assertEqual((st["iteration"], len(st["rows"]), len(st["bars"])), (None, 2, 1))


class RobustnessTest(TimelineCase):
    def test_unknown_agent_in_the_logs_gets_rows_and_a_bar(self):
        self.msg(1, frm="ghost", to="manager")
        self.act(5, "ghost", "idle")
        st = self.state()
        self.assertEqual(len(st["rows"]), 2)
        ghost = self.bars_of(st, "ghost")
        self.assertEqual([(b["start_row"], b["end_row"], b["self_start"]) for b in ghost],
                         [(0, 1, True)])
        self.assertEqual(self.column(st, "ghost")["working_s"], 4)

    def test_message_with_missing_endpoints_does_not_crash(self):
        self.fx.message(ts=ts(1), **{"from": None, "to": None})
        self.fx.message(ts=ts(2), **{"from": "manager", "to": None})
        st = self.state()
        self.assertEqual(len(st["rows"]), 2)
        self.assertEqual([b["agent"] for b in st["bars"]], ["manager"])

    def test_empty_logs_give_empty_timeline(self):
        st = self.state()
        self.assertEqual((st["rows"], st["bars"]), ([], []))

    def test_ten_thousand_records_answer_quickly(self):
        names = ["manager", "tech-board", "dev-board-3", "a1", "a2"]
        msgs, acts = [], []
        for i in range(5000):
            msgs.append(json.dumps({"ts": ts(i * 2), "msg_id": "m%d" % i, "from": names[i % 5],
                                    "to": names[(i + 1) % 5], "type": None, "task": None,
                                    "text": "x", "iteration": 1}))
            acts.append(json.dumps({"ts": ts(i * 2 + 1), "agent": names[(i * 3) % 5],
                                    "status": ["working", "blocked", "idle", "done"][i % 4],
                                    "iteration": 1}))
        self.fx.write("messages.jsonl", "\n".join(msgs) + "\n")
        self.fx.write("activity.jsonl", "\n".join(acts) + "\n")
        srv = self.fx.start(now=ts(20000))
        started = time.monotonic()
        st = srv.state()
        self.assertLess(time.monotonic() - started, 5)
        self.assertGreaterEqual(len(st["rows"]), 5000)


class RetiredAgentTest(TimelineCase):
    """BRD-28 (a), (c), (d): a bar of an agent that is not live ends at its last event."""
    RETIRED = {"agent": "dev-board-3", "role": "Developer", "status": "retired 2026-10-12 (done)"}

    def setUp(self):
        super().setUp()
        self.fx.roster([MANAGER, TECH, self.RETIRED])

    def only_bar(self, st, agent="dev-board-3"):
        (bar,) = self.bars_of(st, agent)
        return bar

    def test_a_retired_agent_with_one_working_record_gets_a_closed_bar_of_zero_seconds(self):
        self.act(10, "dev-board-3", "working")
        bar = self.only_bar(self.state())
        self.assertEqual((bar["open"], bar["end_ts"], bar["duration_s"]), (False, ts(10), 0))

    def test_the_bar_ends_at_the_last_message_in_or_out(self):
        self.act(10, "dev-board-3", "working")
        self.msg(40, frm="dev-board-3", to="tech-board")
        self.msg(70, frm="tech-board", to="dev-board-3")
        st = self.state()
        bar = self.only_bar(st)
        self.assertEqual((bar["open"], bar["end_ts"], bar["duration_s"]), (False, ts(70), 60))
        self.assertEqual(self.column(st, "dev-board-3")["working_s"], 60)

    def test_a_live_agent_with_the_same_records_stays_open_until_now(self):
        self.fx.roster([MANAGER, TECH, dict(self.RETIRED, status="live (respawned 2026-10-14)")])
        self.act(10, "dev-board-3", "working")
        self.msg(40, frm="dev-board-3", to="tech-board")
        st = self.state(now=300)
        bar = self.only_bar(st)
        self.assertEqual((bar["open"], bar["end_ts"], bar["duration_s"]), (True, None, 290))

    def test_an_agent_only_seen_in_the_log_is_closed_at_its_last_event(self):
        self.msg(10, frm="dev-all-9", to="tech-board")
        self.msg(50, frm="tech-board", to="dev-all-9")
        bar = self.only_bar(self.state(), "dev-all-9")
        self.assertEqual((bar["open"], bar["end_ts"], bar["duration_s"]), (False, ts(50), 40))

    def test_an_open_blocked_segment_closes_at_the_same_instant(self):
        self.act(10, "dev-board-3", "working")
        self.act(20, "dev-board-3", "blocked")
        self.msg(60, frm="dev-board-3", to="tech-board")
        st = self.state()
        bar = self.only_bar(st)
        (seg,) = bar["blocked"]
        self.assertEqual((bar["end_ts"], seg["end_ts"], seg["duration_s"]), (ts(60), ts(60), 40))
        self.assertEqual(self.column(st, "dev-board-3")["blocked_s"], 40)

    def test_a_late_message_to_a_retired_agent_extends_the_bar_and_does_not_reopen_it(self):
        self.act(10, "dev-board-3", "working")
        self.act(20, "dev-board-3", "idle")
        self.msg(100, frm="manager", to="dev-board-3")
        bars = self.bars_of(self.state(now=300), "dev-board-3")
        self.assertEqual([(b["start_ts"], b["end_ts"], b["open"]) for b in bars],
                         [(ts(10), ts(20), False), (ts(100), ts(100), False)])

    def test_a_cross_session_address_is_no_column_and_no_bar_but_its_row_stays(self):
        sock = "uds:/run/user/1000/cc-socks/1.sock"
        self.msg(10, frm="tech-board", to=sock)
        st = self.state()
        self.assertNotIn(sock, [c["agent"] for c in st["columns"]])
        self.assertEqual([b["agent"] for b in st["bars"]], ["tech-board"])
        self.assertEqual([r["to"] for r in st["rows"]], [sock])
        self.assertEqual(self.only_bar(st, "tech-board")["open"], True)

    def test_the_roster_status_cell_decides_live_by_its_first_word(self):
        for status, retired in (("live", False), ("Live", False), ("live (respawned 2026-10-14 x)", False),
                                ("retired 2026-10-12 (done)", True), ("gone 2026-10-12", True), ("", True)):
            with self.subTest(status=status):
                self.fx.roster([MANAGER, TECH, dict(self.RETIRED, status=status)])
                st = self.state()
                self.assertEqual(self.column(st, "dev-board-3")["retired"], retired)


class WaitingTest(TimelineCase):
    """BRD-29: `waiting` is a segment inside the bar, not an end of it."""

    def wait_rec(self, t, agent="dev-board-3", detail="monitor"):
        return self.fx.activity(ts=ts(t), agent=agent, status="waiting", detail=detail, iteration=1)

    def only_bar(self, st, agent="dev-board-3"):
        (bar,) = self.bars_of(st, agent)
        return bar

    def test_working_waiting_working_idle_is_one_bar_with_one_segment(self):
        self.act(10, "dev-board-3", "working")
        self.wait_rec(40)
        self.act(100, "dev-board-3", "working")
        self.act(130, "dev-board-3", "idle")
        st = self.state()
        bar = self.only_bar(st)
        (seg,) = bar["waiting"]
        self.assertEqual((bar["open"], bar["duration_s"], seg["duration_s"], seg["detail"]), (False, 120, 60, "monitor"))
        self.assertEqual((seg["start_ts"], seg["end_ts"]), (ts(40), ts(100)))
        col = self.column(st, "dev-board-3")
        self.assertEqual((col["working_s"], col["waiting_s"], col["blocked_s"]), (60, 60, 0))  # 120 s of bar, 60 s of it waiting

    def test_waiting_then_idle_ends_the_bar_and_the_segment_there(self):
        self.act(10, "dev-board-3", "working")
        self.wait_rec(40, detail="shell")
        self.act(70, "dev-board-3", "idle")
        bar = self.only_bar(self.state())
        self.assertEqual((bar["open"], bar["end_ts"], bar["waiting"][0]["end_ts"]), (False, ts(70), ts(70)))

    def test_blocked_during_a_waiting_segment_closes_it_and_opens_the_blocked_one(self):
        self.act(10, "dev-board-3", "working")
        self.wait_rec(40)
        self.act(70, "dev-board-3", "blocked")
        bar = self.only_bar(self.state(now=200))
        self.assertEqual((bar["waiting"][0]["end_ts"], bar["blocked"][0]["start_ts"], bar["blocked"][0]["end_ts"]),
                         (ts(70), ts(70), None))

    def test_waiting_with_no_open_bar_starts_a_self_started_bar(self):
        self.wait_rec(40)
        bar = self.only_bar(self.state(now=100))
        self.assertEqual((bar["self_start"], bar["start_ts"], bar["open"], bar["waiting"][0]["start_ts"]),
                         (True, ts(40), True, ts(40)))

    def test_repeated_waiting_with_the_same_detail_adds_no_segment_a_new_detail_does(self):
        self.act(10, "dev-board-3", "working")
        self.wait_rec(40)
        self.wait_rec(50)
        self.wait_rec(60, detail="shell")
        bar = self.only_bar(self.state(now=100))
        self.assertEqual([(s["detail"], s["start_ts"], s["end_ts"]) for s in bar["waiting"]],
                         [("monitor", ts(40), ts(60)), ("shell", ts(60), None)])
        self.assertEqual(len([r for r in self.state(now=100)["rows"] if r.get("status") == "waiting"]), 2)

    def test_an_open_waiting_segment_runs_to_now(self):
        self.act(10, "dev-board-3", "working")
        self.wait_rec(40)
        st = self.state(now=140)
        self.assertEqual(self.column(st, "dev-board-3")["waiting_s"], 100)
        self.assertEqual(self.column(st, "dev-board-3")["status"], "waiting")

    def test_a_retired_agents_open_waiting_segment_closes_with_its_bar(self):
        self.fx.roster([MANAGER, TECH, {"agent": "dev-board-3", "role": "Developer", "status": "retired 2026-10-12"}])
        self.act(10, "dev-board-3", "working")
        self.wait_rec(40)
        self.msg(70, frm="dev-board-3", to="tech-board")
        st = self.state(now=500)
        seg = self.only_bar(st)["waiting"][0]
        self.assertEqual((seg["end_ts"], seg["duration_s"]), (ts(70), 30))

    def test_a_waiting_manager_is_not_idle(self):
        self.act(10, "manager", "waiting")
        self.assertEqual(self.column(self.state(), "manager")["status"], "waiting")


if __name__ == "__main__":
    unittest.main()
