"""squad-report tasks (ticket 03): hand-computed fixture; see comments for the arithmetic."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import squadreport as sr  # noqa: E402
import squadreport_tasks as st  # noqa: E402

B = 1_700_000_000
CANARY = "CANARYSECRET"


def msg(t, frm, to, text):
    parts = text.split()
    m = sr.Msg(B + t, frm, to, parts[0], parts[1] if len(parts) > 1 else "", text)
    return m


def seg(a, b, bucket, on=None):
    return sr.Seg(B + a, B + b, bucket, "peer" if bucket == "blocking" else None, on)


def turn(t, cost):
    return sr.Turn(B + t, {"input": 10, "cache_read": 0, "cache_write": 0, "output": 5}, cost, "m")


def agent(name, role, segs, turns):
    return sr.AgentTL(name, role, True, False, 1, segs, turns)


def build(tmp, origin=True):
    issues = Path(tmp) / ".scratch" / "feat" / "issues"
    issues.mkdir(parents=True)
    (issues / "07-slug.md").write_text("Status: x\n# 07: Seven thing\n", encoding="utf-8")
    (issues / "08-eight.md").write_text("# 08: Eight\n", encoding="utf-8")
    (issues / "09-nine.md").write_text("# 09: Nine\n", encoding="utf-8")
    home = Path(tmp) / ".claude" / "squads" / "sq" / "scopes" / "sc"
    home.mkdir(parents=True)
    f1 = "FAIL 07:  one   blocking\n finding, tests only"
    f2 = "FAIL 07 " + "x" * 300
    msgs = [
        msg(100, "tl", "dev", "ASSIGN 07-slug (T0) go"),
        msg(1000, "dev", "qa", "HANDIN 07 branch a"),
        msg(1005, "dev", "tl", "HANDIN 07 branch a"),
        msg(1010, "dev", "qa2", "HANDIN 07 branch a"),
        msg(1100, "qa", "dev", "ASK 07 %s" % CANARY),
        msg(1500, "qa", "dev", f1), msg(1502, "qa", "tl", f1), msg(1503, "qa", "qa2", f1),
        msg(2000, "dev", "qa", "HANDIN 07 again"),
        msg(2600, "qa", "dev", f2),
        msg(3000, "dev", "qa", "HANDIN 07 third"),
        msg(3300, "qa", "dev", "PASS 07"),
        msg(3400, "tl", "dev", "STATUS? how is it"),
        msg(4000, "tl", "dev", "ASSIGN 08 next"),
        msg(4100, "dev", "qa", "HANDIN 08 x"),
        msg(4400, "qa", "dev", "PASS 08"),
        msg(4500, "tl", "dev", "ASSIGN T5 stray"),
    ]
    msgs[10].iteration = msgs[13].iteration = 2
    msgs[0].iteration = 1
    agents = {
        "dev": agent("dev", "developer",
                     [seg(0, 3000, "working"), seg(3000, 3300, "blocking", "qa"),
                      seg(3300, 4000, "idle"), seg(4000, 4400, "working")],
                     [turn(50, 1.0), turn(500, 2.0), turn(1700, 0.5), turn(4200, 0.5)]),
        "qa": agent("qa", "qa-whitebox",
                    [seg(0, 1000, "idle"), seg(1000, 1600, "working"), seg(1600, 2000, "idle"),
                     seg(2000, 2700, "working"), seg(2700, 4100, "idle"), seg(4100, 4400, "working")],
                    [turn(1100, 0.25), turn(2650, 0.25), turn(4200, 0.25)]),
        "dev2": agent("dev2", "developer", [seg(500, 800, "working")], [turn(600, 0.125)]),
        "tl": agent("tl", "team-lead", [seg(0, 200, "working")], [turn(20, 0.0625)]),
    }
    esc = [sr.Escalation("E1", "T" * 300, B + 1200, B + 1800), sr.Escalation("E2", "Second", B + 4000, None)]
    roster = [{"Agent": "dev2", "Role": "developer", "Owns": "ticket 09"}]
    c = sr.Collected(home, "sq", "sc", "M", (B, B + 5000), agents, msgs, esc, roster,
                     {"min_segment_s": 30}, {"harness_origin": origin}, [])
    return c


def new_data(c):
    return {"scope": {"partial": False, "partial_reasons": []},
            "totals": {"cost_usd": round(sum(t.cost for a in c.agents.values() for t in a.turns), 4)},
            "agents": []}


class TasksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.c = build(self.tmp.name)
        self.d = new_data(self.c)
        st.fill(self.d, self.c)
        self.t = {x["id"]: x for x in self.d["tasks"]}

    def test_task_rows(self):
        self.assertEqual(sorted(self.t), ["07", "08", "09", "T5"])
        t = self.t["07"]
        self.assertEqual(t["aliases"], ["07-slug", "T0"])
        self.assertEqual(t["title"], "Seven thing")
        self.assertEqual((t["returns"], t["flag"], t["status"]), (2, False, "passed"))
        self.assertEqual((t["rework_s"], t["rework_cost_usd"]), (900, 0.75))
        self.assertEqual(t["cycle_s"], 3200)
        self.assertEqual(t["cost_usd"], 3.0)
        self.assertEqual(t["dev"], "dev")
        self.assertEqual(t["iteration"], 2)
        self.assertEqual([(w["wait_s"], w["verdict"]) for w in t["review_waits"]],
                         [(500, "FAIL"), (600, "FAIL"), (300, "PASS")])
        self.assertEqual([r["reason"] for r in t["returns_list"]],
                         ["one blocking finding, tests only", "x" * 200])
        self.assertEqual([r["handin_at"] is not None for r in t["returns_list"]], [True, True])
        self.assertEqual(self.t["08"]["cycle_s"], 400)
        self.assertEqual(self.t["09"]["buckets_s"]["working"], 300)
        self.assertEqual(self.t["09"]["dev"], "dev2")
        self.assertEqual(self.t["T5"]["status"], "open")

    def test_totals(self):
        tot = self.d["totals"]
        self.assertEqual((tot["returns"], tot["tasks_passed"]), (2, 2))
        self.assertEqual(tot["cost_per_passed_task_usd"], 2.4688)
        a = tot["attributed"]
        self.assertEqual(a["layers"], {"message": 5300, "branch": 300, "overhead": 200})
        self.assertEqual((a["time_pct"], a["cost_pct"]), (96.6, 78.5))
        po = tot["po_wait"]
        self.assertEqual((po["count"], po["total_s"], po["longest_s"], po["pct_of_elapsed"]),
                         (2, 1600, 1000, 32.0))
        self.assertIsNone(po["items"][1]["answered_at"])
        self.assertEqual(len(po["items"][0]["title"]), 120)

    def test_iterations(self):
        its = self.d["iterations"]
        self.assertEqual(self.d["scope"]["iterations"], [1, 2])
        self.assertEqual([(i["n"], i["agent_s"], i["cost_usd"], i["returns"]) for i in its],
                         [(1, 6500, 4.1875, 2), (2, 2800, 0.75, 0)])

    def test_invariants(self):
        total = self.d["totals"]["cost_usd"]
        over = sum(m["cost_usd"] for m in self.d["matrix"] if m["task"] is None)
        self.assertAlmostEqual(sum(t["cost_usd"] for t in self.d["tasks"]) + over, total, places=3)
        self.assertAlmostEqual(sum(m["cost_usd"] for m in self.d["matrix"]), total, places=3)
        agent_s = sum(sg.end - sg.start for a in self.c.agents.values() for sg in a.segs)
        self.assertEqual(sum(m["time_s"] for m in self.d["matrix"]), agent_s)
        self.assertEqual(self.d["totals"]["tasks_passed"], sum(1 for t in self.d["tasks"] if t["status"] == "passed"))
        for t in self.d["tasks"]:
            for r in t["returns_list"]:
                self.assertIn("handin_at", r)
                self.assertTrue(r["fail_at"])
            for w in t["review_waits"]:
                if w["verdict"] != "none":
                    self.assertTrue(w["verdict_at"])
            for k in ("id", "aliases", "title", "dev", "status", "iteration", "window", "cycle_s", "buckets_s",
                      "tokens", "cost_usd", "returns", "flag", "returns_list", "rework_s",
                      "rework_cost_usd", "review_waits"):
                self.assertIn(k, t)
            for r in t["returns_list"]:
                self.assertEqual(sorted(r), ["fail_at", "fail_by", "handin_at", "reason"])

    def test_segments_events(self):
        ag = {a["name"]: a for a in self.d["agents"]}
        self.assertEqual(ag["dev"]["segments"], [
            [0, 100, "w", None, None], [100, 3000, "w", "07", None], [3000, 3300, "b", "07", "qa"],
            [3300, 4000, "i", None, None], [4000, 4400, "w", "08", None]])
        self.assertIn([1500, "FAIL", "07"], ag["qa"]["events"])
        self.assertEqual(sum(1 for e in ag["qa"]["events"] if e[1] == "FAIL"), 2)

    def test_tiny_segment_absorbed(self):
        pcs = [(B, B + 100, "working", None, "07"), (B + 100, B + 110, "working", None, "08"),
               (B + 110, B + 200, "working", None, "07")]
        self.assertEqual(st._segments(pcs, B, 30), [[0, 200, "w", "07", None]])

    def test_blocking_merge_needs_same_on(self):
        pcs = [(B, B + 100, "blocking", "a", "07"), (B + 100, B + 200, "blocking", "b", "07")]
        self.assertEqual(len(st._segments(pcs, B, 30)), 2)

    def test_canary_and_redact(self):
        self.assertNotIn(CANARY, json.dumps(self.d))
        d2 = new_data(self.c)
        st.fill(d2, self.c, redact=True)
        s = json.dumps(d2)
        for bad in ("Seven thing", "Eight", "one blocking", "x" * 20, "TTTT", "Second"):
            self.assertNotIn(bad, s)
        t = {x["id"]: x for x in d2["tasks"]}["07"]
        self.assertEqual((t["returns"], t["rework_s"], t["cycle_s"]), (2, 900, 3200))
        self.assertEqual(d2["totals"]["po_wait"]["total_s"], 1600)

    def test_legacy_no_origin(self):
        c = build(tempfile.mkdtemp(dir=self.tmp.name), origin=False)
        d = new_data(c)
        st.fill(d, c)
        self.assertIn("no_origin", d["scope"]["partial_reasons"])
        self.assertTrue(d["tasks"])

    def test_no_ticket_dir(self):
        with tempfile.TemporaryDirectory() as t2:
            c = build(tempfile.mkdtemp(dir=self.tmp.name))
            c.scope_home = Path(t2) / "x"
            c.scope_home.mkdir()
            d = new_data(c)
            st.fill(d, c)
            ids = {x["id"] for x in d["tasks"]}
            self.assertIn("07-slug", ids)  # alias merge only; no ticket dir
            self.assertIsNone({x["id"]: x for x in d["tasks"]}["07-slug"]["title"])


if __name__ == "__main__":
    unittest.main()


class CollectedScopeTest(unittest.TestCase):
    def test_fill_on_fixture_scope(self):
        import report_fixtures as rf
        from unittest import mock
        fx = rf.Fixture()
        self.addCleanup(fx.close)
        rf.tasks_scope(fx)
        with mock.patch.dict(os.environ, fx.env()):
            c = sr.collect(fx.home, fx.squad, rf.PLUGIN_ROOT, final=True)
        d = sr.base_data(c)
        st.fill(d, c)
        t = {x["id"]: x for x in d["tasks"]}["07"]
        self.assertEqual((t["returns"], t["rework_s"], t["cycle_s"], t["status"]), (1, 300, 1950, "passed"))
        self.assertEqual(d["totals"]["po_wait"]["count"], 2)
        self.assertEqual(d["totals"]["po_wait"]["items"][1]["answered_at"], None)
        self.assertAlmostEqual(sum(m["cost_usd"] for m in d["matrix"]), d["totals"]["cost_usd"], places=3)
        self.assertEqual(sum(m["time_s"] for m in d["matrix"]), d["totals"]["agent_s"])
        json.dumps(d, sort_keys=True)
