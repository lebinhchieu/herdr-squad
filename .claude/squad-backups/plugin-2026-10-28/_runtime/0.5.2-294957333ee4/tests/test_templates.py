"""Template layers: the standing squad, a scope and a goal each hold only what belongs to their level."""
import json
import re
import unittest
from pathlib import Path

T = Path(__file__).resolve().parent.parent / "templates"
ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "dev", "token-coach", "designer", "architect")


def files(d):
    return {str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()}


class TemplateLayersTest(unittest.TestCase):
    def test_standing_squad_has_no_per_scope_files(self):
        got = files(T / "squad")
        self.assertTrue({"process.md", "project.md", "process-log.md"} <= got)
        for banned in ("goal.md", "roster.md", "scopes.md", "escalations.md"):
            self.assertNotIn(banned, got)
        self.assertFalse([f for f in got if f.startswith(("iterations/", "contracts/", "roles/"))])

    def test_scope_template_holds_the_per_scope_files(self):
        self.assertTrue({"scope.md", "roster.md", "escalations.md", "iterations/TEMPLATE.md"} <= files(T / "scope"))

    def test_goal_template_holds_the_shared_folder_and_the_goal_files(self):
        self.assertTrue({"goal.md", "roster.md", "escalations.md", "shared/decisions.md"} <= files(T / "goal"))

    def test_brief_placeholders_are_the_ones_squad_start_fills(self):
        for kind in ("scope", "goal"):
            text = (T / kind / f"{kind}.md").read_text()
            found = set(re.findall(r"\{\{(\w+)\}\}", text))
            self.assertTrue({"name", "brief", "touches"} <= found, kind)
            self.assertLessEqual(found, {"name", "brief", "touches", "goal"})

    def test_fresh_decisions_file_has_no_entries_so_a_new_goal_closes_without_promotion(self):
        self.assertFalse([l for l in (T / "goal/shared/decisions.md").read_text().splitlines() if l.startswith("- ")])
        self.assertFalse([l for l in (T / "goal/goal.md").read_text().splitlines() if l.startswith("promoted:")])

    def test_rosters_have_the_session_column_that_squad_usage_writes_to(self):
        for kind in ("scope", "goal"):
            self.assertIn("| Agent | Role | Scope | Owns | Status | Session |", (T / kind / "roster.md").read_text())

    def test_every_role_has_settings_that_parse_and_the_manager_may_run_the_squad_commands(self):
        for role in ROLES:
            self.assertIn("permissions", json.loads((T / "squad/settings" / f"{role}.json").read_text()), role)
        allow = json.loads((T / "squad/settings/manager.json").read_text())["permissions"]["allow"]
        for cmd in ("squad-start", "squad-spawn", "squad-retire", "squad-respawn", "squad-close", "squad-usage"):
            self.assertIn(f"Bash({cmd}:*)", allow)

    def test_only_developers_and_the_manager_may_merge_and_nobody_may_push_or_switch_to_main(self):
        for role in ROLES:
            perms = json.loads((T / "squad/settings" / f"{role}.json").read_text())["permissions"]
            if role in ("dev", "manager"):
                self.assertIn("Bash(git merge:*)", perms["allow"])
                self.assertNotIn("Bash(git merge:*)", perms["deny"])
                for cmd in ("git push", "git rebase", "git reset --hard", "git checkout main", "git checkout dev"):
                    self.assertIn(f"Bash({cmd}:*)", perms["deny"], cmd)
            elif "deny" in perms:
                self.assertIn("Bash(git merge:*)", perms["deny"], role)
                self.assertNotIn("Bash(git merge:*)", perms.get("allow", []), role)

    def test_token_coach_may_write_only_its_own_proposal_files(self):
        perms = json.loads((T / "squad/settings/token-coach.json").read_text())["permissions"]
        self.assertIn("Write(/.claude/squads/*/scopes/*/iterations/*.coach.md)", perms["allow"])
        self.assertIn("Write(/.claude/squads/*/goals/*/coach/*.coach.md)", perms["allow"])
        for level in ("*/*.md", "*/scopes/*/*.md", "*/goals/*/*.md"):
            self.assertIn(f"Write(/.claude/squads/{level})", perms["deny"])

    def test_designer_may_write_only_ui_design_files(self):
        perms = json.loads((T / "squad/settings/designer.json").read_text())["permissions"]
        writes = [p for p in perms["allow"] if p.startswith(("Write(", "Edit("))]
        self.assertEqual(sorted(writes), ["Edit(/.claude/squads/*/scopes/*/ui-design/**)",
                                          "Write(/.claude/squads/*/scopes/*/ui-design/**)"])
        for level in ("*/*.md", "*/scopes/*/*.md", "*/goals/*/*.md", "*/settings/**"):
            self.assertIn(f"Write(/.claude/squads/{level})", perms["deny"])
        self.assertIn("Bash(squad-respawn:*)", perms["allow"])
        self.assertFalse([p for p in perms["deny"] if p.startswith("Read(")])


if __name__ == "__main__":
    unittest.main()
