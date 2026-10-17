"""Task B: --body-file stores LF only, whatever line ending the file has."""
import sys
import unittest
from pathlib import Path

from test_squadinbox import Base, listing, run

sys.dont_write_bytecode = True

TEXT = "line one\nline two\n\n- bullet\n"


class BodyFileLineEndings(Base):
    def add(self, name, data, kind="answer"):
        f = Path(self.tmp) / name
        f.write_bytes(data)
        args = ["add", "--kind", kind, "--title", "T" + name, "--body-file", str(f)]
        if kind == "answer":
            args += ["--options", "(a) yes; (b) no"]
        r = run(self.home, *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def stored(self, kind="answer"):
        out = {}
        for name, data in (("lf", TEXT), ("crlf", TEXT.replace("\n", "\r\n")), ("cr", TEXT.replace("\n", "\r"))):
            self.add(name, data.encode("utf-8"), kind)
        for i in listing(self.home)["items"]:
            if i["title"] in ("Tlf", "Tcrlf", "Tcr"):
                out[i["title"][1:]] = i["body"].replace(i["title"] + "<br>", "", 1)
        return out

    def test_answer_row_same_for_lf_crlf_cr(self):
        got = self.stored()
        self.assertEqual(got["crlf"], got["lf"])
        self.assertEqual(got["cr"], got["lf"])
        self.assertNotIn("\r", got["crlf"] + got["cr"])
        self.assertEqual(got["lf"], "line one<br>line two<br><br>- bullet")

    def test_escalation_file_has_no_cr(self):
        self.add("crlf", TEXT.replace("\n", "\r\n").encode("utf-8"))
        self.add("cr", TEXT.replace("\n", "\r").encode("utf-8"))
        data = (self.home / "escalations.md").read_bytes()
        fixture = (Path(__file__).parent / "fixtures" / "inbox" / "home" / "escalations.md").read_bytes()
        self.assertEqual(data.count(b"\r"), fixture.count(b"\r"))
        self.assertEqual(data.count(b"line one<br>line two<br><br>- bullet |"), 2)

    def test_read_item_same_for_lf_crlf_cr(self):
        got = self.stored("read")
        self.assertEqual(got["crlf"], got["lf"])
        self.assertEqual(got["cr"], got["lf"])
        self.assertNotIn("\r", got["cr"])

    def test_stdin_body_is_normalised(self):
        r = run(self.home, "add", "--kind", "read", "--title", "Tstdin", stdin="a\r\nb\rc")
        self.assertEqual(r.returncode, 0, r.stderr)
        body = [i for i in listing(self.home)["items"] if i["title"] == "Tstdin"][0]["body"]
        self.assertEqual(body, "a\nb\nc")

    def test_empty_or_only_crlf_body_is_still_refused(self):
        for name, data in (("empty", b""), ("crlf", b"\r\n\r\n"), ("cr", b"\r\r")):
            f = Path(self.tmp) / name
            f.write_bytes(data)
            before = (self.home / "escalations.md").read_bytes()
            r = run(self.home, "add", "--kind", "answer", "--title", "T", "--body-file", str(f))
            self.assertNotEqual(r.returncode, 0, name)
            self.assertIn("needs a body", r.stderr)
            self.assertEqual((self.home / "escalations.md").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
