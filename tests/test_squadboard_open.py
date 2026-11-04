"""Ticket 34: POST /api/open runs `code --goto <file>` (T34.TA1-TA4). The `code` program is always a stub here;
the real VS Code windows are the PO's check (T34.AC10-AC14). Page tests reuse the Files-panel harness of ticket 30."""
import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
import unittest.mock
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import squadboard_open  # noqa: E402
import test_squadboard_server as ts  # noqa: E402
from test_squadboard_panels import CHROME, HEAD14, PRE14, payloads14, real_payloads, run_page  # noqa: E402

REFUSAL = squadboard_open.REFUSAL


def stub_code(dirpath, log):
    """A `code` script that appends its arguments to `log`; STUB_EXIT, STUB_SLEEP, STUB_SAY set by environment."""
    f = Path(dirpath) / "code"
    f.write_text('#!/bin/sh\nfor a in "$@"; do printf "%s\\n" "$a" >> "' + str(log) + '"; done\nprintf -- "--end\\n" >> "' + str(log) +
                 '"\n[ -n "$STUB_SLEEP" ] && sleep "$STUB_SLEEP"\n[ -n "$STUB_SAY" ] && echo "$STUB_SAY"\nexit ${STUB_EXIT:-0}\n', encoding="utf-8")
    f.chmod(f.stat().st_mode | stat.S_IEXEC)


class OpenFile(unittest.TestCase):
    def test_T34_TA1_pick_and_judge_table(self):
        cp = lambda rc=0, out="": unittest.mock.Mock(returncode=rc, stdout=out, stderr="")
        wsl = {"WSL_DISTRO_NAME": "D", "HOME": "/h", "XDG_RUNTIME_DIR": "/r"}
        cases = [
            ("path", {"PATH": "/bin"}, "/bin/code", cp(), {}, True, "path"),
            ("wsl live of two", wsl, None, cp(), {"live": "/r/vscode-ipc-b.sock"}, True, "socket"),
            ("env hook live", dict(wsl, VSCODE_IPC_HOOK_CLI="/r/vscode-ipc-e.sock"), None, cp(), {"live": "/r/vscode-ipc-e.sock"}, True, "socket"),
            ("nothing", {"PATH": ""}, None, cp(), {}, False, None),
            ("refusal text, exit 0", {"PATH": "/bin"}, "/bin/code", cp(0, REFUSAL), {}, False, "path"),
            ("timeout", {"PATH": "/bin"}, "/bin/code", None, {}, False, "path"),
            ("exit 1, no text", {"PATH": "/bin"}, "/bin/code", cp(1), {}, False, "path"),
            ("exit 0, silent, live socket", wsl, None, cp(), {"live": "/r/vscode-ipc-a.sock"}, True, "socket"),
            ("nt and a cmd.exe character", {"PATH": "/bin"}, "/bin/code", cp(), {"nt": 1}, False, None),
        ]
        for name, env, which, res, opt, ok, how in cases:
            with self.subTest(name), unittest.mock.patch("squadboard_open.shutil.which", return_value=which), \
                    unittest.mock.patch("squadboard_open._remote_cli", return_value="/h/rc/code"), \
                    unittest.mock.patch("squadboard_open._sockets", return_value=["/r/vscode-ipc-a.sock", "/r/vscode-ipc-b.sock"]), \
                    unittest.mock.patch("squadboard_open._live", side_effect=lambda s: s == opt.get("live")), \
                    unittest.mock.patch("squadboard_open.subprocess.run", return_value=res) as run:
                if res is None:
                    run.side_effect = squadboard_open.subprocess.TimeoutExpired("code", 5)
                nt = unittest.mock.patch("squadboard_open.os.name", "nt") if opt.get("nt") else unittest.mock.patch.dict(os.environ)
                with nt:
                    r = squadboard_open.open_file("/x/a&b.md" if opt.get("nt") else "/x/a b.md", env=env)
                self.assertEqual((r["ok"], r["how"]), (ok, how))
                if name == "nothing":
                    self.assertEqual(r["why"], "no-vscode"); run.assert_not_called()
                if name.startswith("nt"):
                    self.assertEqual(r["why"], "refused"); run.assert_not_called()
                if name == "timeout":
                    self.assertEqual(r["why"], "timeout")
                if run.called:
                    argv = run.call_args[0][0]
                    self.assertIsInstance(argv, list)
                    self.assertNotIn("shell", run.call_args[1])
                    self.assertEqual(argv[-2:], ["--goto", "/x/a b.md"])
                    if how == "socket":
                        self.assertEqual(run.call_args[1]["env"]["VSCODE_IPC_HOOK_CLI"], opt["live"])
                        self.assertEqual(argv[0], "/h/rc/code")
                    if how == "path":
                        self.assertEqual(argv, ["/bin/code", "--goto", "/x/a b.md"])


def post(url, body, token=None, host=None, ctype="application/json", headers=None):
    h = {"Content-Type": ctype, **(headers or {})}
    if token is not None:
        h["X-Board-Token"] = token
    if host:
        h["Host"] = host
    req = urllib.request.Request(url, data=body if isinstance(body, bytes) else json.dumps(body).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


class Route(ts.Base):
    def setUp(self):
        super().setUp()
        self.bindir = tempfile.TemporaryDirectory()
        self.addCleanup(self.bindir.cleanup)
        self.log = Path(self.bindir.name) / "log.txt"
        stub_code(self.bindir.name, self.log)
        for k, v in {"PATH": self.bindir.name + os.pathsep + os.environ.get("PATH", ""), "STUB_EXIT": "", "STUB_SAY": "", "STUB_SLEEP": ""}.items():
            p = unittest.mock.patch.dict(os.environ, {k: v}); p.start(); self.addCleanup(p.stop)
        self.srv, self.url = self.serve()
        self.f = self.squad / "scopes" / "alpha" / "note.md"
        (self.repo / ".scratch").mkdir()
        (self.repo / ".scratch" / "s.md").write_text("s", encoding="utf-8")
        self.api = self.url + "/api/open?squad=" + self.squad.name

    def calls(self):
        return self.log.read_text(encoding="utf-8").count("--end") if self.log.exists() else 0

    def go(self, path, **kw):
        kw.setdefault("token", self.srv.token)
        return post(self.api, {"path": str(path)}, **kw)

    def test_T34_TA2_gate(self):
        outside = Path(self.tmp.name).parent / "outside-34.txt"
        link = self.squad / "link-out"
        outside.write_text("x", encoding="utf-8"); self.addCleanup(outside.unlink)
        link.symlink_to(outside)
        for name, (code, kw), path in [
            ("no token", (403, {"token": ""}), self.f), ("wrong host", (403, {"host": "evil.test"}), self.f),
            ("outside", (403, {}), outside), ("dotdot", (400, {}), str(self.f.parent / ".." / "alpha" / "note.md")),
            ("relative", (400, {}), "scopes/alpha/note.md"), ("dash", (400, {}), "-x"), ("symlink out", (403, {}), link),
            ("missing", (404, {}), self.f.parent / "none.md")]:
            with self.subTest(name):
                self.assertEqual(self.go(path, **kw)[0], code)
        self.assertEqual(post(self.api, {"path": str(self.f)}, token=self.srv.token, ctype="text/plain")[0], 415)
        self.assertEqual(self.calls(), 0)
        for p in (self.f, self.repo / ".scratch" / "s.md"):
            c, j = self.go(p)
            self.assertEqual((c, j["data"]["ok"], j["data"]["how"]), (200, True, "path"))
        self.assertEqual(self.calls(), 2)
        lines = self.log.read_text(encoding="utf-8").split("\n")[:3]
        self.assertEqual(lines, ["--goto", str(self.f.resolve()), "--end"])
        self.assertEqual(urllib.request.Request(self.api).get_method(), "GET")
        for method, path in (("GET", "/api/open"), ("PUT", "/api/open"), ("DELETE", "/api/open"), ("PATCH", "/api/open"), ("POST", "/api/ui"), ("POST", "/api/other")):
            req = urllib.request.Request(self.url + path + "?squad=" + self.squad.name, method=method, data=b"{}" if method != "GET" else None,
                                         headers={"Content-Type": "application/json", "X-Board-Token": self.srv.token})
            with self.subTest(method + " " + path), self.assertRaises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(req)
            self.assertEqual(e.exception.code, 405 if path != "/api/other" or method != "GET" else 404)
        c, j = post(self.url + "/api/open?squad=nope", {"path": str(self.f)}, token=self.srv.token)
        self.assertEqual(c, 404); self.assertIn("unknown squad", j["error"])
        self.assertEqual(self.calls(), 2)

    def test_T34_TA8_foreign_origin_refused_before_the_route(self):
        port = self.srv.port
        for origin in ("http://evil.example.com", "null", "http://127.0.0.1:1", "https://127.0.0.1:%d" % port):
            with self.subTest(origin):
                c, j = self.go(self.f, headers={"Origin": origin})
                self.assertEqual((c, j["error"]), (403, "origin not allowed"))
        self.assertEqual(self.calls(), 0)
        for origin in ("http://127.0.0.1:%d" % port, "http://localhost:%d" % port):
            self.assertEqual(self.go(self.f, headers={"Origin": origin})[0], 200)
        self.assertEqual(self.calls(), 2)
        called = []
        self.srv.put_routes["/api/ui"] = lambda server, params, body: called.append(1) or {}
        req = urllib.request.Request(self.url + "/api/ui", data=b"{}", method="PUT",
                                     headers={"X-Board-Token": self.srv.token, "Origin": "http://evil.example.com"})
        with self.assertRaises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual((e.exception.code, called), (403, []))

    def test_T34_TA2_refusal_and_exit_code_give_ok_false_and_one_at_a_time(self):
        for k, v in (("STUB_SAY", REFUSAL), ("STUB_EXIT", "1")):
            with unittest.mock.patch.dict(os.environ, {k: v}):
                j = self.go(self.f)[1]["data"]
                self.assertEqual((j["ok"], j["why"]), (False, "refused"))
        self.assertNotIn("Command is only", json.dumps(j))   # no process text in the answer
        self.assertTrue(squadboard_open._BUSY.acquire(blocking=False))
        try:
            self.assertEqual(self.go(self.f)[0], 429)
        finally:
            squadboard_open._BUSY.release()

    def test_T34_TA3_no_file_written(self):
        def snap():
            return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.repo.rglob("*") if p.is_file()}
        before = snap()
        for _ in range(5):
            self.go(self.f); self.go(self.f.parent / "none.md")
        self.assertEqual(before, snap())


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Page34(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = dict(real_payloads(), saved=None, f14=payloads14())

    def page(self, body):
        return run_page(PRE14 + body, self.real, "#/scope/checkout", HEAD14)

    SETUP = r"""
await start14();
const panel=$('section[data-panel=files]');
const posts=[],follow=[];let answer={ok:true};
const realFetch=window.fetch;
window.fetch=async(u,o)=>{if(String(u).startsWith('/api/open')){posts.push({u,o});return {ok:true,json:async()=>({data:answer})}}return realFetch(u,o)};
panel.addEventListener('click',e=>{const a=e.target.closest('a');if(a&&a.dataset.fb){follow.push(a.dataset.abs)}if(a)e.preventDefault()});
const rows=Array.from(panel.querySelectorAll('tr[data-open] a[data-abs]'));
const file=rows.find(a=>!a.dataset.folder),folder=rows.find(a=>a.dataset.folder);
"""

    def test_T34_TA4_click_posts_once_and_falls_back_only_on_failure(self):
        r = self.page(self.SETUP + r"""
const ev=(o)=>new MouseEvent('click',Object.assign({bubbles:true,cancelable:true},o));
file.dispatchEvent(ev({}));await sleep(100);
const okPosts=posts.length,okFollow=follow.length,body=JSON.parse(posts[0].o.body),hdr=posts[0].o.headers['X-Board-Token'],status=(panel.querySelector('[role=status]')||{}).textContent;
answer={ok:false,why:'no-vscode'};file.dispatchEvent(ev({}));await sleep(100);
const failFollow=follow.length,failText=panel.textContent;
const n=posts.length;
folder.dispatchEvent(ev({}));file.dispatchEvent(ev({ctrlKey:true}));file.dispatchEvent(ev({button:1}));await sleep(50);
out({okPosts,okFollow,abs:file.dataset.abs,body,hdr,status,failFollow,failText,more:posts.length-n,tabs:document.querySelectorAll('a[target]').length,
 imgs:panel.querySelectorAll('img').length});
""")
        self.assertEqual((r["okPosts"], r["okFollow"]), (1, 0))      # worked: the link is not followed
        self.assertEqual(r["body"], {"path": r["abs"]})
        self.assertTrue(r["hdr"])
        self.assertEqual(r["status"], "Sent to VS Code: " + r["abs"] + " Copy path")
        self.assertEqual(r["failFollow"], 1)                          # failed: the href is followed once
        self.assertNotRegex(r["failText"], r"(?i)error|could not")
        self.assertEqual(r["more"], 0)                                # folder, ctrl-click, middle click: no route call
        self.assertEqual(r["tabs"], 0)


if __name__ == "__main__":
    unittest.main()
