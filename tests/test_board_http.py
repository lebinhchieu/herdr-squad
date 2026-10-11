"""Seam A, BRD-05: squad-board HTTP hardening (bind, token, Host/Origin, jump, port fallback).

Every test runs the real `bin/squad-board --replay`. `herdr` is a stub script in a temp dir that is
the only entry of the server's PATH: it records its argv, so a refused jump is proven to run nothing.
"""
import json
import os
import re
import socket
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from board_fixture import BIN, Fixture

NOW = "2026-10-12T12:00:00Z"
STARTUP_RE = re.compile(r"^squad-board: http://127\.0\.0\.1:([0-9]+)/\?token=([A-Za-z0-9_-]{22})$")
MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}
STUB = """#!{python}
import os, sys, time
with open({calls!r}, "a") as f:
    f.write("".join(a + "\\n" for a in sys.argv[1:]))
with open({pidfile!r}, "w") as f:
    f.write(str(os.getpid()))
if {mode!r} == "fail":
    sys.stderr.write("herdr: boom\\n")
    sys.exit(3)
if {mode!r} == "sleep":
    time.sleep(30)
"""


class Resp:
    def __init__(self, raw):
        head, _, self.body = raw.partition(b"\r\n\r\n")
        lines = head.decode("iso-8859-1").split("\r\n")
        self.status = int(lines[0].split()[1])
        self.pairs = [tuple(ln.split(":", 1)) for ln in lines[1:] if ":" in ln]
        self.headers = {k.strip().lower(): v.strip() for k, v in self.pairs}

    def json(self):
        return json.loads(self.body)


def request(port, method, path, headers=(), host="default", version="HTTP/1.1", body=b"",
            content_length=None):
    """One raw HTTP request. host=None sends no Host header; headers may repeat a name."""
    lines = ["%s %s %s" % (method, path, version)]
    if host == "default":
        host = "127.0.0.1:%d" % port
    if host is not None:
        lines.append("Host: " + host)
    lines += ["%s: %s" % (k, v) for k, v in headers]
    lines.append("Content-Length: %d" % (len(body) if content_length is None else content_length))
    data = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + body
    sock = socket.create_connection(("127.0.0.1", port), timeout=15)
    try:
        try:
            sock.sendall(data)
        except OSError:
            pass  # the server may answer and close before a huge body is sent; read the answer
        chunks = []
        while True:
            try:
                chunk = sock.recv(65536)
            except ConnectionResetError:
                break
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        sock.close()
    return Resp(b"".join(chunks))


def launch(root, port, path):
    """Server with stdout and stderr in files; returns (proc, stdout_file, stderr_file)."""
    out, err = tempfile.TemporaryFile(), tempfile.TemporaryFile()
    proc = subprocess.Popen([sys.executable, str(BIN), "--replay", str(root), "--port", str(port),
                             "--now", NOW], stdout=out, stderr=err, env={"PATH": path})
    return proc, out, err


def read_all(f):
    f.flush()
    f.seek(0)
    return f.read().decode("utf-8", "replace")


def occupy(count):
    """Sockets on `count` consecutive free loopback ports (alternating listening / bound only)."""
    for _ in range(50):
        first = socket.socket()
        first.bind(("127.0.0.1", 0))
        base = first.getsockname()[1]
        if base + count > 65000:
            first.close()
            continue
        socks = [first]
        try:
            for i in range(1, count):
                s = socket.socket()
                socks.append(s)
                s.bind(("127.0.0.1", base + i))
        except OSError:
            for s in socks:
                s.close()
            continue
        for i, s in enumerate(socks):
            if i % 2 == 0:
                s.listen(1)
        return base, socks
    raise unittest.SkipTest("no run of %d free ports" % count)


class HttpCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.tmp = Path(tempfile.mkdtemp(prefix="board-stub-"))
        self.addCleanup(subprocess.call, ["rm", "-rf", str(self.tmp)])
        self.calls, self.pidfile = self.tmp / "calls", self.tmp / "pid"
        self.fx.roster([MANAGER, {"agent": "dev-board-1"},
                        {"agent": "old-dev", "status": "retired"}])
        self.fx.activity(agent="ghost-agent", status="working")

    def stub(self, mode="ok"):
        bindir = self.tmp / "bin"
        bindir.mkdir(exist_ok=True)
        path = bindir / "herdr"
        path.write_text(STUB.format(python=sys.executable, calls=str(self.calls),
                                    pidfile=str(self.pidfile), mode=mode))
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return str(bindir)

    def start(self, mode="ok", path=None):
        self.srv = self.fx.start(now=NOW, env={"PATH": path if path is not None else self.stub(mode)})
        return self.srv

    def req(self, method, path, **kw):
        return request(self.srv.port, method, path, **kw)

    def jump(self, name="dev-board-1", token="valid", headers=(), **kw):
        hs = list(headers)
        if token == "valid":
            hs.append(("X-Board-Token", self.srv.token))
        elif token is not None:
            hs.append(("X-Board-Token", token))
        return self.req("POST", "/jump/" + name, headers=hs, **kw)

    def herdr_calls(self):
        return self.calls.read_text().split("\n")[:-1] if self.calls.exists() else []

    def assertNoCall(self):
        self.assertEqual(self.herdr_calls(), [])


class BindAndStartupTest(HttpCase):
    def test_source_binds_loopback_literally(self):
        source = BIN.read_text()
        self.assertTrue('("127.0.0.1",' in source)

    def test_not_reachable_on_other_loopback_address(self):
        self.start()
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.2", self.srv.port), timeout=3).close()

    def test_not_reachable_on_the_hosts_lan_address(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("192.0.2.1", 9))  # sends nothing; only picks the outgoing address
            lan = probe.getsockname()[0]
        except OSError:
            lan = "127.0.0.1"
        finally:
            probe.close()
        if lan.startswith("127."):
            self.skipTest("host has no non-loopback address")
        self.start()
        with self.assertRaises(OSError):
            socket.create_connection((lan, self.srv.port), timeout=3).close()

    def test_startup_line_has_url_with_fresh_token(self):
        first = self.start()
        match = STARTUP_RE.match(first.startup_line)
        self.assertIsNotNone(match, first.startup_line)
        self.assertEqual(int(match.group(1)), first.port)
        self.assertEqual(match.group(2), first.token)
        second = self.fx.start(now=NOW)
        self.assertNotEqual(first.token, second.token)

    def test_token_not_in_state_or_page(self):
        self.start()
        for path in ("/", "/state"):
            resp = self.req("GET", path)
            self.assertEqual(resp.status, 200)
            self.assertNotIn(self.srv.token.encode(), resp.body)
            self.assertNotIn(self.srv.token.encode(), str(resp.pairs).encode())

    def test_token_only_on_the_startup_line(self):
        empty = self.tmp / "empty"  # no herdr on PATH: the jumps below end in 502, which must not leak either
        empty.mkdir()
        proc, out, err = launch(self.fx.root, 0, str(empty))
        self.addCleanup(lambda: (proc.kill(), proc.wait(), out.close(), err.close()))
        deadline = time.monotonic() + 10
        while "\n" not in read_all(out) and time.monotonic() < deadline:
            time.sleep(0.05)
        match = STARTUP_RE.match(read_all(out).splitlines()[0])
        port, token = int(match.group(1)), match.group(2)
        seen = []
        for path, kw in (("/", {}), ("/state", {}), ("/nope", {}), ("/events", {}),
                         ("/state?iteration=zzz", {}), ("/", {"host": "evil.example"})):
            seen.append(request(port, "GET", path, **kw))
        for name in ("dev-board-1", "nobody", "bad name", "../x"):
            seen.append(request(port, "POST", "/jump/" + name.replace(" ", "%20"),
                                headers=[("X-Board-Token", token)]))
            seen.append(request(port, "POST", "/jump/" + name.replace(" ", "%20"),
                                headers=[("X-Board-Token", "wrong")]))
        seen.append(request(port, "OPTIONS", "/jump/x"))
        for resp in seen:
            self.assertNotIn(token.encode(), resp.body)
            self.assertNotIn(token.encode(), str(resp.pairs).encode())
        proc.terminate()
        proc.wait(5)
        self.assertEqual(read_all(out).count(token), 1)
        self.assertEqual(read_all(out).splitlines()[1:], [])
        self.assertEqual(read_all(err), "")


class PortTest(HttpCase):
    def test_port_zero_takes_an_os_port(self):
        self.start()
        self.assertGreater(self.srv.port, 0)
        self.assertEqual(self.req("GET", "/state").status, 200)

    def test_bound_but_not_listening_port_counts_as_busy_and_the_bound_port_is_printed(self):
        base, socks = occupy(1)
        self.addCleanup(lambda: [s.close() for s in socks])
        socks[0].close()
        sock = socket.socket()
        socks[0] = sock
        sock.bind(("127.0.0.1", base))
        srv = self.fx.start(now=NOW, port=base)
        self.assertIn(srv.port, range(base + 1, base + 21))
        self.assertEqual(STARTUP_RE.match(srv.startup_line).group(1), str(srv.port))
        self.assertEqual(srv.get("/state")[0], 200)

    def test_restart_on_the_same_port_after_serving_a_request(self):
        first = self.start()
        port = first.port
        self.assertEqual(first.get("/state")[0], 200)
        first.stop()  # the closed connection lingers in TIME_WAIT; the default port must still be reusable
        again = self.fx.start(now=NOW, port=port)
        self.assertEqual(again.port, port)

    def test_listening_busy_port_falls_forward(self):
        base, socks = occupy(1)
        self.addCleanup(lambda: [s.close() for s in socks])
        socks[0].listen(1)
        srv = self.fx.start(now=NOW, port=base)
        self.assertIn(srv.port, range(base + 1, base + 21))

    def test_all_twenty_one_ports_busy_exits_one_with_message(self):
        base, socks = occupy(21)
        self.addCleanup(lambda: [s.close() for s in socks])
        done = subprocess.run([sys.executable, str(BIN), "--replay", str(self.fx.root),
                               "--port", str(base)], capture_output=True, timeout=20)
        self.assertEqual(done.returncode, 1)
        self.assertIn(str(base), done.stderr.decode())
        self.assertEqual(done.stdout, b"")
        self.assertNotIn(b"Traceback", done.stderr)


class HostAndOriginTest(HttpCase):
    def setUp(self):
        super().setUp()
        self.start()

    def other_port(self):
        return self.srv.port + 1

    def test_foreign_host_is_403_on_every_route(self):
        routes = (("GET", "/"), ("GET", "/state"), ("GET", "/events"),
                  ("POST", "/jump/dev-board-1"), ("GET", "/jump/dev-board-1"), ("OPTIONS", "/state"))
        for host in ("evil.example", "evil.example:%d" % self.srv.port,
                     "127.0.0.1:%d" % self.other_port()):
            for method, path in routes:
                with self.subTest(host=host, method=method, path=path):
                    hs = [("X-Board-Token", self.srv.token)]
                    self.assertEqual(self.req(method, path, host=host, headers=hs).status, 403)
        self.assertNoCall()

    def test_host_edge_cases_are_403(self):
        port = self.srv.port
        for host in (None, "", "127.0.0.1", "localhost", "127.0.0.1.evil.com:%d" % port,
                     "localhost.evil.com:%d" % port, "localhost:%d" % self.other_port(),
                     "127.0.0.1:%dx" % port, "user@127.0.0.1:%d" % port):
            with self.subTest(host=host):
                kw = {"version": "HTTP/1.0"} if host is None else {}
                self.assertEqual(self.req("GET", "/state", host=host, **kw).status, 403)

    def test_two_host_headers_are_403(self):
        resp = self.req("GET", "/state", headers=[("Host", "evil.example")])
        self.assertEqual(resp.status, 403)

    def test_localhost_and_case_variants_are_accepted(self):
        port = self.srv.port
        for host in ("localhost:%d" % port, "LOCALHOST:%d" % port, "127.0.0.1:%d" % port):
            with self.subTest(host=host):
                self.assertEqual(self.req("GET", "/state", host=host).status, 200)

    def test_bad_origin_is_403_on_read_routes_too(self):
        port = self.srv.port
        for origin in ("null", "http://127.0.0.1", "http://evil.example", "http://127.0.0.1:%d" % (port + 1),
                       "https://127.0.0.1:%d" % port, "http://localhost.evil.com:%d" % port, ""):
            with self.subTest(origin=origin):
                self.assertEqual(self.req("GET", "/state", headers=[("Origin", origin)]).status, 403)

    def test_good_origin_is_accepted(self):
        port = self.srv.port
        for origin in ("http://127.0.0.1:%d" % port, "http://localhost:%d" % port):
            with self.subTest(origin=origin):
                self.assertEqual(self.req("GET", "/state", headers=[("Origin", origin)]).status, 200)


class JumpTest(HttpCase):
    def test_success_runs_exactly_one_argv_without_shell(self):
        self.start()
        resp = self.jump()
        self.assertEqual((resp.status, resp.json()), (200, {"ok": True}))
        self.assertEqual(self.herdr_calls(), ["agent", "focus", "dev-board-1"])

    def test_success_with_localhost_host_and_good_origin(self):
        self.start()
        resp = self.jump(host="localhost:%d" % self.srv.port,
                         headers=[("Origin", "http://localhost:%d" % self.srv.port)])
        self.assertEqual(resp.status, 200)

    def test_two_equal_token_headers_are_accepted(self):
        self.start()
        resp = self.jump(token=None, headers=[("X-Board-Token", self.srv.token)] * 2)
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(self.herdr_calls()), 3)

    def test_missing_or_wrong_token_is_403(self):
        self.start()
        token = self.srv.token
        same_length = ("A" if token[0] != "A" else "B") + token[1:]
        cases = {"missing": None, "wrong same length": same_length, "wrong shorter": token[:-1],
                 "wrong longer": token + "x", "empty": "", "non-ascii": "é" * 11,
                 "10 KB": "a" * 10240, "prefix": token[:5]}
        for label, value in cases.items():
            with self.subTest(label):
                self.assertEqual(self.jump(token=value).status, 403)
        self.assertNoCall()

    def test_non_ascii_token_sent_as_utf8_bytes_is_403_not_500(self):
        self.start()
        sock = socket.create_connection(("127.0.0.1", self.srv.port), timeout=10)
        sock.sendall(("POST /jump/dev-board-1 HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nX-Board-Token: " % self.srv.port)
                     .encode() + "é".encode("utf-8") + b"\r\nContent-Length: 0\r\n\r\n")
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        sock.close()
        self.assertEqual(Resp(data).status, 403)
        self.assertNoCall()
        self.assertEqual(self.srv.stderr(), "")

    def test_two_different_token_headers_are_403_in_either_order(self):
        self.start()
        for pair in ((self.srv.token, "wrong"), ("wrong", self.srv.token)):
            with self.subTest(pair=pair):
                hs = [("X-Board-Token", t) for t in pair]
                self.assertEqual(self.jump(token=None, headers=hs).status, 403)
        self.assertNoCall()

    def test_bad_origin_is_403_even_with_a_good_token(self):
        self.start()
        for origin in ("null", "http://evil.example", "http://127.0.0.1"):
            with self.subTest(origin=origin):
                self.assertEqual(self.jump(headers=[("Origin", origin)]).status, 403)
        self.assertNoCall()

    def test_wrong_method_is_405_and_runs_nothing(self):
        self.start()
        hs = [("X-Board-Token", self.srv.token)]
        for method in ("GET", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
            with self.subTest(method=method):
                self.assertEqual(self.req(method, "/jump/dev-board-1", headers=hs).status, 405)
        self.assertNoCall()

    def test_host_is_checked_before_method(self):
        self.start()
        self.assertEqual(self.req("GET", "/jump/x", host="evil.example").status, 403)
        self.assertEqual(self.req("GET", "/jump/x").status, 405)

    def test_bad_names_are_400(self):
        self.start()
        names = ["a%20b", "..%2Fx", "../x", "x;rm", "a" * 33, "", "A", "1abc", "-a", "a.b", "a%00b",
                 "dev-board-1%0A", "%e2%82%ac"]
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(self.jump(name).status, 400)
        self.assertNoCall()

    def test_longest_valid_name_passes_the_regex(self):
        self.start()
        self.assertEqual(self.jump("a" * 32).status, 404)

    def test_name_not_in_roster_is_404(self):
        self.start()
        for name in ("nobody", "ghost-agent", "old-dev"):  # unlisted-in-logs, retired
            with self.subTest(name=name):
                self.assertEqual(self.jump(name).status, 404)
        self.assertNoCall()

    def test_token_is_checked_before_roster_membership(self):
        self.start()
        self.assertEqual(self.jump("nobody", token="wrong").status, 403)
        self.assertEqual(self.jump("nobody", token=None).status, 403)
        self.assertNoCall()

    def test_roster_is_read_on_every_request(self):
        self.start()
        self.assertEqual(self.jump("dev-board-9").status, 404)
        self.fx.roster([MANAGER, {"agent": "dev-board-1"}, {"agent": "dev-board-9"}])
        self.assertEqual(self.jump("dev-board-9").status, 200)
        self.assertEqual(self.herdr_calls(), ["agent", "focus", "dev-board-9"])

    def test_request_body_is_ignored(self):
        self.start()
        self.assertEqual(self.jump(content_length=10 ** 9).status, 200)
        self.assertEqual(self.jump(body=b"x" * (4 * 1024 * 1024)).status, 200)
        self.assertEqual(self.req("GET", "/state").status, 200)
        self.assertEqual(self.herdr_calls()[:3], ["agent", "focus", "dev-board-1"])


class HerdrFailureTest(HttpCase):
    def assertBadGateway(self, resp):
        self.assertEqual(resp.status, 502)
        self.assertFalse(resp.json()["ok"])
        self.assertNotIn(b"Traceback", resp.body)
        self.assertNotIn(b"boom", resp.body)
        self.assertEqual(self.srv.stderr(), "")

    def test_herdr_exiting_non_zero_is_502(self):
        self.start("fail")
        self.assertBadGateway(self.jump())

    def test_herdr_missing_from_path_is_502(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.start(path=str(empty))
        self.assertBadGateway(self.jump())

    def test_herdr_not_executable_is_502(self):
        bindir = self.stub()
        (Path(bindir) / "herdr").chmod(stat.S_IRUSR)
        self.start(path=bindir)
        self.assertBadGateway(self.jump())

    def test_hanging_herdr_is_killed_after_about_five_seconds(self):
        self.start("sleep")
        began = time.monotonic()
        resp = self.jump()
        took = time.monotonic() - began
        self.assertBadGateway(resp)
        self.assertTrue(4.5 < took < 9, took)
        pid = int(self.pidfile.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)


class HeadersTest(HttpCase):
    def test_no_store_everywhere_nosniff_on_json_and_no_cors(self):
        self.start()
        hs = [("X-Board-Token", self.srv.token)]
        cases = [("GET", "/", {}, 200), ("GET", "/state", {}, 200), ("GET", "/state?iteration=x", {}, 400),
                 ("GET", "/nope", {}, 404), ("GET", "/state", {"host": "evil.example"}, 403),
                 ("GET", "/jump/x", {}, 405), ("OPTIONS", "/jump/x", {"headers": hs}, 405),
                 ("POST", "/jump/Bad", {"headers": hs}, 400), ("POST", "/jump/nobody", {"headers": hs}, 404),
                 ("POST", "/jump/nobody", {}, 403), ("POST", "/jump/dev-board-1", {"headers": hs}, 200),
                 ("BREW", "/state", {}, 501)]
        for method, path, kw, status in cases:
            with self.subTest(method=method, path=path, status=status):
                resp = self.req(method, path, **kw)
                self.assertEqual(resp.status, status)
                self.assertEqual(resp.headers.get("cache-control"), "no-store")
                self.assertFalse([k for k in resp.headers if k.startswith("access-control-")])
                if resp.headers["content-type"].startswith("application/json"):
                    self.assertEqual(resp.headers.get("x-content-type-options"), "nosniff")
                    json.loads(resp.body)

    def test_options_with_cors_preflight_headers_is_not_2xx(self):
        self.start()
        resp = self.req("OPTIONS", "/jump/x", headers=[("Origin", "http://127.0.0.1:%d" % self.srv.port),
                                                      ("Access-Control-Request-Method", "POST")])
        self.assertIn(resp.status, (405, 501))
        self.assertFalse([k for k in resp.headers if k.startswith("access-control-")])


class SourceGateTest(unittest.TestCase):
    """The greps qaw-board runs on bin/squad-board (security-flagged ticket)."""

    def test_forbidden_constructs_are_absent(self):
        source = BIN.read_text()
        for needle in ("shell=True", "os.system", "0.0.0.0", "Access-Control", "eval(", "exec(", "pickle",
                       'ThreadingHTTPServer(("",', "SO_REUSEPORT"):
            self.assertFalse(needle in source, needle)

    def test_token_is_only_compared_with_compare_digest_on_bytes(self):
        source = BIN.read_text()
        self.assertTrue("hmac.compare_digest" in source)
        self.assertNotRegex(source, r"token\s*(==|!=)|(==|!=)\s*[\w.]*token|\bin\s+[\w.]*token")


if __name__ == "__main__":
    unittest.main()
