"""Pod routes in M and L go to the Team Lead. The cards hold no routes; the rules do (checked per role and size)."""
import unittest

from rulesview import ROOT, acts, composed

AGENTS = ROOT / "agents"
COMMON = ["started by the squad Manager", "the Manager's briefing", "message from the Manager"]
ALLOW = {  # a card line that says "Manager" must carry one of these
    "team-lead.md": COMMON + ["the Manager hears from you only"], "token-coach.md": COMMON + ["the Manager decides"], "tech-lead.md": COMMON + ["go to the Manager"],
    "manager.md": [""],  # the Manager's own card
}


class PodContactRoutes(unittest.TestCase):
    def test_every_manager_line_of_a_card_is_allowed(self):  # was test_every_manager_line_is_allowed
        for p in sorted(AGENTS.glob("*.md")):
            allowed = ALLOW.get(p.name, COMMON + ["unless the Manager settles a dispute"])
            for n, line in enumerate(p.read_text().splitlines(), 1):
                if "Manager" in line:
                    with self.subTest(file=p.name, line=n):
                        self.assertTrue(any(a in line for a in allowed), f"{p.name}:{n}: {line}")

    def test_team_lead_routes_in_l(self):
        dev, qw, qb = (composed(r, "L") for r in ("dev", "qa-whitebox", "qa-blackbox"))
        self.assertNotIn("copy the Team Lead", dev)  # ledger replaces copies
        self.assertIn("Tell the Team Lead and wait; it retires you", dev)
        self.assertIn("the Team Lead (plan or order)", dev)
        self.assertNotIn("copy the Team Lead", qw)  # ledger replaces copies
        self.assertNotIn("copy the Team Lead", qb)  # ledger replaces copies
        self.assertIn("tells the Team Lead", composed("ba", "L"))
        tl = composed("tech-lead", "L")
        self.assertIn("Hand the plan and its `## Handover` section to the Team Lead", tl)
        self.assertIn("Help the Team Lead plan", tl)
        self.assertNotIn("In S and M you also own the plan", tl)

    def test_s_paths_go_to_the_manager(self):
        dev = composed("dev", "S")
        self.assertIn("to the Manager", dev.split("## REV-13a")[1])
        self.assertIn("Tell the Manager and wait; it retires you", dev)
        self.assertEqual(acts("REV-1", "S"), ("manager",))
        self.assertIn("## REV-22", dev)
        self.assertNotIn("Tech Lead", dev.split("## REV-13a")[1].split("## EVID")[0])
        self.assertNotIn("the Team Lead retires you", dev)

    def test_m_paths_go_to_the_qas_and_done_to_the_manager(self):
        dev = composed("dev", "M")
        self.assertIn("Tell the Manager and wait; it retires you", dev)
        self.assertIn("tell the Manager after both pass it", dev)
        self.assertNotIn("Team Lead", dev.split("## REV-14c")[1].split("##")[0])
        self.assertEqual(acts("REV-14b", "M"), ())

    def test_qa_blackbox_not_copying_team_lead_and_dev_blocked_route(self):
        qb = composed("qa-blackbox", "M")
        self.assertNotIn("copy the Team Lead", qb)  # ledger replaces copies
        self.assertNotIn("and the BA", qb.split("## REV-12")[1].split("##")[0])
        self.assertIn("`BLOCKED <task>` and `STATUS?` answers go to the Manager", composed("dev", "M"))
        

if __name__ == "__main__":
    unittest.main()
