"""Guards on the REAL process.md template, its snapshots and its changelog (design §3, §8.4)."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadprocess as sp  # noqa: E402

TEMPLATE = ROOT / "templates/squad/process.md"
SKILL = ROOT / "skills/squad-process-update"
HISTORY = SKILL / "history"


def snapshot(n):
    return (HISTORY / f"process-v{n}.md").read_text()


class RealHistoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.P = sp.plugin_version(ROOT)
        cls.items = sp.read_changelog(SKILL / "changelog.md")

    def test_template_line_3_is_the_version_and_equals_plugin_version(self):
        line = TEMPLATE.read_text().splitlines()[2]
        self.assertRegex(line, r"^process-version: [1-9][0-9]*$")
        self.assertEqual(int(line.split(": ")[1]), self.P)
        self.assertEqual(sp.parse_version(TEMPLATE.read_text()), (self.P, "ok"))

    def test_snapshots_run_1_to_P_without_gaps(self):
        found = sorted(int(p.stem.split("-v")[1]) for p in HISTORY.glob("process-v*.md"))
        self.assertEqual(found, list(range(1, self.P + 1)))

    def test_changelog_blocks_run_2_to_P_without_gaps(self):
        self.assertEqual(sorted({i.version for i in self.items}), list(range(2, self.P + 1)))
        for i in self.items:
            self.assertEqual(i.snapshot, f"history/process-v{i.version}.md")

    def test_every_listed_section_and_fenced_wording_is_in_its_snapshot(self):
        for it in self.items:
            new = dict(sp.sections(snapshot(it.version)))
            old = dict(sp.sections(snapshot(it.version - 1)))
            heads = [] if it.sections == "all" else it.sections
            for h in heads:
                with self.subTest(v=it.version, section=h):
                    self.assertIn(h, old if it.change == "remove" else new)
            if it.new_kind == "text":
                self.assertIn(it.new_text.strip(), "\n".join(new.get(h, "") for h in heads) or snapshot(it.version))
            if it.old_kind == "text":
                self.assertIn(it.old_text.strip(), snapshot(it.version - 1))

    def test_current_snapshot_is_the_template(self):
        self.assertEqual(snapshot(self.P), TEMPLATE.read_text())

    def test_a_squad_made_from_the_template_is_current_and_detection_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            squad = Path(tmp) / "squad"
            shutil.copytree(ROOT / "templates/squad", squad)
            c = sp.check(squad, ROOT)
            self.assertEqual((c["state"], c["stamp"], c["message"]), ("current", "stamped", ""))
            r = subprocess.run([str(ROOT / "bin/squad-process"), "check", "--quiet", "--squad-dir", str(squad)],
                               capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
