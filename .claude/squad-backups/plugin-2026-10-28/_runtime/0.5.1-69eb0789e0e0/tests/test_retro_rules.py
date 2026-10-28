"""Ticket 13: the Coach builds on earlier backlogs and tool findings leave the retro (ITER-13..16)."""
import re
import unittest
from pathlib import Path

from rulesview import ROLES, acts, composed, run, who

ROOT = Path(__file__).resolve().parent.parent


def rule(role, rid, size="M"):
    return composed(role, size).split(f"## {rid} ")[1].split(" ## ")[0]


class RetroRulesTest(unittest.TestCase):
    def test_who_shows_the_coach_on_the_backlog_rules_and_the_manager_on_the_follow_ups(self):
        for rid in ("ITER-13", "ITER-14"):
            for size in "SML":
                self.assertEqual(acts(rid, size), ("token-coach",), (rid, size))
        for rid in ("ITER-15", "ITER-16"):
            for size in "SML":
                self.assertEqual(acts(rid, size), ("manager",), (rid, size))

    def test_coach_reads_backlogs_promotes_repeats_and_cites_both(self):
        r = rule("token-coach", "ITER-13")
        self.assertIn("every `## Backlog`", r)
        self.assertIn("`scopes/_done/**`, `goals/_done/**`", r)
        self.assertIn("2 or more scopes", r)
        self.assertIn("cite both coach files", r)
        self.assertIn("earlier backlogs", rule("token-coach", "ITER-7"))     # no longer "read only usage"
        self.assertNotIn("Read only", rule("token-coach", "ITER-7"))

    def test_manager_spawns_the_coach_with_a_prompt_and_never_polls(self):
        r = rule("manager", "ITER-6")
        for text in ('--prompt "<text>"', "iterations/<n>.coach.md", "coach/<goal>.coach.md", "`usage-events.jsonl`",
                     "earlier backlogs", "message the Manager with the file and the proposal count"):
            self.assertIn(text, r)
        w = rule("manager", "ITER-6c")
        for text in ("never loop, sleep or poll for the file", "`herdr agent list`", "only when no message came", "[MSG-8a]"):
            self.assertIn(text, w)
        self.assertIn("iterations/<n>.coach.md", rule("token-coach", "ITER-7"))
        self.assertIn("the file and the proposal count", rule("token-coach", "ITER-7"))

    def test_coach_writes_overlay_operations_and_plugin_proposals(self):
        r = rule("token-coach", "ITER-14")
        self.assertIn("`process.local.md` syntax with `upstream: proposed`", r)
        self.assertIn("`## Plugin proposals`", r)
        self.assertIn("tool", r)
        self.assertIn("role-card", r)

    def test_manager_turns_plugin_items_into_drafts_in_tasks_or_a_tracker(self):
        r = rule("manager", "ITER-15")
        self.assertIn("`## Plugin proposals`", r)
        self.assertIn('"Plugin follow-ups"', r)
        self.assertIn("`$SCOPE_DIR/tasks/`", r)
        self.assertIn("never the project root", r)
        self.assertIn("[FILE-11]", r)
        self.assertIn("`project.md` names the plugin's tracker", r)
        self.assertIn("List the draft paths", r)
        self.assertRegex(rule("manager", "ITER-16"), r"squad-close --scope.*Went well.*Friction.*Process changes made.*--force")

    def test_developer_rules_are_untouched_and_the_card_has_one_stance_line(self):
        for rid in ("ITER-13", "ITER-14", "ITER-15", "ITER-16"):
            self.assertNotIn(rid, composed("dev", "M"))
        card = (ROOT / "agents" / "token-coach.md").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"earlier backlogs", card)), 1)

    def test_lint_passes(self):
        r = run("lint")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
