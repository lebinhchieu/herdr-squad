"""squad-board CLI and server (ticket 03). Tests are named for the business AC (T03.ACn) or technical risk they cover.

A tiny temp squad stands in for the fixture of ticket 02. Nothing here starts a browser or uses a fixed port."""
import contextlib
import hashlib
import io
import json
import os
import socket
import tempfile
import threading
import unittest
import unittest.mock
import urllib.error
import urllib.request
from pathlib import Path

import inproc
from squadtest import BIN, clean_env

import sys
sys.path.insert(0, str(BIN))
import squadboard  # noqa: E402


def make_squad(repo, name="t", flat=False):
    sq = Path(repo) / ".claude" / "squads" / name
    sq.mkdir(parents=True)
    (sq / "process.md").write_text("x", encoding="utf-8")
    if flat:
        (sq / "roster.md").write_text("r", encoding="utf-8")
        return sq
    for d in ("scopes/alpha", "scopes/_done/old", "goals/g1"):
        (sq / d).mkdir(parents=True)
    (sq / "scopes" / "alpha" / "note.md").write_text("hello", encoding="utf-8")
    (sq / "scopes" / "alpha" / "page.html").write_text("<script>1</script>", encoding="utf-8")
    return sq


def get(url, host=None):
    req = urllib.request.Request(url, headers={"Host": host} if host else {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def listening(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.squad = make_squad(self.repo)
        self.env = clean_env(SQUAD_DIR=str(self.squad))
        patch = unittest.mock.patch.dict(os.environ, self.env, clear=True)  # direct main() calls see the temp squad
        patch.start()
        self.addCleanup(patch.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, env=None):
        return inproc.run("squad-board", list(args), env=env or self.env)

    def serve(self, squads=None, routes=None, initial=None):
        squads = squads or squadboard.find_squads([], env=self.env)
        srv = squadboard.BoardServer(0, squads, initial, routes if routes is not None else {})
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(lambda: (srv.shutdown(), srv.server_close(), t.join(5)))
        return srv, "http://127.0.0.1:%d" % srv.port


class CliTest(Base):
    def test_T03_AC9_help_lists_every_flag(self):
        r = self.cli("--help")
        self.assertEqual(r.returncode, 0)
        for flag in ("--squad", "--goal", "--scope", "--port", "--no-open"):
            self.assertIn(flag, r.stdout)

    def test_T03_AC1_AC2_opens_browser_unless_no_open_and_prints_url(self):
        for extra, opened in (([], 1), (["--no-open"], 0)):
            urls, stop = [], threading.Event()
            stop.set()  # the server ends as soon as it runs
            code = squadboard.main(["--port", "0"] + extra, open_browser=urls.append, stop=stop)
            self.assertEqual(code, 0)
            self.assertEqual(len(urls), opened)

    def test_T03_AC2_port_busy_is_a_message_and_nonzero(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            r = self.cli("--no-open", "--port", str(s.getsockname()[1]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("busy", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_T03_AC2_port_n_answers_on_n(self):
        port = free_port()
        stop = threading.Event()
        t = threading.Thread(target=lambda: squadboard.main(["--no-open", "--port", str(port)], stop=stop), daemon=True)
        t.start()
        self.addCleanup(lambda: (stop.set(), t.join(5)))
        for _ in range(50):
            if listening(port):
                break
            threading.Event().wait(0.1)
        self.assertEqual(get("http://127.0.0.1:%d/api/squads" % port)[0], 200)

    def test_T03_AC3_several_squads_none_named_refuses_and_lists(self):
        make_squad(self.repo, "u")
        env = clean_env()
        env["SQUAD_DIR"] = ""
        cwd = os.getcwd()
        os.chdir(self.repo)  # no git here: the repo root falls back to the cwd
        try:
            r = self.cli("--no-open", "--port", "0", env=env)
        finally:
            os.chdir(cwd)
        self.assertEqual(r.returncode, 2)
        self.assertIn("t", r.stderr)
        self.assertIn("u", r.stderr)

    def test_T03_AC4_unknown_squad_goal_scope_list_names_and_never_listen(self):
        port = free_port()
        for flags, known in ((["--squad", "nope"], "t"), (["--scope", "zzz"], "alpha"), (["--goal", "zzz"], "g1")):
            r = self.cli("--no-open", "--port", str(port), *flags)
            self.assertEqual(r.returncode, 2, flags)
            self.assertIn(known, r.stderr)
            self.assertFalse(listening(port))

    def test_T03_AC5_goal_and_scope_together_refused_naming_both(self):
        port = free_port()
        r = self.cli("--no-open", "--port", str(port), "--goal", "g1", "--scope", "alpha")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--goal", r.stderr)
        self.assertIn("--scope", r.stderr)
        self.assertFalse(listening(port))

    def test_T03_AC6_squad_path_in_another_repo_opens_and_others_are_not_scanned(self):
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        target = make_squad(other.name, "far")
        make_squad(other.name, "hidden")
        squads = squadboard.find_squads([str(target)], env=self.env)
        self.assertEqual([s.name for s in squads], ["far"])
        srv, base = self.serve(squads)
        names = [s["name"] for s in json.loads(get(base + "/api/squads")[2])["data"]["squads"]]
        self.assertEqual(names, ["far"])

    def test_T03_AC7_AC8_picker_rows_multiple_flag_and_flat_squad(self):
        flat = make_squad(self.repo, "flatty", flat=True)
        squads = squadboard.find_squads([str(self.squad), str(flat)], env=self.env)
        _, base = self.serve(squads)
        d = json.loads(get(base + "/api/squads")[2])
        self.assertTrue(d["data"]["multiple"])
        rows = {s["name"]: s for s in d["data"]["squads"]}
        self.assertEqual(rows["flatty"]["message"], "flat squad: not supported")
        self.assertEqual(rows["t"]["scopes"], ["alpha"])
        self.assertEqual(rows["t"]["closed_scopes"], ["old"])
        _, base1 = self.serve(squadboard.find_squads([], env=self.env))
        self.assertFalse(json.loads(get(base1 + "/api/squads")[2])["data"]["multiple"])


class ServerTest(Base):
    def raw(self, port, text):
        """Status code of a hand-written request (an empty Host header cannot be sent by urllib)."""
        with socket.create_connection(("127.0.0.1", port), timeout=5) as c:
            c.sendall(text.encode("ascii"))
            c.shutdown(socket.SHUT_WR)
            data = b""
            while chunk := c.recv(4096):
                data += chunk
        return int(data.split(b" ", 2)[1])

    def test_T03_AC10_bound_to_loopback_only_and_wrong_host_refused(self):
        srv, base = self.serve()
        self.assertEqual(srv.server_address[0], "127.0.0.1")
        self.assertEqual(get(base + "/api/squads")[0], 200)
        self.assertEqual(get(base + "/api/squads", host="evil.example:%d" % srv.port)[0], 403)
        self.assertEqual(get(base + "/api/squads", host="127.0.0.1:1")[0], 403)
        for bad in ("127.0.0.1.evil.com", "127.0.0.1@evil.com", "127.0.0.1.evil.com:%d" % srv.port):
            self.assertEqual(get(base + "/api/squads", host=bad)[0], 403, bad)
        self.assertEqual(self.raw(srv.port, "GET /api/squads HTTP/1.0\r\nHost:\r\n\r\n"), 403)
        self.assertEqual(get(base + "/api/squads", host="localhost:%d" % srv.port)[0], 200)
        try:  # the machine's LAN address gets no answer (skipped result when the host has none)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("10.255.255.255", 1))
                lan = s.getsockname()[0]
        except OSError:
            return
        if not lan.startswith("127."):
            with socket.socket() as s:
                s.settimeout(2)
                self.assertNotEqual(s.connect_ex((lan, srv.port)), 0)

    def test_selection_required_400_and_unknown_404(self):
        calls = []
        route = {"name": "x", "path": "/api/x", "read": lambda sel: calls.append(sel) or {"data": 1, "quality": "exact", "unknown": []}}
        _, base = self.serve(routes={"/api/x": route})
        code, _, body = get(base + "/api/x")
        self.assertEqual((code, json.loads(body)["error"]), (400, "selection required"))
        self.assertEqual(calls, [])
        self.assertEqual(get(base + "/api/x?scope=nope")[0], 404)
        self.assertEqual(get(base + "/api/x?scope=alpha&goal=g1")[0], 400)
        code, _, body = get(base + "/api/x?scope=alpha")
        d = json.loads(body)
        self.assertEqual((code, d["schema_version"], d["data"]), (200, 1, 1))
        self.assertEqual(calls[0]["home"], self.squad.resolve() / "scopes" / "alpha")

    def test_reader_that_raises_is_unknown_not_a_crash(self):
        def boom(sel):
            raise RuntimeError("x")
        _, base = self.serve(routes={"/api/b": {"name": "b", "path": "/api/b", "read": boom, "selection": False}})
        d = json.loads(get(base + "/api/b")[2])
        self.assertEqual((d["unknown"], d["quality"]), (["b"], "unknown"))

    def test_routes_are_discovered_from_a_readers_dir_and_a_broken_one_is_skipped(self):
        d = self.repo / "readers"
        d.mkdir()
        (d / "squadboard_good.py").write_text('ROUTE = {"name": "good", "path": "/api/good", "selection": False, '
                                              '"read": lambda sel: {"data": 7}}\n', encoding="utf-8")
        (d / "squadboard_bad.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
        (d / "squadboard_badroute.py").write_text('ROUTE = {"path": "nope"}\n', encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            routes, errors = squadboard.load_routes(dirs=[d])
        self.assertEqual(sorted(errors), ["squadboard_bad", "squadboard_badroute"])
        self.assertEqual(len([l for l in err.getvalue().splitlines() if "skipped reader" in l]), 2)
        _, base = self.serve(routes=routes)  # the server still starts
        good = json.loads(get(base + "/api/good")[2])
        self.assertEqual((good["data"], good["quality"], good["unknown"]), (7, "unknown", []))  # defaults filled
        bad = json.loads(get(base + "/api/bad")[2])
        self.assertEqual((get(base + "/api/bad")[0], bad["unknown"]), (200, ["bad"]))
        self.assertEqual(squadboard.load_routes()[1], [])  # the real bin/ loads clean

    def test_reader_over_budget_is_unknown_and_selection_has_a_fixed_now(self):
        import time
        seen = {}
        def slow(sel):
            time.sleep(2)
            return {"data": 1}
        def clock(sel):
            seen["now"] = sel["now"]
            return {"data": 1}
        routes = {"/api/slow": {"name": "slow", "path": "/api/slow", "read": slow, "selection": False},
                  "/api/c": {"name": "c", "path": "/api/c", "read": clock, "selection": False}}
        srv, base = self.serve(routes=routes)
        self.assertEqual(squadboard.READ_BUDGET_S, 3.0)
        with unittest.mock.patch.object(squadboard, "READ_BUDGET_S", 0.2):
            d = json.loads(get(base + "/api/slow")[2])
        self.assertEqual((d["unknown"], d["quality"], d["data"]), (["slow"], "unknown", None))
        srv.clock = lambda: 1234.5
        get(base + "/api/c")
        self.assertEqual(seen["now"], 1234.5)

    def test_token_and_write_routes(self):
        srv, base = self.serve()
        tok = json.loads(get(base + "/api/session")[2])["data"]["token"]
        self.assertEqual(tok, srv.token)
        srv.put_routes["/api/ui"] = lambda server, params, body: {"data": "saved"}
        for headers, want in (({}, 403), ({"X-Board-Token": "wrong"}, 403), ({"X-Board-Token": tok}, 200)):
            req = urllib.request.Request(base + "/api/ui", data=b"{}", method="PUT", headers=headers)
            try:
                code = urllib.request.urlopen(req, timeout=10).status
            except urllib.error.HTTPError as e:
                code = e.code
            self.assertEqual(code, want)
        called = []
        srv.put_routes["/api/ui"] = lambda server, params, body: called.append(1) or {}
        self.assertEqual(self.raw(srv.port, "PUT /api/ui HTTP/1.0\r\nHost: evil.com\r\nX-Board-Token: %s\r\nContent-Length: 2\r\n\r\n{}" % tok), 403)
        self.assertEqual(called, [])  # refused on Host before the route ran
        req = urllib.request.Request(base + "/api/squads", data=b"{}", method="POST", headers={"X-Board-Token": tok})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(cm.exception.code, 405)

    def test_file_route_allow_list_and_csp(self):
        (self.repo / ".scratch" / "f").mkdir(parents=True)
        (self.repo / ".scratch" / "f" / "spec.md").write_text("spec", encoding="utf-8")
        outside = self.repo / "secret.txt"
        outside.write_text("no", encoding="utf-8")
        link = self.squad / "scopes" / "alpha" / "link.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            link = None
        _, base = self.serve()
        q = lambda p: get(base + "/api/file?path=" + urllib.request.quote(str(p), safe=""))
        code, h, body = q(self.squad / "scopes" / "alpha" / "note.md")
        self.assertEqual((code, body), (200, b"hello"))
        self.assertIn("text/plain", h["Content-Type"])
        code, h, _ = q("scopes/alpha/page.html")  # relative to the squad folder
        self.assertEqual((code, h["Content-Security-Policy"]), (200, "sandbox"))
        self.assertEqual(q(self.repo / ".scratch" / "f" / "spec.md")[0], 200)
        self.assertEqual(q(outside)[0], 403)
        self.assertEqual(q(self.squad / "scopes" / ".." / ".." / ".." / ".." / "secret.txt")[0], 403)
        self.assertEqual(q("/etc/passwd")[0], 403)
        evil = self.squad.parent / (self.squad.name + "-evil")  # sibling folder with the same name prefix
        evil.mkdir()
        (evil / "x.txt").write_text("no", encoding="utf-8")
        self.assertEqual(q(evil / "x.txt")[0], 403)
        self.assertIn(get(base + "/api/file?path=scopes%2Falpha%2F%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fsecret.txt")[0], (403, 404))
        self.assertEqual(q("C:\\Windows\\win.ini")[0], 404)  # not a path here; never read
        self.assertEqual(q(self.squad / "scopes" / "alpha" / "note.md")[1]["X-Content-Type-Options"], "nosniff")
        if link:
            self.assertEqual(q(link)[0], 403)
        self.assertEqual(q(self.squad / "nothing.md")[0], 404)
        self.assertIn("default-src 'self'", get(base + "/")[1]["Content-Security-Policy"])

    def test_T03_AC11_serving_changes_nothing_in_the_squad_folder(self):
        def snap():
            return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size, p.stat().st_mtime_ns)
                    for p in sorted(self.squad.rglob("*")) if p.is_file()}
        before = snap()
        route = {"name": "x", "path": "/api/x", "read": lambda sel: {"data": sorted(p.name for p in sel["home"].iterdir())}}
        _, base = self.serve(routes={"/api/x": route})
        get(base + "/api/x?scope=alpha")
        for path in ("/", "/api/session", "/api/squads", "/api/file?path=scopes/alpha/note.md", "/api/nope"):
            get(base + path)
        self.assertEqual(snap(), before)


class StartPrintsTest(unittest.TestCase):
    def test_T03_AC12_squad_start_does_not_start_the_board(self):
        src = (BIN / "squad-start").read_text(encoding="utf-8")
        self.assertNotIn("import squadboard", src)
        self.assertNotIn("webbrowser", src)
        self.assertNotIn('"squad-board"', src)  # printed as text only, never spawned (tests/test_squad_start.py checks the line)


if __name__ == "__main__":
    unittest.main()
