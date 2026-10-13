"""squad-board-start: finds or starts the board tab, prints its URL, never starts a second board.

The fake `herdr` keeps tabs in a JSON file and has the shapes of the real one (captured in
evidence/BRD-22/real-run.txt): `tab list` -> {"result":{"tabs":[...]}}, `tab create` -> root_pane + tab,
`pane list` -> {"result":{"panes":[...]}}, `pane read` -> plain text."""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-board-start"
FAKE_HERDR = r'''#!/usr/bin/env python3
import json, os, re, sys
d = os.environ["FAKE_DIR"]
state_path = os.path.join(d, "state.json")
state = json.load(open(state_path))
a = sys.argv[1:]
open(os.path.join(d, "calls.log"), "a").write(" ".join(a) + "\n")

def opt(name):
    return a[a.index(name) + 1] if name in a else None

def save():
    json.dump(state, open(state_path, "w"))

def out(result):
    print(json.dumps({"result": result}))

if a[:2] == ["tab", "list"]:
    ws = opt("--workspace")
    out({"tabs": [t for t in state["tabs"] if ws is None or t["workspace_id"] == ws], "type": "tab_list"})
elif a[:2] == ["tab", "create"]:
    ws = opt("--workspace") or "wFocus"
    state["n"] += 1
    tab = {"label": opt("--label"), "tab_id": "%s:t%d" % (ws, state["n"]), "workspace_id": ws}
    state["tabs"].append(tab)
    state["panes"].append({"pane_id": "%s:p%d" % (ws, state["n"]), "tab_id": tab["tab_id"], "workspace_id": ws})
    save()
    out({"tab": tab, "root_pane": {"pane_id": "%s:p%d" % (ws, state["n"])}})
elif a[:2] == ["tab", "close"]:
    state["tabs"] = [t for t in state["tabs"] if t["tab_id"] != a[2]]
    state["panes"] = [p for p in state["panes"] if p["tab_id"] != a[2]]
    save()
elif a[:2] == ["pane", "list"]:
    ws = opt("--workspace")
    out({"panes": [p for p in state["panes"] if ws is None or p["workspace_id"] == ws]})
elif a[:2] == ["pane", "run"]:
    state["n"] += 1
    state["runs"].append(a[3])
    if os.environ.get("FAKE_BOARD_SILENT") != "1":
        open(os.path.join(d, "screen-" + a[2]), "w").write(
            "$ %s\nsquad-board: http://127.0.0.1:7420/?token=Tok_%d-xY\n" % (a[3], state["n"]))
    else:
        open(os.path.join(d, "screen-" + a[2]), "w").write("$ %s\nPermission denied: port 7420\n" % a[3])
    save()
elif a[:2] == ["pane", "wait-output"]:
    try:
        text = open(os.path.join(d, "screen-" + a[2])).read()
    except OSError:
        text = ""
    sys.exit(0 if re.search(opt("--regex"), text) else 1)
elif a[:2] == ["pane", "read"]:
    try:
        sys.stdout.write(open(os.path.join(d, "screen-" + a[2])).read())
    except OSError:
        pass
else:
    sys.exit(2)
'''


class BoardStartTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = self.root / "proj" / ".claude" / "squads" / "t"
        self.squad.mkdir(parents=True)
        (self.squad / "process.md").write_text("x")
        subprocess.run(["git", "init", "-q", str(self.root / "proj")], check=True)
        self.fake = self.root / "fake"
        self.fake.mkdir()
        (self.fake / "herdr").write_text(FAKE_HERDR)
        (self.fake / "herdr").chmod(0o755)
        self.set_state({"n": 0, "tabs": [], "panes": [], "runs": []})
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR", "HERDR"))}
        self.env.update(HERDR_ENV="1", HERDR_WORKSPACE_ID="wA", SQUAD_DIR=str(self.squad), FAKE_DIR=str(self.fake),
                        PATH=f"{self.fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def set_state(self, state):
        (self.fake / "state.json").write_text(json.dumps(state))

    def state(self):
        return json.loads((self.fake / "state.json").read_text())

    def run_it(self, *args, env=None):
        return subprocess.run([str(SCRIPT), *args], env=env or self.env, text=True, capture_output=True,
                              timeout=60, cwd=self.root / "proj")

    def boards(self, ws="wA"):
        return [t for t in self.state()["tabs"] if t["label"] == "board" and t["workspace_id"] == ws]

    def test_not_found_starts_one_board_tab_and_prints_only_the_url(self):
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"^http://127\.0\.0\.1:7420/\?token=Tok_\d+-xY\n$")
        self.assertEqual(len(self.boards()), 1)
        calls = (self.fake / "calls.log").read_text()
        self.assertIn("--no-focus", calls)
        self.assertIn("--workspace wA", calls)
        self.assertIn(f"--cwd {os.path.realpath(self.root / 'proj')}", calls)

    def test_the_command_runs_this_plugins_board_with_the_squad_dir_quoted(self):
        spaced = self.root / "a b" / ".claude" / "squads" / "t"
        spaced.mkdir(parents=True)
        (spaced / "process.md").write_text("x")
        self.env["SQUAD_DIR"] = str(spaced)
        self.assertEqual(self.run_it().returncode, 0)
        run = self.state()["runs"][0]
        self.assertTrue(run.startswith("SQUAD_DIR="), run)
        self.assertIn(os.path.realpath(spaced).replace(" ", "\\ "), run)
        self.assertTrue(run.endswith("/bin/squad-board"), run)

    def test_found_prints_the_same_url_and_starts_nothing(self):
        first = self.run_it().stdout
        second = self.run_it()
        self.assertEqual((second.returncode, second.stdout), (0, first))
        self.assertEqual(len(self.boards()), 1)
        self.assertEqual(len(self.state()["runs"]), 1)

    def test_restart_closes_the_old_tab_and_prints_a_new_url(self):
        first = self.run_it().stdout
        r = self.run_it("--restart")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(r.stdout, first)
        self.assertRegex(r.stdout, r"^http://127\.0\.0\.1:7420/\?token=\S+\n$")
        self.assertEqual(len(self.boards()), 1)
        self.assertIn("tab close wA:t1", (self.fake / "calls.log").read_text())

    def test_a_board_that_never_prints_a_url_exits_1_and_shows_the_pane(self):
        self.env["FAKE_BOARD_SILENT"] = "1"
        r = self.run_it()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("Permission denied: port 7420", r.stderr)

    def test_outside_herdr_exits_1(self):
        self.env["HERDR_ENV"] = "0"
        r = self.run_it()
        self.assertEqual((r.returncode, r.stdout), (1, ""))
        self.assertIn("HERDR_ENV", r.stderr)
        self.assertFalse((self.fake / "calls.log").exists())

    def test_only_the_callers_workspace_counts(self):
        self.set_state({"n": 1, "runs": [], "tabs": [{"label": "board", "tab_id": "wB:t1", "workspace_id": "wB"}],
                        "panes": [{"pane_id": "wB:p1", "tab_id": "wB:t1", "workspace_id": "wB"}]})
        (self.fake / "screen-wB:p1").write_text("squad-board: http://127.0.0.1:7421/?token=other\n")
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("other", r.stdout)
        self.assertEqual(len(self.boards("wA")), 1)
        self.assertEqual(len(self.boards("wB")), 1)

    def test_a_caller_workspace_with_its_own_board_reuses_it_not_the_other(self):
        self.set_state({"n": 2, "runs": [], "tabs": [
            {"label": "board", "tab_id": "wB:t1", "workspace_id": "wB"},
            {"label": "board", "tab_id": "wA:t2", "workspace_id": "wA"}],
            "panes": [{"pane_id": "wB:p1", "tab_id": "wB:t1", "workspace_id": "wB"},
                      {"pane_id": "wA:p2", "tab_id": "wA:t2", "workspace_id": "wA"}]})
        (self.fake / "screen-wB:p1").write_text("squad-board: http://127.0.0.1:7421/?token=other\n")
        (self.fake / "screen-wA:p2").write_text("squad-board: http://127.0.0.1:7420/?token=mine\n")
        r = self.run_it()
        self.assertEqual((r.returncode, r.stdout), (0, "http://127.0.0.1:7420/?token=mine\n"))

    def test_the_token_is_not_written_to_a_file_or_the_call_log(self):
        r = self.run_it()
        token = re.search(r"token=(\S+)", r.stdout).group(1)
        for f in list(self.squad.rglob("*")) + [self.fake / "calls.log"]:
            if f.is_file():
                self.assertNotIn(token, f.read_text(), f)

    def test_no_squad_folder_is_an_error(self):
        self.env["SQUAD_DIR"] = str(self.root / "nowhere")
        r = self.run_it()
        self.assertEqual(r.returncode, 1)
        self.assertIn("no squad folder", r.stderr)


if __name__ == "__main__":
    unittest.main()
