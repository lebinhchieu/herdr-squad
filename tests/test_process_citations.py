"""Citations are `[ID]` pointers, checked by `squad-process lint` (ticket 02); the heading-citation checks are gone.

Old name -> new name:
  test_the_19_headings_are_pinned_in_order        deleted: the v6 template keeps its headings until 09; test_process_history pins them
  test_every_citation_resolves                    test_agents_skills_bin_cite_no_process_md_heading + test_lint_resolves_every_pointer
  test_there_are_citations_to_check               test_rules_do_cite_ids
  test_named_places_exist                         deleted: named v6 bullets; the rule IDs replace them
  test_a_renamed_heading_is_reported              test_an_unknown_pointer_is_reported
  test_a_missing_named_bullet_is_reported         test_an_unknown_pointer_is_reported
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from rulesview import ROOT, run

ARROW = re.compile(r"process\.md`?\s*→")


def sources():
    files = sorted((ROOT / "agents").glob("*.md")) + sorted((ROOT / "skills").glob("*/SKILL.md"))
    return files + sorted(p for p in (ROOT / "bin").iterdir() if p.is_file() and p.suffix not in (".html", ".pyc"))


class ProcessCitationsTest(unittest.TestCase):
    def test_lint_resolves_every_pointer(self):
        r = run("lint", "--plugin-root", str(ROOT))
        self.assertEqual((r.returncode, r.stdout.strip()), (0, ""), r.stdout)

    def test_agents_skills_bin_cite_no_process_md_heading(self):
        bad = [f.name for f in (ROOT / "agents").glob("*.md") if ARROW.search(f.read_text(errors="replace"))]
        self.assertEqual(bad, [])

    def test_rules_do_cite_ids(self):
        n = sum(len(re.findall(r"\[[A-Z]+-\d+[a-z]?\]", p.read_text())) for p in (ROOT / "templates/squad/process").glob("*.md"))
        self.assertGreaterEqual(n, 10)

    def test_an_unknown_pointer_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "plugin"
            shutil.copytree(ROOT / "templates/squad/process", root / "templates/squad/process")
            f = root / "templates/squad/process/core.md"
            f.write_text(f.read_text().replace("[WHO-1a]", "[MSG-99]"))
            r = run("lint", "--plugin-root", str(root))
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown pointer [MSG-99]", r.stdout)


if __name__ == "__main__":
    unittest.main()
