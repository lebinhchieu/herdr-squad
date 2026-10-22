"""The roles that consume a UI design know where it is (now: through rules targeting, not card text)."""
import unittest

from rulesview import ROOT, acts, composed


class DesignerHandoffTest(unittest.TestCase):
    def test_consuming_roles_mention_the_design_folder(self):
        for role in ("dev", "qa-blackbox", "tech-lead"):
            self.assertIn("ui-design/", composed(role, "M", design="yes"), role)

    def test_tech_lead_keys_on_design_yes(self):
        self.assertIn("tech-lead", acts("LC-11", "L"))
        self.assertIn("## LC-11 Design with a UI", composed("tech-lead", "L", design="yes"))
        self.assertNotIn("## LC-11 ", composed("tech-lead", "L", design="no"))
        self.assertIn("manager", acts("LC-11b", "M"))

    def test_readme_counts_nine_roles_and_names_the_designer(self):
        text = (ROOT / "README.md").read_text()
        self.assertIn("9 role definitions", text)
        self.assertIn("Designer", text)


if __name__ == "__main__":
    unittest.main()
