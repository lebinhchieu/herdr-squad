"""Guard (T3 / D11): every Python file in bin/ stays safe on Windows, where the default text encoding is
cp1252 and "\\n" is turned into "\\r\\n" on write. The rules are checked on the AST, so strings and comments
never match; a failure names the file and line."""
import ast
import subprocess
import sys
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
SUBPROCESS_CALLS = {"run", "Popen", "check_output", "check_call", "call"}
WRITE_CHARS = set("wax+")


def kw(call, name):
    return next((k.value for k in call.keywords if k.arg == name), None)


def is_true(node):
    return isinstance(node, ast.Constant) and node.value is True


def is_lf(node):
    return isinstance(node, ast.Constant) and node.value == "\n"


def call_name(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id, None
    if isinstance(f, ast.Attribute):
        return f.attr, f.value.id if isinstance(f.value, ast.Name) else None
    return None, None


def mode_node(call, name, owner):
    """The mode argument of open() / Path.open() / os.fdopen(), or None when it is left out (text read)."""
    if (m := kw(call, "mode")) is not None:
        return m
    pos = 0 if name == "open" and owner not in (None, "io", "builtins") else 1
    return call.args[pos] if len(call.args) > pos else None


def scan(source, name="<src>"):
    """Rule violations of one Python source as 'name:line: message'."""
    tree = ast.parse(source)
    out = []

    def bad(node, msg):
        out.append(f"{name}:{node.lineno}: {msg}")

    for node in tree.body:  # (d) a top-level import; a try/except guarded one is fine
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "fcntl" for a in node.names):
            bad(node, "module-level `import fcntl` (does not exist on Windows; guard it with try/except ImportError)")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "fcntl":
            bad(node, "module-level `from fcntl import` (does not exist on Windows)")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn, owner = call_name(node)
        has_enc, nl = kw(node, "encoding") is not None, kw(node, "newline")
        method = isinstance(node.func, ast.Attribute)  # a bare read_text(path) is a module's own helper
        if fn == "write_text" and method:  # (a)(b) no way to say newline="\n" before Python 3.10, and 3.10+ only
            bad(node, "write_text() (use open(p, 'w', encoding='utf-8', newline='\\n'))")
        elif fn == "read_text" and method and not has_enc:
            bad(node, "read_text() without encoding=")
        elif fn in ("open", "fdopen") and not (owner == "os" and fn == "open"):
            if fn == "open" and owner not in (None, "io", "builtins") and not isinstance(node.func.value, ast.Name):
                pass  # e.g. a chained call result; the mode rules below still apply to Path.open()
            mode = mode_node(node, fn, owner)
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
                if "b" in mode.value:
                    continue  # a literal binary mode is exempt
                writes = bool(WRITE_CHARS & set(mode.value))
            elif mode is None:
                writes = False
            else:  # a mode that is not a literal: needs both
                writes = True
            if not has_enc:
                bad(node, f"{fn}() in text mode without encoding=")
            if writes and not is_lf(nl):
                bad(node, f"{fn}() writes text without newline='\\n'")
        elif fn in SUBPROCESS_CALLS and owner == "subprocess":  # (c)
            if (is_true(kw(node, "text")) or is_true(kw(node, "universal_newlines"))) and not has_enc:
                bad(node, f"subprocess.{fn}() with text=True / universal_newlines=True without encoding=")
    return out


def main_calls_utf8_stdio(source):
    """(e) True when the file has no `main`, or its main calls utf8_stdio()."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            return any(isinstance(c, ast.Call) and call_name(c)[0] == "utf8_stdio" for c in ast.walk(node))
    return True


def python_files():
    for p in sorted(BIN.iterdir()):
        if p.is_file() and p.suffix != ".pyc":
            head = p.read_text(encoding="utf-8").split("\n", 1)[0]
            if p.suffix == ".py" or ("python" in head and head.startswith("#!")):
                yield p


class BinIsWindowsSafe(unittest.TestCase):
    def test_every_python_file_in_bin_follows_the_rules(self):
        files = list(python_files())
        self.assertGreaterEqual(len(files), 10, files)  # the scan really found the scripts
        found = [v for p in files for v in scan(p.read_text(encoding="utf-8"), f"bin/{p.name}")]
        self.assertEqual(found, [])

    def test_every_cli_with_a_main_calls_utf8_stdio(self):
        missing = [p.name for p in python_files() if not main_calls_utf8_stdio(p.read_text(encoding="utf-8"))]
        self.assertEqual(missing, [])

    def test_the_known_clis_are_among_the_files_checked(self):
        names = {p.name for p in python_files()}
        for n in ("squad-label", "squad-usage", "squad-migrate", "squad-notify", "squad-start", "squad-inbox",
                  "squad-process", "processlint.py", "squadinbox.py", "squadio.py"):
            self.assertIn(n, names)

    def test_write_calls_in_usage_migrate_and_notify_carry_newline_lf(self):
        for n in ("squad-usage", "squad-migrate"):
            src = (BIN / n).read_text(encoding="utf-8")
            self.assertEqual(scan(src, n), [])
            self.assertIn('newline="\\n"', src)  # they do write text
        # squad-notify writes only bytes to a tty; it must stay free of text writes without newline
        self.assertEqual(scan((BIN / "squad-notify").read_text(encoding="utf-8"), "squad-notify"), [])

    def test_a_tab_label_cli_cannot_lose_its_utf8_stdio_call(self):
        self.assertTrue(main_calls_utf8_stdio("def main():\n    squadio.utf8_stdio()\n"))


class RulesCatchABadLine(unittest.TestCase):
    """The scanner itself: each bad line is caught, each good one is not."""

    BAD = {
        "open without encoding": "open(p)\n",
        "open w without encoding": "open(p, 'w', newline='\\n')\n",
        "open w without newline": "open(p, 'w', encoding='utf-8')\n",
        "open mode kwarg": "open(p, mode='a', encoding='utf-8')\n",
        "mode variable": "open(p, m, encoding='utf-8')\n",
        "Path.open": "p.open('w', encoding='utf-8')\n",
        "read_text": "p.read_text()\n",
        "write_text": "p.write_text('x', encoding='utf-8')\n",
        "write_text newline": "p.write_text('x', encoding='utf-8', newline='\\n')\n",
        "fdopen w": "os.fdopen(fd, 'w')\n",
        "run text": "subprocess.run(['x'], text=True)\n",
        "run universal_newlines": "subprocess.check_output(['x'], universal_newlines=True)\n",
        "Popen text": "subprocess.Popen(['x'], text=True)\n",
        "import fcntl": "import fcntl\n",
        "from fcntl": "from fcntl import flock\n",
    }
    GOOD = {
        "read": "open(p, encoding='utf-8')\n",
        "write": "open(p, 'w', encoding='utf-8', newline='\\n')\n",
        "binary": "open(p, 'rb')\nopen(p, 'wb')\nopen(p, 'ab')\nos.fdopen(fd, 'wb')\n",
        "os.open": "os.open(p, os.O_RDONLY)\n",
        "run": "subprocess.run(['x'], text=True, encoding='utf-8')\nsubprocess.run(['x'])\n",
        "guarded fcntl": "try:\n    import fcntl\nexcept ImportError:\n    fcntl = None\n",
        "bare read_text helper": "read_text(path)\n",
        "strings and comments": "x = 'open(p)'  # p.write_text(x)\n",
    }

    def test_each_bad_line_is_caught_with_its_line_number(self):
        for label, src in self.BAD.items():
            with self.subTest(label):
                found = scan("x = 1\n" + src, "f")
                self.assertTrue(found and found[0].startswith("f:2:"), found)

    def test_each_good_line_passes(self):
        for label, src in self.GOOD.items():
            with self.subTest(label):
                self.assertEqual(scan(src, "f"), [])

    def test_a_main_without_utf8_stdio_is_caught(self):
        self.assertFalse(main_calls_utf8_stdio("def main():\n    pass\n"))


class GitAttributes(unittest.TestCase):
    ROOT = BIN.parent

    def git(self, *a):
        return subprocess.run(["git", *a], cwd=self.ROOT, capture_output=True, text=True, encoding="utf-8", timeout=60)

    def test_the_file_has_the_two_rules(self):
        lines = (self.ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, ["* text=auto eol=lf", "bin/* text eol=lf"])

    def test_bin_files_are_text_with_eol_lf(self):
        r = self.git("check-attr", "eol", "text", "--", "bin/squad-spawn", "bin/squadinbox.py")
        self.assertEqual(r.returncode, 0, r.stderr)
        for f in ("bin/squad-spawn", "bin/squadinbox.py"):
            self.assertIn(f"{f}: eol: lf", r.stdout)
            self.assertIn(f"{f}: text: set", r.stdout)

    def test_no_tracked_file_is_crlf_in_the_index_or_the_worktree(self):
        r = self.git("ls-files", "--eol")
        self.assertEqual(r.returncode, 0, r.stderr)
        crlf = [l for l in r.stdout.splitlines() if "i/crlf" in l or "w/crlf" in l]
        self.assertEqual(crlf, [])


if __name__ == "__main__":
    sys.exit(unittest.main())
