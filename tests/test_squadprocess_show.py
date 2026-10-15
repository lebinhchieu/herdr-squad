"""squad-process show <role>: role map, section view, fallbacks, exit codes. Temp folders only."""
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadprocess as sp  # noqa: E402

CLI = ROOT / "bin" / "squad-process"
TEMPLATE = ROOT / "templates" / "squad" / "process.md"
ENV = {k: v for k, v in os.environ.items() if k != "SQUAD_DIR"}

SYN = """# How this squad works

process-version: 2

Intro line.

| Role | Reads |
|---|---|

## Sizes

### Under unwanted

hidden sub

## Messages

msg body

### Under wanted

wanted sub

```
## Safety
# not a heading
```

## Task lifecycle

life

## Notes

notes body

## Notes from the PO

po notes

## Cost rules

cost

## Safety

safe
"""


def run(*args, squad=None, env=None):
    a = [sys.executable, str(CLI), "show", *args] + (["--squad-dir", str(squad)] if squad else [])
    return subprocess.run(a, capture_output=True, text=True, env=env or ENV)


def heads(out):
    return [ln for ln, fenced in sp._fence_flags(out.splitlines()) if not fenced and ln.startswith("#")]


class Squad(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.dir = Path(self._t.name)
        (self.dir / "process.md").write_text(SYN)


class ShowTest(Squad):
    def test_dev_view_order_and_content(self):
        r = run("dev", squad=self.dir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr, "")
        self.assertEqual(heads(r.stdout), ["# How this squad works", "## Messages", "### Under wanted",
                                           "## Task lifecycle", "## Cost rules", "## Safety"])
        self.assertTrue(r.stdout.startswith("squad-process show dev: Messages, Task lifecycle, Cost rules, Safety;"))
        self.assertIn("Intro line.", r.stdout)
        self.assertIn("| Role | Reads |", r.stdout)
        self.assertNotIn("process-version", r.stdout)
        self.assertNotIn("hidden sub", r.stdout)
        self.assertNotIn("notes body", r.stdout)

    def test_fenced_heading_is_not_a_heading_and_stays_in_text(self):
        out = run("dev", squad=self.dir).stdout
        self.assertEqual(out.count("## Safety"), 2)  # the fenced line and the real heading
        self.assertIn("# not a heading", out)

    def test_other_qa_roles_same_as_dev_and_normalised(self):
        dev = run("dev", squad=self.dir).stdout.split("\n", 2)[2]
        for role in ("qa-whitebox", "qa-blackbox", "QA whitebox", "Dev", "QA Blackbox"):
            r = run(role, squad=self.dir)
            self.assertEqual(r.returncode, 0, role)
            self.assertEqual(r.stdout.split("\n", 2)[2], dev, role)

    def test_designer_has_no_task_lifecycle(self):
        r = run("designer", squad=self.dir)
        self.assertEqual(heads(r.stdout), ["# How this squad works", "## Messages", "### Under wanted",
                                           "## Cost rules", "## Safety"])

    def test_unwanted_subsection_excluded_wanted_included(self):
        out = run("dev", squad=self.dir).stdout
        self.assertIn("wanted sub", out)
        self.assertNotIn("Under unwanted", out)

    def test_prefix_match_prints_every_match_once_in_file_order(self):
        r = run("dev", "--also", "Notes", squad=self.dir)
        hs = heads(r.stdout)
        self.assertEqual(hs.count("## Notes"), 1)
        self.assertEqual(hs.count("## Notes from the PO"), 1)
        self.assertEqual(hs, ["# How this squad works", "## Messages", "### Under wanted", "## Task lifecycle",
                              "## Notes", "## Notes from the PO", "## Cost rules", "## Safety"])

    def test_reworded_suffix_still_matches(self):
        (self.dir / "process.md").write_text(SYN.replace("## Safety", "## Safety rules, local"))
        r = run("dev", squad=self.dir)
        self.assertEqual(r.stderr, "")
        self.assertIn("## Safety rules, local", r.stdout)

    def test_also_repeatable_and_missing_falls_back(self):
        r = run("dev", "--also", "Notes", "--also", "Sizes", squad=self.dir)
        self.assertIn("## Sizes", r.stdout)
        self.assertIn("hidden sub", r.stdout)  # the ### under a wanted ## comes along
        r = run("dev", "--also", "Inside a goal", squad=self.dir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Inside a goal", r.stderr)
        self.assertEqual(r.stdout, SYN)

    def test_missing_wanted_section_whole_file_and_names_it(self):
        (self.dir / "process.md").write_text(SYN.replace("## Task lifecycle", "## Something else"))
        r = run("dev", squad=self.dir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, SYN.replace("## Task lifecycle", "## Something else"))
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        self.assertIn("Task lifecycle", r.stderr)

    def test_unknown_role_whole_file_stderr_lists_roles(self):
        r = run("banana", squad=self.dir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, SYN)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        for w in ("banana", "dev", "designer", "qa-whitebox", "qa-blackbox", "manager", "tech-lead", "ba",
                  "team-lead", "token-coach"):
            self.assertIn(w, r.stderr)

    def test_whole_file_roles_silent(self):
        for role in ("manager", "Tech Lead", "ba", "team-lead", "token-coach"):
            r = run(role, squad=self.dir)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, SYN, ""), role)

    def test_live_read_no_cache(self):
        run("dev", squad=self.dir)
        (self.dir / "process.md").write_text(SYN.replace("safe\n", "safe\n\nnew rule line\n"))
        self.assertIn("new rule line", run("dev", squad=self.dir).stdout)


class ErrorTest(Squad):
    def test_missing_file(self):
        (self.dir / "process.md").unlink()
        r = run("dev", squad=self.dir)
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn(str(self.dir / "process.md"), r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_no_squad_dir(self):
        r = run("dev")
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("no --squad-dir and $SQUAD_DIR is not set", r.stderr)

    def test_env_default(self):
        r = run("dev", env={**ENV, "SQUAD_DIR": str(self.dir)})
        self.assertEqual(r.returncode, 0)
        self.assertIn("## Messages", r.stdout)

    def test_duplicate_heading_exit_2_and_writes_nothing(self):
        (self.dir / "process.md").write_text(SYN + "\n## Safety\n\ndup\n")

        def tree():
            return sorted((str(p), hashlib.sha256(p.read_bytes()).hexdigest()) for p in self.dir.rglob("*"))
        before = tree()
        r = run("dev", squad=self.dir)
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("duplicate heading", r.stderr)
        self.assertEqual(tree(), before)

    def test_help_lists_show(self):
        r = subprocess.run([sys.executable, str(CLI), "--help"], capture_output=True, text=True)
        self.assertIn("show", r.stdout)
        self.assertIn("squad-process show", CLI.read_text().split('"""')[1])


class TemplatePinTest(unittest.TestCase):
    @staticmethod
    def _table_names(row_start):
        for ln in TEMPLATE.read_text().splitlines():
            if ln.startswith("| " + row_start):
                return tuple(n.strip() for n in ln.split("|")[2].rsplit(";", 1)[1].split(".")[0].strip().split(","))
        raise AssertionError(row_start)

    def test_map_equals_template_role_table(self):
        dq = self._table_names("Developer, QA whitebox, QA blackbox")
        for role in ("dev", "qa-whitebox", "qa-blackbox"):
            self.assertEqual(sp.ROLE_SECTIONS[role], dq)
        self.assertEqual(sp.ROLE_SECTIONS["designer"], self._table_names("UI/UX Designer"))
        self.assertEqual(set(sp.ROLE_SECTIONS), {"dev", "qa-whitebox", "qa-blackbox", "designer"})

    def test_every_mapped_name_matches_exactly_one_template_heading(self):
        hs = [h for h, _ in sp.sections(TEMPLATE.read_text()) if h.startswith("## ")]
        for names in sp.ROLE_SECTIONS.values():
            for n in names:
                self.assertEqual(len([h for h in hs if h.startswith("## " + n)]), 1, n)


class RealTemplateTest(unittest.TestCase):
    def test_template_views(self):
        text = TEMPLATE.read_text()
        out, warn = sp.show(text, "dev")
        self.assertIsNone(warn)
        self.assertEqual(heads(out), ["# How this squad works", "## Messages", "## Task lifecycle",
                                      "## Cost rules", "## Safety"])
        out, _ = sp.show(text, "designer")
        self.assertEqual(heads(out), ["# How this squad works", "## Messages", "## Cost rules", "## Safety"])


if __name__ == "__main__":
    unittest.main()
