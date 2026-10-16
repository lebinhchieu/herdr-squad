"""Role files name the Team Lead for routine pod matters in M and L.

Every line that says "Manager" must carry an allowed phrase (a legitimate
path: PO item, size change, dispute, briefing, empty-env fallback, spawn
frontmatter, S-only). A new Manager route fails here.
"""
import re
import unittest
from pathlib import Path

AGENTS = Path(__file__).resolve().parent.parent / "agents"

COMMON = ["started by the squad Manager", "the Manager's briefing", "message from the Manager"]
ALLOW = {
    "dev.md": COMMON + ["fallback: ask the Manager", "the Manager retires you"],
    "qa-whitebox.md": COMMON,
    "qa-blackbox.md": COMMON,
    "designer.md": COMMON,
    "ba.md": COMMON + ["unless the Manager settles a dispute", "escalate via the Manager:** goal change, scope cut"],
    "tech-lead.md": COMMON + [
        "tell the Manager: the scope moves up to M",
        "Escalate via the Manager:** irreversible choices",
    ],
}


class PodContactRoutes(unittest.TestCase):
    def test_every_manager_line_is_allowed(self):
        for name, allowed in ALLOW.items():
            for n, line in enumerate((AGENTS / name).read_text().splitlines(), 1):
                if "Manager" in line:
                    with self.subTest(file=name, line=n):
                        self.assertTrue(any(a in line for a in allowed), f"{name}:{n}: {line}")

    def test_team_lead_routes_in_m_and_l(self):
        read = lambda n: (AGENTS / n).read_text()
        dev = read("dev.md")
        self.assertIn("copy the Team Lead (M, L)", dev)
        self.assertIn("the Team Lead retires you", dev)
        self.assertIn("Plan or order → the Team Lead", dev)
        self.assertIn("copy the Team Lead (M, L)", read("qa-whitebox.md"))
        self.assertIn("copy the Team Lead (M, L).", read("qa-blackbox.md"))
        self.assertIn("tell the Team Lead", read("ba.md"))
        tl = read("tech-lead.md")
        self.assertIn("**In S you also own the plan**", tl)
        self.assertNotIn("In S and M you also own the plan", tl)
        self.assertIn("hand the plan and its `## Handover` section to the Team Lead", tl)
        self.assertIn("Help the Team Lead plan** (M, L)", tl)

    def test_s_paths_stay(self):
        dev = (AGENTS / "dev.md").read_text()
        tl = (AGENTS / "tech-lead.md").read_text()
        self.assertIn("hand in to the **Tech Lead** instead of the QAs", dev)
        self.assertIn("S: tell the Tech Lead; the Manager retires you", dev)
        self.assertIn("In S you are also the checker", tl)
        self.assertIn("tl-review.md", tl)
        self.assertIn("the scope moves up to M", tl)

    def test_qa_blackbox_copies_team_lead_only_and_dev_blocked_route(self):
        qb = (AGENTS / "qa-blackbox.md").read_text()
        qw = (AGENTS / "qa-whitebox.md").read_text()
        self.assertIn("copy the Team Lead (M, L).", qb)
        self.assertNotIn("and the BA", qb)
        self.assertIn("copy the Team Lead (M, L).", qw)
        dev = (AGENTS / "dev.md").read_text()
        self.assertIn("`BLOCKED <task>` and answers to `STATUS?` go to the Team Lead (S: the Tech Lead); a permission prompt is not sent anywhere", dev)


if __name__ == "__main__":
    unittest.main()
