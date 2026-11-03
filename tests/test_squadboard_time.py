"""squadboard_time: ISO in, epoch out, offset aware; unreadable gives None."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
from squadboard_time import parse_iso  # noqa: E402

E = 1_700_000_000  # 2023-11-14T22:13:20Z


class ParseIso(unittest.TestCase):
    def test_offsets_give_the_same_instant(self):
        for s in ("2023-11-14T22:13:20Z", "2023-11-14T22:13:20+00:00",
                  "2023-11-15T05:13:20+07:00", "2023-11-14T17:13:20-05:00"):
            self.assertEqual(parse_iso(s), E, s)

    def test_T17_TA4_real_strings(self):
        # copied from this scope: messages.jsonl ts, inbox.jsonl ts
        self.assertEqual(parse_iso("2026-11-03T14:21:58.000Z"), 1793715718.0)
        self.assertEqual(parse_iso("2026-11-03T14:16:42Z"), 1793715402.0)

    def test_naive_is_utc(self):
        self.assertEqual(parse_iso("2023-11-14T22:13:20"), E)

    def test_fraction(self):
        self.assertAlmostEqual(parse_iso("2023-11-14T22:13:20.500Z"), E + 0.5)

    def test_unknown_not_exception(self):
        for bad in (None, "", "  ", "nope", 12, "2023-13-45T00:00:00Z"):
            self.assertIsNone(parse_iso(bad), bad)


if __name__ == "__main__":
    unittest.main()
