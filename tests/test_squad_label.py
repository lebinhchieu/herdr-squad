"""squad-label: relabel a tab from the stored role, number and title.

The fake `herdr` has the shapes of the real one (evidence/TAB-01/herdr-agent-list.json):
`agent list` -> {"result":{"agents":[{"name","tab_id",...}]}}, `agent get` -> {"result":{"agent":{...}}}."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
sys.path.insert(0, str(BIN))
import squadlabel as sl  # noqa: E402

FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent list") python3 -c 'import json,os; print(json.dumps({"result":{"agents":[{"name":n,"tab_id":"tab-"+n} for n in os.environ["LIVE"].split()]}}))' ;;
  "agent get") echo "{\\"result\\":{\\"agent\\":{\\"name\\":\\"$3\\",\\"tab_id\\":\\"tab-$3\\"}}}" ;;
  "tab rename") [[ -n ${FAIL_RENAME:-} ]] && { echo boom >&2; exit 1; } ;;
esac
exit 0
"""


class LabelCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = Path(self.tmp.name)
        self.squad, self.scope, self.goal = r / "squad", r / "squad" / "scopes" / "s1", r / "squad" / "goals" / "g"
        self.scope.mkdir(parents=True)
        self.goal.mkdir(parents=True)
        fake = r / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR)
        (fake / "herdr").chmod(0o755)
        self.log = r / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR", "HERDR"))}
        self.env.update(HERDR_ENV="1", HERDR_LOG=str(self.log), LIVE="dev-1 dev-2 mgr",
                        PATH=f"{fake}:{os.environ['PATH']}", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, **env):
        e = {**self.env, **env}
        return subprocess.run([str(BIN / "squad-label"), *args], env=e, text=True, capture_output=True, timeout=20)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def as_dev(self, name="dev-2", **kw):
        return dict(SQUAD_NAME=name, SQUAD_ROLE="dev", SCOPE_DIR=str(self.scope), **kw)

    def test_self_relabel_renames_its_tab_and_prints_label(self):
        sl.write_entry(self.scope, "dev-2", "dev", 2, "old")
        r = self.run_cli("TAB-02 tabs", **self.as_dev())
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "🤖 Dev 2 · TAB-02 tabs"), r.stderr)
        self.assertIn("tab rename tab-dev-2 🤖 Dev 2 · TAB-02 tabs", self.calls())
        self.assertEqual(sl.read_entry(self.scope, "dev-2")["title"], "TAB-02 tabs")

    def test_blank_clears_title(self):
        sl.write_entry(self.scope, "dev-2", "dev", None, "old")
        r = self.run_cli("", **self.as_dev())
        self.assertEqual(r.stdout.strip(), "🤖 Dev")
        self.assertEqual(sl.read_entry(self.scope, "dev-2")["title"], "")
        self.assertIn("tab rename tab-dev-2 🤖 Dev", self.calls())

    def test_title_is_data_not_shell(self):
        sl.write_entry(self.scope, "dev-2", "dev", None, "")
        marker = Path(self.tmp.name) / "pwned"
        r = self.run_cli(f"$(touch {marker}); `touch {marker}`", **self.as_dev())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(marker.exists())

    def test_non_manager_cannot_relabel_someone_else(self):
        sl.write_entry(self.scope, "dev-1", "dev", 1, "keep")
        r = self.run_cli("--agent", "dev-1", "hijack", **self.as_dev())
        self.assertEqual(r.returncode, 2)
        self.assertIn("only the Manager may relabel another agent", r.stderr)
        self.assertEqual(sl.read_entry(self.scope, "dev-1")["title"], "keep")
        self.assertEqual(self.calls(), [])

    def test_non_manager_may_name_itself_with_agent(self):
        sl.write_entry(self.scope, "dev-2", "dev", None, "")
        r = self.run_cli("--agent", "dev-2", "me", **self.as_dev())
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "🤖 Dev · me"))

    def test_goal_manager_finds_entry_in_a_scope_home(self):
        sl.write_entry(self.scope, "dev-1", "dev", 1, "")
        r = self.run_cli("--agent", "dev-1", "TAB-09", SQUAD_NAME="mgr", SQUAD_ROLE="manager", GOAL_DIR=str(self.goal))
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "🤖 Dev 1 · TAB-09"), r.stderr)
        self.assertIn("tab rename tab-dev-1 🤖 Dev 1 · TAB-09", self.calls())
        self.assertEqual(sl.read_entry(self.scope, "dev-1")["title"], "TAB-09")

    def test_manager_lookup_none_or_ambiguous_exits_1(self):
        mgr = dict(SQUAD_NAME="mgr", SQUAD_ROLE="manager")
        self.assertEqual(self.run_cli("--agent", "dev-1", "x", **mgr).returncode, 1)
        sl.write_entry(self.scope, "dev-1", "dev", 1, "")
        other = self.squad / "scopes" / "s2"
        sl.write_entry(other, "dev-1", "dev", 1, "")
        r = self.run_cli("--agent", "dev-1", "x", **mgr)
        self.assertEqual(r.returncode, 1)
        self.assertIn("several", r.stderr)
        sl.write_entry(self.squad / "scopes" / "_done", "dev-1", "dev", 1, "")  # _done is not searched
        (other / "labels" / "dev-1.json").unlink()
        self.assertEqual(self.run_cli("--agent", "dev-1", "x", **mgr).returncode, 0)

    def test_init_renames_newly_numbered_peer_and_prints_only_new_label(self):
        sl.write_entry(self.scope, "dev-1", "dev", None, "TAB-01")
        r = self.run_cli("--init", "--agent", "dev-2", "--role", "dev", "--title", "TAB-02", SCOPE_DIR=str(self.scope))
        self.assertEqual((r.returncode, r.stdout), (0, "🤖 Dev 2 · TAB-02\n"), r.stderr)
        self.assertEqual(self.calls()[1:], ["agent get dev-1", "tab rename tab-dev-1 🤖 Dev 1 · TAB-01"])
        self.assertEqual(self.calls()[0], "agent list")
        self.assertEqual(sl.read_entry(self.scope, "dev-2")["number"], 2)

    def test_init_first_agent_has_no_number_and_no_tab_call(self):
        r = self.run_cli("--init", "--agent", "dev-1", "--role", "dev", SCOPE_DIR=str(self.scope))
        self.assertEqual(r.stdout, "🤖 Dev\n")
        self.assertEqual(self.calls(), ["agent list"])

    def test_outside_herdr_updates_store_and_calls_no_herdr(self):
        sl.write_entry(self.scope, "dev-2", "dev", None, "")
        env = self.as_dev(HERDR_ENV="0")
        r = self.run_cli("quiet", **env)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "🤖 Dev · quiet"))
        r = self.run_cli("--init", "--agent", "dev-3", "--role", "dev", **env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_failing_rename_warns_and_exits_0_with_store_written(self):
        sl.write_entry(self.scope, "dev-2", "dev", None, "")
        r = self.run_cli("t", FAIL_RENAME="1", **self.as_dev())
        self.assertEqual(r.returncode, 0)
        self.assertIn("warning", r.stderr)
        self.assertEqual(sl.read_entry(self.scope, "dev-2")["title"], "t")

    def test_bad_agent_name_is_refused(self):
        r = self.run_cli("--agent", "../x", "t", SQUAD_NAME="mgr", SQUAD_ROLE="manager", SCOPE_DIR=str(self.scope))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.scope.parent / "x.json").exists())


if __name__ == "__main__":
    unittest.main()
