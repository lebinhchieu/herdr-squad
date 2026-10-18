"""squad-report digest (ticket 04): hand-computed ranking, cap of 8, thresholds, process drift, field shape."""
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import squadreport_digest as dg  # noqa: E402

ITEM_KEYS = {"id", "kind", "weight", "text", "value", "unit", "target"}


def task(i, cost, returns=0, rework=0.0, waits=()):
    return {"id": i, "cost_usd": cost, "returns": returns, "rework_cost_usd": rework,
            "review_waits": [{"wait_s": w} for w in waits]}


def role(name, r, cost, exp=0.0, n=0):
    return {"name": name, "role": r, "cost_usd": cost, "expiry_cost_usd": exp, "cache_expiries": n, "transcript_found": True}


def data(**kw):
    d = {"totals": {"cost_usd": 10.0, "agent_s": 1000, "wall_s": 500, "parallelism": 2.0,
                    "buckets_s": {"idle": 100}, "po_wait": {"total_s": 0, "count": 0, "pct_of_elapsed": 0},
                    "attributed": {"time_pct": 90.0, "layers": {"message": 9, "branch": 0, "overhead": 1}}},
         "tasks": [], "roles": [], "matrix": [], "agents": []}
    d.update(kw)
    return d


class Digest(unittest.TestCase):
    def test_hand_computed_ranking(self):
        d = data(tasks=[task("07", 6.0, returns=3, rework=1.0, waits=(50, 100, 150)), task("08", 2.0, returns=1)],
                 roles=[role("dev", "developer", 7.0, exp=0.5, n=2), role("qa", "qa", 1.0)],
                 matrix=[{"task": None, "agent": "dev", "cost_usd": 2.0}],
                 agents=[{"name": "dev", "segments": [[0, 100, "b", None, "qa"], [100, 150, "b", None, "tl"]]}])
        d["totals"]["po_wait"] = {"total_s": 100, "count": 1, "pct_of_elapsed": 20.0}
        got = [(i["kind"], i["weight"]) for i in dg.digest(d)]
        # weights: top_cost_task .6, top_cost_role .7, overhead .2, idle .1, longest_block 100/1000=.1,
        # po_wait .2, review_wait 100/500=.2, most_returns 3/4=.75, rework .1, respawns .05, parallelism 2/1=1 -> clipped
        self.assertEqual(got, [("parallelism", 1.0), ("most_returns", 0.75), ("top_cost_role", 0.7), ("top_cost_task", 0.6),
                               ("scope_overhead", 0.2), ("po_wait", 0.2), ("review_wait", 0.2), ("idle_share", 0.1)])
        self.assertEqual(dg.digest(d), dg.digest(d))

    def test_texts_and_fields(self):
        d = data(tasks=[task("07", 6.0)], roles=[role("dev", "developer", 6.0)],
                 agents=[{"name": "dev", "segments": [[0, 120, "b", None, "qa"]]}])
        by = {i["kind"]: i for i in dg.digest(d)}
        self.assertEqual(by["top_cost_task"]["text"], "Task 07 took 60.0% of cost ($6.00)")
        self.assertEqual(by["longest_block"]["text"], "dev waited 2m00s on qa (12.0% of agent-time)")
        for i in by.values():
            self.assertEqual(set(i), ITEM_KEYS)
            self.assertEqual(set(i["target"]), {"view", "id"})

    def test_most_returns_quotes_each_reason(self):
        t = task("07", 6.0, returns=3)
        t["returns_list"] = [{"reason": "one blocking finding"}, {"reason": "tests missing"}, {"reason": None}]
        by = {i["kind"]: i for i in dg.digest(data(tasks=[t]))}
        self.assertEqual(by["most_returns"]["text"], 'Task 07 came back 3 times (3 returns in all): '
                         '"one blocking finding" / "tests missing" / "not shared"')
        self.assertEqual(set(by["most_returns"]), ITEM_KEYS)

    def test_attribution_low_only_below_60(self):
        d = data()
        self.assertNotIn("attribution_low", [i["kind"] for i in dg.digest(d)])
        d["totals"]["attributed"]["time_pct"] = 59.9
        top = dg.digest(d)[0]
        self.assertEqual((top["kind"], top["weight"]), ("attribution_low", 1.0))

    def test_most_returns_needs_three(self):
        d = data(tasks=[task("07", 1.0, returns=2)])
        self.assertNotIn("most_returns", [i["kind"] for i in dg.digest(d)])

    def test_capped_at_eight_and_empty_scope(self):
        d = data(tasks=[task("07", 6.0, returns=3, rework=1.0, waits=(10,))], roles=[role("dev", "developer", 6.0, 1.0, 1)],
                 matrix=[{"task": None, "agent": "dev", "cost_usd": 1.0}],
                 agents=[{"name": "dev", "segments": [[0, 100, "b", None, "qa"]]}])
        d["totals"]["po_wait"] = {"total_s": 100, "count": 1, "pct_of_elapsed": 20.0}
        d["totals"]["attributed"]["time_pct"] = 10.0
        self.assertEqual(len(dg.digest(d)), 8)
        self.assertEqual(dg.digest({"totals": {}}), [])

    def test_message_types_match_squad_log_message(self):
        src = (HERE.parent / "bin" / "squad-log-message").read_text(encoding="utf-8")
        m = re.search(r'capture\("\^\(\?<t>([A-Z|]+)\)', src)
        self.assertIsNotNone(m)
        self.assertEqual(set(m.group(1).split("|")), set(dg.MESSAGE_TYPES))


if __name__ == "__main__":
    unittest.main()
