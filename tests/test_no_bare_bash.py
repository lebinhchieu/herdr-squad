"""Guard: no code under bin/, hooks/, tools/ launches a bare "bash" or "sh" through subprocess.

On Windows a bare `bash` is C:\Windows\System32\bash.exe (the WSL launcher) or the Store stub; use
squadio.need_bash() / squadio.pick_bash() instead."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ("bin", "hooks", "tools")
CALLS = {"run", "Popen", "call", "check_call", "check_output"}
BARE = {"bash", "sh"}


def bare_bash_calls(source):
    """Line numbers of subprocess.<call>([...]) whose argv list/tuple starts with a bare "bash" or "sh"."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in CALLS
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess" and node.args):
            continue
        argv = node.args[0]
        if isinstance(argv, (ast.List, ast.Tuple)) and argv.elts:
            first = argv.elts[0]
            if isinstance(first, ast.Constant) and first.value in BARE:
                hits.append(node.lineno)
    return hits


def python_sources():
    for d in DIRS:
        for f in sorted((ROOT / d).rglob("*")) if (ROOT / d).is_dir() else ():
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            text = f.read_bytes()[:200].decode("utf-8", "replace")
            if f.suffix == ".py" or (text.startswith("#!") and "python" in text.splitlines()[0]):
                yield f


class NoBareBashTest(unittest.TestCase):
    def test_the_scanner_flags_a_planted_bare_bash(self):
        for bad in ('import subprocess\nsubprocess.run(["bash", "x.sh"])',
                    "import subprocess\nsubprocess.Popen(('sh', '-c', 'x'))",
                    'import subprocess\nsubprocess.check_output(["bash"])'):
            with self.subTest(bad=bad):
                self.assertEqual(len(bare_bash_calls(bad)), 1)

    def test_the_scanner_passes_a_picked_bash_and_other_commands(self):
        for ok in ('import subprocess\nsubprocess.run([need_bash(), "x"])',
                   'import subprocess\nsubprocess.run(["git", "status"])',
                   'import subprocess\nsubprocess.run([bash, "x"])'):
            with self.subTest(ok=ok):
                self.assertEqual(bare_bash_calls(ok), [])

    def test_no_script_under_bin_hooks_tools_launches_a_bare_bash(self):
        files = list(python_sources())
        self.assertTrue(files)
        for f in files:
            with self.subTest(file=f.relative_to(ROOT).as_posix()):
                self.assertEqual(bare_bash_calls(f.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
