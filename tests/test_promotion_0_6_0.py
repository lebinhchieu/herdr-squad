"""Ticket 13 (promotion, plugin 0.6.0): the size word is gone from rules and docs outside an allow-list, the version
is the same everywhere it is written, ADR 0018 states what it overrides, the v9 snapshot equals the rule folder."""
import json
import re
import subprocess
import unittest

from squadtest import ROOT
SIZE = r"(?i)\bsize\b(?!-\d)"  # `-iw` would also match the surviving SIZE-n rule IDs
VERSION = "0.6.0"
def grep(pattern, *paths, perl=True):
    out = subprocess.run(["git", "grep", "-c", "-P" if perl else "-E", pattern, "--", *paths], cwd=ROOT,
                         capture_output=True, text=True, check=False).stdout
    return {l.rsplit(":", 1)[0]: int(l.rsplit(":", 1)[1]) for l in out.splitlines()}


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class NoSizeWord(unittest.TestCase):
    def test_rules_have_no_size_word_outside_the_tombstones(self):
        self.assertEqual(grep(SIZE, "templates/squad/process", ":!templates/squad/process/_removed.md"), {})


class Version(unittest.TestCase):
    def test_version_is_identical_in_plugin_json_changelog_and_readme(self):
        # plugin.json may be patched past the promotion release (0.6.1 ...); changelog and README keep the release's own text
        cur = tuple(int(n) for n in json.loads(read(".claude-plugin/plugin.json"))["version"].split("."))
        self.assertGreaterEqual(cur, tuple(int(n) for n in VERSION.split(".")))
        changelog = read("skills/squad-process-update/changelog.md")
        v9 = changelog.split("## v9", 1)[1].split("\n## v8", 1)[0]
        self.assertIn(f"Plugin {VERSION}", v9.split("\nadded:", 1)[0])
        self.assertIn(f"**{VERSION} (breaking)", read("README.md"))

    def test_tombstones_carry_why_and_replaced_by(self):
        blocks = re.split(r"(?m)^## ", read("templates/squad/process/_removed.md"))[1:]
        self.assertTrue(blocks)
        for b in blocks:
            self.assertRegex(b, r"(?m)^why: .{10,}", b[:20])
            self.assertRegex(b, r"(?m)^replaced_by: \S+", b[:20])


if __name__ == "__main__":
    unittest.main()
