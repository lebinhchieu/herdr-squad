"""squad-retire: closes only the retired agent, even when the PO has merged several agents into one herdr tab."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import winlaunch
from squadtest import BIN, clean_env, fake_herdr


class RetireTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        fake = root / "fakebin"
        fake.mkdir()
        fake_herdr(fake)
        self.panes = root / "panes"
        self.log = root / "herdr.log"
        self.env = clean_env(HERDR_ENV="1", HERDR_LOG=str(self.log), PANES=str(self.panes), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def retire(self, name, *args):
        return winlaunch.run_script(BIN / "squad-retire", [name, "--no-notes", *args], env=self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=20)

    def survivors(self):
        return [line.split()[2] for line in self.panes.read_text(encoding="utf-8").splitlines()]

    def test_retire_in_own_tab_closes_that_agent(self):
        self.panes.write_text("p1 t1 mgr\np2 t2 tl\np3 t3 dev\n", encoding="utf-8")
        r = self.retire("dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.survivors(), ["mgr", "tl"])

    def test_retire_deletes_the_agents_scratch_dir_and_squad_tmp_rm_stays_inside_scratch(self):
        # tmp-scratch 02/04: tools delete scratch, so no agent runs rm (Claude Code's dangerous-rm check prompts on it)
        tmp = [str(BIN / "squad-tmp")]
        mk = lambda *a: subprocess.run(["python3", *tmp, *a], env=self.env, text=True, capture_output=True)
        scratch = Path(mk("make", "dev").stdout.strip())
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (scratch / "big").mkdir()
        (scratch / "link").symlink_to(outside)
        env = {**self.env, "SQUAD_TMP": str(scratch)}
        rm = lambda *a: subprocess.run(["python3", *tmp, "rm", *a], env=env, text=True, capture_output=True).returncode
        self.assertEqual(rm(str(scratch / "big"), str(scratch / "link")), 0)
        self.assertEqual(sorted(p.name for p in scratch.iterdir()), [])
        self.assertTrue(outside.is_dir())  # the link went, not its target
        for bad in (str(outside), str(scratch), str(scratch / ".." / "dev")):
            self.assertEqual(rm(bad), 2, bad)
        self.assertTrue(outside.is_dir() and scratch.is_dir())
        self.assertEqual(mk("clean", "..").returncode, 2)
        self.panes.write_text("p3 t3 dev\n", encoding="utf-8")
        self.assertEqual(self.retire("dev").returncode, 0)
        self.assertFalse(scratch.exists())

    def test_retire_leaves_agents_sharing_its_tab_alone(self):
        # The PO merged the Manager and Tech Lead panes into the dev's tab; closing the tab killed all three.
        self.panes.write_text("p1 t1 mgr\np2 t1 tl\np3 t1 dev\n", encoding="utf-8")
        r = self.retire("dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.survivors(), ["mgr", "tl"])

    def test_retire_appends_a_retire_event_and_a_log_failure_only_warns(self):
        self.panes.write_text("p1 t1 mgr\np3 t3 dev\n", encoding="utf-8")
        home = Path(self.tmp.name) / "scope"
        home.mkdir()
        (home / "roster.md").write_text("| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
                                        "| dev | dev | s1 | x | live | sid |\n", encoding="utf-8")
        self.env["SCOPE_DIR"] = str(home)
        self.assertEqual(self.retire("dev").returncode, 0)
        [ev] = [json.loads(l) for l in (home / "usage-events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((ev["rule"], ev["agent"], ev["role"], ev["scope"]), ("retire", "dev", "dev", "s1"))
        self.panes.write_text("p3 t3 dev\n", encoding="utf-8")
        (home / "usage-events.jsonl").unlink()
        (home / "usage-events.jsonl").mkdir()  # not writable as a file
        r = self.retire("dev")
        self.assertEqual(r.returncode, 0)
        self.assertIn("could not write the retire event", r.stderr)

    def test_unknown_agent_is_an_error_and_closes_nothing(self):
        self.panes.write_text("p1 t1 mgr\n", encoding="utf-8")
        r = self.retire("ghost")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.survivors(), ["mgr"])


if __name__ == "__main__":
    unittest.main()
