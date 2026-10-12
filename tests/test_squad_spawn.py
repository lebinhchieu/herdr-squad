"""squad-spawn --dry-run: role defaults and session id."""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-spawn"
TABLE = {"manager": ("opus", "medium"), "tech-lead": ("sonnet", "high"), "ba": ("sonnet", "high"),
         "team-lead": ("sonnet", "medium"), "dev": ("sonnet", "medium"),
         "qa-whitebox": ("sonnet", "high"), "qa-blackbox": ("sonnet", "high"),
         "token-coach": ("sonnet", "medium")}
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
if [[ "$1 $2" == "agent get" ]]; then
  [[ " ${LIVE:-} " == *" $3 "* ]] && { echo '{"result":{"agent":{"tab_id":"t0"}}}'; exit 0; }
  echo '{"error":{"code":"agent_not_found"}}'; exit 1
fi
[[ $1 == tab ]] && echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}'
exit 0
"""


class SpawnDryRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = Path(self.tmp.name) / ".claude" / "squads" / "t"
        self.squad.mkdir(parents=True)
        (self.squad / "process.md").write_text("x")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD")}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, role, *args):
        r = subprocess.run([str(SCRIPT), role, "x", "--dry-run", *args], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_role_defaults_match_the_table(self):
        for role, (model, effort) in TABLE.items():
            with self.subTest(role=role):
                self.assertRegex(self.spawn(role), rf"--model {model} --effort {effort}\b")

    def test_flags_override_role_defaults(self):
        self.assertRegex(self.spawn("dev", "--model", "opus", "--effort", "high"), r"--model opus --effort high\b")

    def test_dry_run_passes_a_session_id_and_plans_the_roster_write(self):
        out = self.spawn("dev")
        self.assertRegex(out, rf"--session-id {UUID}\b")
        self.assertRegex(out, rf"--set-session x {UUID}")

    def test_spawn_records_the_same_session_id_in_roster(self):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "herdr").write_text(FAKE_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(log))
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n| manager | Manager | all | x | live |\n")
        r = subprocess.run([str(SCRIPT), "dev", "dev-1", "--scope", "s"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        passed = re.search(rf"--session-id ({UUID})", log.read_text()).group(1)
        self.assertIn(f"| dev-1 | dev | s |  | live | {passed} |", (self.squad / "roster.md").read_text())
        self.assertIn(passed, r.stdout)


    def _fake_herdr(self, live):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir(exist_ok=True)
        (bin_dir / "herdr").write_text(FAKE_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        self.log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.log), LIVE=live)
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n")

    def test_refuses_a_name_that_is_already_live_in_another_squad(self):
        self._fake_herdr(live="bill-ba-invoices")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already live", r.stderr)
        self.assertNotIn("tab create", self.log.read_text())

    def test_spawns_when_the_name_is_free(self):
        self._fake_herdr(live="other-name")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_every_role_has_settings_that_parse(self):
        settings = SCRIPT.parent.parent / "templates" / "squad" / "settings"
        for role in TABLE:
            with self.subTest(role=role):
                self.assertIn("permissions", json.loads((settings / f"{role}.json").read_text()))


if __name__ == "__main__":
    unittest.main()
