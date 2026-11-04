"""squad-board Files list (ticket 14, business AC T14.AC1-AC6 and technical TA1-TA6). Fixture: ticket 02, extended in a temp copy."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import board_fixtures as bf  # noqa: E402
import squadboard  # noqa: E402
import squadboard_files as sf  # noqa: E402
from test_squadboard_page import CHROME  # noqa: E402

ROW = {"name", "kind", "what", "scope", "path", "mtime"}


def put(p, text="x\n"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.fx = bf.copy_fixture(git=False)
        self.squad = squadboard.Squad(self.fx.squad, "fix")
        self.home = self.squad.find("scope", "checkout")
        self.scratch = self.squad.repo_root / ".scratch" / "checkout"
        h = self.home
        put(h / "tasks" / "features.md")
        put(h / "tasks" / "03-x.md")
        put(h / "ui-design" / "design-v5.md")
        put(h / "ui-design" / "proto-a.html", "<p>hi</p>")
        put(h / "ui-design" / "img" / "shot.png")  # an image is not listed
        put(h / "promote.md")
        put(h / "evidence" / "03" / "qa-w.md")
        put(h / "roles" / "fix-dev-03.notes.md")   # not listed
        put(h / "inbox.jsonl", "{}\n")             # not listed
        put(self.scratch / "issues" / "03-x" / "evidence.md")
        put(self.squad.path / "adr" / "0001.md")   # an ADR is not listed

    def tearDown(self):
        bf.cleanup(self.fx)

    def sel(self, kind="scope", name="checkout"):
        return {"squad": self.squad, "kind": kind, "name": name, "home": self.squad.find(kind, name)}


class Reader(Base):
    def test_T14_AC1_TA1_TA2_scope_lists_artifacts_prototype_promote_with_row_shape_and_nothing_else(self):
        r = sf.read(self.sel())
        self.assertEqual((r["quality"], r["unknown"]), ("exact", []))
        rows = r["data"]["rows"]
        self.assertTrue(all(set(x) == ROW and isinstance(x["mtime"], int) and x["kind"] in sf.KINDS for x in rows), rows)
        got = {x["name"]: x["kind"] for x in rows}
        self.assertEqual(got["ui-design/proto-a.html"], "prototype")
        self.assertEqual(got["promote.md"], "promote")
        self.assertEqual(got["tasks/features.md"], "other")
        self.assertEqual(got["tasks/03-x.md"], "ticket")
        self.assertEqual(got["ui-design/design-v5.md"], "design")
        self.assertEqual(got["evidence/03/qa-w.md"], "evidence")
        self.assertEqual(got[".scratch/checkout/issues/03-x/evidence.md"], "evidence")
        self.assertEqual(got["escalations.md"], "answer")
        for bad in ("inbox.jsonl", "messages.jsonl", "roles/fix-dev-03.notes.md", "ui-design/img/shot.png"):
            self.assertNotIn(bad, got)
        self.assertFalse([n for n in got if "adr" in n])
        fol = r["data"]["folders"]  # T29.AC1: a separate list, not in rows
        self.assertEqual([x["name"] for x in fol], [".scratch", "fix"])
        self.assertEqual([x["what"] for x in fol], ["Repo tickets folder", "Squad folder"])
        self.assertTrue(all(x["kind"] == "folder" and set(x) == ROW | {"abs"} for x in fol))
        self.assertFalse([x for x in rows if x["kind"] == "folder"])
        for x in rows:  # a listed path is the one /api/file takes
            self.assertTrue((self.squad.path / x["path"]).is_file() or Path(x["path"]).is_file(), x)

    def test_T14_AC4_AC5_live_scope_has_no_report_closed_scope_lists_report_and_data(self):
        live = sf.read(self.sel())["data"]
        self.assertTrue(live["report_expected"] and live["report"] is None and not live["closed"])
        put(self.squad.find("scope", "closed-release") / "report" / "report.html", "<p>r</p>")
        done = sf.read(self.sel(name="closed-release"))["data"]
        self.assertTrue(done["closed"])
        self.assertEqual({r["name"] for r in done["rows"] if r["kind"] in ("report", "data")}, {"report/report.html", "report/data.json"})
        self.assertEqual(done["report"]["name"], "report/report.html")

    def test_T14_TA1_goal_lists_shared_decisions_and_a_symlink_out_of_the_allow_list_is_not_listed(self):
        kinds = {r["name"]: r["kind"] for r in sf.read(self.sel("goal", "alpha"))["data"]["rows"]}
        self.assertEqual(kinds["shared/decisions.md"], "decision")
        outside = Path(tempfile.mkdtemp(prefix="board-out-"))
        try:
            put(outside / "secret.md")
            try:
                (self.home / "tasks" / "leak.md").symlink_to(outside / "secret.md")
                (self.home / "evidence" / "loop").symlink_to(self.home / "evidence")
                (self.home / "ui-design" / "linkdir").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks cannot be created here")
            names = {r["name"] for r in sf.read(self.sel())["data"]["rows"]}  # also proves the loop symlink does not hang
            self.assertNotIn("tasks/leak.md", names)
            self.assertFalse([n for n in names if "linkdir" in n or "loop" in n], names)
        finally:
            for p in sorted(outside.rglob("*"), reverse=True) + [outside]:
                p.rmdir() if p.is_dir() else p.unlink()

    def test_T14_TA5_a_tasks_subfolder_is_not_listed_and_does_not_set_truncated(self):
        put(self.home / "tasks" / "issues" / "01-a.md")
        put(self.home / "tasks" / "issues-tech" / "01.md")
        d = sf.read(self.sel())["data"]
        self.assertFalse(d["truncated"])
        self.assertFalse([r for r in d["rows"] if r["name"].startswith("tasks/issues")])
        self.assertIn("tasks/features.md", [r["name"] for r in d["rows"]])

    def test_T14_TA5_cap_sets_truncated_and_a_missing_folder_is_unknown(self):
        with mock.patch.object(sf, "MAX_ROWS", 3):
            d = sf.read(self.sel())["data"]
        self.assertEqual((len(d["rows"]), d["truncated"]), (3, True))
        self.assertFalse(sf.read(self.sel())["data"]["truncated"])
        gone = dict(self.sel(), home=self.home / "nope")
        self.assertEqual(sf.read(gone), {"data": None, "quality": "unknown", "unknown": ["files"]})

    def test_T29_AC4_AC5_AC9_TA4_TA5_ticket_rows_of_this_scope_only_with_title_and_each_file_once(self):
        mine = self.squad.repo_root / ".scratch" / "checkout-tasks"  # the fixture scope.md declares `tickets: checkout-tasks`
        put(mine / "issues" / "10-a.md", "# 10 First ticket\nStatus: ready\n")
        put(mine / "spec.md", "# Spec\n")
        put(self.squad.repo_root / ".scratch" / "other" / "issues" / "01-z.md", "# Z\n")
        put(self.home / "tasks" / "03-x.md", "# 03 Plan ticket\n")
        rows = sf.read(self.sel())["data"]["rows"]
        by = {r["name"]: r for r in rows}
        self.assertEqual(by[".scratch/checkout-tasks/issues/10-a.md"]["kind"], "ticket")  # AC4
        self.assertEqual(by[".scratch/checkout-tasks/issues/10-a.md"]["what"], "First ticket")  # AC11 title
        self.assertEqual(by[".scratch/checkout-tasks/spec.md"]["kind"], "ticket")  # AC9
        self.assertFalse([n for n in by if "/other/" in n])  # AC5
        paths = [r["path"] for r in rows]
        self.assertEqual(len(paths), len(set(paths)))  # TA5: one row per file

    def test_T29_AC4_flat_scope_tasks_list_as_tickets_with_title_when_no_ticket_folder(self):
        h = self.squad.find("scope", "closed-release")
        put(h / "tasks" / "01.md", "# 01 Repro: a pane\nStatus: done (ok)\n")
        rows = {r["name"]: r for r in sf.read(self.sel(name="closed-release"))["data"]["rows"]}
        self.assertEqual((rows["tasks/01.md"]["kind"], rows["tasks/01.md"]["what"]), ("ticket", "Repro: a pane"))

    def test_T29_AC6_AC3_TA3_folders_quiet_when_scratch_missing_or_linked_out_and_cap_holds(self):
        import shutil
        sc = self.squad.repo_root / ".scratch"
        out = Path(tempfile.mkdtemp(prefix="board-out-"))
        try:
            shutil.rmtree(sc)
            self.assertEqual([f["name"] for f in sf.read(self.sel())["data"]["folders"]], ["fix"])  # no .scratch: one row, no error
            try:
                sc.symlink_to(out, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks cannot be created here")
            self.assertEqual([f["name"] for f in sf.read(self.sel())["data"]["folders"]], ["fix"])  # link out: no row
            sc.unlink()
            sc.mkdir()
            with mock.patch.object(sf, "MAX_ROWS", 3):
                d = sf.read(self.sel())["data"]
            self.assertEqual([f["name"] for f in d["folders"]], [".scratch", "fix"])  # not counted in the cap
        finally:
            out.rmdir()

    def test_T14_TA6_listing_writes_nothing(self):
        def snap():
            return sorted((str(p), p.stat().st_mtime_ns, hashlib.sha1(p.read_bytes()).hexdigest()) for p in self.squad.path.rglob("*") if p.is_file())
        before = snap()
        sf.read(self.sel())
        sf.read(self.sel("goal", "alpha"))
        self.assertEqual(before, snap())


class Served(Base):
    """The real server: the list route, the file route's refusals (AC3) and the sandbox (AC6)."""

    def setUp(self):
        super().setUp()
        self.srv = squadboard.BoardServer(0, [self.squad], {})
        self.srv.routes, _ = squadboard.load_routes()
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:%d" % self.srv.port

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def get(self, url):
        try:
            with urllib.request.urlopen(self.base + url, timeout=20) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()

    def test_T14_TA3_route_lists_and_each_listed_path_opens_through_the_file_route(self):
        code, _, body = self.get("/api/files?squad=fix&scope=checkout")
        self.assertEqual(code, 200)
        j = json.loads(body)
        self.assertEqual(j["schema_version"], 1)
        for r in j["data"]["rows"]:
            c, _, _ = self.get("/api/file?squad=fix&path=" + urllib.request.quote(r["path"]))
            self.assertEqual(c, 200, r)

    def test_T14_AC3_outside_paths_and_dotdot_answer_a_message_and_no_content(self):
        secret = Path(tempfile.mkdtemp(prefix="board-out-")) / "secret.txt"
        try:
            secret.write_text("TOP-SECRET", encoding="utf-8")
            for p in (str(secret), "../../../../../../../../../../.." + str(secret), "scopes/checkout/../../../../../../../../.." + str(secret)):
                code, _, body = self.get("/api/file?squad=fix&path=" + urllib.request.quote(p))
                self.assertIn(code, (403, 404), p)
                self.assertNotIn(b"TOP-SECRET", body)
                self.assertIn("error", json.loads(body))
        finally:
            secret.unlink()
            secret.parent.rmdir()

    @unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
    def test_T14_AC6_TA4_an_agent_page_is_sandboxed_and_cannot_call_the_board_data(self):
        put(self.home / "ui-design" / "evil.html",
            "<body id=b>pending<script>fetch('/api/state?squad=fix&scope=checkout').then(()=>{document.getElementById('b').textContent='LEAKED'})"
            ".catch(()=>{document.getElementById('b').textContent='BLOCKED'})</script>")
        code, hdr, _ = self.get("/api/file?squad=fix&path=scopes/checkout/ui-design/evil.html")
        csp = hdr["Content-Security-Policy"]
        self.assertTrue(code == 200 and csp.startswith("sandbox") and "allow-same-origin" not in csp, csp)
        seen = []
        orig = squadboard.Handler.do_GET

        def spy(h):
            seen.append(h.path)
            return orig(h)
        with mock.patch.object(squadboard.Handler, "do_GET", spy), tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--user-data-dir=" + prof, "--virtual-time-budget=4000",
                                "--dump-dom", self.base + "/api/file?squad=fix&path=scopes/checkout/ui-design/evil.html"],
                               capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-300:])
        self.assertIn('<body id="b">pending<script>', r.stdout)  # the script never ran (a run would have replaced the body text)
        self.assertEqual([p for p in seen if p.startswith("/api/state")], [])


if __name__ == "__main__":
    unittest.main()
