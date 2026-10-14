"""squadprocess + squad-process: version parse, check, sections, changelog, CLI. Temp folders only."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadprocess as sp  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "process"
CLI = ROOT / "bin" / "squad-process"
V1 = ROOT / "skills" / "squad-process-update" / "history" / "process-v1.md"
V1_SHA256 = "1fe9970ba4e15a68c6b909268e1a269156f5eeced6859fb1163d057221764ede"


class ParseTest(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(sp.parse_version("# T\n\nprocess-version: 12\n"), (12, "ok"))
        self.assertEqual(sp.parse_version("process-version:3  \n"), (3, "ok"))

    def test_missing(self):
        self.assertEqual(sp.parse_version("# T\nno line\n"), (None, "missing"))

    def test_malformed(self):
        for bad in ("1.2", "abc", "", "0", "-1", "1 2"):
            self.assertEqual(sp.parse_version(f"process-version: {bad}\n"), (None, "malformed"), bad)

    def test_two_lines_is_malformed(self):
        self.assertEqual(sp.parse_version("process-version: 1\nprocess-version: 1\n"), (None, "malformed"))

    def test_line_in_code_fence_is_ignored(self):
        self.assertEqual(sp.parse_version("```\nprocess-version: 9\n```\n"), (None, "missing"))
        self.assertEqual(sp.parse_version("```\nprocess-version: 9\n```\nprocess-version: 2\n"), (2, "ok"))

    def test_numeric_not_text_compare(self):
        self.assertEqual(sp.parse_version("process-version: 10\n")[0] > 9, True)


def squad(tmp, text):
    d = Path(tmp) / "squad"
    d.mkdir(exist_ok=True)
    if text is not None:
        (d / "process.md").write_text(text)
    return d


class VersionTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)

    def test_squad_version(self):
        self.assertEqual(sp.squad_version(squad(self.t.name, "process-version: 2\n")), (2, "stamped"))
        self.assertEqual(sp.squad_version(squad(self.t.name, "# T\n")), (1, "unstamped"))
        self.assertEqual(sp.squad_version(squad(self.t.name, "process-version: x\n")), (1, "malformed"))

    def test_squad_version_without_file_raises_clearly(self):
        with self.assertRaises(sp.ProcessError):
            sp.squad_version(squad(self.t.name, None))

    def test_plugin_version(self):
        self.assertEqual(sp.plugin_version(FIX / "plugin-v3"), 3)

    def test_plugin_version_raises_on_missing_or_malformed(self):
        for text in (None, "# T\n", "process-version: 1.2\n"):
            root = Path(self.t.name) / "p"
            (root / "templates" / "squad").mkdir(parents=True, exist_ok=True)
            f = root / "templates" / "squad" / "process.md"
            f.unlink(missing_ok=True)
            if text is not None:
                f.write_text(text)
            with self.assertRaises(sp.ProcessError):
                sp.plugin_version(root)

    def check(self, text, plugin):
        return sp.check(squad(self.t.name, text), FIX / plugin)

    def test_current(self):
        r = self.check("process-version: 2\n", "plugin-v2")
        self.assertEqual((r["state"], r["stamp"], r["message"]), ("current", "stamped", ""))

    def test_behind_names_both_versions_and_the_command(self):
        r = self.check("process-version: 1\n", "plugin-v3")
        self.assertEqual(r["state"], "behind")
        for s in ("1", "3", "migrate the process", "/squad:squad-process-update", "nothing changes until you confirm"):
            self.assertIn(s, r["message"])
        self.assertNotIn("\n", r["message"])

    def test_ahead(self):
        r = self.check("process-version: 3\n", "plugin-v2")
        self.assertEqual(r["state"], "ahead")
        for s in ("3", "2", "update the plugin", "will not run"):
            self.assertIn(s, r["message"])

    def test_unstamped_and_malformed_say_so(self):
        r = self.check("# T\n", "plugin-v3")
        self.assertEqual((r["state"], r["squad"], r["stamp"]), ("behind", 1, "unstamped"))
        self.assertIn("treated as version 1", r["message"])
        self.assertIn("migrate the process", r["message"])
        r = self.check("process-version: 1.2\n", "plugin-v3")
        self.assertEqual((r["state"], r["stamp"]), ("behind", "malformed"))
        self.assertIn("malformed", r["message"])
        self.assertIn("treated as version 1", r["message"])

    def test_unstamped_against_plugin_1_is_current_but_still_warns(self):
        r = self.check("# T\n", "plugin-v1")
        self.assertEqual(r["state"], "current")
        self.assertIn("treated as version 1", r["message"])


class SectionsTest(unittest.TestCase):
    TEXT = ("# Title\n\nprocess-version: 2\n\n## A\nline a\n\n\n### B\n```\n# not a heading\n"
            "process-version: 9\n```\n| # | x |\n| #1 | y |\n#hash\n\n## C\nc\n")

    def test_flat_split_fence_aware_version_dropped(self):
        got = sp.sections(self.TEXT)
        self.assertEqual([h for h, _ in got], ["# Title", "## A", "### B", "## C"])
        d = dict(got)
        self.assertEqual(d["# Title"], "")
        self.assertEqual(d["## A"], "line a")
        self.assertIn("# not a heading", d["### B"])
        self.assertIn("process-version: 9", d["### B"])  # fenced, so kept
        self.assertNotIn("process-version: 2", "".join(d.values()))
        self.assertEqual(d["## C"], "c")

    def test_non_heading_hash_lines(self):
        body = dict(sp.sections(self.TEXT))["### B"]
        self.assertIn("| #1 | y |", body)
        self.assertIn("#hash", body)

    def test_duplicate_heading_raises(self):
        with self.assertRaises(sp.ProcessError):
            sp.sections("## A\nx\n## A\ny\n")

    def test_text_before_first_heading(self):
        self.assertEqual(sp.sections("intro\n## A\nx\n"), [("", "intro"), ("## A", "x")])


class ChangelogTest(unittest.TestCase):
    def test_toy_changelog(self):
        a, b, d = sp.read_changelog(FIX / "changelog.md")
        self.assertEqual((a.version, a.date, a.snapshot, a.title), (2, "2026-10-14", "history/process-v2.md", "Tighten A"))
        self.assertEqual((a.sections, a.change, a.why), (["A"], "reword", "shorter"))
        self.assertEqual((a.old_kind, a.old, a.new_kind), ("text", "old text", "snapshot"))
        self.assertEqual(b.sections, ["B", "C"])
        self.assertEqual((b.old_kind, b.new_kind, b.new), ("none", "text", "## B\n### not a heading here"))
        self.assertEqual((d.old_kind, d.new_kind, d.manual), ("snapshot", "none", "delete section D by hand"))
        self.assertEqual(a.manual, "")

    def test_all_sections(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "c.md"
            p.write_text("## v2 — 2026-10-14\n- snapshot: history/process-v2.md\n\n### T\n"
                         "- sections: all\n- change: reword\n- why: w\n- old: snapshot\n- new: snapshot\n")
            self.assertEqual(sp.read_changelog(p)[0].sections, "all")

    def test_broken_changelogs_fail_loudly(self):
        with self.assertRaises(sp.ProcessError):
            sp.read_changelog(FIX / "changelog-broken.md")
        with self.assertRaises(sp.ProcessError):
            sp.read_changelog(FIX / "nope.md")
        base = "## v2 — 2026-10-14\n- snapshot: s.md\n\n### T\n- sections: A\n- change: add\n- why: w\n"
        for text in (base + "- old: -\n", base + "- old: -\n- new: -\nstray line\n",
                     base + "- old: -\n- new:\n", base + "- old: -\n- new: -\n- old: -\n",
                     "### T\n- sections: A\n", base + "- old: -\n- new: -\n- color: red\n",
                     "## v2 — 2026-10-14\n\n### T\n- sections: A\n"):
            with tempfile.TemporaryDirectory() as t:
                p = Path(t) / "c.md"
                p.write_text(text)
                with self.assertRaises(sp.ProcessError, msg=text):
                    sp.read_changelog(p)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)

    def run_cli(self, text, *args, plugin="plugin-v2"):
        d = squad(self.t.name, text)
        return subprocess.run([sys.executable, str(CLI), *args[:1], "--squad-dir", str(d),
                               "--plugin-root", str(FIX / plugin), *args[1:]],
                              capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})

    def test_version(self):
        r = self.run_cli("# T\n", "version", plugin="plugin-v3")
        self.assertEqual(r.returncode, 0)
        self.assertIn("squad 1 (unstamped), plugin 3, behind", r.stdout)

    def test_version_json(self):
        r = self.run_cli("process-version: 2\n", "version", "--json")
        self.assertEqual(json.loads(r.stdout)["state"], "current")

    def test_check_quiet_is_silent_when_current(self):
        r = self.run_cli("process-version: 2\n", "check", "--quiet")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_check_prints_warning_and_exits_zero(self):
        for text, plugin, word in (("process-version: 1\n", "plugin-v2", "migrate the process"),
                                   ("process-version: 3\n", "plugin-v2", "update the plugin"),
                                   ("junk\n", "plugin-v2", "treated as version 1")):
            r = self.run_cli(text, "check", "--quiet", plugin=plugin)
            self.assertEqual(r.returncode, 0)
            self.assertIn(word, r.stdout)

    def test_bad_files_give_message_not_traceback(self):
        r = self.run_cli(None, "check", "--quiet")
        self.assertEqual(r.returncode, 0)
        self.assertIn("squad-process:", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        r = self.run_cli("# T\n", "version", plugin="nope")
        self.assertEqual(r.returncode, 0)
        self.assertIn("squad 1 (unstamped), plugin unknown", r.stdout)
        self.assertIn("squad-process:", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class SnapshotTest(unittest.TestCase):
    def test_v1_snapshot_is_the_git_object(self):
        """Pinned sha256 of `git show faa64cb:templates/squad/process.md` (no git needed, no live data)."""
        self.assertEqual(hashlib.sha256(V1.read_bytes()).hexdigest(), V1_SHA256)
        self.assertEqual(parse_none(V1), (None, "missing"))


def parse_none(p):
    return sp.parse_version(p.read_text())


if __name__ == "__main__":
    unittest.main()
