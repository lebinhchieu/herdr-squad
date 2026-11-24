"""Template layers: the standing squad, a scope and a goal each hold only what belongs to their level."""
import json
import re
import unittest
from pathlib import Path

T = Path(__file__).resolve().parent.parent / "templates"
ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "dev", "token-coach", "designer", "architect")


def files(d):
    return {p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file()}


class TemplateLayersTest(unittest.TestCase):

    def test_brief_placeholders_are_the_ones_squad_start_fills(self):
        for kind in ("scope", "goal"):
            text = (T / kind / f"{kind}.md").read_text()
            found = set(re.findall(r"\{\{(\w+)\}\}", text))
            self.assertTrue({"name", "brief"} <= found, kind)
            self.assertLessEqual(found, {"name", "brief", "goal"})

    def test_no_rule_or_doc_describes_the_removed_touches_option(self):  # T22.AC1-AC4
        root = T.parent
        for rel in ("skills/squad-start/SKILL.md", "README.md", "templates/squad/process/starting.md", "templates/squad/process/goal.md",
                    "templates/squad/process/files.md"):
            text = (root / rel).read_text(encoding="utf-8")
            self.assertNotIn("--touches", text, rel)
            self.assertNotRegex(text, r"(?i)overlap(s)? (with )?(an )?open scope|\*\*Overlap\.\*\*|exit 3", rel)
        start = (T / "squad/process/starting.md").read_text(encoding="utf-8")
        step3 = start.split("## START-3 ")[1].split("\n## ")[0]
        self.assertEqual(re.findall(r"(?m)^(\d+)\. ", step3), ["1", "2"])
        self.assertNotIn("`touches:`", (T / "squad/process/files.md").read_text(encoding="utf-8"))

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

    def test_git_merge_is_allowed_for_dev_and_manager_and_every_git_risk_asks_never_denied(self):
        for role in ROLES:
            perms = json.loads((T / "squad/settings" / f"{role}.json").read_text())["permissions"]
            if role in ("dev", "manager"):
                self.assertIn("Bash(git merge:*)", perms["allow"])
                self.assertNotIn("Bash(git merge:*)", perms["ask"])
                cmds = ("git push", "git rebase", "git reset --hard", "git checkout main", "git checkout dev", "git branch -D")
            else:
                self.assertIn("Bash(git merge:*)", perms["ask"], role)
                self.assertNotIn("Bash(git merge:*)", perms.get("allow", []), role)
                cmds = ("git push", "git rebase", "git reset --hard", "git branch -D")
            for cmd in cmds:
                self.assertIn(f"Bash({cmd}:*)", perms["ask"], f"{role} {cmd}")
            self.assertFalse([d for d in perms.get("deny", []) if d.startswith("Bash(git")], role)

    def test_token_coach_may_write_only_its_own_proposal_files(self):
        perms = json.loads((T / "squad/settings/token-coach.json").read_text())["permissions"]
        self.assertIn("Write(/.claude/squads/*/scopes/*/iterations/*.coach.md)", perms["allow"])
        self.assertIn("Write(/.claude/squads/*/goals/*/coach/*.coach.md)", perms["allow"])
        for level in ("*/*.md", "*/scopes/*/*.md", "*/goals/*/*.md"):
            self.assertIn(f"Write(/.claude/squads/{level})", perms["deny"])

    def test_designer_may_write_only_ui_design_files(self):
        perms = json.loads((T / "squad/settings/designer.json").read_text())["permissions"]
        writes = [p for p in perms["allow"] if p.startswith(("Write(", "Edit("))]
        # /tmp is open to every role (bd2563c, SAFE-11)
        self.assertEqual(sorted(writes), ["Edit(/.claude/squads/*/scopes/*/ui-design/**)",
                                          "Edit(//tmp/**)",
                                          "Write(/.claude/squads/*/scopes/*/ui-design/**)",
                                          "Write(//tmp/**)"])
        for level in ("*/*.md", "*/scopes/*/*.md", "*/goals/*/*.md", "*/settings/**"):
            self.assertIn(f"Write(/.claude/squads/{level})", perms["deny"])
        self.assertIn("Bash(squad-respawn:*)", perms["allow"])
        self.assertFalse([p for p in perms["deny"] if p.startswith("Read(")])


if __name__ == "__main__":
    unittest.main()
