"""Ticket 20: team models in scope.md (`model <role>: <model> <effort>`), the squad-spawn precedence, the Manager rule."""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPAWN = ROOT / "bin" / "squad-spawn"
START = ROOT / "bin" / "squad-start"
RESPAWN = ROOT / "bin" / "squad-respawn"
TEMPLATE = ROOT / "templates" / "scope" / "scope.md"
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
if [[ "$1 $2" == "agent get" ]]; then echo '{"error":{"code":"agent_not_found"}}'; exit 1; fi
[[ $1 == tab ]] && echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}'
exit 0
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = self.root / ".claude" / "squads" / "t"
        self.scope = self.squad / "scopes" / "s"
        (self.scope / "roles").mkdir(parents=True)
        (self.squad / "goals").mkdir()
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        (self.scope / "roster.md").write_text("| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n", encoding="utf-8")
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def roster_row(self, name):
        with open(self.scope / "roster.md", "a", encoding="utf-8") as f:
            f.write(f"| {name} | dev | s |  | live | 00000000-0000-0000-0000-000000000001 |\n")

    def scope_md(self, *lines):
        (self.scope / "scope.md").write_text("# Scope: s\n\nsize: M\n" + "".join(l + "\n" for l in lines), encoding="utf-8")

    def settings(self, role, data):
        (self.squad / "settings").mkdir(exist_ok=True)
        (self.squad / "settings" / f"{role}.json").write_text(json.dumps(data), encoding="utf-8")

    def run_(self, cmd, **env):
        return subprocess.run([str(c) for c in cmd], env={**self.env, **env}, text=True, encoding="utf-8", capture_output=True, timeout=20)

    def dry(self, role="dev", *args, **env):
        r = self.run_([SPAWN, role, "x", "--scope", "s", "--dry-run", *args], **env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout


class PrecedenceTest(Base):
    def test_template_then_squad_settings_then_scope_md(self):
        self.scope_md()
        self.assertRegex(self.dry(), r"--model sonnet --effort medium\b")  # template default for dev
        self.settings("dev", {"model": "haiku", "effortLevel": "low"})
        self.assertRegex(self.dry(), r"--model haiku --effort low\b")  # squad settings beat the template
        self.scope_md("model dev: opus xhigh")
        self.assertRegex(self.dry(), r"--model opus --effort xhigh\b")  # scope.md beats squad settings

    def test_recorded_override_beats_scope_md(self):
        self.settings("dev", {"model": "haiku", "effortLevel": "low"})
        self.scope_md("model dev: opus xhigh")
        self.roster_row("dev-1")
        (self.scope / "roles" / "dev-1.overrides").write_text("model=sonnet[1m]\neffort=max\n", encoding="utf-8")
        r = self.run_([RESPAWN, "dev-1", "--dry-run"], SCOPE_DIR=str(self.scope), SQUAD_SCOPE="s")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"--model sonnet\[1m\] --effort max ")

    def test_flags_beat_scope_md_per_key(self):
        self.settings("dev", {"model": "haiku", "effortLevel": "low"})
        self.scope_md("model dev: opus xhigh")
        self.assertRegex(self.dry("dev", "--model", "sonnet", "--effort", "max"), r"--model sonnet --effort max\b")
        self.assertRegex(self.dry("dev", "--model", "sonnet"), r"--model sonnet --effort xhigh\b")

    def test_other_roles_are_untouched(self):
        self.scope_md("model dev: opus xhigh")
        self.assertNotRegex(self.dry("qa-whitebox"), r"--model opus --effort xhigh\b")

    def test_team_lead_developer_spawn_picks_the_line_up(self):
        self.scope_md("model dev: opus xhigh")
        self.assertRegex(self.dry("dev", SQUAD_ROLE="team-lead", SQUAD_NAME="t-tl-s"), r"--model opus --effort xhigh\b")

    def test_legacy_flat_squad_without_scope_folder_is_unchanged(self):
        flat = self.root / ".claude" / "squads" / "flat"
        flat.mkdir()
        (flat / "process.md").write_text("x", encoding="utf-8")
        r = self.run_([SPAWN, "dev", "x", "--dry-run"], SQUAD_DIR=str(flat))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"--model sonnet --effort medium\b")


class ParseTest(Base):
    def test_malformed_lines_exit_2_and_name_the_line(self):
        for bad in ("model dev: sonnet", "model dev: sonnet turbo", "model dev sonnet medium", "model: dev sonnet medium",
                    "model dev: so/net medium", "model dev: sonnet medium extra"):
            with self.subTest(line=bad):
                self.scope_md(bad)
                r = self.run_([SPAWN, "dev", "x", "--scope", "s", "--dry-run"])
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertIn(bad, r.stderr)
                self.assertIn("scope.md", r.stderr)

    def test_a_malformed_line_of_another_role_refuses_too_and_nothing_is_made(self):
        self.scope_md("model qa-whitebox: haiku")
        r = self.run_([SPAWN, "dev", "x", "--scope", "s", "--repo", str(self.root)])
        self.assertEqual(r.returncode, 2)
        self.assertFalse(self.log.exists())
        self.assertFalse((self.root / ".worktrees").exists())

    def test_duplicate_role_exits_2(self):
        self.scope_md("model dev: opus low", "model dev: haiku low")
        r = self.run_([SPAWN, "dev", "x", "--scope", "s", "--dry-run"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("twice", r.stderr)

    def test_unknown_role_only_warns(self):
        self.scope_md("model wizard: opus high", "model dev: haiku low")
        r = self.run_([SPAWN, "dev", "x", "--scope", "s", "--dry-run"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("unknown role 'wizard'", r.stderr)
        self.assertRegex(r.stdout, r"--model haiku --effort low\b")

    def test_prose_and_html_comments_are_not_model_lines(self):
        self.scope_md("model choice is the PO's call", "<!-- model dev: opus high -->", "  model dev: opus high")
        self.assertRegex(self.dry(), r"--model sonnet --effort medium\b")

    def test_a_scope_made_from_the_template_has_no_override(self):
        text = TEMPLATE.read_text(encoding="utf-8").replace("{{name}}", "s").replace("{{brief}}", "b").replace("{{goal}}", "").replace("{{touches}}", "")
        self.assertIn("model <role>: <model> <effort>", text)
        (self.scope / "scope.md").write_text(text, encoding="utf-8")
        self.assertRegex(self.dry(), r"--model sonnet --effort medium\b")


class RecordedTest(Base):
    def real(self, *args, name="dev-1"):
        r = self.run_([SPAWN, "dev", name, "--scope", "s", *args])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_scope_md_value_is_never_written_to_overrides_and_a_change_applies_at_respawn(self):
        self.scope_md("model dev: opus xhigh")
        self.real()
        self.roster_row("dev-1")
        self.assertRegex(self.log.read_text(encoding="utf-8"), r"--model opus --effort xhigh\b")
        self.assertFalse((self.scope / "roles" / "dev-1.overrides").exists())
        self.scope_md("model dev: haiku low")  # mid-scope change: next respawn only
        r = self.run_([RESPAWN, "dev-1", "--dry-run"], SCOPE_DIR=str(self.scope), SQUAD_SCOPE="s")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("--model", r.stdout.split("squad-spawn", 1)[1].split("--prompt")[0])
        self.log.unlink()
        self.real(name="dev-2")
        self.assertRegex(self.log.read_text(encoding="utf-8"), r"--model haiku --effort low\b")

    def test_a_flag_is_recorded_and_the_scope_md_value_for_the_other_key_is_not(self):
        self.scope_md("model dev: opus xhigh")
        self.real("--effort", "low")
        self.assertEqual((self.scope / "roles" / "dev-1.overrides").read_text(encoding="utf-8"), "effort=low\n")


class StartResumeTest(Base):
    def test_resume_dry_run_shows_the_scope_md_level(self):
        self.scope_md("model manager: haiku low")
        r = self.run_([START, "--resume", "s", "--dry-run"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("manager model: haiku (from scope.md)", r.stdout)
        self.assertIn("manager effort: low (from scope.md)", r.stdout)

    def test_recorded_override_and_flag_beat_scope_md_on_resume(self):
        self.scope_md("model manager: haiku low")
        (self.scope / "roles" / "t-mgr-s.overrides").write_text("model=opus\n", encoding="utf-8")
        out = self.run_([START, "--resume", "s", "--dry-run", "--effort", "max"]).stdout
        self.assertIn("manager model: opus (from recorded override)", out)
        self.assertIn("manager effort: max (from flag)", out)


class RuleTest(unittest.TestCase):
    def rule(self, rid):
        r = subprocess.run([str(ROOT / "bin" / "squad-process"), "rule", rid], text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_the_manager_rule_has_the_first_move_steps_and_the_scope_md_format(self):
        t = self.rule("START-3b")
        for needle in ("one table", "default model and effort", "advisor", "keep", "model <role>: <model> <effort>",
                       "model dev: sonnet medium", "Roles not listed use their defaults", "next spawn or respawn",
                       "only when the PO asks", "recorded override", "squad settings"):
            self.assertIn(needle, t)

    def test_goal_manager_does_it_per_scope(self):
        self.assertRegex(self.rule("START-3b"), r"goal Manager does this for each scope")

    def test_who_shows_the_manager_acting_at_every_size(self):
        r = subprocess.run([str(ROOT / "bin" / "squad-process"), "who", "START-3b"], text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        for size in "SML":
            lines = [l for l in r.stdout.splitlines() if l.startswith(size)]
            self.assertTrue(lines, f"no who line for size {size}:\n{r.stdout}")
            for l in lines:
                self.assertRegex(l, r"acts: .*manager")

    def test_size_rule_points_at_it(self):
        self.assertIn("[START-3b]", self.rule("SIZE-1"))


if __name__ == "__main__":
    unittest.main()
