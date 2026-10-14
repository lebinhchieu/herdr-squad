"""The roles that consume a UI design know where it is."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel):
    return (ROOT / rel).read_text()


class DesignerHandoffTest(unittest.TestCase):
    def test_consuming_roles_mention_the_design_folder(self):
        for rel in ("agents/dev.md", "agents/qa-blackbox.md", "agents/tech-lead.md"):
            self.assertIn("ui-design/", read(rel), rel)

    def test_tech_lead_keys_on_design_yes(self):
        self.assertIn("design: yes", read("agents/tech-lead.md"))

    def test_readme_counts_nine_roles_and_names_the_designer(self):
        text = read("README.md")
        self.assertIn("9 role definitions", text)
        self.assertIn("Designer", text)


if __name__ == "__main__":
    unittest.main()
