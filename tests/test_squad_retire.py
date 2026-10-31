"""squad-retire: closes only the retired agent, even when the PO has merged several agents into one herdr tab."""
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

    def test_retire_leaves_agents_sharing_its_tab_alone(self):
        # The PO merged the Manager and Tech Lead panes into the dev's tab; closing the tab killed all three.
        self.panes.write_text("p1 t1 mgr\np2 t1 tl\np3 t1 dev\n", encoding="utf-8")
        r = self.retire("dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.survivors(), ["mgr", "tl"])

    def test_unknown_agent_is_an_error_and_closes_nothing(self):
        self.panes.write_text("p1 t1 mgr\n", encoding="utf-8")
        r = self.retire("ghost")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.survivors(), ["mgr"])


if __name__ == "__main__":
    unittest.main()
