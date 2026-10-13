"""Seam A, BRD-10: squad-board live mode and the herdr activity recorder.

Every test runs the real `bin/squad-board` with no `--replay`, `SQUAD_DIR` on a temp folder and
`HERDR_SOCKET_PATH` on a fake herdr (tests/fake_herdr.py). `HOME` is a temp dir, so nothing real is read.
"""
import fcntl
import importlib.machinery
import importlib.util
import json
import os
import re
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from board_fixture import BIN, Fixture, Server
from fake_herdr import FakeHerdr

DEADLINE_S = 10
TS_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
NOW_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
STARTUP_RE = re.compile(r"^squad-board: http://127\.0\.0\.1:([0-9]+)/\?token=([A-Za-z0-9_-]{22})$")
TOP_KEYS = {"now", "iterations", "iteration", "selected_iteration", "pods", "columns", "rows",
            "bars", "tasks", "needs_you", "live"}
COLUMN_KEYS = {"agent", "role", "pod", "status", "retired", "notes_path", "working_s", "blocked_s", "waiting_s",
               "wakes", "context_tokens", "tokens_in", "tokens_out", "model"}
OUTAGE = "herdr unavailable"
MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}


def wait_until(predicate, what, timeout=DEADLINE_S):
    deadline = time.monotonic() + timeout
    while True:
        value = predicate()
        if value:
            return value
        if time.monotonic() > deadline:
            raise AssertionError("timed out waiting for " + what)
        time.sleep(0.02)


def base_env(home, fake_path=None, squad_dir=None):
    env = dict(os.environ)
    for key in ("SQUAD_DIR", "HERDR_SOCKET_PATH", "SQUAD_NAME"):
        env.pop(key, None)
    env["HOME"] = str(home)
    env["SQUAD_BOARD_RECONNECT_S"] = "0.05"
    if fake_path:
        env["HERDR_SOCKET_PATH"] = str(fake_path)
    if squad_dir:
        env["SQUAD_DIR"] = str(squad_dir)
    return env


def launch(args, env, cwd):
    """Start the real command and wait for its startup line. Returns a board_fixture Server."""
    # Append mode, so a test that rewinds the file to read stderr cannot make the child overwrite it
    handle, name = tempfile.mkstemp(prefix="board-stderr-")
    os.close(handle)
    stderr_file = open(name, "a+b")
    os.unlink(name)
    # SIGINT back to its default: a parent that ignores it (a shell job) would make Python skip its handler
    proc = subprocess.Popen([sys.executable, str(BIN), "--port", "0"] + list(args), stdout=subprocess.PIPE,
                            stderr=stderr_file, env=env, cwd=str(cwd), bufsize=0,
                            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))
    try:
        line = Fixture._read_startup_line(proc, stderr_file)
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    return Server(proc, stderr_file, line)


class LiveCase(unittest.TestCase):
    """A squad folder with a roster, a fake herdr (not yet listening) and a place to start from."""

    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.tmp = Path(tempfile.mkdtemp(prefix="board-live-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)]))
        (self.tmp / "home").mkdir()
        (self.tmp / "work").mkdir()
        self.fake = FakeHerdr(self.tmp / "h.sock")
        self.addCleanup(self.fake.stop)
        self.rows = [MANAGER, {"agent": "tech-board", "role": "Tech Lead", "scope": "board"},
                     {"agent": "dev-board-10"}]
        self.panes = {}

    # --- setup helpers ---------------------------------------------------------------------

    def add_agent(self, name, status="idle", seed=True, rostered=True):
        """A fake pane for `name`. `seed` writes a last record with the same status, so the start-up
        sync has nothing to add and a test sees only what it causes."""
        pane = "wA:p%d" % (len(self.panes) + 1)
        self.panes[name] = pane
        self.fake.add_pane(name, pane, status)
        if seed and rostered:
            self.fx.activity(agent=name, status=status, iteration=None)
        return pane

    def write_roster(self):
        # Fixture.roster truncates and writes in place, and the recorder can read in between and see an
        # empty roster. Write it under another name and rename, so no test races its own write.
        write = self.fx.write
        self.fx.write = lambda name, text: write(name + ".new", text)
        try:
            self.fx.roster(self.rows)
        finally:
            self.fx.write = write
        os.replace(str(self.fx.root / "roster.md.new"), str(self.fx.root / "roster.md"))

    def start(self, env=None, args=(), cwd=None, wait=True, listen=True):
        self.write_roster()
        if listen:
            self.fake.start()
        full = base_env(self.tmp / "home", self.fake.path, self.fx.root)
        for key, value in (env or {}).items():
            if value is None:
                full.pop(key, None)
            else:
                full[key] = value
        self.srv = launch(args, full, cwd or self.tmp / "work")
        self.addCleanup(self.srv.close)
        if wait and listen:
            try:
                self.fake.wait_ready()
            except AssertionError as e:
                raise AssertionError("%s\nserver stderr: %r" % (e, self.srv.stderr()))
        return self.srv

    # --- reading the log -------------------------------------------------------------------

    def lines(self):
        path = self.fx.root / "activity.jsonl"
        return path.read_text().split("\n")[:-1] if path.exists() else []

    def records(self):
        return [json.loads(line) for line in self.lines()]

    def new_records(self, base):
        return [(r["agent"], r["status"], r["iteration"]) for r in self.records()[base:]]

    def barrier(self, base, agent="manager"):
        """Emit one more event for a known agent and wait for its record: everything sent before it
        on the same connection has then been handled. Returns the records after `base`."""
        status = "blocked" if self.records() and self.records()[-1]["status"] == "working" else "working"
        count = len(self.records())
        self.fake.emit_status(self.panes[agent], status)
        wait_until(lambda: len(self.records()) > count, "barrier record")
        return self.new_records(base)


class RecordTest(LiveCase):
    def test_status_event_appends_one_record_with_millisecond_timestamp(self):
        self.add_agent("manager")
        self.start()
        base = len(self.records())
        before = datetime.now(timezone.utc).replace(microsecond=0)
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) > base, "the record")
        after = datetime.now(timezone.utc)
        rec = self.records()[-1]
        self.assertEqual(set(rec), {"ts", "agent", "status", "iteration"})
        self.assertEqual((rec["agent"], rec["status"], rec["iteration"]), ("manager", "working", None))
        self.assertRegex(rec["ts"], TS_RE)
        stamp = datetime.fromisoformat(rec["ts"][:-1] + "+00:00")
        self.assertTrue(before <= stamp <= after, (before, stamp, after))

    def test_every_status_of_every_agent_is_recorded_in_order(self):
        self.add_agent("manager")
        self.add_agent("tech-board")
        self.start()
        base = len(self.records())
        for name, status in (("manager", "working"), ("tech-board", "working"), ("manager", "blocked"),
                             ("tech-board", "done"), ("manager", "idle")):
            self.fake.emit_status(self.panes[name], status)
        wait_until(lambda: len(self.records()) >= base + 5, "five records")
        self.assertEqual(self.new_records(base), [
            ("manager", "working", None), ("tech-board", "working", None), ("manager", "blocked", None),
            ("tech-board", "done", None), ("manager", "idle", None)])

    def test_unknown_or_foreign_status_values_are_not_recorded(self):
        self.add_agent("manager")
        self.start()
        base = len(self.records())
        for status in ("unknown", "bogus", "WORKING", None, 7):
            self.fake.emit_event_for(self.panes["manager"], {
                "data": {"pane_id": self.panes["manager"], "agent_status": status},
                "event": "pane.agent_status_changed"})
        self.assertEqual(self.barrier(base), [("manager", "working", None)])

    def test_every_record_line_ends_with_one_newline(self):
        self.add_agent("manager")
        self.start()
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) >= 2, "record")
        text = (self.fx.root / "activity.jsonl").read_text()
        self.assertTrue(text.endswith("}\n"))
        self.assertNotIn("\n\n", text)


    def test_the_milliseconds_are_the_real_ones(self):
        # the digits after the dot must be this moment's, not any three digits: ten events, each stamped
        # inside the window between "before the event was sent" and "after its record was seen"
        self.add_agent("manager")
        self.start()
        for i in range(10):
            count = len(self.records())
            before = datetime.now(timezone.utc)
            before = before.replace(microsecond=before.microsecond // 1000 * 1000)  # a stamp is floored to ms
            self.fake.emit_status(self.panes["manager"], ("working", "blocked", "idle")[i % 3])
            wait_until(lambda: len(self.records()) > count, "the record")
            after = datetime.now(timezone.utc)
            stamp = datetime.fromisoformat(self.records()[-1]["ts"][:-1] + "+00:00")
            self.assertTrue(before <= stamp <= after, (i, before, stamp, after))


class SubscriptionTest(LiveCase):
    def test_one_status_subscription_per_agent_pane_plus_pane_created(self):
        self.add_agent("manager")
        self.add_agent("tech-board")
        self.start()
        self.assertEqual(len(self.fake.subscribes), 1)
        subs = self.fake.subscribes[0]
        status_subs = [s for s in subs if s["type"] == "pane.agent_status_changed"]
        self.assertEqual(sorted(s["pane_id"] for s in status_subs), sorted(self.panes.values()))
        self.assertEqual([s for s in subs if s["type"] == "pane.created"], [{"type": "pane.created"}])
        self.assertEqual([s for s in subs if s["type"] == "pane.closed"], [{"type": "pane.closed"}])
        self.assertEqual(len(subs), 4)

    def test_snapshot_is_taken_on_its_own_connection_and_after_subscribing(self):
        # herdr resets a subscribed connection that sends another request
        self.add_agent("manager")
        self.start()
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) >= 2, "record on the subscribed connection")
        self.assertEqual([e[0] for e in self.fake.log][:3], ["snapshot", "subscribe", "snapshot"])

    def test_the_agent_without_a_roster_row_still_gets_a_subscription(self):
        # the roster is checked when a record is written (it may gain the row later), not when subscribing
        self.add_agent("manager")
        self.add_agent("ghost", rostered=False)
        self.start()
        panes = [s["pane_id"] for s in self.fake.subscribes[0] if "pane_id" in s]
        self.assertEqual(sorted(panes), sorted(self.panes.values()))


class RosterFilterTest(LiveCase):
    def test_agent_not_in_the_roster_is_never_recorded(self):
        self.add_agent("manager")
        self.add_agent("ghost", status="working", rostered=False)
        self.start()
        base = len(self.records())
        self.fake.emit_status(self.panes["ghost"], "idle")
        self.fake.emit_status(self.panes["ghost"], "working")
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertNotIn("ghost", (self.fx.root / "activity.jsonl").read_text())

    def test_roster_row_added_after_start_is_picked_up(self):
        self.add_agent("manager")
        self.add_agent("late", rostered=False)
        self.start(env={"SQUAD_BOARD_ROSTER_REREAD_S": "0.2"})
        self.rows.append({"agent": "late"})
        self.write_roster()

        def recorded():
            self.fake.emit_status(self.panes["late"], "working")
            self.fake.emit_status(self.panes["late"], "idle")
            return any(r["agent"] == "late" for r in self.records())
        wait_until(recorded, "a record for the agent added to the roster")

    def test_roster_is_reread_at_most_once_per_interval(self):
        self.add_agent("manager")
        self.add_agent("late", rostered=False)
        self.start(env={"SQUAD_BOARD_ROSTER_REREAD_S": "3"})
        started = time.monotonic()
        base = len(self.records())
        self.fake.emit_status(self.panes["late"], "working")      # unknown: counts as the re-read
        self.assertEqual(self.barrier(base), [("manager", "working", None)])  # so it has been handled
        self.rows.append({"agent": "late"})
        self.write_roster()
        self.fake.emit_status(self.panes["late"], "idle")         # still inside the interval
        self.assertEqual(self.barrier(base), [("manager", "working", None), ("manager", "blocked", None)])
        if time.monotonic() - started > 2.5:
            self.skipTest("machine too slow for the 3 s window")
        time.sleep(max(0, 3.2 - (time.monotonic() - started)))
        self.fake.emit_status(self.panes["late"], "working")
        wait_until(lambda: any(r["agent"] == "late" for r in self.records()), "late agent after the interval")


class NewAgentTest(LiveCase):
    def test_pane_created_then_new_rostered_agent_is_recorded_from_then_on(self):
        self.add_agent("manager")
        self.start()
        self.assertEqual(len(self.fake.subscribes), 1)
        self.rows.append({"agent": "newcomer"})
        self.write_roster()
        pane = self.add_agent("newcomer")
        self.fake.emit_created(pane)
        self.fake.wait_ready(2)
        self.assertEqual(len(self.fake.subscribes), 2)
        wait_until(lambda: self.fake.open_streams == 1, "the old subscription to be closed")
        self.assertIn({"type": "pane.agent_status_changed", "pane_id": pane}, self.fake.subscribes[1])
        self.assertIn({"type": "pane.agent_status_changed", "pane_id": self.panes["manager"]},
                      self.fake.subscribes[1])
        base = len(self.records())
        self.fake.emit_status(pane, "working")
        wait_until(lambda: len(self.records()) > base, "the newcomer's record")
        self.assertEqual(self.records()[-1]["agent"], "newcomer")
        self.assertEqual(self.records()[-1]["status"], "working")

    def test_pane_created_with_no_new_agent_does_not_resubscribe(self):
        self.add_agent("manager")
        self.start()
        snapshots = self.fake.snapshots
        self.fake.emit_created("wA:pZZ")
        wait_until(lambda: self.fake.snapshots > snapshots, "a re-snapshot")
        self.assertEqual(len(self.fake.subscribes), 1)

    def test_pane_created_event_before_the_agent_status_event_loses_nothing(self):
        # the new pane is already `working` in the snapshot: the sync after subscribing records it
        self.add_agent("manager")
        self.start()
        self.rows.append({"agent": "newcomer"})
        self.write_roster()
        pane = self.add_agent("newcomer", status="working", seed=False)
        base = len(self.records())
        self.fake.emit_created(pane)
        wait_until(lambda: len(self.records()) > base, "the sync record")
        self.assertEqual(self.new_records(base), [("newcomer", "working", None)])


class InitialSyncTest(LiveCase):
    def test_working_agent_with_no_prior_record_gets_one_record_at_start(self):
        self.add_agent("manager", status="working", seed=False)
        self.start()
        wait_until(lambda: len(self.records()) == 1, "the sync record")
        self.assertEqual(self.new_records(0), [("manager", "working", None)])

    def test_agent_whose_last_record_already_matches_gets_none(self):
        self.add_agent("manager", status="working", seed=True)
        self.start()
        base = len(self.records())
        self.assertEqual(self.barrier(base), [("manager", "blocked", None)])
        self.assertEqual(base, 1)

    def test_a_snapshot_status_the_board_does_not_know_is_not_recorded(self):
        self.add_agent("manager", status="unknown", seed=False)
        self.add_agent("tech-board", status="idle")
        self.start()
        base = len(self.records())
        self.assertEqual(self.barrier(base, "tech-board"), [("tech-board", "working", None)])
        self.assertEqual(base, 1)

    def test_last_record_decides_not_an_earlier_one(self):
        self.fx.activity(agent="manager", status="working", iteration=None)
        self.fx.activity(agent="manager", status="idle", iteration=None)
        self.add_agent("manager", status="working", seed=False)
        self.start()
        wait_until(lambda: len(self.records()) == 3, "the sync record")
        self.assertEqual(self.new_records(2), [("manager", "working", None)])

    def test_each_agent_is_compared_with_its_own_last_record(self):
        self.fx.activity(agent="tech-board", status="working", iteration=None)
        self.add_agent("manager", status="working", seed=False)
        self.add_agent("tech-board", status="working", seed=False)
        self.start()
        wait_until(lambda: len(self.records()) == 2, "one sync record")
        self.assertEqual(self.new_records(1), [("manager", "working", None)])

    def test_sync_after_reconnect_records_only_what_changed_meanwhile(self):
        self.add_agent("manager", status="working")
        self.add_agent("tech-board", status="idle")
        self.start()
        base = len(self.records())
        self.fake.stop()
        self.fake.set_status(self.panes["manager"], "done")    # nobody was told
        self.fake.start()
        self.fake.wait_ready(2)
        wait_until(lambda: len(self.records()) > base, "the reconnect sync record")
        self.assertEqual(self.barrier(base), [("manager", "done", None), ("manager", "working", None)])

    def test_reconnect_with_unchanged_status_adds_nothing(self):
        self.add_agent("manager", status="working")
        self.start()
        self.fake.drop()
        self.fake.wait_ready(2)
        base = len(self.records())
        self.assertEqual(self.barrier(base), [("manager", "blocked", None)])


PANES = Path(__file__).resolve().parent / "fixtures" / "board" / "panes"


def load_board():
    """bin/squad-board as a module, for its pure functions."""
    sys.dont_write_bytecode = True  # no bin/__pycache__ next to the script
    loader = importlib.machinery.SourceFileLoader("squad_board_under_test", str(BIN))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def pane(name):
    return (PANES / (name + ".txt")).read_text()


class ParseBackgroundTest(unittest.TestCase):
    """BRD-29 AC 1: the samples in tests/fixtures/board/panes decide."""

    @classmethod
    def setUpClass(cls):
        cls.parse = staticmethod(load_board().parse_background)

    def test_each_kind_of_background_work_is_found_on_the_mode_line(self):
        for sample, kind in (("agent-1", "agent"), ("monitor-1", "monitor"), ("shell-1", "shell"),
                             ("plural", "monitor"), ("blank-lines", "agent")):
            with self.subTest(sample=sample):
                self.assertEqual(self.parse(pane(sample)), kind)

    def test_no_indicator_when_the_line_has_none_or_the_words_are_above_it(self):
        for sample in ("none", "working-no-indicator", "words-above", "empty"):
            with self.subTest(sample=sample):
                self.assertIsNone(self.parse(pane(sample)))
        self.assertIsNone(self.parse(None))

    def test_the_first_kind_in_the_order_shell_monitor_agent_wins(self):
        self.assertEqual(self.parse("x\n  mode · ← 1 agent · 2 monitors · 1 shell still running\n"), "shell")
        self.assertEqual(self.parse("x\n  mode · ← 1 agent · 2 monitors\n"), "monitor")


class WaitingPollTest(LiveCase):
    """BRD-29: a poller turns `idle` plus a background indicator into `waiting`."""
    POLL = {"SQUAD_BOARD_WAIT_POLL_S": "0.1"}

    def begin(self, status="idle", text="", agents=("manager",), poll=True):
        for name in agents:
            self.add_agent(name, status=status)
        for name in agents:
            self.fake.set_text(name, text)
        return self.start(env=self.POLL if poll else {"SQUAD_BOARD_WAIT_POLL_S": "3600"})

    def waits(self):
        return [(r["status"], r.get("detail")) for r in self.records() if r["agent"] == "manager"][1:]

    def ticks(self, count=3):
        reads = len(self.fake.reads)
        wait_until(lambda: len(self.fake.reads) >= reads + count or self.fake.snapshots > 40, "poll ticks")

    def test_a_tick_with_an_indicator_appends_one_waiting_and_a_second_tick_none(self):
        self.begin(text=pane("monitor-1"))
        wait_until(lambda: self.waits(), "the waiting record")
        self.ticks()
        self.assertEqual(self.waits(), [("waiting", "monitor")])

    def test_a_cleared_indicator_appends_one_idle(self):
        self.begin(text=pane("agent-1"))
        wait_until(lambda: self.waits() == [("waiting", "agent")], "the waiting record")
        self.fake.set_text("manager", pane("none"))
        wait_until(lambda: len(self.waits()) == 2, "the idle record")
        self.ticks()
        self.assertEqual(self.waits(), [("waiting", "agent"), ("idle", None)])

    def test_a_working_pane_is_never_read(self):
        self.begin(status="working", text=pane("monitor-1"))
        time.sleep(0.6)
        self.assertEqual(self.fake.reads, [])
        self.assertEqual(self.waits(), [])

    def test_an_idle_event_with_the_indicator_on_the_pane_appends_waiting_not_idle(self):
        self.begin(status="working", text=pane("shell-1"), poll=False)
        self.fake.set_text("manager", pane("shell-1"))
        self.fake.emit_status(self.panes["manager"], "idle")
        wait_until(lambda: self.waits(), "the record")
        time.sleep(0.2)
        self.assertEqual(self.waits(), [("waiting", "shell")])

    def test_an_idle_event_without_an_indicator_appends_idle(self):
        self.begin(status="working", text=pane("none"), poll=False)
        self.fake.emit_status(self.panes["manager"], "idle")
        wait_until(lambda: self.waits(), "the record")
        self.assertEqual(self.waits(), [("idle", None)])

    def test_a_restart_sync_with_last_waiting_and_herdr_idle_appends_nothing(self):
        self.fx.activity(agent="manager", status="waiting", iteration=None)
        self.add_agent("manager", status="idle", seed=False)
        self.start(env={"SQUAD_BOARD_WAIT_POLL_S": "3600"})
        self.fake.wait_ready()
        time.sleep(0.3)
        self.assertEqual([r["status"] for r in self.records()], ["waiting"])

    def test_an_unrostered_pane_is_never_read_or_written(self):
        self.begin(text=pane("none"), agents=("manager",))
        self.add_agent("stranger", status="idle", rostered=False)
        self.fake.set_text("stranger", pane("monitor-1"))
        self.fake.emit_created(self.panes["stranger"])
        time.sleep(0.6)
        self.assertNotIn("stranger", self.fake.reads)
        self.assertEqual([r["agent"] for r in self.records()], ["manager"])

    def test_a_failed_read_writes_nothing_and_the_poller_goes_on(self):
        self.begin(text=pane("monitor-1"), agents=("manager", "tech-board"))
        self.fake.read_error.add("manager")
        wait_until(lambda: [r for r in self.records() if r["agent"] == "tech-board" and r["status"] == "waiting"],
                   "the other pane's waiting record")
        self.assertEqual([r for r in self.records() if r["agent"] == "manager" and r["status"] == "waiting"], [])
        self.fake.read_error.clear()
        wait_until(lambda: self.waits(), "the record once the read works")

    def test_the_interval_comes_from_the_environment(self):
        self.begin(text=pane("none"), poll=False)  # 3600 s: after the start there is no tick
        time.sleep(0.5)
        self.assertEqual(self.fake.reads, [])


class ClosedPaneTest(LiveCase):
    """BRD-28 (b): herdr sends no idle when a pane closes, so the snapshot decides and `done` is written."""

    def close_pane(self, name, emit=True):
        pane = self.panes[name]
        self.fake.rows[:] = [r for r in self.fake.rows if r["pane_id"] != pane]
        if emit:
            self.fake.send_raw(json.dumps({"event": "pane.closed", "data": {"pane_id": pane}}).encode() + b"\n")

    def test_sync_writes_done_for_a_rostered_agent_missing_from_the_snapshot(self):
        self.add_agent("manager")
        self.fx.activity(agent="dev-board-10", status="working", iteration=None)
        self.start()
        wait_until(lambda: len(self.records()) == 3, "the done record")
        self.assertEqual(self.new_records(2), [("dev-board-10", "done", None)])

    def test_missing_agent_whose_last_status_is_done_or_with_no_record_gets_nothing(self):
        self.add_agent("manager")
        self.fx.activity(agent="dev-board-10", status="done", iteration=None)
        self.start()
        base = len(self.records())
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertEqual(base, 2)  # the seed and the done; tech-board has no record and got none

    def test_a_pane_that_disappears_gets_one_done_and_a_second_sync_adds_none(self):
        self.add_agent("manager")
        self.add_agent("tech-board", status="working")
        self.start()
        base = len(self.records())
        snapshots = self.fake.snapshots
        self.close_pane("tech-board")
        wait_until(lambda: len(self.records()) > base, "the done record")
        self.assertEqual(self.new_records(base), [("tech-board", "done", None)])
        self.fake.emit_created("wA:pZZ")  # another sync
        wait_until(lambda: self.fake.snapshots > snapshots + 1, "a second sync")
        self.barrier(base)
        self.assertEqual([r for r in self.new_records(base) if r[0] == "tech-board"], [("tech-board", "done", None)])

    def test_the_pane_closed_event_triggers_the_resync(self):
        self.add_agent("manager")
        self.add_agent("tech-board", status="working")
        self.start()
        base, snapshots = len(self.records()), self.fake.snapshots
        self.close_pane("tech-board", emit=False)
        self.assertEqual(self.fake.snapshots, snapshots)
        self.fake.send_raw(b'{"event": "pane.closed", "data": {"pane_id": "wA:p2"}}\n')
        wait_until(lambda: len(self.records()) > base, "the done record")
        self.assertEqual(self.new_records(base), [("tech-board", "done", None)])

    def test_an_empty_snapshot_writes_nothing(self):
        self.add_agent("manager", status="working")
        self.add_agent("tech-board", status="working")
        self.start()
        base = len(self.records())
        self.fake.rows[:] = []
        self.fake.send_raw(b'{"event": "pane.closed", "data": {"pane_id": "wA:p1"}}\n')
        snapshots = self.fake.snapshots
        wait_until(lambda: self.fake.snapshots > snapshots, "the sync")
        time.sleep(0.2)
        self.assertEqual(len(self.records()), base)

    def test_an_agent_that_is_not_on_the_roster_is_never_written(self):
        self.add_agent("manager")
        self.add_agent("stranger", status="working", rostered=False)
        self.fx.activity(agent="stranger", status="working", iteration=None)
        self.start()
        base = len(self.records())
        self.assertEqual(self.barrier(base), [("manager", "blocked", None)])


class IterationTagTest(LiveCase):
    def test_null_with_no_iteration_files(self):
        self.add_agent("manager")
        self.start()
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) >= 2, "record")
        self.assertIsNone(self.records()[-1]["iteration"])

    def test_highest_numbered_file_not_alphabetical_and_template_ignored(self):
        for n in (2, 10, 9):
            self.fx.iteration(n)
        self.fx.write("iterations/TEMPLATE.md", "x")
        self.fx.write("iterations/99x.md", "x")
        self.add_agent("manager")
        self.start()
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) >= 2, "record")
        self.assertEqual(self.records()[-1]["iteration"], 10)

    def test_a_file_added_between_two_events_changes_the_tag(self):
        self.fx.iteration(2)
        self.add_agent("manager")
        self.start()
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) >= 2, "first record")
        self.fx.iteration(3)
        self.fake.emit_status(self.panes["manager"], "idle")
        wait_until(lambda: len(self.records()) >= 3, "second record")
        self.assertEqual([r["iteration"] for r in self.records()[1:]], [2, 3])

    def test_a_directory_named_like_an_iteration_does_not_count(self):
        self.fx.iteration(1)
        (self.fx.root / "iterations" / "7.md").mkdir()
        self.add_agent("manager")
        self.start()
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) >= 2, "record")
        self.assertEqual(self.records()[-1]["iteration"], 1)


class ReconnectTest(LiveCase):
    def outage_lines(self):
        return [ln for ln in self.srv.stderr().splitlines() if OUTAGE in ln]

    def test_herdr_absent_at_start_server_answers_and_one_line_per_outage(self):
        self.add_agent("manager")
        self.start(listen=False)
        self.assertEqual(self.srv.state()["columns"][0]["agent"], "manager")
        wait_until(self.outage_lines, "the outage line")
        time.sleep(0.6)                                       # a dozen retries at 0.05 s and doubling
        self.assertEqual(len(self.outage_lines()), 1)
        self.assertNotIn("Traceback", self.srv.stderr())
        self.assertEqual(self.srv.get("/state")[0], 200)

    def test_records_start_when_herdr_comes_up_later(self):
        self.add_agent("manager", status="working", seed=False)
        self.start(listen=False)
        wait_until(self.outage_lines, "the outage line")
        self.fake.start()
        wait_until(lambda: len(self.records()) == 1, "sync record after herdr appeared")
        self.assertEqual(self.new_records(0), [("manager", "working", None)])

    def test_records_resume_after_a_dropped_connection(self):
        self.add_agent("manager")
        self.start()
        self.fake.drop()
        self.fake.wait_ready(2)
        base = len(self.records())
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) > base, "record after reconnect")
        self.assertEqual(self.new_records(base), [("manager", "working", None)])

    def test_a_second_outage_prints_a_second_line_and_a_healthy_start_none(self):
        self.add_agent("manager")
        self.start()
        self.assertEqual(self.outage_lines(), [])
        self.fake.stop()
        wait_until(self.outage_lines, "first outage line")
        time.sleep(0.4)
        self.assertEqual(len(self.outage_lines()), 1)
        self.fake.start()
        self.fake.wait_ready(2)
        self.fake.stop()
        wait_until(lambda: len(self.outage_lines()) == 2, "second outage line")
        self.assertNotIn("Traceback", self.srv.stderr())

    def test_a_dropped_connection_is_an_outage_of_one_line_even_if_herdr_is_back_at_once(self):
        self.add_agent("manager")
        self.start()
        self.fake.drop()
        self.fake.wait_ready(2)
        self.assertEqual(len(self.outage_lines()), 1)


    def test_a_herdr_that_accepts_and_never_answers_is_an_outage_not_a_hang(self):
        class Silent(FakeHerdr):
            """Takes the connection and the request, and says nothing."""
            release = threading.Event()

            def _serve(self, conn):
                self.release.wait(30)
                conn.close()

        healthy = self.fake
        self.add_agent("manager", status="working", seed=False)       # healthy has the pane
        silent = Silent(self.tmp / "h.sock")
        self.addCleanup(silent.release.set)
        self.addCleanup(silent.stop)
        self.fake = silent
        self.start(wait=False)
        self.fake = healthy
        wait_until(self.outage_lines, "the outage line after the request timeout", timeout=12)
        time.sleep(0.4)
        self.assertEqual(len(self.outage_lines()), 1)
        self.assertNotIn("Traceback", self.srv.stderr())
        self.assertEqual(self.srv.get("/state")[0], 200)
        silent.release.set()
        silent.stop()
        healthy.start()
        wait_until(lambda: len(self.records()) == 1, "the record from the healthy herdr", timeout=12)
        self.assertEqual(self.new_records(0), [("manager", "working", None)])


class Closing(FakeHerdr):
    """Accepts every connection and hangs up at once, counting them."""
    accepted = 0

    def _serve(self, conn):
        self.accepted += 1
        conn.close()


class BackoffTest(LiveCase):
    def test_retries_slow_down_by_doubling(self):
        self.fake = Closing(self.tmp / "closing.sock")
        self.addCleanup(self.fake.stop)
        self.add_agent("manager")
        self.start(env={"SQUAD_BOARD_RECONNECT_S": "0.1"}, wait=False)
        time.sleep(1.45)                                    # waits 0.1 0.2 0.4 0.8: 5 attempts, never 15
        self.assertTrue(3 <= self.fake.accepted <= 6, self.fake.accepted)

    def test_the_wait_stops_doubling_at_the_cap(self):
        self.fake = Closing(self.tmp / "closing.sock")
        self.addCleanup(self.fake.stop)
        self.add_agent("manager")
        self.start(env={"SQUAD_BOARD_RECONNECT_S": "0.1", "SQUAD_BOARD_RECONNECT_CAP_S": "0.2"}, wait=False)
        time.sleep(2.0)                                     # capped: about 11 attempts; uncapped, 5
        self.assertGreaterEqual(self.fake.accepted, 8)

    def test_the_wait_starts_over_after_a_good_connection(self):
        self.add_agent("manager")
        self.start(env={"SQUAD_BOARD_RECONNECT_S": "0.1"}, listen=False)
        time.sleep(1.2)                                     # four failures: the next wait would be 1.6 s
        self.fake.start()
        self.fake.wait_ready()
        begun = time.monotonic()
        self.fake.drop()
        self.fake.wait_ready(2)
        self.assertLess(time.monotonic() - begun, 1.0)

    def test_a_quiet_subscription_is_not_an_outage(self):
        self.add_agent("manager")
        self.start()
        time.sleep(5.6)                                     # longer than any request timeout
        self.assertNotIn(OUTAGE, self.srv.stderr())
        base = len(self.records())
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertEqual(len(self.fake.subscribes), 1)


class RobustTest(LiveCase):
    def setUp(self):
        super().setUp()
        self.add_agent("manager")

    def test_garbage_frames_are_skipped(self):
        self.start()
        base = len(self.records())
        pane = self.panes["manager"]
        frames = [b"not json at all\n", b"[1, 2, 3]\n", b"null\n", b'"string"\n', b"{}\n",
                  b'{"event": 5, "data": 5}\n', b'{"event": "pane.agent_status_changed"}\n',
                  b'{"event": "pane.agent_status_changed", "data": []}\n',
                  b'{"event": "pane.agent_status_changed", "data": {"pane_id": 7, "agent_status": "working"}}\n',
                  b'{"event": "pane.agent_status_changed", "data": {"pane_id": "%s"}}\n' % pane.encode(),
                  b'{"event": "something.else", "data": {"pane_id": "%s", "agent_status": "working"}}\n' % pane.encode(),
                  b"\n", b"\xff\xfe\x00\n", b"[" * 100000 + b"\n"]
        for frame in frames:
            self.fake.send_raw(frame)
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertNotIn("Traceback", self.srv.stderr())
        self.assertNotIn(OUTAGE, self.srv.stderr())
        self.assertEqual(len(self.fake.subscribes), 1)

    def test_event_for_unknown_pane_resnapshots_then_is_skipped(self):
        self.start()
        base = len(self.records())
        snapshots = self.fake.snapshots
        self.fake.send_raw(json.dumps({"data": {"agent": "claude", "agent_status": "working", "pane_id": "wA:pZ9",
                                                "workspace_id": "wA"}, "event": "pane.agent_status_changed"}).encode() + b"\n")
        wait_until(lambda: self.fake.snapshots > snapshots, "the re-snapshot")
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertEqual(len(self.fake.subscribes), 1)

    def test_event_for_a_pane_that_appeared_unannounced_is_found_by_the_resnapshot(self):
        self.start()
        self.rows.append({"agent": "newcomer"})
        self.write_roster()
        pane = self.add_agent("newcomer", status="working", seed=False)
        self.fake.send_raw(json.dumps({"data": {"agent_status": "working", "pane_id": pane},
                                       "event": "pane.agent_status_changed"}).encode() + b"\n")
        wait_until(lambda: any(r["agent"] == "newcomer" for r in self.records()), "the newcomer's record")
        self.fake.wait_ready(2)
        self.assertEqual([r["agent"] for r in self.records()].count("newcomer"), 1)
        base = len(self.records())
        self.fake.emit_status(pane, "idle")
        wait_until(lambda: len(self.records()) > base, "event on the new subscription")

    def test_frames_that_are_not_the_reply_are_skipped_while_waiting_for_it(self):
        self.fake.stray = (b'{"id": "someone-else", "result": {"type": "session_snapshot", "snapshot": {"agents": []}}}\n'
                           b'{"id": "someone-else", "error": {"code": "x", "message": "not ours"}}\n'
                           b'{"event": "pane.created", "data": {}}\n')
        self.start()
        base = len(self.records())
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertNotIn(OUTAGE, self.srv.stderr())
        self.assertEqual(len(self.fake.subscribes), 1)

    def test_snapshot_entries_without_a_usable_name_or_pane_are_ignored(self):
        self.fake.odd_agents = [{"name": 5, "pane_id": "wA:p91", "agent_status": "working"},
                                {"name": "", "pane_id": "wA:p92", "agent_status": "working"},
                                {"pane_id": "wA:p93", "agent_status": "working"},
                                {"name": "no-pane", "agent_status": "working"},
                                {"name": "odd-pane", "pane_id": 7, "agent_status": "working"},
                                "a string", None, 3]
        self.start()
        panes = [s["pane_id"] for s in self.fake.subscribes[0] if "pane_id" in s]
        self.assertEqual(panes, [self.panes["manager"]])
        self.assertNotIn(OUTAGE, self.srv.stderr())
        self.assertEqual(len(self.records()), 1)  # the seeded one; nothing for the odd entries

    def test_a_deeply_nested_frame_ahead_of_a_reply_is_skipped(self):
        self.fake.stray = b"[" * 100000 + b"\n"                      # past the recursion limit
        self.start()
        self.assertNotIn(OUTAGE, self.srv.stderr())
        self.assertNotIn("Traceback", self.srv.stderr())
        base = len(self.records())
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertEqual(len(self.fake.subscribes), 1)

    def test_replies_of_the_wrong_shape_mean_no_agents_not_a_crash(self):
        for result in ([1], "text", 5, {"snapshot": "x"}, {"snapshot": [1, 2]}, {"snapshot": {"agents": "x"}}):
            with self.subTest(result=result):
                class Odd(FakeHerdr):
                    def _answer(self, conn, line):
                        request = json.loads(line)
                        conn.sendall(json.dumps({"id": request["id"], "result": result}).encode() + b"\n")
                        return False
                tmp = Path(tempfile.mkdtemp(prefix="board-odd-"))
                self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(tmp)]))
                self.fake = Odd(tmp / "odd.sock")
                self.addCleanup(self.fake.stop)
                self.start(wait=False)
                time.sleep(0.6)
                self.assertNotIn(OUTAGE, self.srv.stderr())
                self.assertNotIn("Traceback", self.srv.stderr())
                self.assertEqual(self.srv.get("/state")[0], 200)
                self.assertEqual(len(self.lines()), 1)            # only the seeded one
                self.srv.close()

    def test_one_megabyte_lines_are_survived(self):
        self.start()
        base = len(self.records())
        self.fake.send_raw(b"x" * 1000000 + b"\n")
        self.fake.send_raw(b'"' + b"y" * 1000000 + b'"\n')
        self.fake.send_raw(b'{"event": "pane.agent_status_changed", "data": {"pane_id": "' + b"z" * 1000000 + b'"}}\n')
        self.assertEqual(self.barrier(base), [("manager", "working", None)])
        self.assertEqual(self.srv.state()["live"], True)
        self.assertNotIn(OUTAGE, self.srv.stderr())

    def test_a_valid_event_over_the_cap_is_dropped_whole(self):
        self.start()
        base = len(self.records())
        pane = self.panes["manager"].encode()
        self.fake.send_raw(b'{"event": "pane.agent_status_changed", "data": {"pane_id": "' + pane +
                           b'", "agent_status": "working", "pad": "' + b"p" * (9 << 20) + b'"}}\n')
        self.assertEqual(self.barrier(base), [("manager", "working", None)])    # only the barrier's own
        self.assertEqual(len(self.records()), base + 1)

    def test_a_line_over_the_cap_is_dropped_whole_and_the_next_frame_still_counts(self):
        self.start()
        base = len(self.records())
        chunk = b"w" * (1 << 20)
        for _ in range(10):                                   # 10 MiB with no newline yet
            self.fake.send_raw(chunk)
        self.fake.send_raw(b"tail of the long line\n")
        self.assertEqual(self.barrier(base), [("manager", "working", None)])

    def test_an_error_reply_to_the_subscription_is_an_outage_not_a_crash(self):
        class Refusing(FakeHerdr):
            def _answer(self, conn, line):
                request = json.loads(line)
                if request["method"] == "events.subscribe":
                    conn.sendall(self._error(request["id"], "nope"))
                    return False
                return super()._answer(conn, line)
        self.fake = Refusing(self.tmp / "refusing.sock")
        self.addCleanup(self.fake.stop)
        self.fake.add_pane("manager", "wA:p1", "idle")
        self.start(wait=False)
        wait_until(lambda: [ln for ln in self.srv.stderr().splitlines() if OUTAGE in ln], "outage line")
        self.assertNotIn("Traceback", self.srv.stderr())
        self.assertEqual(self.srv.get("/state")[0], 200)

    def test_a_snapshot_of_odd_shape_is_skipped_not_a_crash(self):
        class Odd(FakeHerdr):
            def _answer(self, conn, line):
                request = json.loads(line)
                conn.sendall(json.dumps({"id": request["id"], "result": {"snapshot": {"agents": [
                    5, {"name": 1, "pane_id": "wA:p1", "agent_status": "idle"}, {"pane_id": "x"}]}}}).encode() + b"\n")
                return False
        self.fake = Odd(self.tmp / "odd.sock")
        self.addCleanup(self.fake.stop)
        self.start(wait=False)
        time.sleep(0.5)
        self.assertNotIn("Traceback", self.srv.stderr())
        self.assertEqual(self.srv.get("/state")[0], 200)
        self.assertEqual(len(self.lines()), 1)                # only the seeded one


class AppendSafetyTest(LiveCase):
    def test_the_write_waits_for_the_flock(self):
        self.add_agent("manager")
        self.start()
        base = len(self.records())
        fd = os.open(str(self.fx.root / "activity.jsonl"), os.O_RDONLY)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        self.fake.emit_status(self.panes["manager"], "working")
        time.sleep(0.5)
        self.assertEqual(len(self.records()), base)
        fcntl.flock(fd, fcntl.LOCK_UN)
        wait_until(lambda: len(self.records()) > base, "the record after the lock was released")

    def test_two_recorders_on_one_folder_never_split_a_line(self):
        big = "big-" + "x" * 60000                              # a record far larger than any pipe buffer
        self.rows.append({"agent": big})
        self.add_agent(big)
        second = FakeHerdr(self.tmp / "h2.sock")
        self.addCleanup(second.stop)
        second.add_pane(big, "wA:p1", "idle")
        self.start()
        second.start()
        other = launch([], base_env(self.tmp / "home", second.path, self.fx.root), self.tmp / "work")
        self.addCleanup(other.close)
        second.wait_ready()
        before = len(self.lines())
        per = 40
        statuses = ["working", "blocked", "idle", "done"]

        def burst(fake):
            for i in range(per):
                fake.emit_status("wA:p1", statuses[i % 4])
        threads = [threading.Thread(target=burst, args=(f,)) for f in (self.fake, second)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        wait_until(lambda: len(self.lines()) >= before + 2 * per, "all records", timeout=30)
        for line in self.lines():
            rec = json.loads(line)                              # a split or interleaved line fails here
            self.assertEqual(rec["agent"], big)
        self.assertEqual(len(self.lines()), before + 2 * per)

    def test_messages_log_is_not_touched_and_a_hook_writer_runs_alongside(self):
        self.add_agent("manager")
        self.start()
        path = self.fx.root / "messages.jsonl"
        written = []

        def hook():
            for i in range(50):
                line = json.dumps({"ts": "2026-10-12T10:00:00.000Z", "msg_id": "h-%d" % i, "from": "a",
                                   "to": "b", "text": "t", "iteration": 1})
                with open(path, "a") as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    f.write(line + "\n")
                written.append(line)
        writer = threading.Thread(target=hook)
        writer.start()
        base = len(self.records())
        for i in range(10):
            self.fake.emit_status(self.panes["manager"], ["working", "idle"][i % 2])
        writer.join()
        wait_until(lambda: len(self.records()) >= base + 10, "ten records")
        self.assertEqual(path.read_text().split("\n")[:-1], written)


    def test_an_unwritable_log_is_its_own_line_and_not_a_herdr_outage(self):
        self.add_agent("manager")
        log = self.fx.root / "activity.jsonl"
        log.unlink()
        log.mkdir()                                               # a directory where the log should be
        self.start()
        subscribes = len(self.fake.subscribes)
        pane = self.panes["manager"]

        def write_lines():
            return [ln for ln in self.srv.stderr().splitlines() if "cannot write activity.jsonl" in ln]

        for status in ("working", "blocked", "idle"):
            self.fake.emit_status(pane, status)
        wait_until(write_lines, "the write error line")
        time.sleep(0.3)
        self.assertEqual(len(write_lines()), 1)                   # same error, one line
        self.assertIn("Is a directory", write_lines()[0])         # with the reason the OS gave
        self.assertNotIn(OUTAGE, self.srv.stderr())
        self.assertNotIn("Traceback", self.srv.stderr())
        self.assertEqual(len(self.fake.subscribes), subscribes)   # no reconnect, no backoff
        self.assertEqual(self.fake.open_streams, 1)

        log.rmdir()                                               # fixed: records flow again
        self.fake.emit_status(pane, "working")
        wait_until(lambda: len(self.records()) == 1, "a record once the log is writable")
        self.assertEqual(len(write_lines()), 1)

        log.unlink()
        log.mkdir()                                               # broken again: the line comes back
        self.fake.emit_status(pane, "blocked")
        wait_until(lambda: len(write_lines()) == 2, "the line for the second failure")
        self.assertIn("Is a directory", write_lines()[1])


class SecurityTest(LiveCase):
    def test_socket_path_comes_from_the_environment_never_from_a_request(self):
        self.add_agent("manager")
        decoy = FakeHerdr(self.tmp / "decoy.sock")
        self.addCleanup(decoy.stop)
        decoy.start()
        self.start()
        for path in ("/state?socket=%s" % decoy.path, "/?herdr=%s" % decoy.path):
            self.srv.get(path, {"X-Herdr-Socket": decoy.path})
        time.sleep(0.3)
        self.assertEqual(decoy.log, [])

    def test_default_socket_is_under_home_when_the_variable_is_unset(self):
        sock_dir = self.tmp / "home" / ".config" / "herdr"
        sock_dir.mkdir(parents=True)
        self.fake = FakeHerdr(sock_dir / "herdr.sock")
        self.addCleanup(self.fake.stop)
        self.add_agent("manager")
        self.start(env={"HERDR_SOCKET_PATH": None})
        self.assertEqual(len(self.fake.subscribes), 1)

    def test_nothing_is_written_outside_the_squad_folder(self):
        self.add_agent("manager")
        self.start()
        self.fake.emit_status(self.panes["manager"], "working")
        wait_until(lambda: len(self.records()) >= 2, "record")
        self.srv.state()
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["h.sock", "home", "work"])
        self.assertEqual(list((self.tmp / "home").rglob("*")), [])
        self.assertEqual(list((self.tmp / "work").rglob("*")), [])
        self.assertEqual(sorted(p.name for p in self.fx.root.iterdir()), ["activity.jsonl", "roster.md"])

    def test_no_shell_and_no_os_system_in_the_server(self):
        source = BIN.read_text()
        self.assertNotIn("shell=True", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("os.popen", source)

    def test_server_source_is_python_3_9_syntax(self):
        import ast
        ast.parse(BIN.read_text(), feature_version=(3, 9))


class ShutdownTest(LiveCase):
    def stop_with(self, sig):
        self.add_agent("manager")
        srv = self.start()
        begun = time.monotonic()
        srv.proc.send_signal(sig)
        srv.proc.wait(5)
        self.assertLess(time.monotonic() - begun, 2)
        return srv.proc.returncode

    def test_sigterm_stops_promptly_with_herdr_connected(self):
        self.assertEqual(self.stop_with(signal.SIGTERM), -signal.SIGTERM)

    def test_sigint_stops_promptly_and_cleanly_with_herdr_connected(self):
        self.assertEqual(self.stop_with(signal.SIGINT), 0)

    def test_sigint_stops_promptly_while_herdr_is_down(self):
        self.add_agent("manager")
        srv = self.start(listen=False)
        wait_until(lambda: OUTAGE in srv.stderr(), "outage line")
        begun = time.monotonic()
        srv.proc.send_signal(signal.SIGINT)
        srv.proc.wait(5)
        self.assertLess(time.monotonic() - begun, 2)
        self.assertEqual(srv.proc.returncode, 0)


class LiveStateTest(LiveCase):
    def test_state_says_live_and_keeps_the_other_keys(self):
        self.add_agent("manager")
        self.start()
        state = self.srv.state()
        self.assertEqual(set(state), TOP_KEYS)
        self.assertIs(state["live"], True)
        self.assertEqual(set(state["columns"][0]), COLUMN_KEYS)

    def test_now_is_the_wall_clock_and_moves(self):
        self.fx.activity(agent="manager", status="working", iteration=None)   # a log time far from now
        self.add_agent("manager", seed=False)
        self.start()
        first = self.srv.state()["now"]
        time.sleep(1.1)
        second = self.srv.state()["now"]
        self.assertRegex(first, NOW_RE)
        self.assertNotEqual(first, second)
        stamp = datetime.fromisoformat(second[:-1] + "+00:00")
        self.assertLess(abs((datetime.now(timezone.utc) - stamp).total_seconds()), 5)

    def test_tokens_stay_null_without_transcripts(self):
        self.add_agent("manager")
        self.start()
        col = self.srv.state()["columns"][0]
        self.assertEqual([col[k] for k in ("context_tokens", "tokens_in", "tokens_out", "model")], [None] * 4)

    def test_open_bar_runs_to_the_wall_clock(self):
        started = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=1)
        self.fx.activity(agent="manager", status="working", ts=started.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                         iteration=None)
        self.add_agent("manager", status="working", seed=False)
        self.start()
        bar = self.srv.state()["bars"][0]
        stamp = datetime.fromisoformat(self.srv.state()["now"][:-1] + "+00:00")
        self.assertTrue(bar["open"])
        self.assertAlmostEqual(bar["duration_s"], (stamp - started).total_seconds(), delta=5)

    def test_jump_still_runs_herdr_agent_focus_in_live_mode(self):
        bin_dir = self.tmp / "stubbin"
        bin_dir.mkdir()
        calls = self.tmp / "calls"
        stub = bin_dir / "herdr"
        stub.write_text("#!%s\nimport sys\nopen(%r, 'a').write(' '.join(sys.argv[1:]) + '\\n')\n" % (sys.executable, str(calls)))
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        self.add_agent("manager")
        self.add_agent("tech-board")
        self.start(env={"PATH": "%s:%s" % (bin_dir, os.environ["PATH"])})
        status, _, _ = self.srv.post("/jump/tech-board", {"X-Board-Token": self.srv.token})
        self.assertEqual(status, 200)
        self.assertEqual(calls.read_text(), "agent focus tech-board\n")
        status, _, _ = self.srv.post("/jump/ghost", {"X-Board-Token": self.srv.token})
        self.assertEqual(status, 404)


class LiveCommandLineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="board-cli-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)]))
        (self.tmp / "home").mkdir()
        self.servers = []

    def run_cli(self, args=(), cwd=None, env=None):
        full = base_env(self.tmp / "home")
        full["GIT_CEILING_DIRECTORIES"] = str(self.tmp)
        full.update(env or {})
        return subprocess.run([sys.executable, str(BIN)] + list(args), capture_output=True, text=True,
                              timeout=10, cwd=str(cwd or self.tmp), env=full)

    def start(self, cwd, env=None):
        full = base_env(self.tmp / "home", self.tmp / "none.sock")
        full["GIT_CEILING_DIRECTORIES"] = str(self.tmp)
        full.update(env or {})
        srv = launch([], full, cwd)
        self.addCleanup(srv.close)
        return srv

    def roster_in(self, folder, agent):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n"
            "| %s | Manager | all | x | live |\n" % agent)

    def test_no_squad_dir_and_no_squad_folder_exits_2_with_a_message(self):
        res = self.run_cli()
        self.assertEqual(res.returncode, 2)
        self.assertIn("squad folder", res.stderr)
        self.assertEqual(len(res.stderr.strip().splitlines()), 1)
        self.assertNotIn("Traceback", res.stderr)

    def test_squad_dir_that_is_not_a_folder_exits_2(self):
        res = self.run_cli(env={"SQUAD_DIR": str(self.tmp / "missing")})
        self.assertEqual(res.returncode, 2)
        self.assertIn("squad folder", res.stderr)

    def test_empty_squad_dir_variable_falls_back_like_an_unset_one(self):
        res = self.run_cli(env={"SQUAD_DIR": ""})
        self.assertEqual(res.returncode, 2)

    def test_now_without_replay_exits_2(self):
        self.roster_in(self.tmp / "sq", "from-env")
        res = self.run_cli(["--now", "2026-10-12T12:00:00Z"], env={"SQUAD_DIR": str(self.tmp / "sq")})
        self.assertEqual(res.returncode, 2)
        self.assertIn("--now", res.stderr)
        self.assertIn("replay", res.stderr)

    def test_squad_dir_variable_is_used_and_the_startup_line_is_the_same(self):
        self.roster_in(self.tmp / "sq", "from-env")
        self.roster_in(self.tmp / "cwd" / "squad", "from-cwd")
        srv = self.start(self.tmp / "cwd", {"SQUAD_DIR": str(self.tmp / "sq")})
        self.assertRegex(srv.startup_line.strip(), STARTUP_RE)
        self.assertEqual(srv.state()["columns"][0]["agent"], "from-env")

    def test_falls_back_to_squad_under_the_git_toplevel(self):
        top = self.tmp / "repo"
        (top / "deep" / "er").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(top)], check=True)
        self.roster_in(top / "squad", "from-git")
        srv = self.start(top / "deep" / "er")
        self.assertEqual(srv.state()["columns"][0]["agent"], "from-git")

    def test_falls_back_to_squad_in_the_current_folder_outside_git(self):
        self.roster_in(self.tmp / "plain" / "squad", "from-cwd")
        srv = self.start(self.tmp / "plain")
        self.assertEqual(srv.state()["columns"][0]["agent"], "from-cwd")

    def test_git_toplevel_without_a_squad_folder_falls_on_the_one_in_the_current_folder(self):
        top = self.tmp / "repo"
        (top / "sub").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(top)], check=True)
        self.roster_in(top / "sub" / "squad", "from-cwd")
        srv = self.start(top / "sub")
        self.assertEqual(srv.state()["columns"][0]["agent"], "from-cwd")

    def test_git_toplevel_squad_wins_over_the_one_in_the_current_folder(self):
        top = self.tmp / "repo"
        (top / "sub").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(top)], check=True)
        self.roster_in(top / "squad", "from-git")
        self.roster_in(top / "sub" / "squad", "from-cwd")
        srv = self.start(top / "sub")
        self.assertEqual(srv.state()["columns"][0]["agent"], "from-git")


if __name__ == "__main__":
    unittest.main()
