"""Ticket 13: the Coach builds on earlier backlogs and tool findings leave the retro (ITER-13..16)."""
import unittest

from rulesview import acts


class RetroRulesTest(unittest.TestCase):
    def test_who_shows_the_coach_on_the_backlog_rules_and_the_manager_on_the_follow_ups(self):
        for rid in ("ITER-13", "ITER-14"):
            for size in "SML":
                self.assertEqual(acts(rid, size), ("token-coach",), (rid, size))
        for rid in ("ITER-15", "ITER-16"):
            for size in "SML":
                self.assertEqual(acts(rid, size), ("manager",), (rid, size))


if __name__ == "__main__":
    unittest.main()
