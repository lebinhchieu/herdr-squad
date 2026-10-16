"""T9: model and effort live in templates/squad/settings/<role>.json, not in agents/*.md."""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "c1be501"  # permissions are compared with this commit
ROLES = ["ba", "designer", "dev", "manager", "qa-blackbox", "qa-whitebox", "team-lead", "tech-lead", "token-coach"]
EFFORTS = {"low", "medium", "high", "xhigh", "max"}


def frontmatter(path):
    lines = path.read_text().splitlines()
    end = lines.index("---", 1)
    return lines[1:end]


class ModelEffortSettingsTest(unittest.TestCase):
    def test_no_role_file_frontmatter_carries_model_or_effort(self):
        for role in ROLES:
            with self.subTest(role=role):
                fm = frontmatter(ROOT / "agents" / f"{role}.md")
                self.assertEqual([l for l in fm if re.match(r"(model|effort):", l)], [])
                self.assertTrue(any(l.startswith("name:") for l in fm))

    def test_every_settings_file_has_both_keys_with_allowed_values(self):
        for role in ROLES:
            with self.subTest(role=role):
                d = json.loads((ROOT / "templates/squad/settings" / f"{role}.json").read_text())
                self.assertRegex(d["model"], r"^[A-Za-z0-9][][A-Za-z0-9._-]*$")
                self.assertIn(d["effortLevel"], EFFORTS)

    def test_nothing_from_the_base_permissions_was_removed_or_changed(self):
        # Later tasks may add allow/deny entries (T5 did); T9 itself may only add model and effortLevel.
        for role in ROLES:
            with self.subTest(role=role):
                rel = f"templates/squad/settings/{role}.json"
                old = subprocess.run(["git", "show", f"{BASE}:{rel}"], cwd=ROOT, text=True, capture_output=True)
                if old.returncode != 0:
                    self.skipTest(f"{BASE} not in this clone")
                old, now = json.loads(old.stdout), json.loads((ROOT / rel).read_text())
                self.assertLessEqual(set(old) - {"permissions"}, set(now))
                for kind, entries in old["permissions"].items():
                    self.assertLessEqual(set(entries), set(now["permissions"].get(kind, [])), f"{kind} lost entries")
                self.assertEqual(set(now) - set(old), {"model", "effortLevel"})


if __name__ == "__main__":
    unittest.main()
