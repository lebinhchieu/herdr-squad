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


class WakeTest(WatchdogTest):
    """Ticket 08: one message to the Manager per event (passed, 3rd return, pane blocked 10 min); never repeated."""

    def msgs(self, *rows):
        with open(self.home / "messages.jsonl", "a", encoding="utf-8") as fh:
            for typ, frm, text in rows:
                fh.write(json.dumps({"ts": "2026-11-10T10:00:00.000Z", "from": frm, "to": "x", "type": typ, "task": "03",
                                     "text": text}) + "\n")

    def wakes(self):
        return [t for _m, t in self.sent if t.startswith("WAKE")]

    def work(self, **kw):
        self.agents(**dict(dict(t_mgr_s1="working", t_dev_s1="idle", t_qa_s1="working"), **kw))

    def test_passed_once_and_baseline_is_silent(self):
        self.work()
        self.msgs(("HANDIN", "t-dev-s1", "HANDIN 03: commit abc1234 ok"))
        self.tickets(t03="passed", t04="checking")
        self.tick(0)  # first pass: baseline, nothing for the ticket that is already passed
        self.assertEqual(self.wakes(), [])
        self.tickets(t03="passed", t04="passed")
        self.tick(1)
        self.tick(2)  # same state again: no repeat
        self.assertEqual(len(self.wakes()), 1, self.wakes())
        self.assertIn("WAKE passed 04", self.wakes()[0])
        self.tick(3)
        self.assertEqual(len(self.wakes()), 1)
        self.assertTrue(all(m == "t-mgr-s1" for m, _ in self.sent))

    def test_passed_from_pass_messages_when_the_label_is_empty(self):
        """QA whitebox FAIL at 3675aa1: a pass is never written to the ticket label, only PASS messages."""
        with open(self.home / "roster.md", "a", encoding="utf-8") as fh:
            fh.write("| t-qb-s1 | qa-blackbox | s1 | ticket 03 | live | d |\n")
        self.work()
        self.tickets(t03="")
        self.msgs(("HANDIN", "t-dev-s1", "HANDIN 03: commit abc1234 ok"), ("PASS", "t-qa-s1", "PASS 03: abc1234"))
        self.tick(0)  # baseline: one of two checkers passed
        self.tick(1)
        self.assertEqual(self.wakes(), [])
        self.msgs(("PASS", "t-qb-s1", "PASS 03: abc1234"))
        self.tick(2)
        self.tick(3)
        self.assertEqual(len(self.wakes()), 1, self.wakes())
        self.assertIn("WAKE passed 03", self.wakes()[0])
        self.assertIn("abc1234", self.wakes()[0])

    def test_third_return_counts_like_the_ledger_and_sends_once(self):
        import squadledger
        self.work()
        self.tickets(t03="building")
        self.tick(0)
        for n in (1, 2):  # two checkers fail each sha: still one return per sha
            self.msgs(("HANDIN", "t-dev-s1", f"HANDIN 03: commit aaa{n}111"), ("FAIL", "t-qa-s1", f"FAIL 03: aaa{n}111 x"),
                      ("FAIL", "t-qb-s1", f"FAIL 03: aaa{n}111 y"))
        self.tick(1)
        self.assertEqual(self.wakes(), [])
        self.msgs(("HANDIN", "t-dev-s1", "HANDIN 03: commit aaa3111"), ("FAIL", "t-qa-s1", "FAIL 03: aaa3111 z"))
        rows = squadledger.build(squadledger.read_records(self.home / "messages.jsonl"))
        self.assertEqual(rows[0]["returns"], 3)
        self.tick(2)
        self.tick(3)
        self.msgs(("HANDIN", "t-dev-s1", "HANDIN 03: commit aaa4111"), ("FAIL", "t-qa-s1", "FAIL 03: aaa4111 w"))
        self.tick(4)  # a 4th return sends nothing more
        self.assertEqual(len(self.wakes()), 1, self.wakes())
        self.assertIn("returns3 03", self.wakes()[0])
        self.assertIn("aaa3111", self.wakes()[0])

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
        self.work()
        self.tickets(t03="building")
        self.tick(0)
        self.tickets(t03="passed")
        self.work(t_mgr_s1="blocked")
        self.tick(1)
        self.assertEqual(self.wakes(), [])  # a prompt may be open: nothing sent, key not stored
        self.work()
        fails = []
        W.tick(self.home, "t-mgr-s1", now=T0 + 2 * MIN, herdr_json=str(self.herdr), send=lambda m, t: (fails.append(t) or (False, "no")))
        self.tick(3)  # retried and sent
        self.tick(4)
        self.assertEqual((len(fails), len(self.wakes())), (1, 1))

    def test_switch_off_and_old_state_file(self):
        self.work()
        self.tickets(t03="passed")
        self.msgs(*[x for n in (1, 2, 3) for x in (("HANDIN", "t-dev-s1", f"HANDIN 03: commit bbb{n}111"), ("FAIL", "t-qa-s1", f"FAIL 03: bbb{n}111 x"))])
        (self.home / "watchdog.state.json").write_text(json.dumps({"beat": 1, "idle_since": None}), encoding="utf-8")  # before this feature
        self.tick(0)
        self.assertEqual(self.wakes(), [])  # baseline: no flood after a restart, the 3 returns are already known
        W.set_wake(self.home, False)
        self.assertFalse(W.wake_on(self.home))
        self.tickets(t03="building")
        self.tick(1)
        self.tickets(t03="passed")
        self.tick(2)
        self.assertEqual(self.wakes(), [])
        W.set_wake(self.home, True)
        self.tickets(t03="building")
        self.tick(3)
        self.tickets(t03="passed")
        self.tick(4)
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

    def test_cli_wake_switch_and_status(self):
        env = clean_env(PYTHONDONTWRITEBYTECODE="1")
        def run(*a):
            return winlaunch.run_script(str(BIN / "squad-watchdog"), list(a) + ["--home", str(self.home)], env, utf8=True,
                                        encoding="utf-8", capture_output=True)
        self.assertEqual(run("wake", "off").returncode, 0)
        self.assertIn("wake-ups: off", run("status").stdout)
        run("wake", "on")
        self.assertIn("wake-ups: on", run("status").stdout)
