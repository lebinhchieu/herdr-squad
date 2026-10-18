import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BULLET = ("- **Task ID:** every agent writes the ticket number `NN` alone as the task ID, "
          "never an alias, slug or prefix; a Developer's roster `Owns` reads `ticket NN`.")
H = ROOT / "skills/squad-process-update/history"


class TaskIdRule(unittest.TestCase):
    def test_template_has_bullet(self):
        t = (ROOT / "templates/squad/process.md").read_text(encoding="utf-8")
        self.assertIn(BULLET, t.splitlines())

    def test_v5_has_it_v4_not(self):
        self.assertIn(BULLET, (H / "process-v5.md").read_text(encoding="utf-8").splitlines())
        self.assertNotIn("**Task ID:**", (H / "process-v4.md").read_text(encoding="utf-8"))

    def test_rosters_say_ticket_nn(self):
        for p in ("scope", "goal"):
            t = (ROOT / f"templates/{p}/roster.md").read_text(encoding="utf-8")
            self.assertIn("`Owns` reads `ticket NN`", t)


if __name__ == "__main__":
    unittest.main()
