"""Pod routes in M and L go to the Team Lead. The cards hold no routes; the rules do (checked per role and size)."""
import unittest

from rulesview import ROOT, composed

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


        

    def test_routes_follow_the_plan_owner_of_the_team(self):  # team language: plan-owner, doubt-owner, design-notes
        def ids(text):
            return text.split(" rules: ", 1)[1].split(" ## ", 1)[0].split()
        tl, mg = "team-lead, qa-white", "qa-white"
        self.assertIn("MSG-11b", ids(composed("dev", team=tl)))
        self.assertNotIn("MSG-11a", ids(composed("dev", team=tl)))
        self.assertIn("MSG-11a", ids(composed("dev", team=mg)))
        self.assertNotIn("MSG-11b", ids(composed("dev", team=mg)))
        self.assertIn("go to the Team Lead", composed("dev", team=tl))
        self.assertIn("go to the Manager", composed("dev", team=mg))
        self.assertIn("MSG-5", ids(composed("team-lead", team=tl)))
        self.assertIn("MSG-6", ids(composed("team-lead", team=tl)))
        self.assertIn("MSG-14", ids(composed("tech-lead", team="tech-lead")))  # the Tech Lead answers gaps whoever plans
        self.assertIn("MSG-15", ids(composed("tech-lead", team="tech-lead, ba")))
        self.assertNotIn("MSG-15", ids(composed("tech-lead", team="tech-lead")))  # no BA to raise to
        self.assertIn("MSG-12", ids(composed("ba", team="ba")))

    def test_doubts_go_to_the_doubt_owner(self):
        def ids(text):
            return text.split(" rules: ", 1)[1].split(" ## ", 1)[0].split()
        self.assertIn("MSG-16b", ids(composed("designer", team="ba, designer")))
        self.assertNotIn("MSG-16a", ids(composed("designer", team="ba, designer")))
        self.assertIn("MSG-16a", ids(composed("designer", team="designer")))
        self.assertIn("MSG-20b", ids(composed("architect", team="ba, architect")))
        self.assertIn("MSG-20a", ids(composed("architect", team="architect")))
        self.assertIn("MSG-17", ids(composed("designer", team="tech-lead, designer")))  # design-notes = tech-lead
        self.assertIn("MSG-17b", ids(composed("designer", team="designer")))  # design-notes = dev
        a = composed("architect", team="architect")
        self.assertNotIn("moves the scope", a)
        self.assertNotIn("the BA", a.split("## MSG-20a")[1].split("##")[0])


if __name__ == "__main__":
    unittest.main()
