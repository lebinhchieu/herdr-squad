"""T2b: the helper CLIs under a simulated Windows locale (PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252).

Bytes are compared, never read back through the same code (design.md, test method)."""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
WIN = {"PYTHONUTF8": "0", "LC_ALL": "C", "PYTHONIOENCODING": "cp1252"}
ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "dev", "designer", "token-coach")
# The tab label has the byte 0x90 (U+1F980 is f0 9f a6 80; "🦀 Manager" is the label QA blackbox measured).
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "workspace get") echo '{"result":{"workspace":{"label":"w"}}}' ;;
  "tab get") echo '{"result":{"tab":{"label":"🦀 Manager"}}}' ;;
  "agent list") echo '{"result":{"agents":[]}}' ;;
  "agent get") echo '{"error":{"code":"agent_not_found"}}'; exit 1 ;;
  "tab create") echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1","label":"🦀 Manager"}}}' ;;
esac
exit 0
"""


def run(cmd, env, stdin=None, timeout=30):
    """Child with UTF-8 bytes for argv/env; stdout/stderr come back as bytes."""
    enc = lambda x: str(x).encode("utf-8", "surrogateescape")
    return subprocess.run([enc(c) for c in cmd], env={enc(k): enc(v) for k, v in env.items()}, input=stdin,
                          capture_output=True, timeout=timeout)


def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(BIN / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.proj = self.root / os.fsdecode("with space 🦀".encode("utf-8"))
        self.squad = self.proj / ".claude" / "squads" / "t"
        self.scope = self.squad / "scopes" / "s1"
        self.scope.mkdir(parents=True)
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        (self.scope / "scope.md").write_text("team: ba, team-lead, tech-lead, qa-white, qa-black, designer, architect\n", encoding="utf-8")
        (self.scope / "roster.md").write_text("| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n",
                                              encoding="utf-8", newline="\n")
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR", "HERDR"))}
        self.env.update(WIN, HERDR_ENV="1", PYTHONDONTWRITEBYTECODE="1", HERDR_LOG=str(self.log), HOME=str(self.home), SQUAD_DIR=str(self.squad),
                        SCOPE_DIR=str(self.scope), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, name, *args, **kw):
        return run([BIN / name, *args], self.env, **kw)

    def assert_clean(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        # a legacy squad fixture prints exactly these two notices (ticket 24 / squad-process), nothing else
        notices = (b"squad-process: no `plugin:` pin in the home; composing from the running plugin",
                   b"legacy squad: plugin rules attached, local process.md edits not applied; run squad-process adopt --dry-run")
        extra = [ln for ln in r.stderr.split(b"\n") if ln and ln not in notices]
        self.assertEqual(extra, [], r.stderr)


class LabelAndSpawnTest(Base):
    def test_label_prints_the_emoji_label_as_utf8_with_lf(self):
        r = self.cli("squad-label", "--init", "--agent", "dev-2", "--role", "dev", "--home", self.scope, "--title", "TAB-02 tabs")
        self.assert_clean(r)
        self.assertEqual(r.stdout, "🤖 Dev · TAB-02 tabs\n".encode("utf-8"))

    def test_label_reads_a_herdr_reply_with_emoji_on_the_calls_it_makes(self):
        # squad-label calls agent list / agent get / tab rename; the emoji must be on those replies, or the
        # utf-8 decode in herdr() is never exercised (a cp1252 decode error would drop the live peer silently).
        peer = (
            '#!/usr/bin/env bash\necho "$@" >> "$HERDR_LOG"\ncase "$1 $2" in\n'
            '  "agent list") echo \'{"result":{"agents":[{"name":"dev-1","tab_id":"t-dev-1","note":"🦀"}]}}\' ;;\n'
            '  "agent get") echo \'{"result":{"agent":{"name":"dev-1","tab_id":"t-dev-1","note":"🦀"}}}\' ;;\n'
            '  "tab rename") echo "🦀" ;;\nesac\nexit 0\n')
        (self.root / "fakebin" / "herdr").write_text(peer, encoding="utf-8", newline="\n")
        (self.scope / "labels").mkdir()
        (self.scope / "labels" / "dev-1.json").write_text(
            json.dumps({"agent": "dev-1", "role": "dev", "number": None, "title": "TAB-01"}), encoding="utf-8")
        r = self.cli("squad-label", "--init", "--agent", "dev-2", "--role", "dev", "--home", self.scope, "--title", "TAB-02")
        # Not assert_clean: under LC_ALL=C the emoji argv of `tab rename` cannot be encoded by this Linux child
        # (a sim artifact; Windows argv is UTF-16), so the rename warning is expected here.
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "🤖 Dev 2 · TAB-02\n".encode("utf-8"))
        self.assertIn(b"agent get dev-1", self.log.read_bytes())

    def test_spawn_dry_run_and_stubbed_run_for_every_role_with_a_space_and_emoji_path(self):
        for role in ROLES:
            for dry in (True, False):
                with self.subTest(role=role, dry=dry):
                    self.log.unlink(missing_ok=True)
                    args = [role, f"{role}-x", "--scope", "s1", "--title", "TAB-02 tabs", "--prompt", "hello", *(["--dry-run"] if dry else [])]
                    r = self.cli("squad-spawn", *args)
                    self.assert_clean(r)
                    self.assertNotIn(b"squad-label --init failed", r.stderr)
                    if dry:
                        self.assertIn("🦀".encode("utf-8"), r.stdout)
                    else:
                        self.assertIn(b"tab create", self.log.read_bytes())


class UsageTest(Base):
    ROSTER = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n| dev-1 | dev | s1 | café 🦀 | live | sid-1 |\n"

    def test_get_and_set_session_keep_utf8_and_lf(self):
        roster = self.scope / "roster.md"
        roster.write_bytes(self.ROSTER.encode("utf-8"))
        r = self.cli("squad-usage", "--get", "dev-1")
        self.assert_clean(r)
        self.assertEqual(r.stdout, b"dev\ts1\tsid-1\n")
        self.assert_clean(self.cli("squad-usage", "--set-session", "dev-1", "sid-2", "--role", "dev", "--scope", "s1"))
        raw = roster.read_bytes()
        self.assertIn("café 🦀".encode("utf-8"), raw)
        self.assertIn(b"sid-2", raw)
        self.assertNotIn(b"\r", raw)

    def test_check_with_no_transcript_found_is_silent_and_exits_0(self):
        r = self.cli("squad-usage", "--check", "no-such-session")
        self.assert_clean(r)
        self.assertEqual(r.stdout, b"")

    @unittest.skipUnless(shutil.which("jq"), "jq")
    def test_the_stop_hook_with_no_transcript_exits_0_silently(self):
        env = {**self.env, "SQUAD_NAME": "dev-1", "SQUAD_ROLE": "dev"}
        r = run([BIN / "squad-usage-hook"], env, stdin=json.dumps({"session_id": "nope"}).encode())
        self.assert_clean(r)


class NotifyTest(Base):
    def test_a_missing_proc_prints_nothing_and_raises_nothing(self):
        sn = load("squad-notify")
        cfg = self.root / "config.toml"
        cfg.write_text('[ui.toast]\ndelivery = "off"\n', encoding="utf-8")
        env = {"HERDR_ENV": "1", "HERDR_CONFIG_PATH": str(cfg), "HERDR_BIN_PATH": str(self.root / "fakebin" / "herdr")}
        import contextlib
        import io
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()) as out:
            sn.run({"hook_event_name": "Stop"}, env, proc_root=str(self.root / "no-proc"))
        self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))

    def test_the_cli_reads_utf8_stdin_and_exits_0(self):
        r = self.cli("squad-notify", stdin=json.dumps({"hook_event_name": "Stop", "x": "🦀"}, ensure_ascii=False).encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr)


class MigrateTest(Base):
    def test_a_flat_squad_with_non_ascii_text_migrates_to_utf8_lf(self):
        flat = self.root / "flat" / ".claude" / "squads" / "f"
        flat.mkdir(parents=True)
        (flat / "process.md").write_text("x", encoding="utf-8")
        (flat / "goal.md").write_bytes("# G\n\n**Fix café 🦀**\n".encode("utf-8"))
        (flat / "roster.md").write_bytes("| Agent | Role |\n|---|---|\n| a | dev |\n".encode("utf-8"))
        r = self.cli("squad-migrate", flat, "--to", "per-scope", "--scope", "s1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(b"Traceback", r.stderr)
        raw = (flat / "scopes" / "s1" / "scope.md").read_bytes()
        self.assertIn("café 🦀".encode("utf-8"), raw)
        self.assertNotIn(b"\r", raw)


class JqTest(Base):
    def no_jq_path(self):
        d = self.root / "nojq"
        d.mkdir()
        for tool in ("bash", "dirname", "readlink", "cat", "date", "basename", "env", "python3"):
            real = shutil.which(tool)
            if real:
                (d / tool).symlink_to(real)
        (d / "herdr").symlink_to(self.root / "fakebin" / "herdr")
        return str(d)

    def test_respawn_and_retire_stop_with_one_line_naming_jq_before_herdr(self):
        self.env["PATH"] = self.no_jq_path()
        for name in ("squad-respawn", "squad-retire"):
            with self.subTest(name=name):
                r = run(["bash", BIN / name, "dev-1"], self.env)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual(len(r.stderr.decode().splitlines()), 1, r.stderr)
                self.assertIn(b"jq", r.stderr)
                self.assertFalse(self.log.exists())

    def test_log_message_logs_nothing_says_one_line_and_exits_0(self):
        self.env.update(PATH=self.no_jq_path(), SQUAD_NAME="dev-1")
        r = run(["bash", BIN / "squad-log-message"], self.env, stdin=b'{"tool_name":"SendMessage"}')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(r.stderr.decode().splitlines()), 1, r.stderr)
        self.assertIn(b"jq", r.stderr)
        self.assertFalse((self.scope / "messages.jsonl").exists())


class CloseTest(unittest.TestCase):
    def test_the_inline_python_runs_in_utf8_mode(self):
        self.assertIn("python3 -X utf8 -c '", (BIN / "squad-close").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
