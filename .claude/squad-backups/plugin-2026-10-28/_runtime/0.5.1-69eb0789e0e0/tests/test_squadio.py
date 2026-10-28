import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "bin"))
import squadio  # noqa: E402

TEXT = "→ 🦀 é"


def win_out():
    raw = io.BytesIO()
    return raw, io.TextIOWrapper(raw, encoding="cp1252", newline="\r\n")


class Utf8StdioTest(unittest.TestCase):
    def setUp(self):
        self.saved = (sys.stdin, sys.stdout, sys.stderr)
        self.addCleanup(lambda: (setattr(sys, "stdin", self.saved[0]),
                                 setattr(sys, "stdout", self.saved[1]),
                                 setattr(sys, "stderr", self.saved[2])))

    def test_stdout_and_stderr_are_utf8_lf(self):
        for name in ("stdout", "stderr"):
            raw, wrapper = win_out()
            setattr(sys, name, wrapper)
            squadio.utf8_stdio()
            print(TEXT, file=wrapper)
            wrapper.flush()
            self.assertEqual(raw.getvalue(), (TEXT + "\n").encode("utf-8"), name)

    def test_stdin_reads_utf8(self):
        sys.stdin = io.TextIOWrapper(io.BytesIO(TEXT.encode("utf-8")), encoding="cp1252")
        squadio.utf8_stdio()
        self.assertEqual(sys.stdin.read(), TEXT)

    def test_none_and_stringio_do_not_raise(self):
        sys.stdin = sys.stdout = sys.stderr = None
        squadio.utf8_stdio()
        sys.stdin, sys.stdout, sys.stderr = io.StringIO(), io.StringIO(), io.StringIO()
        squadio.utf8_stdio()

    def test_idempotent(self):
        raw, wrapper = win_out()
        sys.stdout = wrapper
        squadio.utf8_stdio()
        squadio.utf8_stdio()
        print(TEXT, file=wrapper)
        wrapper.flush()
        self.assertEqual(raw.getvalue(), (TEXT + "\n").encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
