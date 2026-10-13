"""squad-retire: closes only the retired agent, even when the PO has merged several agents into one herdr tab."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
# $PANES holds "<pane> <tab> <agent>" lines. `tab close` kills every pane in the tab (as herdr does, and
# closing a workspace's last tab closes the workspace); `pane close` kills one pane.
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent get")
    row=$(awk -v n="$3" '$3 == n' "$PANES")
    [[ -n $row ]] || { echo '{"error":{"code":"agent_not_found"}}'; exit 1; }
    read -r pane tab _ <<<"$row"
    echo "{\\"result\\":{\\"agent\\":{\\"pane_id\\":\\"$pane\\",\\"tab_id\\":\\"$tab\\"}}}" ;;
  "tab close") awk -v t="$3" '$2 != t' "$PANES" > "$PANES.new"; mv "$PANES.new" "$PANES" ;;
  "pane close") awk -v p="$3" '$1 != p' "$PANES" > "$PANES.new"; mv "$PANES.new" "$PANES" ;;
esac
exit 0
"""


class RetireTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        fake = root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR)
        (fake / "herdr").chmod(0o755)
        self.panes = root / "panes"
        self.log = root / "herdr.log"
        self.env = {**os.environ, "HERDR_ENV": "1", "HERDR_LOG": str(self.log), "PANES": str(self.panes),
                    "PATH": f"{fake}:{os.environ['PATH']}"}

    def tearDown(self):
        self.tmp.cleanup()

    def retire(self, name, *args):
        return subprocess.run([str(BIN / "squad-retire"), name, "--no-notes", *args], env=self.env,
                              text=True, capture_output=True, timeout=20)

    def survivors(self):
        return [line.split()[2] for line in self.panes.read_text().splitlines()]

    def test_retire_in_own_tab_closes_that_agent(self):
        self.panes.write_text("p1 t1 mgr\np2 t2 tl\np3 t3 dev\n")
        r = self.retire("dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.survivors(), ["mgr", "tl"])

    def test_retire_leaves_agents_sharing_its_tab_alone(self):
        # The PO merged the Manager and Tech Lead panes into the dev's tab; closing the tab killed all three.
        self.panes.write_text("p1 t1 mgr\np2 t1 tl\np3 t1 dev\n")
        r = self.retire("dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.survivors(), ["mgr", "tl"])

    def test_unknown_agent_is_an_error_and_closes_nothing(self):
        self.panes.write_text("p1 t1 mgr\n")
        r = self.retire("ghost")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.survivors(), ["mgr"])


if __name__ == "__main__":
    unittest.main()
