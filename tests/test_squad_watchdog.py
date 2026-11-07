"""squad-watchdog (ticket 03): idle log, nudges at 5 and 15 minutes, PC sleep only when the PO switched it on."""
import json
import os
import tempfile
import unittest
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

    def test_the_pc_sleeps_once_after_5_quiet_minutes_when_every_ticket_is_done(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="done", t04="building")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle")
        self.tick(0)
        self.tick(10)
        self.assertEqual(self.suspended, [])  # a ticket is still open
        self.tickets(t04="done")
        self.tick(11)
        self.tick(15)
        self.assertEqual(self.suspended, [])  # quiet for 4 min only
        self.tick(16)
        self.assertEqual(self.suspended, [1])
        log = self.log().splitlines()
        self.assertRegex(log[-1], r"^2027-01-15T08:16:00Z sleep pc: every ticket is done and nobody on this machine has worked for 5 min")
        self.assertFalse(W.sleep_on(self.home))  # one shot
        self.tick(40)
        self.assertEqual(self.suspended, [1])  # a wake-up does not sleep again

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

    def test_a_goal_sleeps_only_when_the_tickets_of_all_its_scopes_are_done(self):
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
        self.assertEqual(self.suspended, [])
        (squad / "scopes" / "s2" / "tasks" / "01.md").write_text("# T\n\nStatus: done\n", encoding="utf-8")
        for m in (11, 16):
            W.tick(goal, "t-mgr-g1", now=T0 + m * MIN, herdr_json=str(self.herdr), send=lambda *a: (True, ""),
                   suspend_fn=lambda: (self.suspended.append(1) or (True, "")))
        self.assertEqual(self.suspended, [1])

    def test_herdr_not_answering_is_no_decision_for_the_sleep(self):
        W.set_sleep(self.home, True)
        self.tickets(t03="done")
        self.agents(t_mgr_s1="idle")
        self.tick(0)
        self.herdr.write_text("not json", encoding="utf-8")
        self.tick(30)
        self.assertEqual(self.suspended, [])

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
        self.assertIn("sleep-when-done: off", r.stdout)
        r = run("sleep", "on")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("sleep-when-done: ON", r.stdout)
        self.assertTrue(W.sleep_on(self.home))
        self.assertIn("sleep-when-done: ON", run("status").stdout)
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
            self.assertEqual(W.suspend_cmd()[0][0], want)

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
