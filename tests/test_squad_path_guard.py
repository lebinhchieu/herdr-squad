"""squad-path-guard: a non-Developer role cannot write in the project root outside .claude/squads/ (FILE-11)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
sys.path.insert(0, str(BIN))
import importlib.machinery
import importlib.util

_loader = importlib.machinery.SourceFileLoader("squad_path_guard", str(BIN / "squad-path-guard"))
_spec = importlib.util.spec_from_loader("squad_path_guard", _loader)
guard = importlib.util.module_from_spec(_spec)
_loader.exec_module(guard)

ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "token-coach")


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve() / "proj"
        self.squad = self.root / ".claude" / "squads" / "t"
        self.scope = self.squad / "scopes" / "s"
        (self.scope / "tasks").mkdir(parents=True)
        (self.root / ".worktrees" / "t" / "s" / "dev-1").mkdir(parents=True)
        (self.root / ".scratch").mkdir()
        self.outside = Path(self.tmp.name).resolve() / "elsewhere"
        self.outside.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def env(self, role="tech-lead", **extra):
        e = {"SQUAD_DIR": str(self.squad), "SCOPE_DIR": str(self.scope)}
        if role is not None:
            e["SQUAD_ROLE"] = role
        e.update(extra)
        return e

    def decide(self, path, role="tech-lead", tool="file_path", cwd=None, **extra):
        payload = {"tool_input": {tool: str(path)}}
        if cwd is not None:
            payload["cwd"] = str(cwd)
        return guard.decide(self.env(role, **extra), payload)

    def test_every_non_dev_role_is_blocked_in_the_root_and_the_message_names_tasks_and_the_rule(self):
        for role in ROLES:
            with self.subTest(role=role):
                msg = self.decide(self.root / ".scratch" / "x" / "spec.md", role)
                self.assertEqual(msg, f"draft it in {self.scope}/tasks/; a Developer task commits it [FILE-11]")

    def test_squad_folder_is_allowed_for_every_role(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertIsNone(self.decide(self.scope / "tasks" / "x.md", role))
                self.assertIsNone(self.decide(self.squad / "process-log.md", role))

    def test_developer_is_never_limited(self):
        self.assertIsNone(self.decide(self.root / ".scratch" / "x.md", "dev"))
        self.assertIsNone(self.decide(self.root / ".worktrees" / "t" / "s" / "dev-1" / "a.py", "dev"))

    def test_no_role_the_po_is_never_limited(self):
        self.assertIsNone(self.decide(self.root / "README.md", None))

    def test_non_dev_writing_in_a_developer_worktree_is_blocked(self):
        self.assertIsNotNone(self.decide(self.root / ".worktrees" / "t" / "s" / "dev-1" / "a.py", "manager"))

    def test_outside_the_project_is_allowed(self):
        self.assertIsNone(self.decide(self.outside / "x.md"))

    def test_the_root_itself_and_a_sibling_with_the_same_prefix(self):
        self.assertIsNotNone(self.decide(self.root / "x.md"))
        self.assertIsNone(self.decide(str(self.root) + "-other/x.md"))

    def test_dotdot_is_resolved_before_the_check(self):
        self.assertIsNotNone(self.decide(self.scope / "tasks" / ".." / ".." / ".." / ".." / ".." / "x.md"))
        self.assertIsNone(self.decide(self.root / ".scratch" / ".." / ".claude" / "squads" / "t" / "x.md"))

    def test_symlink_into_the_root_is_blocked_and_one_leading_out_is_refused_too(self):
        link = self.outside / "link"
        try:
            os.symlink(self.root / ".scratch", link)
            os.symlink(self.outside, self.scope / "tasks" / "out")
        except (OSError, NotImplementedError):
            self.skipTest("no symlinks")
        self.assertIsNotNone(self.decide(link / "spec.md"))
        # a link inside the root that leads out is still refused: conservative, the draft belongs in tasks/ anyway
        self.assertIsNotNone(self.decide(self.scope / "tasks" / "out" / "x.md"))

    def test_a_file_that_does_not_exist_yet_resolves_through_its_symlinked_parent(self):
        link = self.outside / "dirlink"
        try:
            os.symlink(self.root / ".scratch", link)
        except (OSError, NotImplementedError):
            self.skipTest("no symlinks")
        self.assertIsNotNone(self.decide(link / "new" / "deep" / "spec.md"))   # neither new/ nor spec.md exists

    def test_a_symlink_inside_the_squad_folder_pointing_to_the_root_is_blocked(self):
        try:
            os.symlink(self.root / ".scratch", self.scope / "tasks" / "toroot")
        except (OSError, NotImplementedError):
            self.skipTest("no symlinks")
        self.assertIsNotNone(self.decide(self.scope / "tasks" / "toroot" / "spec.md"))

    def test_windows_case_and_separators_are_normalised(self):
        import ntpath
        from unittest import mock
        env = {"SQUAD_ROLE": "tech-lead", "SQUAD_DIR": "C:\\Proj\\.claude\\squads\\t", "SCOPE_DIR": "C:\\Proj\\.claude\\squads\\t\\scopes\\s"}
        with mock.patch.object(guard.os, "path", ntpath):
            for target in ("c:/proj/.scratch/x/spec.md", "C:\\PROJ\\README.md", "c:\\Proj/.Scratch\\a.md"):
                self.assertIsNotNone(guard.decide(env, {"tool_input": {"file_path": target}, "cwd": "C:\\"}), target)
            for target in ("c:/proj/.claude/squads/t/scopes/s/tasks/a.md", "C:\\PROJ\\.CLAUDE\\Squads\\t\\x.md",
                           "d:/proj/x.md", "c:/proj-other/x.md"):
                self.assertIsNone(guard.decide(env, {"tool_input": {"file_path": target}, "cwd": "C:\\"}), target)

    def test_tools_and_real_role_values(self):
        for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            key = "notebook_path" if tool == "NotebookEdit" else "file_path"
            for role in ("tech-lead", "qa-whitebox", "qa-blackbox", "team-lead", "token-coach"):
                msg = guard.decide(self.env(role), {"tool_name": tool, "tool_input": {key: str(self.root / "x")}})
                self.assertIsNotNone(msg, (tool, role))

    def test_relative_path_resolves_against_cwd_of_the_payload(self):
        self.assertIsNotNone(self.decide("spec.md", cwd=self.root))
        self.assertIsNone(self.decide("x.md", cwd=self.scope / "tasks"))

    def test_notebook_path_is_read_too(self):
        self.assertIsNotNone(self.decide(self.root / "a.ipynb", tool="notebook_path"))

    def test_missing_squad_dir_or_target_allows(self):
        self.assertIsNone(guard.decide({"SQUAD_ROLE": "manager"}, {"tool_input": {"file_path": str(self.root / "x")}}))
        self.assertIsNone(guard.decide(self.env(), {"tool_input": {}}))
        self.assertIsNone(guard.decide(self.env(), {}))

    def test_one_realpath_and_no_git_call(self):
        src = (BIN / "squad-path-guard").read_text(encoding="utf-8")
        self.assertEqual(src.count("realpath("), 1)
        for word in ("subprocess", "socket", "urllib", "git "):
            self.assertNotIn(word, src.split('"""', 2)[2])


class CliTest(unittest.TestCase):
    def run_guard(self, stdin, role="manager", with_dir=True):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t).resolve()
            env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD")}
            env["SQUAD_ROLE"] = role
            if with_dir:
                env["SQUAD_DIR"] = str(root / ".claude" / "squads" / "t")
            data = stdin.replace("ROOT", str(root)) if isinstance(stdin, str) else json.dumps(stdin).replace("ROOT", str(root))
            return subprocess.run([sys.executable, str(BIN / "squad-path-guard")], input=data, env=env,
                                  text=True, encoding="utf-8", capture_output=True, timeout=20)

    def test_blocks_with_exit_2_and_stderr(self):
        r = self.run_guard({"tool_name": "Write", "tool_input": {"file_path": "ROOT/.scratch/x/spec.md"}})
        self.assertEqual(r.returncode, 2)
        self.assertIn("[FILE-11]", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_allows_with_exit_0(self):
        r = self.run_guard({"tool_input": {"file_path": "ROOT/.claude/squads/t/x.md"}})
        self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_a_tooling_problem_never_blocks(self):
        for stdin in ("not json", "", "[1]", "null"):
            with self.subTest(stdin=stdin):
                self.assertEqual(self.run_guard(stdin).returncode, 0)
        self.assertEqual(self.run_guard({"tool_input": {"file_path": "ROOT/x"}}, with_dir=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
