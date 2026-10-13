"""Seam A, BRD-11: live data sources. In live mode each column's tokens and model come from the transcript of
the session herdr reports for that agent, under any `~/.claude*` folder, and refresh on the E8 schedule.

Every test runs the real `bin/squad-board` with no `--replay`: `SQUAD_DIR` is a temp folder, `HERDR_SOCKET_PATH`
a fake herdr (tests/fake_herdr.py) and `HOME` a temp dir, so the real `~/.claude*` is never read.
"""
import json
import os
import stat
import subprocess
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from board_fixture import BIN, Fixture
from test_board_events import Stream
from test_board_recorder import LiveCase, NOW_RE, OUTAGE, wait_until
from test_board_tokens import NULLS, reply

KEYS = tuple(NULLS)
S1, S2, S3 = "11111111-aaaa", "22222222-bbbb", "33333333-cccc"
SENTINEL = "00000000-sentinel"   # the manager's session: its figures appearing means the session map is loaded
FAST_POLL = {"SQUAD_BOARD_POLL_S": "0.05"}


def figures(state, agent):
    col = next(c for c in state["columns"] if c["agent"] == agent)
    return {k: col[k] for k in KEYS}


def tokens_in(agent, total):
    return lambda state: figures(state, agent)["tokens_in"] == total


class LiveTokenCase(LiveCase):
    def setUp(self):
        super().setUp()
        self.home = self.tmp / "home"
        self.add("manager", SENTINEL)
        self.put(SENTINEL, [reply("s1", 1, 0, 0, 1)])

    # --- fixtures --------------------------------------------------------------------------

    def tpath(self, sid, root=".claude", project="p"):
        return self.home / root / "projects" / project / (sid + ".jsonl")

    def put(self, sid, lines, root=".claude", project="p"):
        path = self.tpath(sid, root, project)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(line) + "\n" for line in lines))
        return path

    def grow(self, path, line):
        with open(path, "a") as f:
            f.write(json.dumps(line) + "\n")

    def add(self, name, sid, status="idle"):
        """A fake pane for `name` whose snapshot entry reports session `sid`."""
        self.add_agent(name, status, rostered=name in [r["agent"] for r in self.rows])
        self.fake.rows[-1]["session"] = sid

    def agent(self, name, sid, status="idle"):
        """A roster row plus a pane."""
        self.rows.append({"agent": name})
        self.add(name, sid, status)

    def go(self, refresh="1", env=None, **kw):
        full = dict(FAST_POLL)
        full["SQUAD_BOARD_TOKEN_REFRESH_S"] = refresh
        full.update(env or {})
        self.start(env=full, **kw)
        self.wait_loaded()
        return self.srv

    def wait_loaded(self):
        wait_until(lambda: figures(self.srv.state(), "manager")["tokens_in"] == 1, "the session map to load")

    def figs(self, agent):
        return figures(self.srv.state(), agent)

    def stream(self):
        stream = Stream(self.srv)
        self.addCleanup(stream.close)
        self.assertEqual(stream.status, 200)
        return stream

    def stderr_is_quiet(self):
        self.assertEqual(self.srv.stderr(), "")


# --- AC 1: the session map comes from the herdr snapshot ------------------------------------------------

class SessionMapTest(LiveTokenCase):
    def test_tokens_come_from_the_transcript_of_the_session_herdr_reports(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 100, 1000, 7, "model-a"), reply("m2", 20, 200, 2000, 9, "model-b")])
        self.go()
        self.assertEqual(self.figs("a"), {"context_tokens": 2220, "tokens_in": 3330, "tokens_out": 16,
                                          "model": "model-b"})
        self.stderr_is_quiet()

    def test_each_agent_has_its_own_session_and_nobody_gets_another_agents_figures(self):
        self.agent("a", S1)
        self.agent("b", S2)
        self.agent("c", S3)
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.put(S2, [reply("m1", 70, 0, 0, 5)])
        self.go()
        self.assertEqual(self.figs("a")["tokens_in"], 10)
        self.assertEqual(self.figs("b")["tokens_in"], 70)
        self.assertEqual(self.figs("c"), NULLS)          # a session with no transcript

    def test_an_entry_with_no_usable_session_has_nulls_and_the_rest_are_read(self):
        self.rows.append({"agent": "a"})
        self.add_agent("a")                                     # the fake reports "session-of-a"
        self.fake.odd_agents.append({"name": "x", "pane_id": "wA:p99"})   # no agent_session at all
        self.fake.odd_agents.append({"name": "y", "pane_id": "wA:p98", "agent_session": "not a dict"})
        self.rows.append({"agent": "x"})
        self.rows.append({"agent": "y"})
        self.put("session-of-a", [reply("m1", 10, 0, 0, 1)])   # the fake's default session id for `a`
        self.go()
        self.assertEqual(self.figs("a")["tokens_in"], 10)
        self.assertEqual(self.figs("x"), NULLS)
        self.assertEqual(self.figs("y"), NULLS)
        self.stderr_is_quiet()

    def test_a_new_session_for_the_agent_is_followed_after_a_re_snapshot(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.put(S2, [reply("m1", 90, 0, 0, 1)])
        self.go()
        self.assertEqual(self.figs("a")["tokens_in"], 10)
        next(r for r in self.fake.rows if r["name"] == "a")["session"] = S2
        snapshots = self.fake.snapshots
        self.fake.emit_created("wA:pZZ")                      # any pane.created makes the recorder re-snapshot
        wait_until(lambda: self.fake.snapshots > snapshots, "the re-snapshot")
        wait_until(lambda: self.figs("a")["tokens_in"] == 90, "tokens of the new session")

    def test_a_session_that_is_not_a_valid_id_is_never_looked_up(self):
        # `*` would match any transcript if it reached the glob; the others would leave the project folders
        names = ["*", "../p/%s" % S1, "S1.x", "a b", "", "x" * 65, "[S1]", "?"]
        for i, bad in enumerate(names):
            self.agent("bad-%d" % i, bad)
        self.put("anything", [reply("m1", 5, 0, 0, 1)])
        self.put(S1, [reply("m1", 5, 0, 0, 1)])
        self.put("S1.x", [reply("m1", 5, 0, 0, 1)])
        self.put("a b", [reply("m1", 5, 0, 0, 1)])
        self.put("x" * 65, [reply("m1", 5, 0, 0, 1)])
        self.put("None", [reply("m1", 5, 0, 0, 1)])      # what a missing id would look up
        self.go()
        state = self.srv.state()
        for i in range(len(names)):
            self.assertEqual(figures(state, "bad-%d" % i), NULLS, names[i])
        self.stderr_is_quiet()

    def test_a_session_value_of_the_wrong_type_is_ignored(self):
        self.agent("a", S1)
        self.fake.odd_agents.append({"name": "t", "pane_id": "wA:p97", "agent_session": {"value": 5}})
        self.fake.odd_agents.append({"name": "u", "pane_id": "wA:p96", "agent_session": {"value": None}})
        self.rows += [{"agent": "t"}, {"agent": "u"}]
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.go()
        state = self.srv.state()
        self.assertEqual(figures(state, "t"), NULLS)
        self.assertEqual(figures(state, "u"), NULLS)
        self.assertEqual(figures(state, "a")["tokens_in"], 10)

    def test_an_agent_that_left_herdr_loses_its_session_at_the_next_snapshot(self):
        self.agent("a", S1)
        self.agent("b", S2)
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.put(S2, [reply("m1", 20, 0, 0, 1)])
        self.go()
        self.assertEqual(self.figs("b")["tokens_in"], 20)
        self.fake.rows[:] = [r for r in self.fake.rows if r["name"] != "b"]
        snapshots = self.fake.snapshots
        self.fake.emit_created("wA:pZZ")
        wait_until(lambda: self.fake.snapshots > snapshots, "the re-snapshot")
        wait_until(lambda: self.figs("b") == NULLS, "b to lose its session")
        self.assertEqual(self.figs("a")["tokens_in"], 10)

    def test_the_map_is_kept_while_herdr_is_gone(self):
        # the transcripts are still on disk, so a herdr restart does not blank the board
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.go()
        self.fake.stop()
        wait_until(lambda: OUTAGE in self.srv.stderr(), "the outage line")
        self.assertEqual(self.figs("a")["tokens_in"], 10)


# --- AC 2 and 3: roots, containment ---------------------------------------------------------------------

class RootsTest(LiveTokenCase):
    def test_every_claude_star_folder_of_home_is_a_root_and_nothing_else(self):
        self.agent("a", S1)
        self.agent("b", S2)
        self.agent("c", S3)
        self.put(S1, [reply("m1", 10, 0, 0, 1)], root=".claude-work")
        self.put(S2, [reply("m1", 20, 0, 0, 1)], root=".claude2")
        self.put(S3, [reply("m1", 30, 0, 0, 1)], root="claude")            # no leading dot: not a root
        self.put("other", [reply("m1", 40, 0, 0, 1)], root=".config")
        self.go()
        self.assertEqual(self.figs("a")["tokens_in"], 10)
        self.assertEqual(self.figs("b")["tokens_in"], 20)
        self.assertEqual(self.figs("c"), NULLS)

    def test_a_claude_star_entry_that_is_a_file_is_skipped(self):
        self.agent("a", S1)
        (self.home / ".claude.json").write_text("{}")
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.go()
        self.assertEqual(self.figs("a")["tokens_in"], 10)
        self.stderr_is_quiet()

    def test_the_same_file_through_two_roots_counts_once(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1), reply("m2", 20, 0, 0, 2)])
        (self.home / ".claude-2").mkdir()
        os.symlink(self.home / ".claude" / "projects", self.home / ".claude-2" / "projects")
        self.go()
        self.assertEqual(self.figs("a"), {"context_tokens": 20, "tokens_in": 30, "tokens_out": 3,
                                          "model": "model-a"})

    def test_a_whole_root_that_is_a_symlink_to_another_folder_is_read(self):
        # `~/.claude-work` on another disk is a normal setup; its transcripts stay inside it
        self.agent("a", S1)
        elsewhere = self.tmp / "elsewhere" / "claude-work"
        (elsewhere / "projects" / "p").mkdir(parents=True)
        (elsewhere / "projects" / "p" / (S1 + ".jsonl")).write_text(json.dumps(reply("m1", 10, 0, 0, 1)) + "\n")
        os.symlink(elsewhere, self.home / ".claude-work")
        self.go()
        self.assertEqual(self.figs("a")["tokens_in"], 10)

    def test_the_same_session_in_two_roots_gives_one_stable_answer(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1)], root=".claude-a")
        self.put(S1, [reply("m1", 99, 0, 0, 1)], root=".claude-b")
        self.go()
        first = self.figs("a")["tokens_in"]
        self.assertIn(first, (10, 99))
        for _ in range(3):
            self.assertEqual(self.figs("a")["tokens_in"], first)

    def test_a_transcript_symlinked_out_of_its_root_is_not_read(self):
        self.agent("a", S1)
        outside = self.tmp / "outside.jsonl"
        outside.write_text(json.dumps(reply("m1", 10, 0, 0, 1)) + "\n")
        self.tpath(S1, project="q").parent.mkdir(parents=True)
        os.symlink(outside, self.tpath(S1, project="q"))
        self.go()
        self.assertEqual(self.figs("a"), NULLS)

    def test_a_project_folder_symlinked_out_of_its_root_is_not_read(self):
        self.agent("a", S1)
        (self.tmp / "outside" / "q").mkdir(parents=True)
        (self.tmp / "outside" / "q" / (S1 + ".jsonl")).write_text(json.dumps(reply("m1", 10, 0, 0, 1)) + "\n")
        os.symlink(self.tmp / "outside" / "q", self.home / ".claude" / "projects" / "q")
        self.go()
        self.assertEqual(self.figs("a"), NULLS)

    def test_a_transcript_in_a_second_project_folder_is_found(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1)], project="another-project")
        self.go()
        self.assertEqual(self.figs("a")["tokens_in"], 10)


# --- AC 5: nothing to read ------------------------------------------------------------------------------

class NothingToReadTest(LiveTokenCase):
    def test_herdr_missing_gives_nulls_and_a_healthy_state_with_only_the_outage_line_on_stderr(self):
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.start(env=FAST_POLL, listen=False)
        wait_until(lambda: OUTAGE in self.srv.stderr(), "the one outage line")
        status, _, body = self.srv.get("/state")
        self.assertEqual(status, 200)
        for col in json.loads(body)["columns"]:
            self.assertEqual({k: col[k] for k in KEYS}, NULLS)
        lines = self.srv.stderr().splitlines()
        self.assertEqual(len(lines), 1, lines)
        self.assertNotIn("Traceback", self.srv.stderr())

    def test_an_agent_herdr_does_not_know_has_nulls(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.rows.append({"agent": "ghost"})        # on the roster, in no pane
        self.go()
        self.assertEqual(self.figs("ghost"), NULLS)
        self.assertEqual(self.figs("a")["tokens_in"], 10)
        self.stderr_is_quiet()

    def test_a_known_session_without_a_transcript_has_nulls(self):
        self.agent("a", S1)
        self.go()
        self.assertEqual(self.figs("a"), NULLS)
        self.stderr_is_quiet()

    def test_a_transcript_with_no_usage_lines_has_nulls(self):
        self.agent("a", S1)
        self.put(S1, [{"type": "user", "message": {"content": "hi"}}, {"type": "summary"}])
        self.go()
        self.assertEqual(self.figs("a"), NULLS)
        self.stderr_is_quiet()

    def test_a_home_with_no_claude_folder_at_all_gives_nulls(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.start(env=dict(FAST_POLL, HOME=str(self.tmp / "no-such-home")))
        self.barrier(len(self.records()))      # the recorder has loaded the session map when this returns
        self.assertEqual(self.figs("a"), NULLS)
        self.stderr_is_quiet()


# --- AC 4, 6, 10: the refresh schedule and the watcher ---------------------------------------------------

class RefreshTest(LiveTokenCase):
    def setUp(self):
        super().setUp()
        self.agent("a", S1, status="working")
        self.path = self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.n = 1

    def grow_by(self, amount=100):
        self.n += 1
        self.grow(self.path, reply("m%d" % self.n, amount, 0, 0, 1))

    def start_streaming(self, refresh):
        self.go(refresh=refresh)
        stream = self.stream()
        first = stream.state(5)
        self.assertEqual(figures(first, "a")["tokens_in"], 10)
        return stream

    def restart_the_timer(self, stream):
        """A squad file change rebuilds at once and restarts the token timer; returns when its frame is in."""
        self.fx.message(**{"from": "manager", "to": "a"})
        self.assertIsNotNone(stream.state(5), "the frame of the message")

    def test_state_shows_a_grown_transcript_at_once(self):
        self.go(refresh="30")
        self.grow_by()
        self.assertEqual(self.figs("a")["tokens_in"], 110)

    def test_a_growing_transcript_reaches_the_stream_within_the_refresh_interval_and_not_before(self):
        stream = self.start_streaming("3")
        self.restart_the_timer(stream)
        self.grow_by()
        self.assertIsNone(stream.state_where(tokens_in("a", 110), 1.0), "a rebuild before the interval")
        self.assertIsNotNone(stream.state_where(tokens_in("a", 110), 3 + 4), "no rebuild after the interval")

    def test_a_rebuild_per_poll_would_show_here_the_stream_gets_one_event_per_interval(self):
        stream = self.start_streaming("2")
        self.restart_the_timer(stream)
        got = []
        end = time.monotonic() + 2.5
        while time.monotonic() < end:
            self.grow_by(1)
            state = stream.state(0.1)
            if state:
                got.append(state)
        self.assertLessEqual(len(got), 2, "more than one rebuild per interval")
        self.assertGreaterEqual(len(got), 1)

    def test_a_second_client_does_not_add_a_rebuild(self):
        stream = self.start_streaming("3")
        self.restart_the_timer(stream)
        self.grow_by()
        second = self.stream()
        # the second client is served the build that already exists: it has not seen the growth
        self.assertEqual(figures(second.state(5), "a")["tokens_in"], 10)
        self.assertIsNotNone(stream.state_where(tokens_in("a", 110), 3 + 4))

    def test_the_new_totals_arrive_at_once_when_the_bar_ends(self):
        stream = self.start_streaming("30")
        self.grow_by()
        self.fake.emit_status(self.panes["a"], "idle")
        state = stream.state_where(tokens_in("a", 110), 3)
        self.assertIsNotNone(state, "the bar end did not rebuild")
        self.assertEqual(next(c for c in state["columns"] if c["agent"] == "a")["status"], "idle")

    def test_nothing_is_refreshed_while_nobody_is_working(self):
        self.fake.set_status(self.panes["a"], "idle")
        self.fx.activity(agent="a", status="idle", iteration=None)
        self.fx.activity(agent="manager", status="idle", iteration=None)
        stream = self.start_streaming("1")
        self.grow_by()
        self.assertIsNone(stream.state_where(tokens_in("a", 110), 3.5), "a refresh with nobody working")
        self.assertEqual(self.figs("a")["tokens_in"], 110)          # /state still reads it when asked
        self.fx.activity(agent="a", status="working", iteration=None)   # a new bar: the next build reads it
        self.assertIsNotNone(stream.state_where(tokens_in("a", 110), 3))

    def test_any_working_agent_keeps_the_timer_running(self):
        # `working` means any agent: the manager works, `a` is idle, and a's transcript still refreshes
        self.fx.activity(agent="a", status="idle", iteration=None)
        self.fx.activity(agent="manager", status="working", iteration=None)
        stream = self.start_streaming("1")
        self.grow_by()
        self.assertIsNotNone(stream.state_where(tokens_in("a", 110), 4))

    def test_the_default_interval_is_long(self):
        # the 3 s tests above cover the timer through the knob; watching 3 s of silence only tested this number
        source = BIN.read_text(encoding="utf-8")
        self.assertRegex(source, r'(?m)^TOKEN_REFRESH_S = env_seconds\("SQUAD_BOARD_TOKEN_REFRESH_S", 30\)$')

    def test_an_unchanged_transcript_causes_no_event(self):
        stream = self.start_streaming("1")
        self.assertIsNone(stream.state(3.5), "an event with nothing new in the transcripts")

    def test_a_new_session_for_a_working_agent_reaches_the_stream(self):
        self.put(S2, [reply("m1", 90, 0, 0, 1)])
        stream = self.start_streaming("1")
        self.restart_the_timer(stream)
        next(r for r in self.fake.rows if r["name"] == "a")["session"] = S2
        self.fake.emit_created("wA:pZZ")
        self.assertIsNotNone(stream.state_where(tokens_in("a", 90), 3 + 4))

    def test_a_transcript_that_appears_later_for_a_working_agent_reaches_the_stream(self):
        self.agent("late", S3, status="working")
        stream = self.start_streaming("1")
        self.put(S3, [reply("m1", 55, 0, 0, 1)])
        self.assertIsNotNone(stream.state_where(tokens_in("late", 55), 4))

    def test_replay_mode_has_no_token_timer(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-board-5"}])
        fx.iteration(1)
        fx.activity(agent="dev-board-5", status="working")
        fx.herdr({"dev-board-5": S1})
        fx.transcript("claude", "p", S1, [reply("m1", 10, 0, 0, 1)])
        server = fx.start(now="2026-10-12T12:00:00Z",
                          env=dict(FAST_POLL, SQUAD_BOARD_TOKEN_REFRESH_S="1"))
        stream = Stream(server)
        self.addCleanup(stream.close)
        self.assertEqual(figures(stream.state(5), "dev-board-5")["tokens_in"], 10)
        fx.append_jsonl("replay/claude/projects/p/%s.jsonl" % S1, reply("m2", 100, 0, 0, 1))
        self.assertIsNone(stream.state(3.5), "replay mode rebuilt for a transcript")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 110)   # /state reads it fresh


class RefreshSettingTest(unittest.TestCase):
    def run_with(self, value):
        env = dict(os.environ, SQUAD_BOARD_TOKEN_REFRESH_S=value)
        return subprocess.run([sys.executable, str(BIN), "--replay", "/nonexistent-folder"], env=env,
                              capture_output=True, text=True, timeout=10)

    def test_a_bad_value_is_refused_like_the_other_timings(self):
        for value in ("0", "-1", "abc", "nan", "inf", "100000"):
            done = self.run_with(value)
            self.assertEqual(done.returncode, 2, value)
            self.assertIn("SQUAD_BOARD_TOKEN_REFRESH_S", done.stderr, value)

    def test_a_good_value_is_accepted(self):
        done = self.run_with("0.5")
        self.assertIn("not a directory", done.stderr)      # got as far as the folder check


# --- AC 9: the stamp ------------------------------------------------------------------------------------

class StampTest(LiveTokenCase):
    def seconds_off(self, state):
        stamp = datetime.fromisoformat(state["now"][:-1] + "+00:00")
        return abs((datetime.now(timezone.utc) - stamp).total_seconds())

    def test_the_first_event_carries_live_and_a_wall_clock_now(self):
        self.go()
        state = self.stream().state(5)
        self.assertIs(state["live"], True)
        self.assertRegex(state["now"], NOW_RE)
        self.assertLess(self.seconds_off(state), 5)        # the log timestamps are days older

    def test_a_streamed_open_bar_runs_to_the_wall_clock(self):
        self.agent("w", S2, status="working")
        self.go()
        state = self.stream().state(5)
        bar = next(b for b in state["bars"] if b["agent"] == "w")
        started = datetime.fromisoformat(bar["start_ts"][:-1] + "+00:00")
        self.assertAlmostEqual(bar["duration_s"], (datetime.now(timezone.utc) - started).total_seconds(), delta=5)

    def test_two_clients_a_second_apart_get_different_now_from_one_cached_state(self):
        self.go()
        first = self.stream().state(5)
        time.sleep(1.1)
        second = self.stream().state(5)
        self.assertNotEqual(first["now"], second["now"])
        self.assertLess(self.seconds_off(second), 5)
        self.assertEqual({k: v for k, v in first.items() if k != "now"},
                         {k: v for k, v in second.items() if k != "now"})

    def test_two_events_a_second_apart_differ_in_now(self):
        self.go()
        stream = self.stream()
        first = stream.state(5)
        time.sleep(1.1)
        self.fx.message(**{"from": "manager", "to": "manager"})
        second = stream.state_where(lambda s: s["rows"] != first["rows"])
        self.assertIsNotNone(second)
        self.assertNotEqual(first["now"], second["now"])
        self.assertIs(second["live"], True)
        self.assertLess(self.seconds_off(second), 5)

    def test_state_and_stream_have_the_same_keys(self):
        self.go()
        self.assertEqual(set(self.stream().state(5)), set(self.srv.state()))

    def test_a_state_with_no_change_sends_nothing_however_long_the_clock_runs(self):
        self.go()
        stream = self.stream()
        self.assertIsNotNone(stream.state(5))
        self.assertIsNone(stream.state(2.5), "an event for a clock tick")

    def test_a_file_rewritten_with_the_same_content_sends_nothing_either(self):
        # the files change (so the watcher rebuilds) but the state does not; the clock alone is not a change
        self.fx.activity(agent="manager", status="idle", iteration=None)
        self.go()
        stream = self.stream()
        self.assertIsNotNone(stream.state(5))
        path = self.fx.root / "roster.md"
        path.write_text(path.read_text())
        time.sleep(0.3)
        self.assertIsNone(stream.state(2.5), "an event for a rebuild that changed nothing")

    def test_replay_mode_streams_the_fixed_now_and_live_false(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}])
        fx.iteration(1)
        fx.activity(agent="manager", status="idle")
        server = fx.start(now="2026-10-12T12:00:00Z")
        stream = Stream(server)
        self.addCleanup(stream.close)
        state = stream.state(5)
        self.assertEqual(state["now"], "2026-10-12T12:00:00Z")
        self.assertIs(state["live"], False)
        self.assertEqual(state, server.state())


# --- AC 7: jump in live mode ----------------------------------------------------------------------------

class JumpTest(LiveTokenCase):
    def stub(self):
        bindir = self.tmp / "stubbin"
        bindir.mkdir()
        calls = self.tmp / "calls"
        path = bindir / "herdr"
        path.write_text("#!/bin/sh\necho \"$@\" >> %s\n" % calls)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return str(bindir), calls

    def jump(self, name, token=True):
        request = urllib.request.Request("%s/jump/%s" % (self.srv.base, name), method="POST")
        if token:
            request.add_header("X-Board-Token", self.srv.token)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status
        except urllib.error.HTTPError as e:
            return e.code

    def test_jump_runs_the_real_herdr_on_path_and_checks_the_roster_as_in_replay(self):
        bindir, calls = self.stub()
        self.rows.append({"agent": "old-dev", "status": "retired"})
        self.agent("dev-board-11", S1)
        self.go(env={"PATH": bindir + os.pathsep + os.environ.get("PATH", "")})
        self.assertEqual(self.jump("dev-board-11"), 200)
        self.assertEqual(calls.read_text(), "agent focus dev-board-11\n")
        for name, token, code in (("not-on-roster", True, 404), ("old-dev", True, 404),
                                  ("dev-board-11", False, 403), ("Bad Name", True, 400)):
            self.assertEqual(self.jump(name.replace(" ", "%20"), token), code, name)
        self.assertEqual(calls.read_text(), "agent focus dev-board-11\n")      # the refused ones ran nothing


# --- AC 8: shared state under threads -------------------------------------------------------------------

class ConcurrencyTest(LiveTokenCase):
    def test_requests_while_the_session_map_is_rewritten_all_succeed(self):
        self.agent("a", S1)
        self.put(S1, [reply("m1", 10, 0, 0, 1)])
        self.go()
        stop, failures = threading.Event(), []

        def churn():
            while not stop.is_set():
                self.fake.emit_created("wA:pZZ")
                time.sleep(0.01)

        def ask():
            for _ in range(15):
                try:
                    status, _, body = self.srv.get("/state")
                    state = json.loads(body)
                    if status != 200 or figures(state, "a")["tokens_in"] != 10:
                        failures.append((status, figures(state, "a")))
                except Exception as e:  # noqa: BLE001
                    failures.append(e)

        threads = [threading.Thread(target=churn)] + [threading.Thread(target=ask) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads[1:]:
            t.join(30)
        stop.set()
        threads[0].join(5)
        self.assertEqual(failures, [])
        self.stderr_is_quiet()


if __name__ == "__main__":
    unittest.main()
