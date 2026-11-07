"""squadtask: the one writer of ticket state events (store, fold, checkers, warnings W1-W8, hook entry, CLI)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from squadtest import BIN

sys.path.insert(0, str(BIN))
sys.dont_write_bytecode = True
import squadledger  # noqa: E402
import squadtask  # noqa: E402

CLI = BIN / "squad-task"
# Real messages from the repo's own scopes (REV-4): HANDIN `..sha`, HANDIN `commit sha`, PASS naming a sha, FAIL naming a sha.
H_RANGE = {"from": "plugin-dev-watchdog-2", "to": "plugin-qab-watchdog", "type": "HANDIN", "task": "03",
           "text": "HANDIN 03: diff check 90dbd7c..148a5f9. One line in bin/squad-watchdog (read of /proc/version gets encoding)."}
H_COMMIT = {"from": "plugin-dev-watchdog-2", "to": "plugin-qaw-watchdog", "type": "HANDIN", "task": "03",
            "text": "HANDIN 03: branch squad/plugin/watchdog/plugin-dev-watchdog-2, commit 148a5f9. Fix for your FAIL."}
P_SHA = {"from": "plugin-qab-cleanup", "to": "plugin-dev-cleanup-2", "type": "PASS", "task": "03",
         "text": "PASS 03: sha 09ab86f, no observable CLI change vs main."}
F_SHA = {"from": "plugin-mgr-process-audit", "to": "plugin-dev-process-audit-6", "type": "FAIL", "task": "06",
         "text": "FAIL 06: one finding, AC4 evidence. The screenshots were made at 1b59666; 210876f changed palette."}
P_IDLE = {"from": "qab", "to": "dev", "type": "PASS", "task": "03", "text": "PASS 03"}  # idle case: no sha at all
ROSTER = """| Agent | Role | Scope | Owns | Status | Session |
| --- | --- | --- | --- | --- | --- |
| mgr | manager | s1 |  | live | a |
| tl | team-lead | s1 | plan | live | b |
| qaw | qa-whitebox | s1 | x | live | c |
| qab | qa-blackbox | s1 | x | live | d |
| qaold | qa-blackbox | s1 | x | retired | e |
| dev | dev | s1 |  | live | f |
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sd = Path(self.tmp.name)
        self.home = self.sd / "scopes" / "s1"
        (self.home / "tasks").mkdir(parents=True)
        (self.home / "scope.md").write_text("team: ba, team-lead, qa-white, qa-black\n", encoding="utf-8")
        (self.home / "roster.md").write_text(ROSTER, encoding="utf-8")
        self.ticket(1, "Blocked by: none")
        self.ticket(2, "Blocked by: 01")

    def tearDown(self):
        self.tmp.cleanup()

    def ticket(self, n, line, status="Status: ready-for-agent"):
        (self.home / "tasks" / ("ticket-%02d-x.md" % n)).write_text("# %02d x\n\n%s\n%s\n" % (n, status, line), encoding="utf-8")

    def rec(self, nn, ev, **kw):
        return squadtask.record(self.home, nn, ev, **kw)

    def events(self):
        return squadtask.read_events(self.sd, "s1")

    def state(self, nn="01"):
        return squadtask.fold(self.events()).get(squadledger.key(nn))

    def passes(self, nn="01", sha="aaaaaaa"):
        self.rec(nn, "handin", by="dev", sha=sha)
        for slot in ("qaw", "qab", "confirmer"):
            self.rec(nn, "pass", by=slot, slot=slot)


class CheckersAndWords(Base):
    def test_checkers_m_never_zero_and_confirmer(self):  # T8, AC "M never 0"
        c = squadtask.checkers(self.home)
        self.assertEqual(c, {"qa": ["qaw", "qab"], "confirmer": "Team Lead"})  # retired QA left out
        (self.home / "roster.md").write_text("| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n", encoding="utf-8")
        (self.home / "scope.md").write_text("team: ba\n", encoding="utf-8")
        c = squadtask.checkers(self.home)
        self.assertEqual(c, {"qa": [], "confirmer": "Manager"})
        self.assertEqual(squadtask.slots(c), ["confirmer"])

    def test_words_and_label_table(self):  # states.md s2 precedence, s5 label table
        c = squadtask.checkers(self.home)
        self.assertEqual({k: squadtask.word(None, c, (), k) for k in squadtask.LABELS},
                         {"needs-triage": "todo", "needs-info": "todo", "ready-for-agent": "todo", "ready-for-human": "todo",
                          "claimed": "in progress", "done": "passed", "wontfix": "wontfix"})
        self.assertEqual(squadtask.word(None, c, ["01"], "ready-for-agent"), "blocked")
        self.rec("01", "claim", by="dev")
        self.assertEqual(squadtask.word(self.state(), c), "in progress")
        self.rec("01", "handin", by="dev", sha="aaaaaaa")
        self.assertEqual(squadtask.word(self.state(), c), "checking, 0 of 3 PASS")
        self.rec("01", "fail", by="qaw", slot="qaw")
        self.assertEqual(squadtask.word(self.state(), c), "returned")
        self.rec("01", "blocked", by="dev", why="stuck")
        self.assertEqual(squadtask.word(self.state(), c), "blocked")  # a BLOCKED message beats returned
        self.rec("01", "decision", by="tl")
        self.rec("01", "handin", by="dev", sha="bbbbbbb")
        for s in ("qaw", "qab", "confirmer"):
            self.rec("01", "pass", by=s, slot=s)
        self.assertEqual(squadtask.word(self.state(), c), "passed")
        self.rec("01", "merged", by="mgr", sha="cccccc1")
        self.assertEqual(squadtask.word(self.state(), c), "merged")


class Warnings(Base):
    def test_w1_to_w8_each_returns_text_and_still_writes(self):  # T6; AC8 is the W1 row
        def last(ev):
            return self.events()[-1]["ev"] == ev
        _, w = self.rec("02", "claim", by="dev-a")  # 02 is blocked by 01, not passed
        self.assertEqual(w, ["W1 started while ticket 01 is not yet passed"])
        self.assertTrue(last("claim"))
        self.assertEqual(self.state("02")["owner"], "dev-a")
        self.assertEqual(self.events()[-1]["warn"], w)  # saved in the event (D4)
        _, w = self.rec("02", "claim", by="dev-b")
        self.assertEqual(w[-1], "W2 already owned by dev-a")
        self.assertTrue(last("claim"))
        _, w = self.rec("03", "handin", by="dev-c", sha="aaaaaaa")
        self.assertEqual(w, ["W3 handed in without a claim; owner taken from sender"])
        self.assertEqual(self.state("03")["owner"], "dev-c")
        w = squadtask.from_message(self.home, {"from": "qaw", "type": "PASS", "task": "03", "text": "PASS 03: sha 1234567 ok"},
                                   role="qa-whitebox")  # W5 through the hook path: a sha never handed in
        self.assertEqual(w, ["W5 PASS on a sha that is not the current hand-in"])
        n = len(self.events())
        _, w = self.rec("03", "pass", by="mgr", role="dev", slot=None)  # W4: other role, nothing written
        self.assertEqual(w, ["W4 not a checker; not counted"])
        self.assertEqual(len(self.events()), n)
        _, w = self.rec("04", "pass", by="qaw", slot="qaw")  # W5: no hand-in yet
        self.assertEqual(w, ["W5 PASS on a sha that is not the current hand-in"])
        _, w = self.rec("03", "pass", by="qaw", slot="qaw", sha="zzzzzzz")
        self.assertEqual(w, ["W5 PASS on a sha that is not the current hand-in"])
        _, w = self.rec("03", "pass", by="mgr", slot="confirmer")  # W6: QAs missing
        self.assertEqual(w, ["W6 confirmed early; 1 of 2 checkers PASS"])
        _, w = self.rec("03", "merged", by="mgr", sha="cccccc1")  # W7
        self.assertEqual(w, ["W7 merged without every checker PASS"])
        self.assertTrue(last("merged"))
        self.ticket(5, "Blocked by: none", status="Status: wontfix")
        _, w = self.rec("05", "claim", by="dev")
        self.assertEqual(w, ["W8 ticket is wontfix"])
        self.assertTrue(last("claim"))

    def test_blocker_passed_or_merged_is_not_open(self):
        self.passes("01")
        self.assertEqual(self.rec("02", "claim", by="dev")[1], [])
        self.ticket(3, "Blocked by: 04")
        self.rec("04", "claim", by="dev")
        self.rec("04", "merged", by="mgr", sha="cccccc1")
        self.assertEqual(self.rec("03", "claim", by="dev2")[1], [])  # merged, so not open (W7 is for 04 only)


class StoreAndHook(Base):
    def test_event_shape_and_fold_parity_with_ledger(self):  # T3, T4, T5 on the real samples
        order = [H_COMMIT, P_IDLE, H_RANGE, dict(P_SHA, **{"from": "qaw"}), dict(F_SHA, task="03", **{"from": "qab"}),
                 dict(H_RANGE, text="HANDIN 03: evidence sha 148a5f9 for the Tech Lead"),
                 {"from": "dev", "to": "tl", "type": "ASK", "task": "03", "text": "ASK 03: q"},
                 {"from": "dev", "to": "tl", "type": "BLOCKED", "task": "03", "text": "BLOCKED 03: waits"}]
        roles = {"qaw": "qa-whitebox", "qab": "qa-blackbox", "plugin-qab-cleanup": "qa-blackbox"}
        for r in order:
            squadtask.from_message(self.home, dict(r, ts="2026-11-07T00:00:00.000Z"), role=roles.get(r["from"], "dev"))
        evs = self.events()
        for e in evs:  # T4
            self.assertTrue({"v", "ts", "task", "ev", "by", "scope"} <= set(e))
            self.assertTrue(e["ev"] != "handin" or e["sha"])
        self.assertEqual([e["ev"] for e in evs], ["handin", "pass", "handin", "pass", "fail", "blocked"])  # ASK, evidence: none
        self.assertEqual(evs[0]["warn"], ["W3 handed in without a claim; owner taken from sender"])
        self.assertEqual(evs[0]["branch"], "squad/plugin/watchdog/plugin-dev-watchdog-2")
        st = self.state("03")
        led = squadledger.build(order)[0]
        self.assertEqual(st["verdicts"], led["verdicts"] or {})
        self.assertEqual(st["returns"], led["returns"])
        self.assertEqual(st["blocked_open"], led["blocked"] or [])
        self.assertEqual(st["sha"], led["sha"])

    def test_hook_entry_warns_and_never_fails(self):  # T1
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env["SQUAD_ROLE"] = "dev"  # a Developer sending PASS: W4
        p = subprocess.run([sys.executable, str(CLI), "from-message", "--scope-home", str(self.home)],
                           input=json.dumps(P_IDLE), text=True, capture_output=True, env=env, timeout=20)
        self.assertEqual(p.returncode, 0)
        self.assertIn("W4 not a checker", json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"])
        p = subprocess.run([sys.executable, str(CLI), "from-message", "--scope-home", str(self.home)],
                           input="not json", text=True, capture_output=True, env=env, timeout=20)
        self.assertEqual((p.returncode, p.stdout), (0, ""))
        shutil.rmtree(self.sd / "task-events", ignore_errors=True)
        (self.sd / "task-events").write_text("a file, not a folder", encoding="utf-8")  # the store cannot be written
        self.assertEqual(self.rec("01", "claim", by="dev"), (None, []))  # logged, never raised

    def test_cli_claim_exit_codes(self):  # T1: warning exits 0, usage error 2
        def run(*a):
            return subprocess.run([sys.executable, str(CLI), *a, "--scope-home", str(self.home)], text=True,
                                  capture_output=True, timeout=20)
        p = run("claim", "02", "--owner", "dev")
        self.assertEqual(p.returncode, 0)
        self.assertIn("warning: W1", p.stdout)
        self.assertEqual(run("claim", "02").returncode, 2)
        self.assertEqual(run("merged", "09").returncode, 2)
        self.assertEqual(run("show", "02", "--json").returncode, 0)

    def test_concurrent_writers_and_mkdir_lock(self):  # T2
        code = ("import sys; sys.path.insert(0, %r); import squadtask\n"
                "for i in range(25): squadtask.record(%r, '01', 'blocked', by='w'+sys.argv[1], why='x'*5000)\n"
                % (str(BIN), str(self.home)))
        ps = [subprocess.Popen([sys.executable, "-c", code, str(i)]) for i in range(2)]
        for p in ps:
            self.assertEqual(p.wait(timeout=60), 0)
        self.assertEqual(len(self.events()), 50)  # every line intact (readers skip bad lines)
        raw = squadtask.store_path(self.sd, "s1").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(raw), 50)
        saved, squadtask.fcntl = squadtask.fcntl, None
        try:
            self.rec("01", "claim", by="dev")
        finally:
            squadtask.fcntl = saved
        self.assertEqual(self.events()[-1]["ev"], "claim")
        self.assertFalse(os.path.exists(str(squadtask.store_path(self.sd, "s1")) + ".lock.d"))


if __name__ == "__main__":
    unittest.main()
