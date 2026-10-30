"""`squad-inbox guide` prints the guide path; ITER-4 tells the Manager to read it; the card holds no copy."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def guide(plugin_root, cwd, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ("SCOPE_DIR", "GOAL_DIR")}
    return subprocess.run([sys.executable, str(plugin_root / "bin" / "squad-inbox"), "guide"],
                          cwd=str(cwd), env=env, capture_output=True, text=True)


def copy_tree(dst, with_docs=True):
    (dst / "bin").mkdir(parents=True)
    for f in (ROOT / "bin").iterdir():
        if f.is_file():
            shutil.copy2(f, dst / "bin" / f.name)
    if with_docs:
        (dst / "docs").mkdir()
        shutil.copy2(ROOT / "docs" / "inbox-body-guide.md", dst / "docs")


class TestInboxGuideCmd(unittest.TestCase):
    def test_prints_existing_absolute_path_only(self):
        r = guide(ROOT, "/")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertEqual(out, str(ROOT / "docs" / "inbox-body-guide.md") + "\n")
        self.assertTrue(os.path.isabs(out.strip()) and os.path.isfile(out.strip()))
        self.assertEqual(r.stderr, "")

    def test_works_from_a_copy_of_the_tree_and_other_cwd(self):
        with tempfile.TemporaryDirectory() as t:
            tree = Path(t, "runtime")
            copy_tree(tree)
            cwd = Path(t, "elsewhere")
            cwd.mkdir()
            r = guide(tree, cwd)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(Path(r.stdout.strip()).resolve(), (tree / "docs" / "inbox-body-guide.md").resolve())

    def test_works_through_a_symlink_to_the_script(self):
        with tempfile.TemporaryDirectory() as t:
            tree = Path(t, "runtime")
            copy_tree(tree)
            link = Path(t, "link")
            os.symlink(tree / "bin" / "squad-inbox", link)
            r = subprocess.run([sys.executable, str(link), "guide"], cwd=t, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(Path(r.stdout.strip()).resolve(), (tree / "docs" / "inbox-body-guide.md").resolve())

    def test_missing_file_is_exit_1_with_one_stderr_line(self):
        with tempfile.TemporaryDirectory() as t:
            tree = Path(t, "runtime")
            copy_tree(tree, with_docs=False)
            r = guide(tree, t)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(r.stdout, "")
            self.assertEqual(len(r.stderr.strip().splitlines()), 1)
            self.assertIn("inbox body guide is missing", r.stderr)

    def test_iter4_holds_the_rule_line(self):
        text = (ROOT / "templates/squad/process/iterations.md").read_text(encoding="utf-8")
        block = text.split("## ITER-4 Inbox")[1].split("\n## ")[0]
        self.assertIn("Before your first `squad-inbox add` in a session, read the file `squad-inbox guide` prints.", block)

    def test_manager_card_has_no_guide_text(self):
        self.assertNotIn("inbox-body-guide", (ROOT / "agents/manager.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
