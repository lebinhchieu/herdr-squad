"""squad-watchdog (ticket 03): idle log, nudges at 5 and 15 minutes, sleep only for agents the PO named."""
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
        self.sent, self.retired = [], []
        self.herdr = Path(self.tmp.name) / "herdr.json"

    def tickets(self, **status):
        for n, st in status.items():
            (self.home / "tasks" / f"{n[1:]}.md").write_text(f"# T\n\nStatus: {st}\n", encoding="utf-8")

    def agents(self, **state):
        rows = [{"name": n.replace("_", "-"), "agent_status": s, "pane_id": "p"} for n, s in state.items()]
        self.herdr.write_text(json.dumps({"result": {"agents": rows}}), encoding="utf-8")

    def tick(self, minutes):
        return W.tick(self.home, "t-mgr-s1", now=T0 + minutes * MIN, herdr_json=str(self.herdr),
                      send=lambda m, text: (self.sent.append((m, text)) or (True, "")), retire=lambda a: (self.retired.append(a) or (True, "")))

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
        W.tick(goal, "t-mgr-g1", now=T0, herdr_json=str(self.herdr), send=None, retire=None)
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
    def test_nothing_sleeps_unless_the_po_named_the_agent(self):
        self.tickets(t03="done", t04="done")
        self.agents(t_mgr_s1="idle", t_dev_s1="idle", t_qa_s1="idle")
        for m in (0, 3, 30):
            self.tick(m)
        self.assertEqual(self.retired, [])
        (self.home / "watchdog.sleep").write_text("t-dev-s1\nt-mgr-s1\n", encoding="utf-8")
        self.tick(31)
        self.assertEqual(self.retired, ["t-dev-s1"])  # named and done; the Manager never; t-qa-s1 not named
        self.tick(40)
        self.assertEqual(self.retired, ["t-dev-s1"])  # one try per agent
        self.assertIn("sleep t-dev-s1", self.log())

    def test_a_named_agent_sleeps_only_with_a_done_ticket_and_after_2_idle_minutes(self):
        (self.home / "watchdog.sleep").write_text("t-dev-s1\n", encoding="utf-8")
        self.tickets(t03="building")
        self.agents(t_mgr_s1="working", t_dev_s1="idle")
        self.tick(0)
        self.tick(10)
        self.assertEqual(self.retired, [])  # idle long enough, ticket not done
        self.tickets(t03="done")
        self.agents(t_mgr_s1="working", t_dev_s1="working")
        self.tick(11)
        self.agents(t_mgr_s1="working", t_dev_s1="idle")
        self.tick(12)
        self.tick(13)
        self.assertEqual(self.retired, [])  # done, idle for 1 min only
        self.tick(14)
        self.assertEqual(self.retired, ["t-dev-s1"])

    def test_cli_sleep_turns_an_agent_on_and_off(self):
        r = winlaunch.run_script(str(BIN / "squad-watchdog"), ["sleep", "t-dev-s1", "--home", str(self.home)], clean_env(),
                                 utf8=True, encoding="utf-8", capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(W.sleep_names(self.home), {"t-dev-s1"})
        winlaunch.run_script(str(BIN / "squad-watchdog"), ["sleep", "t-dev-s1", "--off", "--home", str(self.home)], clean_env(),
                             utf8=True, encoding="utf-8", capture_output=True)
        self.assertEqual(W.sleep_names(self.home), set())

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
        calls = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 2, calls)
        self.assertTrue(all(c.startswith("agent prompt t-mgr-s1 WATCHDOG:") for c in calls), calls)
