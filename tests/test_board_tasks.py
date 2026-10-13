"""Seam A, BRD-03: task states with return counts, and needs-you items, read from GET /state."""
import unittest

from board_fixture import Fixture

NOW = "2026-10-12T12:00:00Z"
TASK_KEYS = {"id", "state", "returns", "last_ts", "last_type"}

MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}
DEV = {"agent": "dev-board-1", "role": "Developer"}
TECH = {"agent": "tech-board", "role": "Tech Lead"}

# The live escalations table, verbatim (row 1 answered, row 2 empty).
LIVE_ESCALATIONS = """# Escalations

| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |
|---|---|---|---|---|---|---|
| 1 | 2026-10-12 | goal.md sets size S but also says done = QA whitebox PASS. Which size? | A) S + QA whitebox: Tech Lead plans. B) Full M. C) S exactly as in process.md. | **A.** The spec is complete. | Spawning anyone | 2026-10-12: A |
| 2 | 2026-10-12 | BRD-02..06 must branch from code that has BRD-01. Will you merge `squad/dev-board-1`? | A) PO merges. B) Developers stack. | **A.** One merge unblocks 5 tickets. | BRD-02..06 | |
"""


class TaskCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([MANAGER, DEV, TECH])

    def state(self, iteration=None):
        return self.fx.start(now=NOW).state(iteration)

    def msg(self, type_, task="BRD-03", sender="dev-board-1", to="tech-board", **kw):
        return self.fx.message(**dict({"type": type_, "task": task, "from": sender, "to": to}, **kw))

    def tasks(self, iteration=None):
        return self.state(iteration)["tasks"]

    def task(self, task_id="BRD-03", iteration=None):
        return next(t for t in self.tasks(iteration) if t["id"] == task_id)

    def needs(self, iteration=None):
        return self.state(iteration)["needs_you"]


class StateTableTest(TaskCase):
    def test_decision_makes_building(self):
        self.msg("DECISION")
        self.assertEqual(self.task()["state"], "building")

    def test_status_makes_building(self):
        self.msg("STATUS")
        self.assertEqual(self.task()["state"], "building")

    def test_blocked_makes_blocked(self):
        self.msg("BLOCKED")
        self.assertEqual(self.task()["state"], "blocked")

    def test_handin_makes_checking(self):
        self.msg("HANDIN")
        self.assertEqual(self.task()["state"], "checking")

    def test_fail_makes_returned_and_counts(self):
        self.msg("HANDIN")
        self.msg("FAIL", sender="qaw-board", to="dev-board-1")
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("returned", 1))

    def test_pass_makes_done(self):
        self.msg("HANDIN")
        self.msg("PASS", sender="qaw-board", to="dev-board-1")
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("done", 0))

    def test_ask_and_answer_do_not_change_state(self):
        self.msg("HANDIN")
        self.msg("ASK")
        self.msg("ANSWER", sender="tech-board", to="dev-board-1")
        self.assertEqual(self.task()["state"], "checking")

    def test_first_mention_by_ask_creates_building(self):
        self.msg("ASK")
        self.assertEqual(self.task()["state"], "building")

    def test_first_mention_by_answer_creates_building(self):
        self.msg("ANSWER")
        self.assertEqual(self.task()["state"], "building")

    def test_null_task_creates_nothing(self):
        self.msg("HANDIN", task=None)
        self.assertEqual(self.tasks(), [])

    def test_empty_and_non_string_task_create_nothing(self):
        self.msg("HANDIN", task="")
        self.msg("HANDIN", task=7)
        self.msg("HANDIN", task=["BRD-03"])
        self.assertEqual(self.tasks(), [])

    def test_untyped_message_creates_nothing(self):
        self.msg(None)
        self.msg("CHAT")
        self.assertEqual(self.tasks(), [])

    def test_task_id_is_taken_as_is(self):
        self.msg("DECISION", task="brd-03 ")
        self.assertEqual([t["id"] for t in self.tasks()], ["brd-03 "])

    def test_task_keys_and_last_fields(self):
        self.msg("DECISION")
        rec = self.msg("HANDIN")
        t = self.task()
        self.assertEqual(set(t), TASK_KEYS)
        self.assertEqual((t["last_ts"], t["last_type"]), (rec["ts"], "HANDIN"))

    def test_last_fields_follow_ask_too(self):
        self.msg("HANDIN")
        rec = self.msg("ASK")
        t = self.task()
        self.assertEqual((t["last_ts"], t["last_type"], t["state"]), (rec["ts"], "ASK", "checking"))

    def test_order_is_first_appearance(self):
        self.msg("DECISION", task="BRD-02")
        self.msg("DECISION", task="BRD-01")
        self.msg("PASS", task="BRD-02")
        self.assertEqual([t["id"] for t in self.tasks()], ["BRD-02", "BRD-01"])

    def test_messages_are_applied_in_ts_order_not_log_order(self):
        self.fx.append_jsonl("messages.jsonl", {
            "ts": "2026-10-12T10:00:09.000Z", "msg_id": "late", "from": "qaw-board", "to": "dev-board-1",
            "type": "PASS", "task": "BRD-03", "text": "PASS", "iteration": 1})
        self.fx.append_jsonl("messages.jsonl", {
            "ts": "2026-10-12T10:00:01.000Z", "msg_id": "early", "from": "dev-board-1", "to": "tech-board",
            "type": "HANDIN", "task": "BRD-03", "text": "HANDIN", "iteration": 1})
        self.assertEqual(self.task()["state"], "done")

    def test_bad_log_lines_do_not_break_tasks(self):
        self.fx.append_jsonl("messages.jsonl", "not json")
        self.msg("HANDIN")
        self.assertEqual(self.task()["state"], "checking")


class LoopTest(TaskCase):
    def test_two_returns_then_pass(self):
        for t, s, r in (("HANDIN", "dev-board-1", "qaw-board"), ("FAIL", "qaw-board", "dev-board-1"),
                        ("HANDIN", "dev-board-1", "qaw-board"), ("FAIL", "qaw-board", "dev-board-1")):
            self.msg(t, sender=s, to=r)
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("returned", 2))
        self.msg("HANDIN")
        self.msg("PASS", sender="qaw-board", to="dev-board-1")
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("done", 2))


class ReturnCountTest(TaskCase):
    """`returns` counts HANDIN->FAIL rounds: a FAIL counts only after a HANDIN, or as the first FAIL."""

    def qa_fail(self, sender="qaw-board", to="dev-board-1", **kw):
        return self.msg("FAIL", sender=sender, to=to, **kw)

    def returns(self):
        return self.task()["returns"]

    def test_fan_out_to_three_recipients_is_one_return(self):
        self.msg("HANDIN")
        for to in ("dev-board-1", "manager", "tech-board"):
            self.qa_fail(to=to)
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("returned", 1))

    def test_fan_out_with_a_gap_of_two_seconds_is_one_return(self):
        self.msg("HANDIN", ts="2026-10-12T10:00:00.000Z")
        self.qa_fail(to="dev-board-1", ts="2026-10-12T10:00:10.000Z")
        self.qa_fail(to="manager", ts="2026-10-12T10:00:12.200Z")
        self.assertEqual(self.returns(), 1)

    def test_two_qas_failing_one_handin_is_one_return(self):
        self.msg("HANDIN")
        self.qa_fail(sender="qaw-board")
        self.qa_fail(sender="qab-board")
        self.assertEqual(self.returns(), 1)

    def test_first_fail_without_handin_counts_one(self):
        self.qa_fail()
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("returned", 1))

    def test_second_fail_without_handin_in_between_is_not_counted(self):
        self.qa_fail()
        self.qa_fail()
        self.assertEqual(self.returns(), 1)

    def test_fail_handin_fail_is_two(self):
        self.qa_fail()
        self.msg("HANDIN")
        self.qa_fail()
        self.assertEqual(self.returns(), 2)

    def test_fail_handin_fail_fail_is_two(self):
        self.qa_fail()
        self.msg("HANDIN")
        self.qa_fail()
        self.qa_fail(to="manager")
        self.assertEqual(self.returns(), 2)

    def test_fail_status_fail_is_one(self):
        self.qa_fail()
        self.msg("STATUS")
        self.qa_fail()
        self.assertEqual(self.returns(), 1)

    def test_fail_blocked_fail_is_one(self):
        self.qa_fail()
        self.msg("BLOCKED")
        self.qa_fail()
        self.assertEqual(self.returns(), 1)

    def test_fail_decision_fail_is_one(self):
        self.qa_fail()
        self.msg("DECISION", sender="tech-board", to="dev-board-1")
        self.qa_fail()
        self.assertEqual(self.returns(), 1)

    def test_fan_out_interrupted_by_another_agents_status_is_one(self):
        self.msg("HANDIN")
        self.qa_fail(to="dev-board-1")
        self.msg("STATUS", sender="tech-board", to="manager")
        self.qa_fail(to="manager")
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("returned", 1))

    def test_every_fail_leaves_the_state_returned(self):
        self.qa_fail()
        self.msg("HANDIN")
        self.qa_fail()
        self.qa_fail(to="manager")
        self.assertEqual(self.task()["state"], "returned")

    def test_loop_one_second_apart_counts_each_round(self):
        for t, s, r in (("HANDIN", "dev-board-1", "qaw-board"), ("FAIL", "qaw-board", "dev-board-1"),
                        ("HANDIN", "dev-board-1", "qaw-board"), ("FAIL", "qaw-board", "dev-board-1"),
                        ("HANDIN", "dev-board-1", "qaw-board"), ("PASS", "qaw-board", "dev-board-1")):
            self.msg(t, sender=s, to=r)
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("done", 2))

    def test_handin_fail_handin_fail_one_second_apart_is_two(self):
        for t in ("HANDIN", "FAIL", "HANDIN", "FAIL"):
            self.msg(t)
        self.assertEqual(self.returns(), 2)

    def test_counter_is_per_task(self):
        self.qa_fail(task="BRD-03")
        self.qa_fail(task="BRD-04")
        self.assertEqual((self.task("BRD-03")["returns"], self.task("BRD-04")["returns"]), (1, 1))

    def test_handin_of_another_task_does_not_re_arm(self):
        self.qa_fail(task="BRD-03")
        self.msg("HANDIN", task="BRD-04")
        self.qa_fail(task="BRD-03")
        self.assertEqual(self.task("BRD-03")["returns"], 1)

    def test_pass_does_not_re_arm(self):
        self.msg("HANDIN")
        self.qa_fail()
        self.msg("PASS", sender="qaw-board", to="dev-board-1")
        self.qa_fail()
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("returned", 1))

    def test_fail_then_developer_status_goes_back_to_building(self):
        self.qa_fail()
        self.msg("STATUS", sender="dev-board-1", to="tech-board")
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("building", 1))

    def test_blocked_then_another_agents_status_goes_to_building(self):
        self.msg("BLOCKED")
        self.msg("STATUS", sender="tech-board", to="manager")
        self.assertEqual(self.task()["state"], "building")

    def test_counting_follows_ts_not_log_order(self):
        rows = [("HANDIN", "dev-board-1", "qaw-board", 1), ("FAIL", "qaw-board", "dev-board-1", 2),
                ("FAIL", "qaw-board", "manager", 3), ("HANDIN", "dev-board-1", "qaw-board", 4),
                ("FAIL", "qaw-board", "dev-board-1", 5), ("FAIL", "qaw-board", "manager", 6),
                ("PASS", "qaw-board", "dev-board-1", 7)]
        for type_, sender, to, sec in (rows[6], rows[4], rows[1], rows[3], rows[5], rows[0], rows[2]):
            self.fx.append_jsonl("messages.jsonl", {
                "ts": "2026-10-12T10:00:0%d.000Z" % sec, "msg_id": "m%d" % sec, "from": sender,
                "to": to, "type": type_, "task": "BRD-03", "text": type_, "iteration": 1})
        t = self.task()
        self.assertEqual((t["state"], t["returns"]), ("done", 2))


class DoneStickyTest(TaskCase):
    def setUp(self):
        super().setUp()
        self.msg("HANDIN")
        self.msg("PASS", sender="qaw-board", to="dev-board-1")

    def assert_done_and_follows(self, rec):
        t = self.task()
        self.assertEqual((t["state"], t["returns"], t["last_ts"], t["last_type"]),
                         ("done", 0, rec["ts"], rec["type"]))

    def test_status_naming_the_pass_leaves_done(self):
        self.assert_done_and_follows(self.msg(
            "STATUS", text="STATUS BRD-03: PASS from qaw-board", to="manager"))

    def test_decision_naming_the_pass_leaves_done(self):
        self.assert_done_and_follows(self.msg(
            "DECISION", sender="tech-board", to="manager", text="DECISION BRD-03: PASS by qaw-board"))

    def test_ask_leaves_done(self):
        self.assert_done_and_follows(self.msg("ASK"))

    def test_answer_leaves_done(self):
        self.assert_done_and_follows(self.msg("ANSWER", sender="tech-board", to="dev-board-1"))

    def test_repeated_pass_stays_done(self):
        self.assert_done_and_follows(self.msg("PASS", sender="qaw-board", to="manager"))

    def test_handin_reopens_to_checking(self):
        rec = self.msg("HANDIN")
        t = self.task()
        self.assertEqual((t["state"], t["last_ts"], t["last_type"]), ("checking", rec["ts"], "HANDIN"))

    def test_fail_reopens_to_returned_and_counts(self):
        rec = self.msg("FAIL", sender="qaw-board", to="dev-board-1")
        t = self.task()
        self.assertEqual((t["state"], t["returns"], t["last_ts"], t["last_type"]),
                         ("returned", 1, rec["ts"], "FAIL"))

    def test_blocked_reopens_to_blocked(self):
        rec = self.msg("BLOCKED")
        t = self.task()
        self.assertEqual((t["state"], t["last_ts"], t["last_type"]), ("blocked", rec["ts"], "BLOCKED"))

    def test_blocked_after_done_unblocks_at_the_senders_next_working_event(self):
        self.msg("BLOCKED")
        self.fx.activity(agent="dev-board-1", status="working")
        self.assertEqual(self.task()["state"], "building")

    def test_working_event_of_another_agent_leaves_blocked_after_done(self):
        self.msg("BLOCKED")
        self.fx.activity(agent="tech-board", status="working")
        self.assertEqual(self.task()["state"], "blocked")

    def test_working_event_leaves_a_done_task_done(self):
        self.fx.activity(agent="dev-board-1", status="working")
        self.assertEqual(self.task()["state"], "done")

    def test_done_is_per_task(self):
        self.msg("STATUS", task="BRD-04")
        self.msg("STATUS", task="BRD-04")
        self.assertEqual((self.task("BRD-03")["state"], self.task("BRD-04")["state"]), ("done", "building"))

    def test_sticky_rules_follow_ts_not_log_order(self):
        # written STATUS first, but stamped after the PASS; the PASS is stamped after the HANDIN
        for sec, type_, sender in ((9, "STATUS", "dev-board-1"), (5, "PASS", "qaw-board"),
                                   (1, "HANDIN", "dev-board-1")):
            self.fx.append_jsonl("messages.jsonl", {
                "ts": "2026-10-12T11:00:0%d.000Z" % sec, "msg_id": "x%d" % sec, "from": sender,
                "to": "tech-board", "type": type_, "task": "BRD-07", "text": type_, "iteration": 1})
        self.assertEqual(self.task("BRD-07")["state"], "done")


class RealPatternTest(TaskCase):
    """A small log in the shapes of the live message log, with made-up names and ids."""

    DEV_A, DEV_B, DEV_C = "dev-x-1", "dev-x-2", "dev-x-3"
    QA, LEAD, MGR = "qa-x", "lead-x", "mgr-x"

    def write(self, rows):
        for n, (clock, sender, to, type_, task, text) in enumerate(rows):
            self.fx.append_jsonl("messages.jsonl", {
                "ts": "2026-10-12T09:%sZ" % clock, "msg_id": "r%02d" % n, "from": sender,
                "to": to, "type": type_, "task": task, "text": text, "iteration": 1})

    def test_replay_gives_the_hand_written_states_and_counts(self):
        dev, qa, lead, mgr = self.DEV_A, self.QA, self.LEAD, self.MGR
        self.write([
            # T-1: HANDIN, a FAIL to three recipients 0.2 s apart, the fix, then PASS to three
            ("00:00.000", dev, qa, "HANDIN", "T-1", "HANDIN T-1: commit aaa"),
            ("01:00.100", qa, dev, "FAIL", "T-1", "FAIL T-1 round 1"),
            ("01:00.300", qa, mgr, "FAIL", "T-1", "FAIL T-1 round 1"),
            ("01:00.500", qa, lead, "FAIL", "T-1", "FAIL T-1 round 1"),
            ("01:20.000", lead, dev, "DECISION", "T-1", "DECISION T-1: fix both"),
            ("02:00.000", dev, qa, "HANDIN", "T-1", "HANDIN T-1: commit bbb"),
            ("03:00.100", qa, dev, "PASS", "T-1", "PASS T-1 at bbb"),
            ("03:00.250", qa, mgr, "PASS", "T-1", "PASS T-1 at bbb"),
            ("03:00.400", qa, lead, "PASS", "T-1", "PASS T-1 at bbb"),
            ("03:05.000", dev, mgr, "STATUS", "T-1", "STATUS T-1: PASS from qa-x at bbb"),
            ("03:07.000", lead, mgr, "DECISION", "T-1", "DECISION T-1: PASS by qa-x at bbb"),
            # T-2: a FAIL to two recipients 2.2 s apart, then a PASS and a second PASS 8 minutes later
            ("04:00.000", self.DEV_B, qa, "HANDIN", "T-2", "HANDIN T-2: commit ccc"),
            ("05:00.000", qa, self.DEV_B, "FAIL", "T-2", "FAIL T-2"),
            ("05:02.200", qa, mgr, "FAIL", "T-2", "FAIL T-2"),
            ("06:00.000", self.DEV_B, qa, "HANDIN", "T-2", "HANDIN T-2: commit ddd"),
            ("07:00.000", qa, self.DEV_B, "PASS", "T-2", "PASS T-2"),
            ("15:00.000", qa, mgr, "PASS", "T-2", "PASS T-2 (again)"),
            # T-3: failed, then the Developer reports work again
            ("08:00.000", self.DEV_C, qa, "HANDIN", "T-3", "HANDIN T-3: commit eee"),
            ("09:00.000", qa, self.DEV_C, "FAIL", "T-3", "FAIL T-3"),
            ("09:00.200", qa, mgr, "FAIL", "T-3", "FAIL T-3"),
            ("09:30.000", self.DEV_C, lead, "STATUS", "T-3", "STATUS T-3: fixing"),
        ])
        expected = {"T-1": ("done", 1), "T-2": ("done", 1), "T-3": ("building", 1)}
        got = {t["id"]: (t["state"], t["returns"]) for t in self.tasks()}
        self.assertEqual(got, expected)
        self.assertEqual(self.task("T-1")["last_type"], "DECISION")
        self.assertEqual(self.task("T-2")["last_ts"], "2026-10-12T09:15:00.000Z")


class BlockedBackToBuildingTest(TaskCase):
    def test_working_event_of_the_blocked_sender_returns_to_building(self):
        self.msg("BLOCKED")
        self.fx.activity(agent="dev-board-1", status="working")
        self.assertEqual(self.task()["state"], "building")

    def test_working_event_of_another_agent_changes_nothing(self):
        self.msg("BLOCKED")
        self.fx.activity(agent="tech-board", status="working")
        self.assertEqual(self.task()["state"], "blocked")

    def test_non_working_event_changes_nothing(self):
        self.msg("BLOCKED")
        self.fx.activity(agent="dev-board-1", status="idle")
        self.assertEqual(self.task()["state"], "blocked")

    def test_handin_between_the_two_wins(self):
        self.msg("BLOCKED")
        self.msg("HANDIN")
        self.fx.activity(agent="dev-board-1", status="working")
        self.assertEqual(self.task()["state"], "checking")

    def test_working_event_before_the_blocked_message_is_ignored(self):
        self.fx.activity(agent="dev-board-1", status="working")
        self.msg("BLOCKED")
        self.assertEqual(self.task()["state"], "blocked")

    def test_event_order_is_by_ts_not_log_order(self):
        # the activity line is written first but stamped before the BLOCKED message
        self.fx.append_jsonl("activity.jsonl", {
            "ts": "2026-10-12T10:00:01.000Z", "agent": "dev-board-1", "status": "working", "iteration": 1})
        self.fx.append_jsonl("messages.jsonl", {
            "ts": "2026-10-12T10:00:05.000Z", "msg_id": "b", "from": "dev-board-1", "to": "tech-board",
            "type": "BLOCKED", "task": "BRD-03", "text": "BLOCKED", "iteration": 1})
        self.assertEqual(self.task()["state"], "blocked")

    def test_late_stamped_working_event_written_earlier_still_unblocks(self):
        self.fx.append_jsonl("activity.jsonl", {
            "ts": "2026-10-12T10:00:09.000Z", "agent": "dev-board-1", "status": "working", "iteration": 1})
        self.fx.append_jsonl("messages.jsonl", {
            "ts": "2026-10-12T10:00:05.000Z", "msg_id": "b", "from": "dev-board-1", "to": "tech-board",
            "type": "BLOCKED", "task": "BRD-03", "text": "BLOCKED", "iteration": 1})
        self.assertEqual(self.task()["state"], "building")

    def test_only_the_senders_tasks_unblock(self):
        self.msg("BLOCKED", task="BRD-03")
        self.msg("BLOCKED", task="BRD-04", sender="tech-board", to="manager")
        self.fx.activity(agent="dev-board-1", status="working")
        self.assertEqual(self.task("BRD-03")["state"], "building")
        self.assertEqual(self.task("BRD-04")["state"], "blocked")

    def test_unblock_keeps_last_message_fields(self):
        rec = self.msg("BLOCKED")
        self.fx.activity(agent="dev-board-1", status="working")
        t = self.task()
        self.assertEqual((t["last_ts"], t["last_type"]), (rec["ts"], "BLOCKED"))


class IterationFilterTest(TaskCase):
    def setUp(self):
        super().setUp()
        self.fx.iteration(1)
        self.fx.iteration(2)

    def test_iteration_one_shows_state_at_its_end(self):
        self.msg("HANDIN", iteration=1)
        self.msg("PASS", sender="qaw-board", to="dev-board-1", iteration=2)
        self.assertEqual(self.task(iteration=1)["state"], "checking")
        self.assertEqual(self.task(iteration=2)["state"], "done")

    def test_default_is_the_current_iteration(self):
        self.msg("HANDIN", iteration=1)
        self.msg("PASS", sender="qaw-board", to="dev-board-1", iteration=2)
        self.assertEqual(self.task()["state"], "done")

    def test_task_first_named_later_is_absent(self):
        self.msg("DECISION", task="BRD-09", iteration=2)
        self.assertEqual(self.tasks(iteration=1), [])

    def test_null_iteration_counts_as_lowest(self):
        self.msg("HANDIN", iteration=None)
        self.assertEqual(self.task(iteration=1)["state"], "checking")

    def test_no_iteration_files_filters_nothing(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, DEV])
        fx.message(type="PASS", task="BRD-03", iteration=5)
        self.assertEqual(fx.start(now=NOW).state()["tasks"][0]["state"], "done")

    def test_working_event_of_a_later_iteration_does_not_unblock(self):
        self.msg("BLOCKED", iteration=1)
        self.fx.activity(agent="dev-board-1", status="working", iteration=2)
        self.assertEqual(self.task(iteration=1)["state"], "blocked")
        self.assertEqual(self.task(iteration=2)["state"], "building")

    def test_return_count_and_state_follow_the_filtered_messages(self):
        self.msg("HANDIN", iteration=1)
        for to in ("dev-board-1", "manager", "tech-board"):
            self.msg("FAIL", sender="qaw-board", to=to, iteration=1)
        self.msg("HANDIN", iteration=1)
        self.msg("PASS", sender="qaw-board", to="dev-board-1", iteration=1)
        self.msg("HANDIN", iteration=2)
        self.msg("FAIL", sender="qaw-board", to="dev-board-1", iteration=2)
        first, second = self.task(iteration=1), self.task(iteration=2)
        self.assertEqual((first["state"], first["returns"]), ("done", 1))
        self.assertEqual((second["state"], second["returns"]), ("returned", 2))

    def test_needs_you_is_identical_for_both_queries(self):
        self.fx.escalations([{"answer": ""}])
        self.fx.activity(agent="dev-board-1", status="blocked", iteration=2)
        self.assertEqual(self.needs(iteration=1), self.needs(iteration=2))
        self.assertEqual(len(self.needs(iteration=1)), 2)


class BlockedAgentTest(TaskCase):
    def test_latest_blocked_event_raises_an_item(self):
        rec = self.fx.activity(agent="dev-board-1", status="blocked")
        self.assertEqual(self.needs(), [{
            "id": "blocked:dev-board-1:%s" % rec["ts"], "kind": "blocked",
            "text": "dev-board-1 is blocked", "agent": "dev-board-1", "since": rec["ts"]}])

    def test_later_working_event_removes_it(self):
        self.fx.activity(agent="dev-board-1", status="blocked")
        self.fx.activity(agent="dev-board-1", status="working")
        self.assertEqual(self.needs(), [])

    def test_idle_and_done_remove_it(self):
        self.fx.activity(agent="dev-board-1", status="blocked")
        self.fx.activity(agent="dev-board-1", status="idle")
        self.fx.activity(agent="tech-board", status="blocked")
        self.fx.activity(agent="tech-board", status="done")
        self.assertEqual(self.needs(), [])

    def test_unknown_event_after_blocked_neither_clears_nor_sets(self):
        self.fx.activity(agent="dev-board-1", status="blocked")
        self.fx.activity(agent="dev-board-1", status="unknown")
        self.fx.activity(agent="tech-board", status="working")
        self.fx.activity(agent="tech-board", status="unknown")
        st = self.state()
        self.assertEqual([i["agent"] for i in st["needs_you"]], ["dev-board-1"])
        self.assertEqual(next(c for c in st["columns"] if c["agent"] == "dev-board-1")["status"], "blocked")

    def test_event_order_is_by_ts_not_log_order(self):
        self.fx.append_jsonl("activity.jsonl", {
            "ts": "2026-10-12T10:00:09.000Z", "agent": "dev-board-1", "status": "blocked", "iteration": 1})
        self.fx.append_jsonl("activity.jsonl", {
            "ts": "2026-10-12T10:00:01.000Z", "agent": "dev-board-1", "status": "working", "iteration": 1})
        self.assertEqual([i["since"] for i in self.needs()], ["2026-10-12T10:00:09.000Z"])

    def test_retired_agent_is_skipped(self):
        self.fx.roster([MANAGER, dict(DEV, status="retired"), TECH])
        self.fx.activity(agent="dev-board-1", status="blocked")
        self.assertEqual(self.needs(), [])

    def test_agent_only_in_the_log_is_listed(self):
        self.fx.activity(agent="dev-board-9", status="blocked")
        self.assertEqual([i["agent"] for i in self.needs()], ["dev-board-9"])

    def test_blocked_message_is_not_a_needs_you_item(self):
        self.msg("BLOCKED", sender="dev-board-1", to="tech-board")
        st = self.state()
        self.assertEqual(next(t for t in st["tasks"] if t["id"] == "BRD-03")["state"], "blocked")
        self.assertEqual(st["needs_you"], [])


class EscalationTest(TaskCase):
    def test_unanswered_rows_are_items_answered_are_absent(self):
        self.fx.escalations([{"answer": "2026-10-12: A"}, {"answer": ""}, {"answer": ""}])
        items = self.needs()
        self.assertEqual([i["id"] for i in items], ["escalation:2", "escalation:3"])
        self.assertEqual(items[0]["kind"], "escalation")
        self.assertIsNone(items[0]["agent"])
        self.assertIsNone(items[0]["since"])
        self.assertEqual(items[0]["text"], "q?")

    def test_live_escalations_table_verbatim(self):
        self.fx.write("escalations.md", LIVE_ESCALATIONS)
        items = self.needs()
        self.assertEqual([i["id"] for i in items], ["escalation:2"])
        self.assertTrue(items[0]["text"].startswith("BRD-02..06 must branch"))

    def test_missing_number_falls_back_to_row_index(self):
        self.fx.escalations([{"num": ""}, {"num": 2}])
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:1", "escalation:2"])

    def test_duplicated_number_falls_back_to_row_index(self):
        self.fx.escalations([{"num": 7}, {"num": 7}])
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:1", "escalation:2"])

    def test_short_row_counts_as_unanswered(self):
        self.fx.escalations([{"answer": "A"}])
        with open(self.fx.root / "escalations.md", "a", encoding="utf-8") as f:
            f.write("| 2 | 2026-10-12 | short row? |\n")
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:2"])

    def append_raw(self, *lines):
        with open(self.fx.root / "escalations.md", "a", encoding="utf-8") as f:
            f.write("".join(line + "\n" for line in lines))

    def test_blank_rows_are_not_items(self):
        self.fx.escalations([{"answer": ""}])
        self.append_raw("| | | | | | | |", "|  |", "| | 2026-10-12 | | A) x | | | |")
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:1"])

    def test_whitespace_only_row_between_real_rows(self):
        self.fx.escalations([{"answer": ""}])
        self.append_raw("|   |   |   |   |   |   |   |", "| 3 | 2026-10-12 | third? | A | A | x | |")
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:1", "escalation:3"])

    def test_row_with_only_a_number_is_an_item(self):
        self.fx.escalations([])
        self.append_raw("| 4 | | | | | | |")
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:4"])

    def test_short_row_with_a_number_only_is_unanswered(self):
        self.fx.escalations([])
        self.append_raw("| 5 |")
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:5"])

    def test_short_row_with_a_question_is_unanswered(self):
        self.fx.escalations([])
        self.append_raw("| 1 | 2026-10-12 | short row? |")
        items = self.needs()
        self.assertEqual([(i["id"], i["text"]) for i in items], [("escalation:1", "short row?")])

    def test_placeholder_answer_cells_count_as_answered(self):
        self.fx.escalations([{"answer": "—"}, {"answer": "-"}, {"answer": "  "}])
        self.assertEqual([i["id"] for i in self.needs()], ["escalation:3"])

    def test_missing_file_gives_no_items(self):
        self.assertEqual(self.needs(), [])


FILLED = "# Iteration 1\n\n## PO check-in\n- **Done (with evidence):** BRD-07 passed\n- **Next:** x\n- **Decisions from the PO:**\n"
EMPTY = "# Iteration 1\n\n## PO check-in\n- **Done (with evidence):**\n- **Next:**\n- **Decisions from the PO:**\n"


class ManagerIdleTest(TaskCase):
    def idle_manager(self, status="idle"):
        self.fx.activity(agent="manager", status="working")
        self.fx.activity(agent="manager", status=status)

    def ids(self):
        return [i["id"] for i in self.needs()]

    def test_idle_manager_with_empty_check_in(self):
        self.fx.iteration(1)
        self.idle_manager()
        items = self.needs()
        self.assertEqual([i["id"] for i in items], ["manager_idle:1"])
        self.assertEqual((items[0]["kind"], items[0]["agent"]), ("manager_idle", "manager"))

    def test_done_event_counts_as_idle(self):
        self.fx.iteration(1)
        self.idle_manager("done")
        self.assertEqual(self.ids(), ["manager_idle:1"])

    def test_since_is_the_latest_manager_event(self):
        self.fx.iteration(1)
        self.fx.activity(agent="manager", status="working")
        rec = self.fx.activity(agent="manager", status="idle")
        self.assertEqual(self.needs()[0]["since"], rec["ts"])

    def test_since_follows_a_done_after_an_idle(self):
        self.fx.iteration(1)
        self.fx.activity(agent="manager", status="idle")
        rec = self.fx.activity(agent="manager", status="done")
        self.assertEqual(self.needs()[0]["since"], rec["ts"])

    def test_current_iteration_is_the_highest(self):
        self.fx.iteration(1, FILLED)
        self.fx.iteration(2)
        self.idle_manager()
        self.assertEqual(self.ids(), ["manager_idle:2"])

    def test_not_raised_without_manager_events(self):
        self.fx.iteration(1)
        self.assertEqual(self.ids(), [])

    def test_not_raised_when_manager_is_working(self):
        self.fx.iteration(1)
        self.fx.activity(agent="manager", status="working")
        self.assertEqual(self.ids(), [])

    def test_not_raised_when_manager_is_waiting_on_background_work(self):
        self.fx.iteration(1)
        self.fx.activity(agent="manager", status="waiting", detail="monitor")
        self.assertEqual(self.ids(), [])

    def test_not_raised_when_manager_is_blocked(self):
        self.fx.iteration(1)
        self.fx.activity(agent="manager", status="blocked")
        self.assertEqual([i["kind"] for i in self.needs()], ["blocked"])

    def test_unknown_event_after_idle_changes_nothing(self):
        self.fx.iteration(1)
        self.idle_manager()
        self.fx.activity(agent="manager", status="unknown")
        self.assertEqual(self.ids(), ["manager_idle:1"])

    def test_only_unknown_events_do_not_count_as_events(self):
        self.fx.iteration(1)
        self.fx.activity(agent="manager", status="unknown")
        self.assertEqual(self.ids(), [])

    def test_not_raised_when_done_has_text(self):
        self.fx.iteration(1, "## PO check-in\n- **Done (with evidence):** x\n- **Next:**\n")
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_not_raised_when_next_has_text(self):
        self.fx.iteration(1, "## PO check-in\n- **Done (with evidence):**\n- **Next:** y\n")
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_decisions_from_the_po_alone_does_not_suppress(self):
        self.fx.iteration(1, "## PO check-in\n- **Done (with evidence):**\n- **Next:**\n"
                             "- **Decisions from the PO:** all delegated\n")
        self.idle_manager()
        self.assertEqual(self.ids(), ["manager_idle:1"])

    def test_not_raised_without_iteration_files(self):
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_not_raised_without_a_check_in_section(self):
        self.fx.iteration(1, "# Iteration 1\n\n## Plan\n- x\n")
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_text_after_the_next_heading_is_not_the_check_in(self):
        self.fx.iteration(1, "## PO check-in\n- **Done:**\n- **Next:**\n\n## Retro\n- **Done:** nope\n")
        self.idle_manager()
        self.assertEqual(self.ids(), ["manager_idle:1"])

    def test_check_in_section_not_last(self):
        self.fx.iteration(1, "## PO check-in\n- **Done:** x\n\n## Retro\n- y\n")
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_crlf_line_endings(self):
        self.fx.iteration(1, EMPTY.replace("\n", "\r\n"))
        self.idle_manager()
        self.assertEqual(self.ids(), ["manager_idle:1"])
        self.fx.iteration(1, FILLED.replace("\n", "\r\n"))
        self.assertEqual(self.ids(), [])

    def test_indented_text_on_the_next_line_counts_as_filled(self):
        self.fx.iteration(1, "## PO check-in\n- **Done (with evidence):**\n  BRD-07 passed, see evidence\n"
                             "- **Next:**\n")
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_indented_sub_bullet_counts_as_filled(self):
        self.fx.iteration(1, "## PO check-in\n- **Done:**\n- **Next:**\n  - BRD-08 integration\n")
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_sub_heading_ends_the_bullet_text(self):
        self.fx.iteration(1, "## PO check-in\n- **Done (with evidence):**\n### Notes\ntext under notes\n"
                             "- **Next:**\n")
        self.idle_manager()
        self.assertEqual(self.ids(), ["manager_idle:1"])

    def test_bullet_after_a_sub_heading_still_counts(self):
        self.fx.iteration(1, "## PO check-in\n### Notes\n- **Done:** x\n- **Next:**\n")
        self.idle_manager()
        self.assertEqual(self.ids(), [])

    def test_next_bullet_after_blank_line_does_not_leak_into_done(self):
        self.fx.iteration(1, "## PO check-in\n- **Done:**\n\n- **Next:**\n- **Decisions from the PO:** x\n")
        self.idle_manager()
        self.assertEqual(self.ids(), ["manager_idle:1"])

    def test_no_manager_in_the_roster(self):
        self.fx.roster([DEV, TECH])
        self.fx.iteration(1)
        self.fx.activity(agent="manager", status="working")
        self.fx.activity(agent="manager", status="idle")
        self.assertEqual(self.ids(), [])

    def test_manager_is_found_by_role_not_by_name(self):
        self.fx.roster([dict(MANAGER, agent="boss"), DEV])
        self.fx.iteration(1)
        self.fx.activity(agent="boss", status="idle")
        self.assertEqual(self.ids(), ["manager_idle:1"])

    def test_retired_manager_is_skipped(self):
        self.fx.roster([dict(MANAGER, status="retired"), DEV])
        self.fx.iteration(1)
        self.idle_manager()
        self.assertEqual(self.ids(), [])


class OrderTest(TaskCase):
    def test_blocked_then_escalations_then_manager_idle(self):
        self.fx.iteration(1)
        self.fx.escalations([{"answer": ""}, {"answer": ""}])
        self.fx.activity(agent="manager", status="idle")
        self.fx.activity(agent="tech-board", status="blocked")
        self.fx.activity(agent="dev-board-1", status="blocked")
        kinds = [(i["kind"], i["agent"]) for i in self.needs()]
        self.assertEqual(kinds, [("blocked", "dev-board-1"), ("blocked", "tech-board"),
                                 ("escalation", None), ("escalation", None), ("manager_idle", "manager")])

    def test_blocked_agents_follow_roster_order(self):
        self.fx.roster([MANAGER, dict(DEV, agent="dev-board-2", scope="other"), TECH,
                        dict(DEV, scope="other")])
        self.fx.activity(agent="dev-board-1", status="blocked")
        self.fx.activity(agent="tech-board", status="blocked")
        self.fx.activity(agent="dev-board-2", status="blocked")
        self.assertEqual([i["agent"] for i in self.needs()], ["dev-board-2", "tech-board", "dev-board-1"])


if __name__ == "__main__":
    unittest.main()
