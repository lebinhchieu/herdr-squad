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

    def test_team_lead_routes_in_m_and_l(self):
        dev, qw, qb = (composed(r, "M") for r in ("dev", "qa-whitebox", "qa-blackbox"))
        self.assertIn("copy the Team Lead", dev)
        self.assertIn("the Team Lead retires you", dev)
        self.assertIn("the Team Lead (plan or order)", dev)
        self.assertIn("copy the Team Lead", qw)
        self.assertIn("copy the Team Lead", qb)
        self.assertIn("tells the Team Lead", composed("ba", "M"))
        tl = composed("tech-lead", "M")
        self.assertIn("Hand the plan and its `## Handover` section to the Team Lead", tl)
        self.assertIn("Help the Team Lead plan", tl)
        self.assertNotIn("In S and M you also own the plan", tl)

    def test_s_paths_stay(self):
        dev, tl = composed("dev", "S"), composed("tech-lead", "S")
        self.assertIn("to the Tech Lead", dev.split("## REV-13a")[1])
        self.assertIn("Tell the Tech Lead and wait; the Manager retires you", dev)
        self.assertIn("tl-review.md", tl)
        self.assertIn("tech-lead", acts("REV-1", "S"))
        self.assertNotIn("the Team Lead retires you", dev)

    def test_qa_blackbox_copies_team_lead_only_and_dev_blocked_route(self):
        qb = composed("qa-blackbox", "M")
        self.assertIn("copy the Team Lead", qb)
        self.assertNotIn("and the BA", qb.split("## REV-12")[1].split("##")[0])
        self.assertIn("`BLOCKED <task>` and `STATUS?` answers go to the Team Lead", composed("dev", "M"))
        self.assertIn("a permission prompt goes nowhere", composed("dev", "M"))


if __name__ == "__main__":
    unittest.main()
