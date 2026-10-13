"""Seam A, BRD-15: GET /notes/<name>?token=... (design-iteration-2 "Notes route").

Every test runs the real `bin/squad-board --replay` on a temp squad folder with
`roles/<name>.notes.md` files and talks to it over a raw socket.
"""
import os
import socket
import time
import unittest
from urllib.parse import quote

from board_fixture import BIN, Fixture
from test_board_http import NOW, request

MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}
STEP8 = {
    "content-type": "text/plain; charset=utf-8",
    "x-content-type-options": "nosniff",
    "content-security-policy": "sandbox; default-src 'none'",
    "referrer-policy": "no-referrer",
    "cache-control": "no-store",
    "content-disposition": "inline",
}
NOTES = "# Notes\n\nline with é and ⛔\n<script>alert(1)</script>\n"
LONG_NAME = "a" + "b" * 32  # 33 characters: one over the name rule


class NotesCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([MANAGER, {"agent": "dev-board-1"}, {"agent": "old-dev", "status": "retired"},
                        {"agent": "no-file"}, {"agent": LONG_NAME}, {"agent": "linked"},
                        {"agent": "dirnamed"}, {"agent": "piped"}, {"agent": "big"}, {"agent": "binary"}])
        self.fx.write("roles/dev-board-1.notes.md", NOTES)
        self.fx.write("roles/old-dev.notes.md", "retired notes\n")
        self.fx.write("roles/%s.notes.md" % LONG_NAME, "long name\n")
        self.srv = self.fx.start(now=NOW)

    def notes(self, name, token="valid", method="GET", headers=(), query=None, **kw):
        if query is None:
            query = "token=" + (self.srv.token if token == "valid" else (token or ""))
            if token is None:
                query = ""
        path = "/notes/" + name + ("?" + query if query else "")
        return request(self.srv.port, method, path, headers=headers, **kw)


class SuccessTest(NotesCase):
    def test_body_equals_the_file_and_headers_are_step_8(self):
        r = self.notes("dev-board-1")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body, NOTES.encode("utf-8"))
        for name, value in STEP8.items():
            self.assertEqual(r.headers.get(name), value, name)

    def test_a_retired_roster_agent_is_served(self):
        r = self.notes("old-dev")
        self.assertEqual((r.status, r.body), (200, b"retired notes\n"))

    def test_every_response_carries_the_text_headers_even_errors(self):
        for r in (self.notes("no-file"), self.notes("dev-board-1", token="wrong"), self.notes("UPPER")):
            self.assertEqual(r.headers["content-type"], "text/plain; charset=utf-8")
            self.assertEqual(r.headers["x-content-type-options"], "nosniff")
            self.assertEqual(r.headers["content-security-policy"], "sandbox; default-src 'none'")
            self.assertEqual(r.headers["cache-control"], "no-store")


class TokenTest(NotesCase):
    def assert_refused(self, r):
        self.assertEqual(r.status, 403)
        self.assertNotIn(b"dev-board-1", r.body)
        self.assertNotIn(self.srv.token.encode(), r.body)

    def test_missing_wrong_empty_non_ascii_and_huge_tokens_are_403(self):
        for query in ("", "token=wrong", "token=", "token", "tok=" + "x", "TOKEN=" + "x",
                      "token=%C3%A9%E2%9B%94", "token=é", "token=%FF%FE", "token=" + "A" * 10240,
                      "token=" + self.srv.token + "x", "token=" + self.srv.token[:-1]):
            with self.subTest(query=query[:40]):
                self.assert_refused(self.notes("dev-board-1", query=query))

    def test_a_repeated_token_is_403_even_when_every_copy_is_right(self):
        good = self.srv.token
        for query in ("token=%s&token=%s" % (good, good), "token=%s&token=wrong" % good,
                      "token=wrong&token=%s" % good, "token=%s&token=" % good):
            with self.subTest(query=query[:20]):
                self.assert_refused(self.notes("dev-board-1", query=query))

    def test_the_token_does_not_count_from_a_header(self):
        r = self.notes("dev-board-1", token=None, headers=[("X-Board-Token", self.srv.token)])
        self.assertEqual(r.status, 403)

    def test_a_refused_token_never_tells_roster_members_from_strangers(self):
        member = self.notes("dev-board-1", token="wrong")
        stranger = self.notes("not-on-roster", token="wrong")
        bad_name = self.notes("../x", token="wrong")
        self.assertEqual((member.status, stranger.status, bad_name.status), (403, 403, 403))
        self.assertEqual(member.body, stranger.body)
        self.assertEqual(member.body, bad_name.body)

    def test_a_good_token_then_tells_the_stranger_404(self):
        self.assertEqual(self.notes("not-on-roster").status, 404)


class NameTest(NotesCase):
    def setUp(self):
        super().setUp()
        # what `../x` would reach if the name were joined unchecked, and a file with a matching
        # name next to the roles folder
        self.fx.write("x.notes.md", "CANARY")
        self.fx.write("canary.notes.md", "CANARY")
        self.fx.write("roles/sub/dev-board-1.notes.md", "CANARY")

    def test_bad_names_are_refused_and_no_file_is_read(self):
        for name in ("../x", "..%2fx", "a/b", "a%2fb", "a%2Fb", "%2e%2e", "%2e%2e%2fx", "..", ".",
                     "sub/dev-board-1", "../canary", "dev-board-1/", "dev-board-1%00", "dev-board-1%0a",
                     "DEV-BOARD-1", "Dev-Board-1", "1dev", "-dev", "_dev", "dev board", LONG_NAME, "",
                     "dev-board-1.notes.md", "dev\\board", "é"):
            with self.subTest(name=name):
                r = self.notes(name)
                self.assertIn(r.status, (400, 404))
                self.assertNotIn(b"CANARY", r.body)
                self.assertNotIn(b"line with", r.body)

    def test_the_name_rule_has_no_trailing_newline_loophole(self):
        r = self.notes("dev-board-1%0A")
        self.assertIn(r.status, (400, 404))

    def test_the_longest_allowed_name_is_looked_up_the_33rd_character_is_not(self):
        name32 = LONG_NAME[:32]
        self.fx.roster([MANAGER, {"agent": name32}])
        self.fx.write("roles/%s.notes.md" % name32, "ok 32\n")
        self.assertEqual(self.notes(name32).body, b"ok 32\n")
        self.assertEqual(self.notes(LONG_NAME).status, 400)

    def test_a_good_name_that_is_not_on_the_roster_is_404_and_its_file_is_not_read(self):
        self.fx.write("roles/stranger.notes.md", "CANARY")
        r = self.notes("stranger")
        self.assertEqual(r.status, 404)
        self.assertNotIn(b"CANARY", r.body)

    def test_a_path_under_notes_without_a_name_is_400(self):
        self.assertEqual(self.notes("").status, 400)

    def test_the_roster_is_read_per_request(self):
        self.assertEqual(self.notes("late").status, 404)
        self.fx.roster([MANAGER, {"agent": "late"}])
        self.fx.write("roles/late.notes.md", "late notes\n")
        self.assertEqual(self.notes("late").body, b"late notes\n")


class FileTest(NotesCase):
    def test_a_symlink_leading_out_of_roles_is_404(self):
        outside = self.fx.write("outside.txt", "CANARY")
        os.symlink(str(outside), str(self.fx.root / "roles" / "linked.notes.md"))
        r = self.notes("linked")
        self.assertEqual(r.status, 404)
        self.assertNotIn(b"CANARY", r.body)

    def test_a_symlink_that_stays_inside_roles_is_served(self):
        os.symlink("dev-board-1.notes.md", str(self.fx.root / "roles" / "linked.notes.md"))
        r = self.notes("linked")
        self.assertEqual((r.status, r.body), (200, NOTES.encode("utf-8")))

    def test_a_symlinked_roles_folder_is_judged_by_its_real_path(self):
        real = self.fx.root / "elsewhere"
        real.mkdir()
        (real / "dev-board-1.notes.md").write_text("from the real folder\n")
        for child in (self.fx.root / "roles").iterdir():
            child.unlink()
        (self.fx.root / "roles").rmdir()
        os.symlink(str(real), str(self.fx.root / "roles"))
        self.assertEqual(self.notes("dev-board-1").body, b"from the real folder\n")

    def test_a_directory_named_like_the_file_is_404(self):
        (self.fx.root / "roles" / "dirnamed.notes.md").mkdir()
        self.assertEqual(self.notes("dirnamed").status, 404)

    def test_a_named_pipe_is_404_and_does_not_hang(self):
        os.mkfifo(str(self.fx.root / "roles" / "piped.notes.md"))
        self.assertEqual(self.notes("piped").status, 404)

    def test_a_missing_file_is_404(self):
        r = self.notes("no-file")
        self.assertEqual(r.status, 404)
        self.assertNotIn(str(self.fx.root).encode(), r.body)

    def test_a_missing_roles_folder_is_404(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, {"agent": "dev-board-1"}])
        srv = fx.start(now=NOW)
        r = request(srv.port, "GET", "/notes/dev-board-1?token=" + srv.token)
        self.assertEqual(r.status, 404)

    def test_a_2_mib_file_returns_exactly_its_first_mib(self):
        data = (b"0123456789abcdef" * 131072 * 2)  # 2 MiB
        (self.fx.root / "roles" / "big.notes.md").write_bytes(data)
        r = self.notes("big")
        self.assertEqual(r.status, 200)
        self.assertEqual(len(r.body), 1 << 20)
        self.assertEqual(r.body, data[:1 << 20])

    def test_a_file_of_exactly_1_mib_is_returned_whole(self):
        data = b"x" * (1 << 20)
        (self.fx.root / "roles" / "big.notes.md").write_bytes(data)
        self.assertEqual(self.notes("big").body, data)

    def test_invalid_utf8_is_replaced_not_raised(self):
        (self.fx.root / "roles" / "binary.notes.md").write_bytes(b"ok \xff\xfe\xc3 end\n")
        r = self.notes("binary")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body.decode("utf-8"), "ok ��� end\n")
        self.assertEqual(self.notes("dev-board-1").status, 200)  # the server is still up

    def test_a_cut_inside_a_multibyte_character_is_replaced_not_raised(self):
        data = b"x" * ((1 << 20) - 1) + "é".encode("utf-8")
        (self.fx.root / "roles" / "big.notes.md").write_bytes(data)
        r = self.notes("big")
        self.assertEqual(r.status, 200)
        r.body.decode("utf-8")  # valid UTF-8 whatever the cut
        self.assertTrue(r.body.startswith(b"x" * ((1 << 20) - 1)))

    def test_an_empty_file_is_200_with_an_empty_body(self):
        (self.fx.root / "roles" / "big.notes.md").write_bytes(b"")
        r = self.notes("big")
        self.assertEqual((r.status, r.body), (200, b""))


class DescriptorTest(NotesCase):
    @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "counts the server's open descriptors through /proc")
    def test_every_kind_of_request_closes_what_it_opened(self):
        (self.fx.root / "roles" / "dirnamed.notes.md").mkdir()
        os.mkfifo(str(self.fx.root / "roles" / "piped.notes.md"))
        (self.fx.root / "roles" / "big.notes.md").write_bytes(b"x" * (2 << 20))

        def open_fds():
            return len(os.listdir("/proc/%d/fd" % self.srv.proc.pid))

        def settled():
            # the client sees EOF at the server's shutdown, a moment before the socket closes
            last, deadline = open_fds(), time.monotonic() + 2
            while time.monotonic() < deadline:
                time.sleep(0.05)
                now = open_fds()
                if now == last:
                    return now
                last = now
            return last

        for name in ("dev-board-1", "dirnamed", "piped", "big", "no-file"):  # a warm-up of each path
            self.notes(name)
        before = settled()
        for _ in range(20):
            for name in ("dev-board-1", "dirnamed", "piped", "big", "no-file"):
                self.notes(name)
        self.assertEqual(settled(), before)


class MalformedRequestTest(NotesCase):
    def test_a_space_in_the_target_does_not_echo_the_token_back(self):
        sock = socket.create_connection(("127.0.0.1", self.srv.port), timeout=15)
        try:
            sock.sendall(("GET /notes/dev board?token=%s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n\r\n"
                          % (self.srv.token, self.srv.port)).encode())
            reply = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                reply += chunk
        finally:
            sock.close()
        self.assertTrue(reply.startswith(b"HTTP/1.0 400") or reply.startswith(b"HTTP/1.1 400"), reply[:40])
        self.assertNotIn(self.srv.token.encode(), reply)


class HostAndMethodTest(NotesCase):
    def test_a_foreign_host_is_403_with_a_good_token(self):
        for host in ("evil.example", "evil.example:%d" % self.srv.port, "127.0.0.1", None,
                     "127.0.0.1:1"):
            with self.subTest(host=host):
                r = self.notes("dev-board-1", host=host)
                self.assertEqual(r.status, 403)
                self.assertNotIn(b"line with", r.body)

    def test_a_foreign_origin_is_403(self):
        r = self.notes("dev-board-1", headers=[("Origin", "http://evil.example")])
        self.assertEqual(r.status, 403)
        r = self.notes("dev-board-1", headers=[("Origin", "null")])
        self.assertEqual(r.status, 403)

    def test_the_localhost_host_and_own_origin_are_served(self):
        r = self.notes("dev-board-1", host="localhost:%d" % self.srv.port,
                       headers=[("Origin", "http://localhost:%d" % self.srv.port)])
        self.assertEqual(r.status, 200)

    def test_host_is_checked_before_the_method(self):
        r = self.notes("dev-board-1", method="POST", host="evil.example")
        self.assertEqual(r.status, 403)

    def test_other_methods_are_405_with_and_without_a_token(self):
        for method in ("POST", "PUT", "HEAD", "DELETE", "PATCH", "OPTIONS"):
            for token in ("valid", "wrong", None):
                with self.subTest(method=method, token=token):
                    r = self.notes("dev-board-1", method=method, token=token)
                    self.assertEqual(r.status, 405)
                    self.assertNotIn(b"line with", r.body)

    def test_a_query_value_for_a_different_route_does_not_serve_notes(self):
        self.assertEqual(request(self.srv.port, "GET", "/notes?token=" + self.srv.token).status, 404)
        self.assertEqual(request(self.srv.port, "GET", "/Notes/dev-board-1?token=" + self.srv.token).status, 404)


class TokenSecrecyTest(NotesCase):
    def test_the_token_is_nowhere_but_the_startup_line(self):
        token = self.srv.token
        seen = [self.notes("dev-board-1"), self.notes("dev-board-1", token="wrong"),
                self.notes("no-file"), self.notes("../x"), self.notes("dev-board-1", method="POST"),
                self.notes("dev-board-1", host="evil.example"),
                request(self.srv.port, "GET", "/state"), request(self.srv.port, "GET", "/")]
        for r in seen:
            self.assertNotIn(token.encode(), r.body)
            self.assertNotIn(token, " ".join(k + v for k, v in r.headers.items()))
        self.srv.stop()
        self.assertNotIn(token, self.srv.stderr())
        self.assertEqual(self.srv.stderr(), "")


class SourceGateTest(unittest.TestCase):
    def test_forbidden_constructs_are_absent(self):
        source = BIN.read_text()
        for needle in ("shell=True", "os.system", "eval(", "exec(", "pickle", "Access-Control"):
            self.assertFalse(needle in source, needle)

    def test_the_notes_path_is_built_only_from_the_validated_name(self):
        source = BIN.read_text()
        start = source.index("def read_notes")
        body = source[start:source.index("def handle_notes")]
        self.assertEqual(body.count("os.open("), 1)
        self.assertIn('os.path.join(roles, name + ".notes.md")', body)
        handler = source[source.index("def handle_notes"):source.index("def handle_jump")]
        self.assertLess(handler.index("JUMP_NAME_RE.fullmatch(name)"), handler.index("read_notes("))
        self.assertLess(handler.index("notes_token_ok(handler)"), handler.index("JUMP_NAME_RE.fullmatch(name)"))


if __name__ == "__main__":
    unittest.main()
