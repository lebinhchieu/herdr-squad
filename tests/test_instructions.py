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
    def test_manager_and_dev_know_the_label_rule(self):
        manager = (ROOT / "agents/manager.md").read_text()
        self.assertIn("--title", manager)
        self.assertIn("squad-label --agent", manager)
        self.assertIn("squad-label", (ROOT / "agents/dev.md").read_text())
    def test_project_instructions_row_names_the_team_file(self):
        rows = [r for r in (ROOT / "templates/squad/project.md").read_text().splitlines()
                if r.startswith("| Project instructions |")]
        self.assertEqual(len(rows), 1)
        self.assertIn("AGENTS.md", rows[0])
        self.assertIn("Project instructions", (ROOT / "skills/squad-init/SKILL.md").read_text())

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

    def test_init_ignores_the_message_logs_when_everything_is_committed(self):
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


class ManagerInboxTest(unittest.TestCase):
    text = (ROOT / "agents/manager.md").read_text()

    def test_the_manager_names_each_inbox_command_and_flag(self):
        for token in ("squad-inbox add", "--kind answer|read", "Never offer a merge, push or deploy as an item", "<<'EOF'", "(a) ", "squad-inbox answer", "--source chat", "squad-inbox withdraw",
                      '--blocks ""'):
            self.assertIn(token, self.text)

    def test_the_add_bullet_says_the_body_comes_from_a_quoted_heredoc(self):  # PI-07 AC9
        self.assertIn("body in a quoted heredoc, `squad-inbox add ... <<'EOF' … EOF`; no pipe and no unquoted heredoc (the body would show in chat)", self.text)

    def test_the_inbox_bullets_carry_the_three_live_wording_rules(self):  # PI-08 AC4
        self.assertIn("One `squad-inbox add` per Bash call, never two.", self.text)  # M1
        self.assertIn("your reply is the printed line and nothing else: no body, options or recommendation", self.text)  # M2
        self.assertIn("Run `squad-inbox list` first; never answer from memory of what is open.", self.text)  # M3

    def test_an_inbox_answer_is_never_a_merge_push_or_deploy_request(self):
        self.assertRegex(self.text, r"(?is)never[^.]*merge, push or deploy[^.]*inbox|never[^.]*inbox[^.]*merge, push or deploy"
                         r"|inbox[^.]*never[^.]*merge, push or deploy")
        self.assertIn("\n## Never\n", self.text)
        self.assertIn("needs their explicit request here", self.text)

    def test_every_squad_inbox_word_is_a_cli_command(self):
        words = set(re.findall(r"squad-inbox ([a-z]+)", self.text))
        self.assertTrue(words)
        self.assertLessEqual(words, {"add", "list", "read", "answer", "withdraw", "delivered"})


SECTION_ROLES = ("dev", "qa-whitebox", "qa-blackbox", "designer")
# Literal copy of the role table (PS-01's map is not on this branch); a citation outside it is read with --also.
VIEW = {"dev": ["Messages", "Task lifecycle", "Cost rules", "Safety"],
        "qa-whitebox": ["Messages", "Task lifecycle", "Cost rules", "Safety"],
        "qa-blackbox": ["Messages", "Task lifecycle", "Cost rules", "Safety"],
        "designer": ["Messages", "Cost rules", "Safety"]}
OUTSIDE_VIEW = {"dev": ["Inside a goal"], "designer": ["Notes"]}


class SectionViewTest(unittest.TestCase):
    def test_each_section_role_runs_its_own_show_command(self):
        for name in SECTION_ROLES:
            text = (ROOT / f"agents/{name}.md").read_text()
            self.assertIn(f"squad-process show {name}", text)
            self.assertNotIn("Read `$SQUAD_DIR/process.md`", text)

    def test_other_roles_do_not_use_show(self):
        for name in ("manager", "tech-lead", "ba", "team-lead", "token-coach"):
            self.assertNotIn("squad-process show", (ROOT / f"agents/{name}.md").read_text(), name)

    def test_the_fallback_sentence_names_exactly_the_role_view(self):
        for name in SECTION_ROLES:
            text = (ROOT / f"agents/{name}.md").read_text()
            m = re.search(r"if the command fails, read the `process\.md` sections (.*?) by heading", text)
            self.assertTrue(m, name)
            self.assertEqual(re.findall(r"`([^`]+)`", m.group(1)), VIEW[name], name)

    def test_every_citation_is_in_the_role_view_or_listed_as_outside_it(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("citations", ROOT / "tests/test_process_citations.py")
        citations = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(citations)
        CITATION = citations.CITATION
        for name in SECTION_ROLES:
            text = (ROOT / f"agents/{name}.md").read_text()
            outside = OUTSIDE_VIEW.get(name, [])
            for m in CITATION.finditer(text):
                head = m.group(1).split("→")[0].strip()
                known = [h for h in VIEW[name] + outside if head.startswith(h)]
                self.assertTrue(known, f"{name}.md cites {head!r} outside its view: add it to OUTSIDE_VIEW or drop it")
            if outside:
                self.assertIn("--also", text, name)


    def test_show_is_allowed_for_exactly_the_four_roles_and_never_as_a_wildcard(self):
        import json
        for f in sorted((ROOT / "templates/squad/settings").glob("*.json")):
            allow = json.loads(f.read_text())["permissions"]["allow"]
            self.assertEqual("Bash(squad-process show:*)" in allow, f.stem in SECTION_ROLES, f.name)
            self.assertNotIn("Bash(squad-process:*)", allow, f.name)


    def test_dev_copies_reports_to_evidence_and_sends_a_diff_check_after_a_pass(self):
        lines = (ROOT / "agents/dev.md").read_text().splitlines()
        copy = [l for l in lines if l.startswith("- **Copy a report")]
        after = [l for l in lines if l.startswith("- **After a `PASS`")]
        self.assertEqual(len(copy), 1)
        self.assertEqual(len(after), 1)
        self.assertIn("evidence/<task>/", copy[0])
        self.assertIn("hand in", copy[0])
        self.assertIn("diff check", after[0])
        self.assertIn("both QAs", after[0])


if __name__ == "__main__":
    unittest.main()
