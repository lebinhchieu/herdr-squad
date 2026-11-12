"""squad-tree (ticket 02): the data of the /squads pane. Golden against the committed fixtures, read-only, discovery,
facts equal the board's, light rows, one herdr call, next-step rules, broken files, command texts run for real.

    python3 tests/test_squadtree.py --regen     rewrite hooks/squads/fixtures/tree.json and tree-herdr-down.json
"""
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from squadtest import BIN, ROOT, clean_env

sys.path.insert(0, str(BIN))
sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures" / "squads-tree"))
import build  # noqa: E402
import squadboard  # noqa: E402
import squadboard_list as L  # noqa: E402
import squadcommands  # noqa: E402
import squadtree  # noqa: E402

CLI = str(BIN / "squad-tree")
FIX = ROOT / "hooks" / "squads" / "fixtures"
POSIX = os.name != "nt"
COMMAND_KEYS = {"id", "label", "text", "changes", "runs_by", "group", "state", "reason", "placeholder", "when"}


class Scratch:
    """The scratch repo plus a stub herdr (readable or not) on PATH."""

    def __init__(self, up=True):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.stub = Path(tempfile.mkdtemp())
        self.repo = build.build_repo(self.root)
        build.herdr_stub(self.stub, up)

    def env(self, **extra):
        return clean_env(PATH=str(self.stub) + os.pathsep + str(BIN) + os.pathsep + os.environ["PATH"], **extra)

    def run(self, *args, cwd=None, env=None, check=True):
        r = subprocess.run([sys.executable, CLI, *args], capture_output=True, text=True, encoding="utf-8",
                           cwd=str(cwd or self.repo), env=env or self.env())
        if check:
            assert r.returncode == 0, r.stderr
        return r

    def tree(self, *args, **kw):
        return json.loads(self.run("--repo", str(self.repo), "--json", *args, **kw).stdout)

    def close(self):
        shutil.rmtree(str(self.root), ignore_errors=True)
        shutil.rmtree(str(self.stub), ignore_errors=True)


def normalise(tree, repo):
    text = json.dumps(tree, indent=2, ensure_ascii=False).replace(str(repo), "/work/repo")
    out = json.loads(text)
    out["generated"] = "2026-11-12T10:00:00Z"
    return out


def nodes(tree):
    for s in tree["squads"]:
        todo = s["goals"] + s["scopes"] + s["done"]["goals"] + s["done"]["scopes"]
        while todo:
            n = todo.pop(0)
            yield s, n
            todo += n.get("scopes", [])


def snapshot(root):
    out = {}
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            st = p.stat()
            out[str(p)] = (st.st_size, st.st_mtime_ns, hashlib.sha1(p.read_bytes()).hexdigest())
    return out


@unittest.skipUnless(POSIX, "the herdr stub is a posix script")
class TreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up, cls.down = Scratch(True), Scratch(False)
        cls.tree_up, cls.tree_down = cls.up.tree(), cls.down.tree()

    @classmethod
    def tearDownClass(cls):
        cls.up.close()
        cls.down.close()

    def test_T1_1_golden_herdr_readable_and_down(self):
        for tree, scratch, name in ((self.tree_up, self.up, "tree.json"), (self.tree_down, self.down, "tree-herdr-down.json")):
            want = json.loads((FIX / name).read_text(encoding="utf-8"))
            self.assertEqual(normalise(tree, scratch.repo), want, name)

    def test_T1_2_read_only_run_changes_nothing(self):
        before = snapshot(self.up.repo)
        self.up.run("--repo", str(self.up.repo), "--json")
        self.assertEqual(snapshot(self.up.repo), before)

    def test_T1_4b_field_shape_and_facts_equal_the_board(self):
        six = {"needs_you", "stuck", "tasks_done", "tasks_total", "agents_working", "last_active"}
        for s, n in nodes(self.tree_up):
            self.assertTrue(n["name_safe"])
            self.assertEqual(set(n["next_step"]), {"rule", "text"})
            for c in n["commands"]:
                self.assertEqual(set(c), COMMAND_KEYS, c["id"])
            if n["facts"] is not None:
                self.assertEqual(set(n["facts"]), six)
            if n["status"] == "done":
                self.assertTrue(n["closed_at"])
            if n["kind"] == "goal":
                self.assertIn("scopes", n)
        # the same numbers as the board's rows for the same input
        squad = squadboard.squads_of(self.up.repo)[1]
        sel = {"squads": [squad], "params": {}}
        for s, n in nodes(self.tree_up):  # herdr: the same stub as the CLI run
            if s["name"] != "plugin" or n["kind"] != "scope" or n["facts"] is None:
                continue
            with unittest.mock.patch.dict(os.environ, self.up.env()):
                row = L.scope_row(squad, Path(n["home"]), n["status"], L._ctx(squad, sel))
            self.assertEqual(n["facts"], {k: row[k] for k in six}, n["name"])
        # a goal row too: goal_row over the same scope rows
        plugin = [x for x in self.tree_up["squads"] if x["name"] == "plugin"][0]
        with unittest.mock.patch.dict(os.environ, self.up.env()):
            ctx = L._ctx(squad, sel)
            for g in plugin["goals"]:
                rows = [L.scope_row(squad, Path(k["home"]), k["status"], ctx) for k in g["scopes"]]
                want = L.goal_row(squad, Path(g["home"]), "open", rows)
                self.assertEqual(g["facts"], {k: want[k] for k in six}, g["name"])

    def test_T1_8_AC1_5_AC1_6_sort_order_and_squad_total(self):
        sc = Scratch(True)
        try:
            base = sc.repo / ".claude/squads/plugin/scopes"
            for name, stamp in (("new1", 0), ("old1", 3600)):  # no stuck; last active differs
                shutil.copytree(str(base / "fix"), str(base / name))
                (base / name / "messages.jsonl").write_text("", encoding="utf-8")
                for f in (base / name).iterdir():
                    t = build.LIVE.timestamp() - stamp
                    os.utime(str(f), (t, t))
            shutil.copytree(str(base / "fix"), str(base / "q1"))
            (base / "q1" / "messages.jsonl").write_text("", encoding="utf-8")
            (base / "q1" / "escalations.md").write_text(build.HEAD + "| 1 | 2026-11-12 | Q? | a | a | none | |\n", encoding="utf-8")
            t = sc.tree()
        finally:
            sc.close()
        plugin = [x for x in t["squads"] if x["name"] == "plugin"][0]
        # needs you first, then more stuck, then newest; the lone rows here share needs you 0 except q1
        self.assertEqual([n["name"] for n in plugin["scopes"]], ["q1", "fix", "new1", "old1"])
        self.assertEqual(plugin["needs_you"], 2 + 1)  # goal g1 (api 2) + lone q1 (1): questions, not rows

    def test_T1_5_light_rows_read_no_inbox_and_no_git(self):
        with unittest.mock.patch.object(L.squadinbox, "snapshot", side_effect=AssertionError("inbox")) as snap, \
                unittest.mock.patch.object(L.squadboard_git, "branch_refs", side_effect=AssertionError("git")):
            # a squad with only closed work: every row is light
            only_done = Scratch(True)
            try:
                for p in (only_done.repo / ".claude/squads/plugin/scopes").iterdir():
                    if p.name != "_done":
                        shutil.rmtree(str(p))
                shutil.rmtree(str(only_done.repo / ".claude/squads/plugin/goals/g1"))
                (only_done.repo / ".claude/squads/plugin/scopes/_done/docs/scope.md").unlink()
                t = squadtree.build({"repo": only_done.repo, "names": ["plugin"]})
            finally:
                only_done.close()
            snap.assert_not_called()
        done = t["squads"][0]["done"]
        self.assertTrue(done["goals"] and done["scopes"])
        for _, n in nodes(t):
            self.assertIsNone(n["facts"], n["name"])

    def test_T1_5b_done_scope_of_an_open_goal_has_facts_and_counts(self):
        g1 = self.tree_up["squads"][1]["goals"][0]
        docs = [s for s in g1["scopes"] if s["name"] == "docs"][0]
        self.assertEqual((docs["status"], docs["facts"]["tasks_total"]), ("done", 2))
        self.assertEqual(g1["facts"]["tasks_total"], sum(s["facts"]["tasks_total"] for s in g1["scopes"]))

    def test_T1_6_herdr_runs_once_and_does_not_leak_between_builds(self):
        calls = []
        real = L._herdr_read

        def spy(sel):
            calls.append(1)
            return real(sel)
        sq = self.up.repo / ".claude/squads"
        shutil.copytree(str(sq / "plugin"), str(sq / "second"))
        try:
            with unittest.mock.patch.object(L, "_herdr_read", spy):
                for _ in range(2):
                    squadtree.build({"repo": self.up.repo, "names": []})
        finally:
            shutil.rmtree(str(sq / "second"))
        self.assertEqual(len(calls), 2)  # one per build with two full squads, not one per squad

    def test_T1_3_discovery(self):
        s = self.up
        names = [x["name"] for x in s.tree()["squads"]]
        self.assertEqual(names, ["old-flat", "plugin"])
        flat = s.tree()["squads"][0]
        self.assertEqual((flat["flat"], flat["message"], flat["goals"], flat["scopes"]), (True, "flat squad: not supported", [], []))
        self.assertEqual([(c["id"], c["state"], c["reason"]) for c in flat["commands"]],
                         [("new-work", "wait", "flat layout: squad-start refuses it"), ("close-squad", "ready", None)])
        # SQUAD_DIR set: still both squads; a worktree of the repo finds the main repo's squads
        env = s.env(SQUAD_DIR=str(s.repo / ".claude/squads/plugin"))
        self.assertEqual([x["name"] for x in json.loads(s.run("--json", env=env).stdout)["squads"]], names)
        wt = Path(tempfile.mkdtemp()) / "wt"
        subprocess.run(["git", "worktree", "add", "-q", "-b", "wtb", str(wt)], cwd=str(s.repo), check=True,
                       capture_output=True)
        try:
            out = json.loads(s.run("--json", cwd=wt).stdout)
            self.assertEqual(Path(out["repo"]).resolve(), s.repo)
            self.assertEqual([x["name"] for x in out["squads"]], names)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=str(s.repo), capture_output=True)
        empty = Path(tempfile.mkdtemp())
        try:
            r = s.run("--repo", str(empty), "--json")
            self.assertEqual(json.loads(r.stdout)["squads"], [])
        finally:
            shutil.rmtree(str(empty), ignore_errors=True)
        self.assertEqual(s.run("--repo", str(s.repo / "README.md"), "--json", check=False).returncode, 2)
        self.assertEqual(s.run("--bogus", check=False).returncode, 2)

    def test_T1_10_T1_11_broken_files_and_hostile_text_do_not_crash(self):
        s = Scratch(True)
        try:
            sq = s.repo / ".claude/squads/plugin/scopes"
            (sq / "api" / "scope.md").write_bytes(b"**brief \x1b[31mred\x1b[0m \x07 bell**\n\xff\xfe\ngoal: g1\n")
            (sq / "ui" / "messages.jsonl").unlink()
            (sq / "fix" / "scope.md").unlink()
            (sq / "a b").mkdir()
            (sq / "x;rm").mkdir()
            t = s.tree()
        finally:
            s.close()
        plugin = [x for x in t["squads"] if x["name"] == "plugin"][0]
        api = [n for g in plugin["goals"] for n in g["scopes"] if n["name"] == "api"][0]
        self.assertIn("red", api["brief"])
        ui = [n for g in plugin["goals"] for n in g["scopes"] if n["name"] == "ui"][0]
        self.assertIn("messages.jsonl", ui["unknown"])
        fix = [n for n in plugin["scopes"] if n["name"] == "fix"][0]
        self.assertIn("scope.md", fix["unknown"])
        bad = {n["name"]: n for n in plugin["scopes"]}
        for name in ("a b", "x;rm"):
            self.assertEqual((bad[name]["name_safe"], bad[name]["commands"]), (False, []))
        self.assertTrue(bad["fix"]["name_safe"])

    def test_T1_12_the_copied_texts_run_for_real(self):
        s = self.up
        before = snapshot(s.repo)
        env = s.env(SQUAD_WATCHDOG="off")
        want = {"inbox", "watchdog", "report-status", "close-scope", "resume"}
        ran = set()
        for _, n in nodes(self.tree_up):
            if n["name"] != "ui":
                continue
            for c in n["commands"]:
                if c["id"] in want:
                    argv = shlex.split(c["text"]) + (["--dry-run"] if c["id"] == "resume" else [])
                    r = subprocess.run(argv, cwd=str(s.repo), capture_output=True, text=True, encoding="utf-8", env=env)
                    ok = (0, 3, 4) if c["id"] == "report-status" else (0,)  # status answers fresh, stale or missing
                    self.assertIn(r.returncode, ok, "%s: %s" % (c["text"], r.stderr))
                    ran.add(c["id"])
        self.assertEqual(ran, want)
        self.assertEqual(snapshot(s.repo), before)  # inbox list, report status, dry runs wrote nothing
        # not run (they write, start or never exit): every flag of the text is in the tool's usage
        for _, n in nodes(self.tree_up):
            for c in n["commands"]:
                if c["id"] in ("board", "report", "sleep", "new-work", "new-scope", "retire", "close-goal", "close-squad"):
                    tool = shlex.split(c["text"])[0]
                    usage = subprocess.run([tool, "--help"], capture_output=True, text=True, encoding="utf-8", env=env)
                    text = usage.stdout + usage.stderr
                    for flag in [w for w in shlex.split(c["text"]) if w.startswith("--")]:
                        self.assertIn(flag, text, "%s: %s" % (c["text"], flag))


class NextStepTests(unittest.TestCase):
    def step(self, **f):
        facts = dict(needs_you=0, stuck=0, tasks_done=1, tasks_total=3, agents_working=1, last_active=None)
        facts.update(f)
        return squadtree.next_step({"kind": "scope", "status": "open", "facts": facts, "scopes": []})

    def test_T1_8_one_test_per_rule_and_the_order_cases(self):
        r = lambda **f: self.step(**f)["rule"]  # noqa: E731
        self.assertEqual(r(needs_you=None), 1)
        self.assertEqual(self.step(agents_working=None)["text"], "Cannot read herdr: open board")
        self.assertEqual(r(needs_you=1, stuck=2), 2)  # AC2.1
        self.assertEqual(self.step(needs_you=1)["text"], "Answer 1 question")
        self.assertEqual(r(stuck=2), 3)
        self.assertEqual(r(tasks_done=3), 4)
        self.assertEqual(r(agents_working=0), 5)
        self.assertEqual(r(tasks_total=0, agents_working=2), 6)  # swap case: no tasks beats working
        self.assertEqual(r(), 7)
        goal = {"kind": "goal", "status": "open", "facts": None, "scopes": [{"status": "done"}]}
        self.assertEqual(squadtree.next_step(goal)["rule"], 8)
        self.assertEqual(squadtree.next_step({"kind": "scope", "status": "done", "facts": None})["rule"], 9)

    def test_T1_8_rule_1_is_not_fired_by_unknown_tickets(self):
        node = {"kind": "scope", "status": "open", "unknown": ["tickets"], "scopes": [],
                "facts": dict(needs_you=0, stuck=0, tasks_done=0, tasks_total=0, agents_working=0, last_active=None)}
        self.assertEqual(squadtree.next_step(node)["text"], "No tasks yet")

    def test_T1_9h_goal_names_the_scope_with_most_questions_first_in_order(self):
        sc = lambda n, q: {"name": n, "status": "open", "facts": {"needs_you": q}}  # noqa: E731
        goal = {"kind": "goal", "status": "open", "scopes": [sc("b", 3), sc("a", 3), sc("c", 1)],
                "facts": dict(needs_you=7, stuck=0, tasks_done=0, tasks_total=1, agents_working=0, last_active=None)}
        self.assertEqual(squadtree.next_step(goal)["text"], "Answer 7 questions in b")


if __name__ == "__main__":
    if "--regen" in sys.argv:
        for up, name in ((True, "tree.json"), (False, "tree-herdr-down.json")):
            sc = Scratch(up)
            try:
                data = normalise(sc.tree(), sc.repo)
            finally:
                sc.close()
            (FIX / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        sys.exit(0)
    unittest.main()
