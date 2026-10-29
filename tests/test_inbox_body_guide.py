"""docs/inbox-body-guide.md: its two example bodies are the fixtures the pane tests parse.

The block types the guide states are checked by hooks/po-inbox/markup.test.ts (run by `claude plugin test`).
A hooks test cannot read files, so this test keeps the guide and the fixtures the same text.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = (ROOT / "docs" / "inbox-body-guide.md").read_text(encoding="utf-8")
FIXTURES = (ROOT / "hooks" / "po-inbox" / "fixtures" / "visual.ts").read_text(encoding="utf-8")


def fixture(name):
    found = re.search(re.escape(name) + r": \[\n(.*?)\n  \]\.join", FIXTURES, re.S)
    assert found, "fixture %s not found in visual.ts" % name
    block = found.group(1)
    return "\n".join(line.strip()[1:-2] for line in block.split("\n"))


def example(heading):
    after = GUIDE[GUIDE.index(heading + ":"):]
    return re.search(r"````\n(.*?)\n````", after, re.S).group(1)


class TestInboxBodyGuide(unittest.TestCase):
    def test_example_1_is_the_guide_e1_fixture(self):
        self.assertEqual(example("## Example 1"), fixture("guideE1"))

    def test_example_2_is_the_guide_r1_fixture(self):
        self.assertEqual(example("## Example 2"), fixture("guideR1"))

    def test_every_rule_has_a_why_line(self):
        rules = GUIDE[GUIDE.index("## Rules"):GUIDE.index("## Example 1")].strip().split("\n")[1:]
        rules = [line for line in rules if line.strip()]
        tops = [i for i, line in enumerate(rules) if line.startswith("- ")]
        self.assertGreaterEqual(len(tops), 9)
        for i in tops:
            nxt = rules[i + 1] if i + 1 < len(rules) else ""
            self.assertTrue(nxt.startswith("  - Why: "), "rule without a Why line: %s" % rules[i])


if __name__ == "__main__":
    unittest.main()
