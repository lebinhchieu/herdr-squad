"""squad-watchdog (ticket 03): idle log, nudges at 5 and 15 minutes, PC sleep only when the PO switched it on."""
import json
import os
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

import winlaunch
from squadtest import BIN, clean_env, load_cli

W = load_cli("squad-watchdog")
T0 = 1_800_000_000.0
MIN = 60.0
ROSTER = """# Roster

| Agent | Role | Scope | Owns | Status | Session |
| --- | --- | --- | --- | --- | --- |
| t-mgr-s1 | manager | s1 | plan | live | a |
| t-dev-s1 | dev | s1 | ticket 03 | building | b |
| t-qa-s1 | qa-whitebox | s1 | ticket 04 | live | c |
"""


class WatchdogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / ".claude" / "squads" / "t" / "scopes" / "s1"
        (self.home / "tasks").mkdir(parents=True)
        (self.home / "scope.md").write_text("# s1\n", encoding="utf-8")
        (self.home / "roster.md").write_text(ROSTER, encoding="utf-8")
        self.sent, self.suspended = [], []
        self.herdr = Path(self.tmp.name) / "herdr.json"

    def tickets(self, **status):
        for n, st in status.items():
            (self.home / "tasks" / f"{n[1:]}.md").write_text(f"# T\n\nStatus: {st}\n", encoding="utf-8")

    def agents(self, **state):
        rows = [{"name": n.replace("_", "-"), "agent_status": s, "pane_id": "p"} for n, s in state.items()]
        self.herdr.write_text(json.dumps({"result": {"agents": rows}}), encoding="utf-8")

    def tick(self, minutes):
        return W.tick(self.home, "t-mgr-s1", now=T0 + minutes * MIN, herdr_json=str(self.herdr),
                      send=lambda m, text: (self.sent.append((m, text)) or (True, "")), suspend_fn=lambda: (self.suspended.append(1) or (True, "")))

    def log(self):
        return (self.home / "watchdog.log").read_text(encoding="utf-8")

    # AC1
    def test_an_idle_start_is_logged_with_every_agents_state_and_the_waiting_tickets(self):
        self.tickets(t03="ready", t04="done")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="blocked")
        self.tick(0)
        self.tick(1)  # the same spell: no second line
        line = self.log().strip()
        self.assertEqual(len(line.splitlines()), 1, line)
        self.assertRegex(line, r"^2027-01-15T08:00:00Z idle start: nobody works and work waits \(03 ready\)\. Agents: "
                               r"t-mgr-s1 idle, t-dev-s1 idle, t-qa-s1 blocked$")

    def test_scopes_of_a_goal_that_share_a_ticket_folder_list_each_ticket_once(self):
        squad = self.home.parent.parent
        goal = squad / "goals" / "g1"
        goal.mkdir(parents=True)
        (goal / "goal.md").write_text("# g1\n", encoding="utf-8")
        (goal / "roster.md").write_text(ROSTER.replace("s1", "g1"), encoding="utf-8")
        tickets = Path(self.tmp.name) / ".scratch" / "slug" / "issues"
        tickets.mkdir(parents=True)
        (tickets / "03-a.md").write_text("# A\n\nStatus: ready\n", encoding="utf-8")
        for sc in ("s1", "s2"):
            (squad / "scopes" / sc).mkdir(exist_ok=True)
            (squad / "scopes" / sc / "scope.md").write_text(f"# {sc}\ngoal: g1\ntickets: slug\n", encoding="utf-8")
        (self.home / "tasks" / "03.md").unlink(missing_ok=True)
        self.agents(t_mgr_g1="idle")
        W.tick(goal, "t-mgr-g1", now=T0, herdr_json=str(self.herdr), send=None, suspend_fn=None)
        self.assertIn("work waits (03 ready). Agents:", (goal / "watchdog.log").read_text(encoding="utf-8"))

    # AC2
    def test_the_manager_is_nudged_once_at_5_and_once_at_15_minutes(self):
        self.tickets(t03="ready")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle")
        for m in (0, 4, 5, 6, 14, 15, 16, 40):
            self.tick(m)
        self.assertEqual([m for m, _ in self.sent], ["t-mgr-s1", "t-mgr-s1"])
        first, second = (t for _, t in self.sent)
        self.assertIn("nobody has worked for 5 minutes (since 08:00 UTC)", first)
        self.assertIn("still nobody working after 15 minutes", second)
        self.assertIn("Waiting: 03 ready.", first)
        self.assertIn("t-dev-s1 idle", first)
        self.assertEqual(sum("nudge" in l for l in self.log().splitlines()), 2)

    def test_work_ends_the_spell_and_the_next_spell_nudges_again(self):
        self.tickets(t03="ready")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        self.tick(0)
        self.tick(5)
        self.agents(t_mgr_s1="idle", t_dev_s1="working")
        self.tick(7)
        self.assertIn("idle end after 7 min", self.log())
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        self.tick(8)
        self.tick(13)
        self.assertEqual(len(self.sent), 2)  # 5 min of the first spell, 5 min of the second

    def test_no_waiting_ticket_or_no_answer_from_herdr_means_no_idle_spell(self):
        self.tickets(t03="done", t04="blocked")
        self.agents(t_mgr_s1="idle")
        self.tick(0)
        self.tick(30)
        self.herdr.write_text("not json", encoding="utf-8")
        self.tickets(t03="ready")
        self.tick(60)
        self.assertEqual(self.sent, [])
        self.assertNotIn("idle start", self.log())
        self.assertIn("herdr does not answer", self.log())

    # AC3
    def test_the_pc_never_sleeps_unless_the_switch_is_on(self):
        self.tickets(t03="done", t04="done")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle")
        for m in (0, 6, 60):
            self.tick(m)
        self.assertEqual(self.suspended, [])
        self.assertFalse(W.sleep_on(self.home))

    def test_the_pc_sleeps_once_after_5_quiet_minutes_when_every_ticket_is_passed(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="passed", t04="passed")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        self.tick(0)
        self.tick(4)
        self.assertEqual(self.suspended, [])  # quiet for 4 min only
        self.tick(5)
        self.assertEqual(self.suspended, [1])
        self.assertRegex(self.log().splitlines()[-1], r"^2027-01-15T08:05:00Z sleep pc: all tickets passed; nobody on this machine has worked for 5 min")
        self.assertFalse(W.sleep_on(self.home))  # one shot
        self.tick(40)
        self.assertEqual(self.suspended, [1])  # a wake-up does not sleep again

    def test_the_pc_sleeps_after_5_quiet_minutes_with_open_tickets_and_names_that_reason(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="passed", t04="building")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        self.tick(0)
        self.tick(4)
        self.assertEqual(self.suspended, [])
        self.tick(5)
        self.assertEqual(self.suspended, [1])
        self.assertRegex(self.log().splitlines()[-1], r"sleep pc: team idle with open tickets; nobody on this machine has worked for 5 min")
        self.assertFalse(W.sleep_on(self.home))

    def test_with_no_ticket_at_all_the_log_does_not_say_open_tickets(self):
        W.set_sleep(self.home, True)
        self.agents(t_mgr_s1="idle")
        self.tick(0)
        self.tick(5)
        self.assertRegex(self.log().splitlines()[-1], r"sleep pc: team idle; nobody on this machine")
        self.assertNotIn("open tickets", self.log().splitlines()[-1])

    def test_a_working_agent_resets_the_quiet_timer_even_with_open_tickets(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="building")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        self.tick(0)
        self.tick(4)
        self.agents(t_mgr_s1="idle", t_dev_s1="working")
        self.tick(5)
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        self.tick(6)
        self.tick(10)
        self.assertEqual(self.suspended, [])  # the timer restarted at 6
        self.tick(11)
        self.assertEqual(self.suspended, [1])

    def test_the_pc_never_sleeps_with_the_switch_off_however_long_the_team_is_idle(self):
        W.set_sleep(self.home, False)
        self.tickets(t03="building")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        for m in (0, 6, 600):
            self.tick(m)
        self.assertEqual(self.suspended, [])

    def test_an_agent_of_another_squad_working_holds_the_sleep_and_restarts_the_clock(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="done")
        self.agents(t_mgr_s1="idle", other_mgr_x="working")  # not in this roster, but on this machine
        self.tick(0)
        self.tick(20)
        self.assertEqual(self.suspended, [])
        self.agents(t_mgr_s1="idle", other_mgr_x="idle")
        self.tick(21)
        self.tick(25)
        self.assertEqual(self.suspended, [])  # the clock restarted at 21
        self.tick(26)
        self.assertEqual(self.suspended, [1])

    def test_a_goal_sleeps_when_the_machine_is_quiet_whatever_the_tickets_of_its_scopes_say(self):
        squad = self.home.parent.parent
        goal = squad / "goals" / "g1"
        goal.mkdir(parents=True)
        (goal / "goal.md").write_text("# g1\n", encoding="utf-8")
        (goal / "roster.md").write_text(ROSTER.replace("s1", "g1"), encoding="utf-8")
        for sc, st in (("s1", "done"), ("s2", "building")):
            (squad / "scopes" / sc / "tasks").mkdir(parents=True, exist_ok=True)
            (squad / "scopes" / sc / "scope.md").write_text(f"# {sc}\ngoal: g1\n", encoding="utf-8")
            (squad / "scopes" / sc / "tasks" / "01.md").write_text(f"# T\n\nStatus: {st}\n", encoding="utf-8")
        W.set_sleep(goal, True)
        self.agents(t_mgr_g1="idle")
        for m in (0, 10):
            W.tick(goal, "t-mgr-g1", now=T0 + m * MIN, herdr_json=str(self.herdr), send=lambda *a: (True, ""),
                   suspend_fn=lambda: (self.suspended.append(1) or (True, "")))
        self.assertEqual(self.suspended, [1])  # s2 is still building: the goal's tickets do not hold the sleep
        self.assertIn("team idle with open tickets", (goal / "watchdog.log").read_text(encoding="utf-8"))

    def test_herdr_not_answering_is_no_decision_for_the_sleep(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="done")
        self.agents(t_mgr_s1="idle")
        self.tick(0)
        self.herdr.write_text("not json", encoding="utf-8")
        self.tick(30)
        self.assertEqual(self.suspended, [])
        (self.home / "watchdog.state.json").unlink()  # a fresh home or a 0.9.5 state file has no bg keys
        self.tick(31)  # must not raise
        self.assertIn("herdr does not answer", self.log())

    def test_a_herdr_outage_restarts_the_quiet_clock_so_the_pc_does_not_sleep_at_the_first_check_after_it(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="done")
        self.agents(t_mgr_s1="idle")
        self.tick(0)
        self.tick(4)  # quiet for 4 of 5 minutes
        self.herdr.write_text("not json", encoding="utf-8")
        self.tick(10)
        self.agents(t_mgr_s1="idle")
        self.tick(11)  # herdr is back, machine quiet: the clock starts here
        self.assertEqual(self.suspended, [])
        self.tick(15)
        self.assertEqual(self.suspended, [])  # 4 min since the outage ended
        self.tick(16)
        self.assertEqual(self.suspended, [1])

    def test_cli_sleep_on_and_off_and_status_shows_the_switch(self):
        def run(*args):
            return winlaunch.run_script(str(BIN / "squad-watchdog"), [*args, "--home", str(self.home)], clean_env(),
                                        utf8=True, encoding="utf-8", capture_output=True)
        r = run("status")
        self.assertIn("sleep-when-idle: off", r.stdout)
        r = run("sleep", "on")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("sleep-when-idle: ON", r.stdout)
        self.assertTrue(W.sleep_on(self.home))
        self.assertIn("sleep-when-idle: ON", run("status").stdout)
        run("sleep", "off")
        self.assertFalse(W.sleep_on(self.home))
        self.assertNotEqual(run("sleep", "mango").returncode, 0)

    # AC3b, AC3c
    def test_the_suspend_command_comes_from_the_env_or_the_host_and_runs_after_the_log_and_the_switch(self):
        self.tickets(t03="done")
        self.agents(t_mgr_s1="idle")
        W.set_sleep(self.home, True)
        seen = Path(self.tmp.name) / "seen.txt"
        state = (self.home / "watchdog.state.json")
        state.write_text(json.dumps({"quiet_since": 0}), encoding="utf-8")
        env = clean_env(SQUAD_WATCHDOG_SLEEP_CMD=f'cat "{self.home}/watchdog.log" "{self.home}/watchdog.sleep" > "{seen}"')
        r = winlaunch.run_script(str(BIN / "squad-watchdog"), ["tick", "--home", str(self.home), "--manager", "t-mgr-s1",
                                                              "--herdr-json", str(self.herdr)], env, utf8=True, encoding="utf-8", capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")  # the log is the output, no raw event lines
        text = seen.read_text(encoding="utf-8")
        self.assertIn("sleep pc:", text)  # logged first
        self.assertIn("\noff\n", text)  # and the switch was already off
        old = (W.sys.platform, os.environ.get("WSL_DISTRO_NAME"), os.environ.pop("SQUAD_WATCHDOG_SLEEP_CMD", None))
        self.addCleanup(lambda: (setattr(W.sys, "platform", old[0]), os.environ.pop("WSL_DISTRO_NAME", None),
                                 old[1] and os.environ.__setitem__("WSL_DISTRO_NAME", old[1])))
        os.environ.pop("WSL_DISTRO_NAME", None)
        for plat, wsl, want in (("win32", None, "rundll32.exe"), ("darwin", None, "pmset"), ("linux", "Ubuntu", "powershell.exe")):
            W.sys.platform = plat
            if wsl:
                os.environ["WSL_DISTRO_NAME"] = wsl
            with mock.patch.object(W.shutil, "which", return_value=None), mock.patch.object(W.os.path, "exists", return_value=False):
                self.assertEqual(W.suspend_cmd()[0][0], want)  # host-independent: no powershell anywhere -> the bare name

    # watchdog-blind 03 AC3: WSL powershell by PATH, else /mnt/c path, else the bare name; nothing suspends
    def test_wsl_suspend_cmd_takes_path_then_mnt_c_then_the_bare_name_and_a_failure_names_the_path(self):
        old = (W.sys.platform, os.environ.pop("SQUAD_WATCHDOG_SLEEP_CMD", None), os.environ.get("WSL_DISTRO_NAME"))
        self.addCleanup(lambda: (setattr(W.sys, "platform", old[0]), os.environ.pop("WSL_DISTRO_NAME", None),
                                 old[2] and os.environ.__setitem__("WSL_DISTRO_NAME", old[2])))
        W.sys.platform, os.environ["WSL_DISTRO_NAME"] = "linux", "Ubuntu"
        boom = mock.patch.object(W.subprocess, "run", side_effect=AssertionError("must not suspend"))
        with boom:
            with mock.patch.object(W.shutil, "which", return_value="/usr/bin/powershell.exe"):
                argv, shell = W.suspend_cmd()
                self.assertEqual((argv[0], argv[1:], shell), ("/usr/bin/powershell.exe", ["-NoProfile", "-Command", W.WSL_PS], False))
            with mock.patch.object(W.shutil, "which", return_value=None), mock.patch.object(W.os.path, "exists", return_value=True):
                self.assertEqual(W.suspend_cmd()[0][0], W.WSL_PS_PATH)
            with mock.patch.object(W.shutil, "which", return_value=None), mock.patch.object(W.os.path, "exists", return_value=False):
                self.assertEqual(W.suspend_cmd()[0][0], "powershell.exe")
        with mock.patch.object(W.shutil, "which", return_value=None), mock.patch.object(W.os.path, "exists", return_value=False), \
                mock.patch.object(W.subprocess, "run", side_effect=FileNotFoundError("powershell.exe")):
            ok, why = W.suspend()
        self.assertFalse(ok)
        self.assertIn(W.WSL_PS_PATH, why)

    # watchdog-blind 03 AC1 + T1
    def test_a_working_manager_does_not_hold_the_idle_spell_but_still_counts_for_stop_and_sleep(self):
        import copy
        self.tickets(t03="building")
        self.agents(t_mgr_s1="working", t_dev_s1="idle", t_qa_s1="idle")
        snap = W.snapshot(self.home, str(self.herdr))
        st0 = {"idle_since": None}
        before = copy.deepcopy(st0)
        st, ev = W.decide(st0, snap, T0, True)
        self.assertEqual(st0, before)
        self.assertEqual([e[0] for e in ev], ["start"])  # Manager working, rest idle: the spell starts
        self.assertIsNone(st["quiet_since"])  # machine_working is untouched: no sleep clock
        # a Manager's bg shell does not hold it either
        snap["bg"] = {"t-mgr-s1": "1 shell"}
        st, ev = W.decide({"idle_since": None}, snap, T0, False)
        self.assertEqual([e[0] for e in ev if e[0] != "bg_busy"], ["start"])
        # a working Developer does hold it
        self.agents(t_mgr_s1="idle", t_dev_s1="working", t_qa_s1="idle")
        self.assertEqual(W.decide({"idle_since": None}, W.snapshot(self.home, str(self.herdr)), T0, False)[1], [])

    def test_goals_all_blocked_or_done_with_a_working_manager_still_follow_the_all_agents_rule(self):
        goal = self.home.parent.parent / "goals" / "g1"
        goal.mkdir(parents=True)
        (goal / "goal.md").write_text("# g1\n", encoding="utf-8")
        (goal / "roster.md").write_text(ROSTER.replace("s1", "g1"), encoding="utf-8")
        (goal / "goals.md").write_text("| # | Goal | Status |\n|---|---|---|\n| G1 | x | done |\n", encoding="utf-8")
        self.agents(t_mgr_g1="working", t_dev_g1="idle", t_qa_g1="idle")
        snap = W.snapshot(goal, str(self.herdr))
        self.assertNotIn("stop", [e[0] for e in W.decide({}, snap, T0, False)[1]])  # Manager working: never stops
        self.agents(t_mgr_g1="idle", t_dev_g1="idle", t_qa_g1="idle")
        self.assertIn("stop", [e[0] for e in W.decide({}, W.snapshot(goal, str(self.herdr)), T0, False)[1]])
        (goal / "goals.md").write_text("| # | Goal | Status | Reason |\n|---|---|---|---|\n| G1 | x | blocked | r |\n", encoding="utf-8")
        self.agents(t_mgr_g1="working", t_dev_g1="idle", t_qa_g1="idle")
        ev = W.decide({}, W.snapshot(goal, str(self.herdr)), T0, False)[1]
        self.assertNotIn("all_blocked", [e[0] for e in ev])  # unchanged: needs nobody working
        self.assertNotIn("start", [e[0] for e in ev])

    # watchdog-blind 03 AC2 + T2/T3 (real status_of: State: lines)
    def test_blind_is_logged_and_sent_once_per_spell_and_again_in_a_new_one(self):
        (self.home / "tasks" / "03.md").write_text("# T\n\nno status here\n", encoding="utf-8")
        for n in ("04", "05"):
            (self.home / "tasks" / f"{n}.md").write_text("# T\n\nnothing\n", encoding="utf-8")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle", t_tl_s1="idle")
        self.tick(0)
        self.tick(1)
        text = "blind: 3 tickets, none with a status"
        self.assertEqual([x for _m, x in self.sent if x.startswith("blind")], [text])
        self.assertEqual(self.sent[0][0], "t-tl-s1")  # route(): the scope's Team Lead, as a nudge
        self.assertRegex(self.log(), r"(?m)^2027-01-15T08:00:00Z blind: 3 tickets, none with a status$")
        self.assertEqual(self.log().count("blind to t-tl-s1: sent: " + text), 1)
        self.assertEqual(json.loads((self.home / "watchdog.state.json").read_text(encoding="utf-8"))["blind_logged"], True)
        self.tickets(t03="ready")  # a status appears: the spell ends
        self.tick(2)
        for n in ("04", "05"):
            (self.home / "tasks" / f"{n}.md").unlink()
        (self.home / "tasks" / "03.md").write_text("# T\n\nnone\n", encoding="utf-8")
        self.tick(3)
        self.assertEqual(len([x for _m, x in self.sent if x.startswith("blind")]), 1 + 1)
        self.assertIn("blind: 1 tickets, none with a status", self.log())

    def test_blind_needs_tickets_none_with_a_status_and_no_goals(self):
        self.agents(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle")
        self.tick(0)  # no ticket
        (self.home / "tasks" / "03.md").write_text("# T\n\nStatus: ready\n", encoding="utf-8")
        (self.home / "tasks" / "04.md").write_text("# T\n\nState: ready\n", encoding="utf-8")  # 02: a State: line is a status
        self.tick(1)  # one has a status
        self.assertNotIn("blind", self.log())
        (self.home / "tasks" / "03.md").write_text("# T\n\nnone\n", encoding="utf-8")
        goals = self.home / "goals.md"
        goals.write_text("| # | Goal | Status |\n|---|---|---|\n| G1 | x | in progress |\n", encoding="utf-8")
        self.tick(2)  # goals recorded
        self.assertNotIn("blind", self.log())

    def test_a_name_listed_twice_in_the_roster_shows_once_in_the_log_and_the_nudge(self):
        (self.home / "roster.md").write_text(ROSTER + "| t-dev-s1 | dev | s1 | ticket 03 | live | b |\n", encoding="utf-8")
        self.tickets(t03="ready")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle")
        self.tick(0)
        self.assertEqual(self.log().count("t-dev-s1"), 1)

    def test_tick_in_a_process_sends_the_nudge_to_the_manager_through_herdr(self):
        fake = Path(self.tmp.name) / "bin"
        fake.mkdir()
        (fake / "herdr").write_text('#!/usr/bin/env bash\necho "$@" >> "$HERDR_LOG"\n', encoding="utf-8", newline="\n")
        (fake / "herdr").chmod(0o755)
        log = Path(self.tmp.name) / "h.log"
        self.tickets(t03="ready")
        self.agents(t_mgr_s1="idle")
        env = clean_env(HERDR_LOG=str(log), PATH=f"{fake}:{os.environ['PATH']}", PYTHONDONTWRITEBYTECODE="1")
        # the state says the spell began 20 minutes ago: both nudges are due
        (self.home / "watchdog.state.json").write_text(json.dumps({"idle_since": 0, "nudged": []}), encoding="utf-8")
        r = winlaunch.run_script(str(BIN / "squad-watchdog"), ["tick", "--home", str(self.home), "--manager", "t-mgr-s1",
                                                              "--herdr-json", str(self.herdr)], env, utf8=True, encoding="utf-8", capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")  # no raw event lines
        calls = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 2, calls)
        self.assertTrue(all(c.startswith("agent prompt t-mgr-s1 WATCHDOG:") for c in calls), calls)


class WakeTest(WatchdogTest):
    """Ticket 08: one message to the Manager per event (pane blocked 10 min); never repeated."""

    def msgs(self, *rows):
        with open(self.home / "messages.jsonl", "a", encoding="utf-8") as fh:
            for typ, frm, text in rows:
                fh.write(json.dumps({"ts": "2026-11-10T10:00:00.000Z", "from": frm, "to": "x", "type": typ, "task": "03",
                                     "text": text}) + "\n")

    def wakes(self):
        return [t for _m, t in self.sent if t.startswith("WAKE")]

    def work(self, **kw):
        self.agents(**dict(dict(t_mgr_s1="working", t_dev_s1="idle", t_qa_s1="working"), **kw))

    def test_a_ticket_that_passes_or_returns_three_times_sends_and_logs_nothing(self):
        self.work()
        self.tickets(t03="building")
        self.tick(0)
        self.tickets(t03="passed")
        self.msgs(*[x for n in (1, 2, 3) for x in (("HANDIN", "t-dev-s1", f"HANDIN 03: commit aaa{n}111"), ("FAIL", "t-qa-s1", f"FAIL 03: aaa{n}111 x"))])
        self.tick(1)
        self.tick(2)
        self.assertEqual(self.sent, [])
        self.assertNotIn("wake", self.log() if (self.home / "watchdog.log").exists() else "")

    def test_blocked_pane_wakes_once_after_10_minutes_and_never_relays(self):
        self.work(t_dev_s1="blocked")
        self.tickets(t03="building")
        self.tick(0)
        self.tick(9)
        self.assertEqual(self.wakes(), [])
        self.tick(10)
        self.tick(20)
        self.assertEqual(len(self.wakes()), 1)
        self.assertIn("Chieu's to answer", self.wakes()[0])
        self.assertIn("t-dev-s1", self.wakes()[0])
        self.work(t_dev_s1="working")  # unblocked, then blocked again: a new spell, a new message
        self.tick(21)
        self.work(t_dev_s1="blocked")
        self.tick(22)
        self.tick(33)
        self.assertEqual(len(self.wakes()), 2)

    def test_no_wake_into_a_blocked_manager_pane_and_a_failed_send_is_retried(self):
        self.work(t_dev_s1="blocked")
        self.tickets(t03="building")
        self.tick(0)
        self.work(t_dev_s1="blocked", t_mgr_s1="blocked")
        self.tick(11)
        self.assertEqual(self.wakes(), [])  # a prompt may be open: nothing sent, key not stored
        self.work(t_dev_s1="blocked")
        fails = []
        W.tick(self.home, "t-mgr-s1", now=T0 + 12 * MIN, herdr_json=str(self.herdr), send=lambda m, t: (fails.append(t) or (False, "no")))
        self.tick(13)  # retried and sent
        self.tick(14)
        self.assertEqual((len(fails), len(self.wakes())), (1, 1))

    def test_switch_off_and_old_state_file(self):
        self.work(t_dev_s1="blocked")
        self.tickets(t03="building")
        (self.home / "watchdog.state.json").write_text(json.dumps({"beat": 1, "idle_since": None, "wake_status": {"03": "building"}}),
                                                      encoding="utf-8")  # an old file with the removed key
        self.tick(0)
        self.assertNotIn("wake_status", json.loads((self.home / "watchdog.state.json").read_text(encoding="utf-8")))
        W.set_wake(self.home, False)
        self.assertFalse(W.wake_on(self.home))
        self.tick(11)
        self.assertEqual(self.wakes(), [])
        W.set_wake(self.home, True)
        self.tick(12)
        self.assertEqual(len(self.wakes()), 1)

    def test_roster_text_is_one_capped_line(self):
        self.assertEqual(W.clean("a\x1b[31m\nb" + "x" * 200).count("\n"), 0)
        self.assertLessEqual(len(W.clean("x" * 200)), 80)
        self.assertNotIn("\x1b", W.clean("a\x1b[31mb"))
        self.work(t_dev_s1="blocked")
        r = (self.home / "roster.md").read_text(encoding="utf-8").replace("ticket 03", "ticket 03 " + "y" * 200)
        (self.home / "roster.md").write_text(r, encoding="utf-8")
        self.tickets(t03="building")
        self.tick(0)
        self.tick(11)
        self.assertTrue(all(len(t) < 300 and "\n" not in t for t in self.wakes()) and self.wakes())

    def test_sleep_on_starts_the_homes_watchdog_unless_it_runs(self):  # AC4
        from squadtest import fake_herdr
        bindir = Path(self.tmp.name) / "fakebin"
        bindir.mkdir()
        fake_herdr(bindir)
        hlog = Path(self.tmp.name) / "h.log"
        env = clean_env(PYTHONDONTWRITEBYTECODE="1", HERDR_ENV="1", HERDR_LOG=str(hlog), PATH=f"{bindir}:{os.environ['PATH']}")
        env.pop("SQUAD_WATCHDOG", None)
        def run(*a):
            return winlaunch.run_script(str(BIN / "squad-watchdog"), list(a) + ["--home", str(self.home)], env, utf8=True,
                                        encoding="utf-8", capture_output=True)
        def tabs():
            return sum(l.startswith("tab create") and "--label watchdog" in l for l in hlog.read_text(encoding="utf-8").splitlines()) if hlog.exists() else 0
        self.assertEqual(run("sleep", "off").returncode, 0)
        self.assertEqual(tabs(), 0)  # off starts nothing
        r = run("sleep", "on")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(tabs(), 1)
        self.assertTrue(W.sleep_on(self.home))
        (self.home / "watchdog.state.json").write_text(json.dumps({"beat": time.time()}), encoding="utf-8")
        run("sleep", "on")
        self.assertEqual(tabs(), 1)  # running: no second one

    def test_cli_wake_switch_and_status(self):
        env = clean_env(PYTHONDONTWRITEBYTECODE="1")
        def run(*a):
            return winlaunch.run_script(str(BIN / "squad-watchdog"), list(a) + ["--home", str(self.home)], env, utf8=True,
                                        encoding="utf-8", capture_output=True)
        self.assertEqual(run("wake", "off").returncode, 0)
        self.assertIn("wake-ups: off", run("status").stdout)
        run("wake", "on")
        self.assertIn("wake-ups: on", run("status").stdout)


GOALS = """# Goals

| # | Goal | Status | Reason / what Chieu must do | Updated |
|---|---|---|---|---|
| G1 | Ship the report |  In Progress | | 2027-01-15 |
| G2 | Fix the login | blocked | needs the prod key; inbox item i7 | 2027-01-15 |
| G3 | Old thing | done | | 2027-01-14 |
"""
ALL_DONE = "| # | Goal | Status |\n|---|---|---|\n| G1 | x | done |\n| G2 | y | Done |\n"


class GoalsTest(WatchdogTest):
    """Ticket 03: the watchdog follows <home>/goals.md."""

    def goals(self, text=GOALS):
        (self.home / "goals.md").write_text(text, encoding="utf-8")

    def idle(self, **kw):
        self.agents(**dict(dict(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle"), **kw))

    def test_read_goals_is_tolerant_and_none_without_a_file(self):
        self.assertIsNone(W.read_goals(self.home))
        self.goals(GOALS.replace("blocked", "  BLOCKED ").replace("done", "weird"))
        self.assertEqual(W.read_goals(self.home), [("G1", "Ship the report", "in progress", ""),
                         ("G2", "Fix the login", "blocked", "needs the prod key; inbox item i7"), ("G3", "Old thing", "in progress", "")])
        self.goals("# Goals\n\n| # | Goal | Status | Reason | Updated |\n|---|---|---|---|---|\n")
        self.assertEqual(W.read_goals(self.home), [])

    def test_open_goal_and_idle_nudges_at_5_and_15_with_status_and_reason(self):
        self.goals()
        self.idle()  # no ticket waits: the goals alone keep the spell open
        for m in (0, 4, 5, 14, 15, 40):
            self.tick(m)
        self.assertEqual(len(self.sent), 2)
        first, second = (t for _, t in self.sent)
        self.assertIn("nobody has worked for 5 minutes", first)
        self.assertIn("still nobody working after 15 minutes", second)
        self.assertIn("G1 Ship the report: in progress", first)
        self.assertNotIn("G2", first)  # blocked: never listed
        self.assertNotIn("G3", first)
        self.assertIn("solve", first)
        self.assertNotIn("ignore this", first)
        self.assertIn("idle start: nobody works and goals are open (G1", self.log())
        self.assertNotIn("watchdog stops", self.log())

    BLOCKED = "| # | Goal | Status | Reason |\n|---|---|---|---|\n| G1 | Ship | blocked | inbox i7 |\n| G2 | Fix | blocked | key |\n"
    MIXED = BLOCKED.replace("G1 | Ship | blocked", "G1 | Ship | in progress")

    def test_all_blocked_goals_get_no_nudge_one_log_line_and_the_watchdog_keeps_running(self):  # AC1
        self.goals(self.BLOCKED)
        self.idle()
        for m in (0, 5, 15, 40):
            self.tick(m)
        self.assertEqual(self.sent, [])
        self.assertEqual(self.log().count("open goals are all blocked"), 1)
        self.assertNotIn("watchdog stops", self.log())
        self.assertNotIn(("stop",), self.tick(41))

    def test_mixed_goals_nudge_names_only_the_in_progress_ones(self):  # AC2
        self.goals(self.MIXED)
        self.idle()
        for m in (0, 5, 15):
            self.tick(m)
        self.assertEqual(len(self.sent), 2)
        for _, text in self.sent:
            self.assertIn("G1 Ship: in progress", text)
            self.assertNotIn("G2", text)
            self.assertNotIn("blocked", text)

    def test_goal_turning_blocked_stops_the_nudges_and_back_to_in_progress_starts_a_fresh_spell(self):  # AC3
        self.goals(self.MIXED)
        self.idle()
        self.tick(0)
        self.tick(5)
        self.assertEqual(len(self.sent), 1)
        self.goals(self.BLOCKED)
        self.tick(16)
        self.tick(30)
        self.assertEqual(len(self.sent), 1)  # no 15 min nudge
        self.goals(self.MIXED)
        self.tick(40)  # fresh spell starts here
        self.tick(44)
        self.assertEqual(len(self.sent), 1)
        self.tick(45)
        self.assertEqual(len(self.sent), 2)

    def test_all_goals_done_and_nobody_working_stops_and_run_returns(self):
        self.goals(ALL_DONE)
        self.idle()
        self.tickets(t03="building")  # an open ticket does not matter once goals are recorded
        self.assertIn(("stop",), self.tick(0))
        self.assertIn("all goals done; watchdog stops", self.log())
        self.assertIsNone(W.read_state(self.home)["beat"])
        self.assertEqual(self.sent, [])
        # the real run loop (real clock, no beat left): it returns instead of looping
        self.assertEqual(W.run(self.home, "t-mgr-s1", 0.01, str(self.herdr)), 0)
        self.assertIn("watchdog started", self.log())

    def test_all_goals_done_but_an_agent_working_does_not_stop(self):
        self.goals(ALL_DONE)
        self.idle(t_dev_s1="working")
        self.assertNotIn(("stop",), self.tick(0))
        self.assertFalse((self.home / "watchdog.log").exists())

    def test_the_stop_waits_for_a_pending_pc_sleep(self):
        self.goals(ALL_DONE)
        self.idle()
        W.set_sleep(self.home, True)
        self.tick(0)
        self.assertNotIn(("stop",), self.tick(6))
        self.assertEqual(self.suspended, [1])
        self.assertIn(("stop",), self.tick(7))  # the switch is off now

    def test_no_goals_file_or_an_empty_table_behaves_as_before(self):
        self.tickets(t03="ready")
        self.idle()
        self.goals("| # | Goal | Status |\n|---|---|---|\n")
        for m in (0, 5, 15):
            self.assertNotIn(("stop",), self.tick(m))
        self.assertEqual(len(self.sent), 2)
        self.assertIn("Waiting: 03 ready.", self.sent[0][1])
        self.assertNotIn("ignore this", self.sent[0][1])

    def test_status_shows_the_open_goal_count(self):
        self.goals()
        r = winlaunch.run_script(str(BIN / "squad-watchdog"), ["status", "--home", str(self.home)], clean_env(), utf8=True,
                                 encoding="utf-8", capture_output=True)
        self.assertIn("open goals: 2", r.stdout)

    def test_ensure_starts_once_and_a_second_call_does_nothing(self):
        import subprocess
        import time
        from unittest import mock
        started = []

        def fake_popen(argv, **kw):
            started.append(argv)
            W.write_state(self.home, {"beat": time.time()})  # what the started `run` does
        env = {k: v for k, v in os.environ.items() if k not in ("HERDR_ENV", "SQUAD_WATCHDOG")}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(subprocess, "Popen", fake_popen):
            self.assertTrue(W.ensure(self.home, "t-mgr-s1"))
            self.assertFalse(W.ensure(self.home, "t-mgr-s1"))
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0][-4:], ["--home", str(self.home), "--manager", "t-mgr-s1"])


class BgTest(unittest.TestCase):
    """Ticket 03 (watchdog-shell): a herdr `bg` shell token counts as working, capped, and the log says why."""
    setUp = WatchdogTest.setUp
    tickets, tick, log = WatchdogTest.tickets, WatchdogTest.tick, WatchdogTest.log

    def agents(self, **spec):
        """name=status, or name=(status, bg token). A row copied from a live herdr list has `tokens` only when a shell runs."""
        rows = []
        for n, v in spec.items():
            status, bg = v if isinstance(v, tuple) else (v, None)
            row = {"name": n.replace("_", "-"), "agent_status": status, "pane_id": "p"}
            if bg:
                row["tokens"] = {"bg": bg}
            rows.append(row)
        self.herdr.write_text(json.dumps({"result": {"agents": rows}}), encoding="utf-8")

    def setup_busy(self, dev=("done", "\u23f5 1 shell"), **more):
        self.tickets(t03="building")
        self.agents(**dict(dict(t_mgr_s1="idle", t_dev_s1=dev, t_qa_s1="idle"), **more))

    def test_a_dev_with_a_token_holds_the_idle_spell_and_a_blocked_one_still_wakes(self):
        self.setup_busy()
        for m in range(0, 31, 5):
            self.tick(m)
        self.assertEqual(self.sent, [])
        self.assertNotIn("idle start", self.log())
        self.assertEqual(self.log().count("bg busy:"), 1)
        # blocked with a token: stays blocked, never busy, and the 10-minute WAKE comes as before
        self.setup_busy(dev=("blocked", "\u23f5 1 shell"), t_mgr_s1="working", t_qa_s1="working")
        for m in (40, 51):
            self.tick(m)
        self.assertEqual(len([t for _m, t in self.sent if t.startswith("WAKE")]), 1)
        self.assertNotIn("busy (bg shell)", self.log().split("bg busy:")[-1].split("\n", 1)[-1])

    def test_decide_keeps_its_input_and_loads_a_state_without_bg_keys(self):
        import copy
        self.setup_busy()
        snap = W.snapshot(self.home, str(self.herdr))
        st = {"nudged": [5], "idle_since": T0, "bg_since": {"t-dev-s1": T0 - 10}, "bg_busy": ["t-dev-s1"], "wake_blocked": {"x": 1}}
        before = copy.deepcopy(st)
        W.decide(st, snap, T0, False)
        self.assertEqual(st, before)
        new, _ = W.decide({"idle_since": None}, snap, T0, False)
        self.assertEqual((new["bg_since"], new["bg_busy"]), ({"t-dev-s1": T0}, ["t-dev-s1"]))

    def test_the_cap_ends_the_hold_once_per_stretch_and_a_work_pass_resets_the_clock(self):
        self.setup_busy()
        self.tick(0)
        self.tick(59)
        self.assertEqual(self.sent, [])
        self.tick(60)  # cap: the idle spell starts now, nudges follow 5 and 15 min later
        self.tick(64)
        self.assertEqual(len(self.sent), 0)
        self.tick(65)
        self.tick(75)
        self.tick(90)
        self.assertEqual(len(self.sent), 2)
        log = self.log()
        self.assertEqual(log.count("bg busy: t-dev-s1 has a background shell (\u23f5 1 shell); counted as working for at most 60 min"), 1)
        self.assertEqual(log.count("bg cap: t-dev-s1 counted as working for 60 min; idle check resumes"), 1)
        self.assertIn("idle start:", log)
        self.assertIn("t-dev-s1 idle", log.split("idle start:")[1])  # past the cap: no more `busy`
        self.assertEqual(self.sent and "nobody has worked for 5 minutes" in self.sent[0][1], True)
        # new stretch: a token that goes absent for one pass and returns restarts the clock
        self.setup_busy(dev="idle")
        self.tick(91)
        self.setup_busy()
        self.tick(92)
        self.assertEqual(W.read_state(self.home)["bg_busy"], ["t-dev-s1"])
        self.assertEqual(self.log().count("bg busy:"), 2)

    def test_a_working_pass_in_a_long_hold_resets_the_cap(self):
        self.setup_busy()
        self.tick(0)
        self.setup_busy(dev="working")
        self.tick(50)
        self.assertEqual(W.read_state(self.home)["bg_since"], {})  # no entry without a token: no growth
        self.setup_busy()
        self.tick(51)
        self.tick(110)
        self.assertEqual(W.read_state(self.home)["bg_busy"], ["t-dev-s1"])
        self.tick(111)
        self.assertEqual(W.read_state(self.home)["bg_busy"], [])

    def test_the_cap_env_falls_back_to_60_and_zero_turns_the_rule_off(self):
        from unittest import mock
        for val, want in (("", 3600), ("abc", 3600), ("-5", 3600), ("nan", 3600), ("0", 0), ("2", 120)):
            with mock.patch.dict(os.environ, {"SQUAD_WATCHDOG_BG_MAX": val}):
                self.assertEqual(W.bg_max_s(), want, val)
        self.setup_busy()
        with mock.patch.dict(os.environ, {"SQUAD_WATCHDOG_BG_MAX": "0"}):
            self.tick(0)
        self.assertIn("idle start", self.log())
        self.assertNotIn("bg busy", self.log())

    def test_an_other_squads_token_holds_the_sleep_until_the_cap_and_is_not_logged(self):
        self.agents(other_dev_1=("done", "\u23f5 1 shell"), t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle")
        W.set_sleep(self.home, True)
        self.tick(0)
        self.tick(6)
        self.assertEqual(self.suspended, [])
        self.tick(61)  # past the cap: the quiet clock starts
        self.assertEqual(self.suspended, [])
        self.tick(67)
        self.assertEqual(self.suspended, [1])
        self.assertNotIn("bg busy", self.log() if (self.home / "watchdog.log").exists() else "")

    def test_a_busy_roster_agent_holds_the_stop_until_the_cap(self):
        self.tickets(t03="building")
        (self.home / "goals.md").write_text("| # | Goal | Status |\n|---|---|---|\n| G1 | x | done |\n", encoding="utf-8")
        self.agents(t_mgr_s1="idle", t_dev_s1=("done", "\u23f5 1 shell"), t_qa_s1="idle")
        self.assertNotIn(("stop",), self.tick(0))
        self.assertNotIn(("stop",), self.tick(59))
        self.assertNotIn("watchdog stops", self.log())
        self.assertIn(("stop",), self.tick(60))
        self.assertIn("all goals done; watchdog stops", self.log())


class TeamLeadTest(unittest.TestCase):
    """Ticket 06: a scope home wakes its own Team Lead (t-tl-s1), the Manager only as fallback; a goal home keeps the Manager."""

    setUp = WatchdogTest.setUp
    tickets, agents, tick, log = WatchdogTest.tickets, WatchdogTest.agents, WatchdogTest.tick, WatchdogTest.log

    def setUp(self):  # noqa: F811
        WatchdogTest.setUp(self)
        with open(self.home / "roster.md", "a", encoding="utf-8") as fh:  # the Team Lead is in the roster, as in a real squad
            fh.write("| t-tl-s1 | team-lead | s1 | plan | live | d |\n")

    def up(self, **kw):
        self.agents(**dict(dict(t_mgr_s1="idle", t_tl_s1="idle", t_dev_s1="idle"), **kw))

    def test_ac1_the_nudge_goes_to_the_team_lead_with_its_own_wording(self):
        self.tickets(t03="ready")
        self.up()
        for m in (0, 5, 15):
            self.tick(m)
        self.assertEqual([m for m, _ in self.sent], ["t-tl-s1", "t-tl-s1"])
        self.assertIn("spawn one within your cap, or `ASK` the Manager", self.sent[0][1])
        self.assertNotIn("route:", self.log())

    def test_goal_status_is_asked_of_the_team_lead_when_no_ticket_is_open(self):
        self.tickets(t03="passed")
        (self.home / "goals.md").write_text("| # | Goal | Status |\n|---|---|---|\n| G1 | Ship the report | in progress |\n"
                                            "| G2 | Fix login | blocked |\n| G3 | Add search | in progress |\n", encoding="utf-8")
        self.up()
        for m in (0, 5, 15):
            self.tick(m)
        self.assertEqual([m for m, _ in self.sent], ["t-tl-s1", "t-tl-s1"])
        for _, text in self.sent:
            self.assertIn("G1 Ship the report: in progress", text)
            self.assertNotIn("G2", text)
            self.assertIn("send the Manager one line per open goal, naming its id", text)
            for gid in ("G1", "G3"):
                self.assertIn(f"`goal {gid} done` or `goal {gid} blocked: <reason>`", text)
            self.assertIn("`goal <id> blocked: <reason>`", text)
            self.assertNotIn("STATUS", text)
            self.assertNotIn("goal G2 ", text)
            self.assertIn("done when all its tickets passed, else blocked with the reason", text)
            self.assertIn("you never edit it", text)
            self.assertNotIn("write goals.md", text)

    def test_goal_status_is_not_asked_while_a_ticket_is_open_and_without_goals(self):
        self.tickets(t03="ready")
        (self.home / "goals.md").write_text("| # | Goal | Status |\n|---|---|---|\n| G1 | Ship the report | in progress |\n", encoding="utf-8")
        self.up()
        for m in (0, 5, 15):
            self.tick(m)
        self.assertEqual(len(self.sent), 2)
        for _, text in self.sent:
            self.assertIn("Waiting: 03 ready", text)
            self.assertIn("G1 Ship the report: in progress", text)
            self.assertNotIn("send the Manager one line", text)
            self.assertNotIn("STATUS", text)
        only_blocked = W.team_lead_nudge_text(5, 0, {"tickets": [], "agents": [], "goals": [("G2", "Fix login", "blocked", "")]})
        self.assertNotIn("G2", only_blocked)
        self.assertNotIn("send the Manager one line", only_blocked)
        self.assertNotIn("STATUS", only_blocked)
        plain = W.team_lead_nudge_text(5, 0, {"tickets": [], "agents": [], "goals": []})
        self.assertNotIn("Open goals", plain)
        self.assertIn("Waiting: none open", plain)
        self.assertNotIn("STATUS", plain)

    def test_ac2_absent_then_blocked_team_lead_falls_back_to_the_manager_and_a_blocked_manager_holds(self):
        self.tickets(t03="ready")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")  # no Team Lead in the herdr list
        self.tick(0)
        self.tick(5)
        self.assertEqual([m for m, _ in self.sent], ["t-mgr-s1"])
        self.assertIn("route: 5 min idle -> t-mgr-s1 (team lead absent)", self.log())
        self.up(t_tl_s1="blocked")
        self.tick(15)
        self.assertEqual([m for m, _ in self.sent], ["t-mgr-s1", "t-mgr-s1"])
        self.assertIn("(team lead blocked)", self.log())
        # both panes blocked: nothing sent, the key stays free for a later pass
        self.sent.clear()
        (self.home / "watchdog.state.json").write_text(json.dumps({"idle_since": T0, "nudged": []}), encoding="utf-8")
        self.up(t_tl_s1="blocked", t_mgr_s1="blocked")
        self.tick(20)
        self.assertEqual(self.sent, [])
        self.assertIn("held: t-mgr-s1 is blocked", self.log())
        self.up(t_tl_s1="blocked")
        self.tick(21)
        self.assertEqual(len(self.sent), 2)  # 5 and 15 both due and now sent

    def test_ac3_a_blocked_developer_wakes_the_team_lead_and_a_blocked_team_lead_the_manager(self):
        self.tickets(t03="building")
        self.up(t_dev_s1="blocked")
        self.tick(0)
        self.tick(10)
        self.assertEqual([m for m, t in self.sent if t.startswith("WAKE")], ["t-tl-s1"])
        self.sent.clear()
        self.up(t_dev_s1="working", t_tl_s1="blocked")
        self.tick(11)
        self.tick(22)
        self.assertEqual([(m, "t-tl-s1" in t) for m, t in self.sent if t.startswith("WAKE")], [("t-mgr-s1", True)])
        self.assertNotIn("route:", self.log())  # the design, not a fallback

    def test_ac4_a_goal_home_nudges_the_goal_manager_and_wakes_no_scope_pane(self):
        squad = self.home.parent.parent
        goal = squad / "goals" / "g1"
        goal.mkdir(parents=True)
        (goal / "goal.md").write_text("# g1\n", encoding="utf-8")
        (goal / "roster.md").write_text(ROSTER.replace("s1", "g1"), encoding="utf-8")
        (self.home / "scope.md").write_text("# s1\ngoal: g1\n", encoding="utf-8")
        self.tickets(t03="building")
        self.agents(t_mgr_g1="idle", t_dev_g1="idle", t_qa_g1="idle", t_dev_s1="blocked", t_tl_s1="idle")
        for m in (0, 5, 11, 15):
            W.tick(goal, "t-mgr-g1", now=T0 + m * MIN, herdr_json=str(self.herdr),
                   send=lambda t, x: (self.sent.append((t, x)) or (True, "")))
        self.assertEqual([m for m, _ in self.sent], ["t-mgr-g1", "t-mgr-g1"])
        self.assertFalse(any(x.startswith("WAKE") for _, x in self.sent))
        # the scope's own watchdog wakes its Team Lead for the same pane
        self.tick(0)
        self.tick(11)
        self.assertIn(("t-tl-s1", True), [(m, x.startswith("WAKE")) for m, x in self.sent])
        # every goal done: stop, as before
        (goal / "goals.md").write_text("| # | Goal | Status |\n|---|---|---|\n| G1 | x | done |\n", encoding="utf-8")
        self.agents(t_mgr_g1="idle", t_dev_s1="idle")
        W.tick(goal, "t-mgr-g1", now=T0 + 30 * MIN, herdr_json=str(self.herdr), send=None)
        self.assertIn("all goals done; watchdog stops", (goal / "watchdog.log").read_text(encoding="utf-8"))

    def test_the_default_manager_of_an_in_goal_scope_is_the_goal_manager(self):
        (self.home / "scope.md").write_text("# s1\ngoal: g1\n", encoding="utf-8")
        self.assertEqual(W.default_manager(self.home), "t-mgr-g1")


class ColdCacheTest(unittest.TestCase):
    """Warm-cache ticket 03: the cold-cache pass (design notes C4 and "Cold-cache pass"). `send` and `respawn` are fakes."""

    ROSTER = ("# Roster\n\n| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n"
              "| t-mgr-s1 | manager | s1 | plan | live | sid-mgr |\n| t-tl-s1 | team-lead | s1 | plan | live | sid-tl |\n"
              "| t-dev-s1 | dev | s1 | ticket 03 | building | sid-dev |\n")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.home = root / ".claude" / "squads" / "t" / "scopes" / "s1"
        (self.home / "tasks").mkdir(parents=True)
        (self.home / "roles").mkdir()
        (self.home / "scope.md").write_text("# s1\n", encoding="utf-8")
        (self.home / "roster.md").write_text(self.ROSTER, encoding="utf-8")
        (self.home / "tasks" / "03.md").write_text("# T\n\nStatus: building\n", encoding="utf-8")
        self.proj = root / "claude" / "projects" / "-p"
        self.proj.mkdir(parents=True)
        env = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(root / "claude")})
        env.start()
        self.addCleanup(env.stop)
        self.herdr = root / "herdr.json"
        self.sent, self.calls, self.result = [], [], (True, "")

    def turn(self, sid, at_min, ctx=120_000, side=False):
        """An assistant turn `at_min` minutes after T0 in the main transcript, or in its subagent folder."""
        rec = {"type": "assistant", "timestamp": W.iso(T0 + at_min * MIN), "message": {
            "id": f"m{at_min}", "model": "m", "usage": {"input_tokens": 1, "cache_read_input_tokens": ctx - 1,
                                                       "cache_creation_input_tokens": 0, "output_tokens": 5}}}
        path = self.proj / f"{sid}.jsonl"
        if side:
            path = self.proj / sid / "subagents" / "a.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")

    def agents(self, **spec):
        rows = []
        for n, v in spec.items():
            status, bg = v if isinstance(v, tuple) else (v, None)
            rows.append({"name": n.replace("_", "-"), "agent_status": status, "pane_id": "p", **({"tokens": {"bg": bg}} if bg else {})})
        self.herdr.write_text(json.dumps({"result": {"agents": rows}}), encoding="utf-8")

    def tick(self, minutes, home=None, manager="t-mgr-s1"):
        return W.tick(home or self.home, manager, now=T0 + minutes * MIN, herdr_json=str(self.herdr),
                      send=lambda m, text: (self.sent.append((m, text)) or (True, "")),
                      respawn=lambda argv, env, timeout: (self.calls.append((argv, env, timeout)) or self.result))

    def prompts(self):
        return [(m, t) for m, t in self.sent if t.startswith("COLD CACHE")]

    def log(self, home=None):
        return ((home or self.home) / "watchdog.log").read_text(encoding="utf-8")

    def notes(self, name, at_min, home=None):
        p = (home or self.home) / "roles" / f"{name}.notes.md"
        p.write_text("notes\n", encoding="utf-8")
        os.utime(p, (T0 + at_min * MIN, T0 + at_min * MIN))

    def busy(self, **more):
        self.agents(**dict(dict(t_mgr_s1="working", t_tl_s1="working", t_dev_s1="idle"), **more))

    # AC2, AC3
    def test_idle_means_55_minutes_since_the_last_main_turn_and_a_subagent_turn_does_not_count(self):
        self.turn("sid-dev", 0)
        self.turn("sid-dev", 50, side=True)  # newer than the main turn: must not hide the idleness
        self.busy()
        self.tick(54)
        self.assertEqual(self.prompts(), [])
        self.tick(56)
        self.tick(57)  # once per message
        self.assertEqual([m for m, _ in self.prompts()], ["t-dev-s1"])
        self.assertIn("COLD CACHE: t-dev-s1, your prompt cache expires in about 5 minutes. Write roles/t-dev-s1.notes.md now (NOTE-1)", self.prompts()[0][1])
        self.assertIn("cold-cache: prompted t-dev-s1 (1/2, ctx 120k, idle 56 min)", self.log())

    # AC4
    def test_notes_newer_than_the_prompt_respawn_lazy_with_a_clean_environment(self):
        self.turn("sid-dev", 0)
        self.busy()
        self.tick(56)
        self.notes("t-dev-s1", 55)  # older than the prompt: not enough
        self.tick(57)
        self.assertEqual(self.calls, [])
        self.notes("t-dev-s1", 57)
        parent = {"SCOPE_DIR": "/parent/scope", "GOAL_DIR": "/parent/goal", "SQUAD_ROLE": "team-lead", "SQUAD_NAME": "parent"}
        with mock.patch.dict(os.environ, parent):
            self.tick(58)
        (argv, env, timeout), = self.calls
        self.assertEqual((Path(argv[0]).name, argv[1:], timeout), ("squad-respawn", ["t-dev-s1", "--lazy"], 120))
        self.assertNotIn("SQUAD_ROLE", env)
        self.assertNotIn("SQUAD_NAME", env)
        self.assertNotIn("GOAL_DIR", env)
        self.assertEqual((env["SCOPE_DIR"], env["SQUAD_DIR"]), (str(self.home), str(self.home.parent.parent)))
        self.assertIn("cold-cache: respawned lazy t-dev-s1", self.log())
        self.assertFalse((self.home / "watchdog.cold.json").read_text(encoding="utf-8").count("t-dev-s1"))

    def test_a_failed_respawn_is_logged_and_not_retried(self):
        self.turn("sid-dev", 0)
        self.busy()
        self.tick(56)
        self.notes("t-dev-s1", 57)
        self.result = (False, "timeout")
        for m in (58, 60, 70):
            self.tick(m)
        self.assertEqual(len(self.calls), 1)
        self.assertIn("cold-cache: respawn lazy failed t-dev-s1: timeout", self.log())

    # AC10
    def test_a_goal_home_respawns_its_own_manager_with_goal_dir_and_no_scope_dir(self):
        goal = self.home.parent.parent / "goals" / "g1"
        (goal / "roles").mkdir(parents=True)
        (goal / "goal.md").write_text("# g1\n", encoding="utf-8")
        (goal / "roster.md").write_text(self.ROSTER.replace("s1", "g1"), encoding="utf-8")
        self.turn("sid-mgr", 0)
        self.turn("sid-dev", 0)  # a scope agent of the goal is not this home's roster row to touch
        self.agents(t_mgr_g1="idle", t_dev_g1="idle")
        self.tick(56, goal, "t-mgr-g1")
        self.assertEqual([m for m, _ in self.prompts()], ["t-mgr-g1"])  # a Manager needs no open work
        self.notes("t-mgr-g1", 57, goal)
        with mock.patch.dict(os.environ, {"SCOPE_DIR": "/parent/scope"}):
            self.tick(58, goal, "t-mgr-g1")
        (argv, env, _), = self.calls
        self.assertEqual(argv[1:], ["t-mgr-g1", "--lazy"])
        self.assertNotIn("SCOPE_DIR", env)
        self.assertEqual(env["GOAL_DIR"], str(goal))

    # AC5
    def test_two_prompts_then_gave_up_and_a_new_turn_starts_a_new_spell(self):
        self.turn("sid-dev", 0)
        self.busy()
        for m in (56, 57, 59, 62, 65, 70):
            self.tick(m)
        self.assertEqual(len(self.prompts()), 2)
        self.assertEqual(self.log().count("cold-cache: gave up: notes not written t-dev-s1"), 1)
        self.assertEqual(self.calls, [])
        self.turn("sid-dev", 71)
        self.tick(130)
        self.assertEqual(len(self.prompts()), 3)

    # AC6
    def test_a_blocked_pane_a_background_shell_and_a_small_context_are_logged_once_and_get_no_message(self):
        self.turn("sid-dev", 0)
        self.turn("sid-mgr", 0, ctx=30_000)
        self.turn("sid-tl", 0)
        self.agents(t_mgr_s1="idle", t_tl_s1=("idle", "1 shell"), t_dev_s1="blocked")
        for m in (56, 57, 60):
            self.tick(m)
        log = self.log()
        self.assertEqual(self.prompts(), [])
        for line in ("cold-cache: unavoidable: blocked t-dev-s1", "cold-cache: unavoidable: background shell t-tl-s1",
                     "cold-cache: skipped: small context t-mgr-s1 (ctx 30k)"):
            self.assertEqual(log.count(line), 1, line)

    # AC7
    def test_nothing_open_tells_the_team_lead_once_and_prompts_no_one_but_a_manager_is_respawned(self):
        (self.home / "tasks" / "03.md").write_text("# T\n\nStatus: passed\n", encoding="utf-8")
        for sid in ("sid-dev", "sid-mgr"):
            self.turn(sid, 0)
        self.agents(t_mgr_s1="idle", t_tl_s1="idle", t_dev_s1="idle")
        for m in (56, 57):
            self.tick(m)
        told = [(m, t) for m, t in self.sent if "has nothing open" in t]
        self.assertEqual(told, [("t-tl-s1", "t-dev-s1 has nothing open and a 120k context; retire it (COST-13b)")])
        self.assertEqual(self.log().count("cold-cache: nothing open t-dev-s1 (told t-tl-s1)"), 1)
        self.assertEqual([m for m, _ in self.prompts()], ["t-mgr-s1"])  # the Manager has no open work to need
        self.assertNotIn("t-dev-s1", "".join(a[1] for a in self.calls))

    # AC8, AC9, AC1
    def test_the_state_file_survives_garbage_and_an_env_override_and_the_kill_switch_apply(self):
        self.turn("sid-dev", 0, ctx=60_000)
        self.busy()
        (self.home / "watchdog.cold.json").write_text("{nope", encoding="utf-8")
        with mock.patch.dict(os.environ, {"SQUAD_WATCHDOG_COLD_CTX": "70000"}):
            self.tick(56)
        self.assertIn("skipped: small context t-dev-s1 (ctx 60k)", self.log())
        with mock.patch.dict(os.environ, {"SQUAD_WATCHDOG_COLD_CTX": "x"}):  # a bad value: the 50k default
            self.tick(57)
        self.assertEqual(len(self.prompts()), 1)
        self.assertIsInstance(json.loads((self.home / "watchdog.cold.json").read_text(encoding="utf-8")), dict)
        with mock.patch.dict(os.environ, {"SQUAD_WATCHDOG_COLD": "0"}):
            self.tick(300)
        self.assertEqual(len(self.prompts()), 1)

    def test_a_failure_in_the_pass_is_logged_and_the_idle_events_still_run(self):
        (self.home / "tasks" / "03.md").write_text("# T\n\nStatus: ready\n", encoding="utf-8")
        self.agents(t_mgr_s1="idle", t_tl_s1="idle", t_dev_s1="idle")
        with mock.patch.object(W, "last_turn", side_effect=RuntimeError("boom")):
            self.tick(0)
        log = self.log()
        self.assertIn("idle start", log)
        self.assertIn("cold-cache: pass failed: RuntimeError: boom", log)

    # QA whitebox F1
    def test_the_heartbeat_stays_fresh_while_several_agents_are_respawned_in_one_pass(self):
        """Each respawn can take minutes and squad-spawn's `ensure` starts a second watchdog once the beat is stale."""
        start = load_cli("squad-start")
        for sid in ("sid-mgr", "sid-tl", "sid-dev"):
            self.turn(sid, 0)
        self.agents(t_mgr_s1="idle", t_tl_s1="idle", t_dev_s1="idle")
        self.tick(56)
        for n in ("t-mgr-s1", "t-tl-s1", "t-dev-s1"):
            self.notes(n, 57)
        clock, alive = [T0 + 58 * MIN], []

        def slow(argv, env, timeout):
            clock[0] += 100  # 3 x 100 s: longer than the 180 s a beat may be old
            alive.append(start.watchdog_alive(self.home))
            return True, ""
        with mock.patch.object(time, "time", lambda: clock[0]):
            W.tick(self.home, "t-mgr-s1", now=T0 + 58 * MIN, herdr_json=str(self.herdr), send=lambda m, t: (True, ""), respawn=slow)
        self.assertEqual(alive, [True, True, True])


class UnsentMarkerTest(unittest.TestCase):
    """Spawn-prompt-unsent 02: the watchdog wakes the spawner of an agent whose roles/<name>.unsent marker is left."""

    ROSTER = ColdCacheTest.ROSTER

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.home = root / ".claude" / "squads" / "t" / "scopes" / "s1"
        (self.home / "tasks").mkdir(parents=True)
        (self.home / "roles").mkdir()
        (self.home / "scope.md").write_text("# s1\n", encoding="utf-8")
        (self.home / "roster.md").write_text(self.ROSTER, encoding="utf-8")
        self.herdr, self.sent = root / "herdr.json", []
        self.marker = self.home / "roles" / "t-dev-s1.unsent"

    def mark(self, spawner="t-tl-s1", at=0):
        self.marker.write_text(spawner + "\n", encoding="utf-8")
        os.utime(self.marker, (T0 + at * MIN, T0 + at * MIN))

    def agents(self, **state):
        rows = [{"name": n.replace("_", "-"), "agent_status": s, "pane_id": "p"} for n, s in state.items()]
        self.herdr.write_text(json.dumps({"result": {"agents": rows}}), encoding="utf-8")

    def tick(self, minutes):
        return W.tick(self.home, "t-mgr-s1", now=T0 + minutes * MIN, herdr_json=str(self.herdr),
                      send=lambda m, text: (self.sent.append((m, text)) or (True, "")))

    def unsent(self):
        return [(m, t) for m, t in self.sent if "did not start" in t]

    def test_ac1_idle_agent_after_2_minutes_tells_the_spawner_once_and_never_sends_enter(self):  # AC1
        self.mark()
        self.agents(t_mgr_s1="working", t_tl_s1="working", t_dev_s1="idle")
        self.tick(1)
        self.assertEqual(self.unsent(), [])  # marker only 1 min old
        self.tick(2)
        self.tick(5)
        got = self.unsent()
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0][0], "t-tl-s1")
        self.assertIn("t-dev-s1", got[0][1])
        self.assertIn("herdr agent send-keys t-dev-s1 Enter", got[0][1])
        self.assertTrue(self.marker.exists())
        self.assertIn("unsent t-dev-s1 to t-tl-s1: sent", (self.home / "watchdog.log").read_text(encoding="utf-8"))

    def test_ac2_working_gone_or_retired_removes_the_marker_without_a_message_and_blocked_does_nothing(self):  # AC2
        for state, kept in (("working", False), ("blocked", True)):
            self.mark()
            self.agents(t_mgr_s1="working", t_tl_s1="working", t_dev_s1=state)
            self.tick(10)
            self.assertEqual(self.marker.exists(), kept, state)
        self.agents(t_mgr_s1="working", t_tl_s1="working")  # gone
        self.tick(11)
        self.assertFalse(self.marker.exists())
        self.mark()
        (self.home / "roster.md").write_text(self.ROSTER.replace("building", "retired"), encoding="utf-8")
        self.agents(t_mgr_s1="working", t_tl_s1="working", t_dev_s1="idle")
        self.tick(12)
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.unsent(), [])

    def test_ac3_a_missing_spawner_falls_back_to_the_team_lead_then_the_manager(self):  # AC3
        self.mark(spawner="t-gone-s1")
        self.agents(t_mgr_s1="working", t_tl_s1="working", t_dev_s1="idle")
        self.tick(5)
        self.assertEqual([m for m, _t in self.unsent()], ["t-tl-s1"])
        self.sent.clear()
        self.mark(spawner="", at=10)
        self.agents(t_mgr_s1="working", t_dev_s1="idle")  # no Team Lead in herdr
        self.tick(15)
        self.assertEqual([m for m, _t in self.unsent()], ["t-mgr-s1"])
