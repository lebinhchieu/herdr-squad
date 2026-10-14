"""Every `process.md → <Section>` citation in agents, skills and bin resolves to a heading or a named bullet of the template."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates/squad/process.md"

HEADINGS = [
    "# How this squad works",
    "## Work is grouped by scope",
    "## Files are the truth, messages are the talk",
    "## Defaults",
    "## Starting work",
    "## Lifetimes: every scope starts fresh",
    "## Sizes: not every scope runs the full pod",
    "### When a role is left out, its duties move. They are never dropped.",
    "### Changing size",
    "## Inside a goal",
    "## Promotion: knowledge goes up to the project",
    "## Closing",
    "## Messages",
    "## Who decides",
    "## Task lifecycle",
    "## Iterations",
    "## Cost rules",
    "## Notes",
    "## Safety",
]
# Named places agents refer to without an arrow citation.
NAMED = ["**Stacked branches.**", "**Merge only on the PO's request.**", "`## Backlog`", "## Lifetimes"]

CITATION = re.compile(r"process\.md`?\s*→\s*([A-Z][^.;:,()`]*(?:→\s*[A-Z][^.;:,()`]*)*)")


def headings(text):
    out, fenced = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,3} ", line):
            out.append(line)
    return out


def sources():
    files = sorted((ROOT / "agents").glob("*.md")) + sorted((ROOT / "skills").glob("*/SKILL.md"))
    return files + sorted(p for p in (ROOT / "bin").iterdir() if p.is_file() and p.suffix != ".html")


def unresolved(template_text, files):
    """Return 'file: citation' for every citation whose heading or named bullet is not in the template."""
    heads = [h.lstrip("#").strip() for h in headings(template_text)]
    bad = []
    for f in files:
        for m in CITATION.finditer(f.read_text(errors="replace")):
            first, *rest = [p.strip() for p in m.group(1).split("→")]
            words = first.split()
            head = next((" ".join(words[:n]) for n in range(len(words), 0, -1)
                         if any(h.startswith(" ".join(words[:n])) for h in heads)), None)
            if head is None:
                bad.append(f"{f.name}: {m.group(0)}")
                continue
            if any(f"**{p}" not in template_text for p in rest):
                bad.append(f"{f.name}: {m.group(0)}")
    return bad


class ProcessCitationsTest(unittest.TestCase):
    def test_the_19_headings_are_pinned_in_order(self):
        self.assertEqual(headings(TEMPLATE.read_text()), HEADINGS)

    def test_every_citation_resolves(self):
        self.assertEqual(unresolved(TEMPLATE.read_text(), sources()), [])

    def test_there_are_citations_to_check(self):
        n = sum(len(CITATION.findall(f.read_text(errors="replace"))) for f in sources())
        self.assertGreaterEqual(n, 10)

    def test_named_places_exist(self):
        text = TEMPLATE.read_text()
        for name in NAMED:
            self.assertIn(name, text)

    def test_a_renamed_heading_is_reported(self):
        text = TEMPLATE.read_text().replace("## Promotion: knowledge", "## Handing up: knowledge")
        bad = unresolved(text, sources())
        self.assertTrue(any("Promotion" in b for b in bad), bad)
        self.assertNotEqual(headings(text), HEADINGS)

    def test_a_missing_named_bullet_is_reported(self):
        text = TEMPLATE.read_text().replace("**Merge only on the PO's request.**", "**Merge rule.**")
        self.assertTrue(any("Merge only" in b for b in unresolved(text, sources())))


if __name__ == "__main__":
    unittest.main()
