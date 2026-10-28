"""Ticket 12 (S4): reader inventory of the old scope language. Every hit of the old keys (`size:`, 'size', "size",
`qa-b`) in bin/ hooks/ agents/ skills/ (history and changelog excluded) is in the allow-list below, with its reason.
A new hit, or a hit count that moves, fails: add the reason here and in the ticket, or remove the reader."""
import os
import subprocess
import unittest
from collections import Counter

from rulesview import ROOT

PATTERN = r"size:|'size'|\"size\"|qa-b\b"
CONVERTER = "converter input or old-format rejection (names the old key to point at the converter)"
ALLOW = {
    "bin/squad-log-message": (1, "comment: old `size:` scope.md is not guessed"),
    "bin/squad-respawn": (2, "pinned-runtime comment and refusal text (D7)"),
    "bin/squad-spawn": (2, "pinned-runtime comment and refusal text (D7)"),
    "bin/squadcompose.py": (4, CONVERTER),
    "bin/squadinbox.py": (1, "false positive: os.stat st_size"),
    "bin/squadreport.py": (3, "report display of legacy rows"),
    "bin/squadreport_rollup.py": (3, "report display of legacy rows"),
    "bin/squadrules.py": (10, "OLD_WHEN_KEYS, legacy_team, lint messages"),
    "bin/squadruntime.py": (1, CONVERTER),
    "bin/squadteam.py": (2, CONVERTER),
    "bin/squadupgrade.py": (4, "overlay report: old-when translation table (AC 21)"),
    "hooks/po-inbox/fixtures/visual.ts": (1, "false positive: evidence file name qa-b-spec-review"),
    "hooks/po-inbox/mod.test.ts": (2, "false positive: fs.stat size"),
    "hooks/po-inbox/testkit.ts": (1, "false positive: fs.stat size"),
    "hooks/po-inbox/ui.test.ts": (1, "false positive: fs.stat size"),
}


class OldLanguageInventory(unittest.TestCase):
    def test_hits_are_allow_listed(self):
        out = subprocess.run(
            ["git", "grep", "-nE", PATTERN, "--", "bin", "hooks", "agents", "skills",
             ":!skills/*/history/*", ":!skills/*/changelog.md"],
            cwd=ROOT, capture_output=True, text=True, check=False).stdout
        got = Counter(line.split(":", 1)[0] for line in out.splitlines())
        want = {f: n for f, (n, _) in ALLOW.items()}
        self.assertEqual(dict(got), want)

    def test_po_visible_text_has_no_size_word(self):
        """AC 29: no `size` word in PO-visible text, outside the legacy-squad error, converter output and the
        overlay report (those live in bin/*.py error strings, not in these files)."""
        import re
        paths = ["bin/squad-start", "templates/scope", "templates/goal", "agents"]
        for rel in paths:
            base = os.path.join(ROOT, rel)
            files = [base] if os.path.isfile(base) else [os.path.join(d, f) for d, _, fs in os.walk(base) for f in fs]
            for f in files:
                with open(f, encoding="utf-8") as fh:
                    for n, line in enumerate(fh, 1):
                        self.assertIsNone(re.search(r"\bsize\b", line, re.I), f"{f}:{n}: {line.strip()}")
        who = subprocess.run([os.path.join(ROOT, "bin", "squad-process"), "who", "--help"], capture_output=True,
                             text=True, check=False)
        self.assertIsNone(re.search(r"\bsize\b", who.stdout + who.stderr, re.I))


if __name__ == "__main__":
    unittest.main()
