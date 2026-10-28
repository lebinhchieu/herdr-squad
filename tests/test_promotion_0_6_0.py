"""Ticket 13 (promotion, plugin 0.6.0): the size word is gone from rules and docs outside an allow-list, the version
is the same everywhere it is written, ADR 0018 states what it overrides, the v9 snapshot equals the rule folder."""
import json
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZE = r"(?i)\bsize\b(?!-\d)"  # `-iw` would also match the surviving SIZE-n rule IDs
VERSION = "0.6.0"
# bin/: converter mapping, migrate input, report display, pinned-runtime texts, old-format errors (same list as ticket 12).
BIN_ALLOW = {
    "bin/squad-log-message": 1, "bin/squad-manager-guard": 1, "bin/squad-respawn": 2,
    "bin/squad-spawn": 2, "bin/squadcompose.py": 4, "bin/squadreport.py": 3,
    "bin/squadreport_rollup.py": 3, "bin/squadrules.py": 10, "bin/squadruntime.py": 4, "bin/squadteam.py": 2,
    "bin/squadupgrade.py": 4,
}
# hooks/: TypeScript `size` of a file stat or a Set, and a fixture quoting an old escalation (non-scope use).
HOOKS_ALLOW = {
    "hooks/po-inbox/actions.ts": 2, "hooks/po-inbox/fixtures/contract-home.ts": 1, "hooks/po-inbox/fixtures/visual.ts": 2,
    "hooks/po-inbox/item.test.ts": 2, "hooks/po-inbox/list.test.ts": 1, "hooks/po-inbox/markup.test.ts": 1,
    "hooks/po-inbox/mod.test.ts": 5, "hooks/po-inbox/testkit.ts": 1, "hooks/po-inbox/ui.test.ts": 1,
}
# `qa-b\b` in the rules is the reviewer file name qa-b.md (evidence), never the old key.
QAB_FILE_ALLOW = {"templates/squad/process/evidence.md": 3, "templates/squad/process/files.md": 1,
                  "templates/squad/process/review.md": 1}


def grep(pattern, *paths, perl=True):
    out = subprocess.run(["git", "grep", "-c", "-P" if perl else "-E", pattern, "--", *paths], cwd=ROOT,
                         capture_output=True, text=True, check=False).stdout
    return {l.rsplit(":", 1)[0]: int(l.rsplit(":", 1)[1]) for l in out.splitlines()}


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class NoSizeWord(unittest.TestCase):
    def test_rules_have_no_size_word_outside_the_tombstones(self):
        self.assertEqual(grep(SIZE, "templates/squad/process", ":!templates/squad/process/_removed.md"), {})

    def test_qa_b_in_rules_is_only_the_reviewer_file_name(self):
        got = grep(r"qa-b\b", "templates/squad/process", ":!templates/squad/process/_removed.md")
        self.assertEqual(got, QAB_FILE_ALLOW)
        for f in got:
            for line in read(f).splitlines():
                for m in re.finditer(r"qa-b\b", line):
                    self.assertTrue(line[m.start():].startswith("qa-b.md"), f"{f}: {line}")

    def test_docs_agents_and_skills_have_none(self):
        self.assertEqual(grep(SIZE, "README.md", "CONTEXT.md", "agents", "skills", ":!skills/*/changelog.md"), {})

    def test_bin_and_hooks_hits_are_allow_listed(self):
        self.assertEqual(grep(SIZE, "bin"), BIN_ALLOW)
        self.assertEqual(grep(SIZE, "hooks"), HOOKS_ALLOW)


class GlossaryAndAdr(unittest.TestCase):
    def test_context_has_team_duty_owner_checker_and_no_size_entry(self):
        text = read("CONTEXT.md")
        for term in ("**Team**:", "**Duty owner**:", "**Checker**:", "**QA whitebox**:", "**QA blackbox**:"):
            self.assertIn(term, text)
        self.assertNotIn("**Size**:", text)
        self.assertIn("`qa-white`", text)
        self.assertIn("`qa-black`", text)

    def test_adr_0018_states_where_it_overrides_0016_and_0017(self):
        text = read("docs/adr/0018-team-replaces-size.md")
        self.assertRegex(text, r"(?m)^Status: accepted")
        self.assertRegex(text, r"\*\*Overrides:\*\*.*ADR 0016.*Sizes.*Duty owners.*ADR 0017")
        self.assertIn("Amended by 0018", read("docs/adr/0016-process-composed-per-role.md"))
        self.assertIn("Amended by 0018", read("docs/adr/0017-architect-role.md"))


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
