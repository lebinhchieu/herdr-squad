"""Instruction files (roles, process, skills, templates) must describe the per-scope layout and nothing that was removed."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = sorted((ROOT / "agents").glob("*.md"))
INSTRUCTIONS = AGENTS + [ROOT / "templates/squad/process.md", ROOT / "templates/squad/project.md"] \
    + sorted((ROOT / "skills").glob("*/SKILL.md")) + sorted((ROOT / "templates/scope").rglob("*.md")) \
    + sorted((ROOT / "templates/goal").rglob("*.md"))
# Files and places that no longer exist at squad level.
STALE = ["scopes.md", "scopes-done", "$SQUAD_DIR/roster", "$SQUAD_DIR/roles", "$SQUAD_DIR/tasks", "$SQUAD_DIR/evidence",
         "$SQUAD_DIR/contracts", "$SQUAD_DIR/iterations", "$SQUAD_DIR/usage-events", "$SQUAD_DIR/goal.md", "roles/archive",
         "XL", "coach-$SQUAD", "iterations/TEMPLATE"]
# Roles used to be long-lived across a whole run; every role now lives for one scope.
AGENT_STALE = ["long-lived", "whole run", "stay for the whole"]
ALLOWED_STALE = {"templates/scope/iterations/TEMPLATE.md": ["iterations/TEMPLATE"]}


class InstructionsTest(unittest.TestCase):
    def test_no_file_refers_to_something_that_was_removed(self):
        for f in INSTRUCTIONS:
            rel = str(f.relative_to(ROOT))
            text = f.read_text()
            for token in STALE:
                if token in ALLOWED_STALE.get(rel, []):
                    continue
                self.assertNotIn(token, text, f"{rel} still mentions {token!r}")

    def test_no_role_is_described_as_living_beyond_its_scope(self):
        for f in AGENTS:
            for token in AGENT_STALE:
                self.assertNotIn(token, f.read_text(), f"{f.name} still mentions {token!r}")

    def test_every_scope_role_starts_by_reading_its_scope_folder(self):
        for f in AGENTS:
            if f.stem in ("manager", "token-coach"):
                continue
            text = f.read_text()
            self.assertIn("$SCOPE_DIR/scope.md", text, f.name)
            self.assertIn("$GOAL_DIR/goal.md", text, f.name)
            self.assertIn("shared/", text, f.name)
            self.assertIn("$SCOPE_DIR/roles/$SQUAD_NAME.notes.md", text, f.name)

    def test_no_role_still_writes_its_notes_to_a_squad_level_roles_folder(self):
        for f in AGENTS:
            for m in re.finditer(r"`roles/\$SQUAD_NAME\.notes\.md`", f.read_text()):
                start = f.read_text()[max(0, m.start() - 12):m.start()]
                self.assertNotIn("$SQUAD_DIR/", start, f.name)

    def test_process_documents_every_variable_and_every_squad_command(self):
        text = (ROOT / "templates/squad/process.md").read_text()
        for token in ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "squad-start", "squad-close", "squad-respawn",
                      "squad-spawn", "--base", "--in-goal", "promoted:", "shared/decisions.md", "scopes/_done"):
            self.assertIn(token, text)

    def test_every_command_an_instruction_tells_agents_to_run_exists(self):
        names = {p.name for p in (ROOT / "bin").iterdir()}
        for f in INSTRUCTIONS:
            for cmd in re.findall(r"`(squad-[a-z]+)[ `]", f.read_text()):
                self.assertIn(cmd, names, f"{f.name} runs {cmd}")

    def test_init_ignores_the_board_logs_when_everything_is_committed(self):
        text = (ROOT / "skills/squad-init/SKILL.md").read_text()
        option = text.split("- **Commit everything.**")[1].split("- **Ignore everything.**")[0]
        self.assertIn("*.jsonl", option)

    def test_the_manager_covers_both_modes_and_closes_through_squad_close(self):
        text = (ROOT / "agents/manager.md").read_text()
        for token in ("goal Manager", "squad-close <squad> --scope", "squad-close <squad> --goal", "--in-goal", "--base",
                      "promoted:", "Never read or write another scope's folder"):
            self.assertIn(token, text)

    def test_the_designer_is_wired_into_process_manager_and_scope_template(self):
        process = (ROOT / "templates/squad/process.md").read_text()
        for token in ("design: yes", "ui-design/", "`ux`"):
            self.assertIn(token, process)
        self.assertIn("\ndesign: no\n", (ROOT / "templates/scope/scope.md").read_text())
        self.assertIn("`designer`", (ROOT / "agents/manager.md").read_text())


if __name__ == "__main__":
    unittest.main()
