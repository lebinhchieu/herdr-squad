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
    block = re.search(name + r": \[\n(.*?)\n  \]\.join", FIXTURES, re.S).group(1)
    return "\n".join(line.strip()[1:-2] for line in block.split("\n"))


def example(heading):
    after = GUIDE[GUIDE.index(heading):]
    return re.search(r"````\n(.*?)\n````", after, re.S).group(1)


class InboxBodyGuide(unittest.TestCase):
    def test_example_1_is_the_guideE1_fixture(self):
        self.assertEqual(example("## Example 1"), fixture("guideE1"))

    def test_example_2_is_the_guideR1_fixture(self):
        self.assertEqual(example("## Example 2"), fixture("guideR1"))

    def test_every_form_the_guide_names_is_drawn_by_the_pane(self):
        draw = (ROOT / "hooks" / "po-inbox" / "draw.tsx").read_text(encoding="utf-8") + (ROOT / "hooks" / "po-inbox" / "markup.ts").read_text(encoding="utf-8")
        for word in ("decision", "warning", "info", "ok", "fail", "warn", "skip", "diagram", "link", "badge", "callout"):
            self.assertIn(word, draw)

    def test_the_guide_does_not_touch_role_files(self):
        self.assertNotIn("agents/", GUIDE)


if __name__ == "__main__":
    unittest.main()
