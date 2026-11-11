"""squad-respawn: same name, role, scope and worktree; new session id in roster.md; old pane closed last."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
import winlaunch
from squadtest import BIN, clean_env, fake_herdr, git, load_cli

_DEV = json.loads((BIN.parent / "templates/squad/settings/dev.json").read_text(encoding="utf-8"))
DEV = (_DEV["model"], _DEV["effortLevel"])


class RespawnTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = self.root / ".claude" / "squads" / "t"
        self.squad.mkdir(parents=True)
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        (self.squad / "scope.md").write_text("team: none\n", encoding="utf-8")  # decided: a non-Manager compose of an undecided home exits 2
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            "| manager | Manager | all | x | live | |\n| dev-1 | Dev | settings | task 1 | live | old-sid |\n", encoding="utf-8")
        fake = self.root / "fakebin"
        fake.mkdir()
        fake_herdr(fake, "live")
        self.log = self.root / "herdr.log"
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{fake}:{os.environ['PATH']}")

        self.put_notes("dev-1")  # squad-respawn refuses an agent without fresh notes

    def tearDown(self):
        self.tmp.cleanup()

    def put_notes(self, agent, home=None, text="Now: x\n"):
        path = (home or self.squad) / "roles" / f"{agent}.notes.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def respawn(self, *args):
        return winlaunch.run_script(BIN / "squad-respawn", ["dev-1", *args], env=self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=20)

    def test_dev_keeps_worktree_and_branch_and_roster_gets_new_session(self):
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        wt = self.root / ".worktrees" / "t" / "dev-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/t/dev-1", cwd=repo)
        (wt / "wip.txt").write_text("uncommitted", encoding="utf-8")

        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)

        log = self.log.read_text(encoding="utf-8").splitlines()
        self.assertIn(f"tab create --cwd {Path(wt).as_posix()} --label 🤖 Dev --no-focus", " ".join(log))
        self.assertTrue(any(re.fullmatch(r"agent rename dev-1 prev-\d+", l) for l in log))
        self.assertEqual(log[-1], "pane close p-dev-1")  # old pane goes last
        start = next(l for l in log if l.startswith("agent start dev-1"))
        self.assertIn("--agent squad:dev", start)
        self.assertIn(f"--model {DEV[0]} --effort {DEV[1]}", start)  # from settings/dev.json
        sid = re.search(r"--session-id (\S+)", start).group(1)
        self.assertIn(f"| dev-1 | Dev | settings | task 1 | live | {sid} |", (self.squad / "roster.md").read_text(encoding="utf-8"))
        prompt = next(l for l in log if l.startswith("agent prompt"))
        self.assertIn("roles/dev-1.notes.md", prompt)

        self.assertEqual((wt / "wip.txt").read_text(encoding="utf-8"), "uncommitted")
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=wt, text=True, encoding="utf-8", capture_output=True).stdout.strip()
        self.assertEqual(branch, "squad/t/dev-1")
        self.assertFalse(any("worktree add" in l for l in log))

    def test_agent_without_worktree_respawns_in_project_dir(self):
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"tab create --cwd {Path(self.root).as_posix()} --label 🤖 Dev", self.log.read_text(encoding="utf-8"))

    def test_manager_row_as_written_by_squad_spawn_respawns_with_role_and_notes(self):
        # squad-start spawns manager-t; squad-spawn --set-session adds this row (empty scope, empty Owns).
        with (self.squad / "roster.md").open("a", encoding="utf-8") as f:
            f.write("| manager-t | manager |  |  | live | old-sid |\n")
        self.put_notes("manager-t")
        r = winlaunch.run_script(BIN / "squad-respawn", ["manager-t"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log.read_text(encoding="utf-8").splitlines()
        start = next(l for l in log if l.startswith("agent start manager-t"))
        self.assertIn("--agent squad:manager", start)
        sid = re.search(r"--session-id (\S+)", start).group(1)
        self.assertIn(f"| manager-t | manager |  |  | live | {sid} |", (self.squad / "roster.md").read_text(encoding="utf-8"))
        self.assertIn(f"tab create --cwd {Path(self.root).as_posix()} --label 🦀 Manager", " ".join(log))
        self.assertIn("SQUAD_SCOPE=", " ".join(log))
        self.assertNotIn("SQUAD_SCOPE=old-sid", " ".join(log))  # an empty scope must not shift the columns
        self.assertEqual(log[-1], "pane close p-manager-t")
        prompt = next(l for l in log if l.startswith("agent prompt"))
        self.assertIn("roles/manager-t.notes.md", prompt)

    def dry_prompt(self, agent, role):
        with (self.squad / "roster.md").open("a", encoding="utf-8") as f:
            f.write(f"| {agent} | {role} |  |  | live | old-sid |\n")
        self.put_notes(agent)
        r = winlaunch.run_script(BIN / "squad-respawn", [agent, "--dry-run"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_legacy_prompt_names_the_notes_and_neither_process_md_nor_show(self):
        for agent, role in (("d2", "Dev"), ("w1", "QA whitebox"), ("b1", "QA blackbox"), ("ux", "Designer"),
                            ("m1", "Manager"), ("t1", "Tech Lead"), ("l1", "Team Lead")):
            out = self.dry_prompt(agent, role)
            self.assertIn(f"Read your notes $SQUAD_DIR/roles/{agent}.notes.md and continue from them.", out)
            self.assertNotIn("process.md", out)
            self.assertNotIn("show", out)

    def test_respawn_of_a_legacy_agent_reproduces_the_rules_attachment(self):
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        rules = self.squad / "roles" / "dev-1.rules.md"
        start = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent start dev-1"))
        self.assertIn(f"--append-system-prompt-file {Path(rules).as_posix()}", start)
        self.assertIn("--setting-sources project,local", start)  # a respawn starts lean too (squad-spawn builds the line)
        self.assertTrue(rules.read_text(encoding="utf-8").startswith("# Your process rules"))
        self.assertEqual(r.stderr.count("legacy squad: plugin rules attached"), 1)

    def test_respawn_brings_back_the_title_and_the_number(self):
        init = winlaunch.run_script(BIN / "squad-label", ["--init", "--home", str(self.squad), "--agent", "dev-1", "--role", "dev", "--title", "plan"], env=self.env, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(init.returncode, 0, init.stderr)
        self.log.write_text("", encoding="utf-8")
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--label 🤖 Dev · plan --no-focus", self.log.read_text(encoding="utf-8"))

    def test_an_agent_with_no_stored_entry_respawns_with_a_label_without_title(self):
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(" · ", next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("tab create")))

    def test_every_rename_argument_is_a_valid_herdr_name_even_for_a_32_character_agent(self):
        name = "squad-board-dev-squad-tabs-2xxxxx"[:32]
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            f"| {name} | Dev | settings | task | live | old-sid |\n", encoding="utf-8")
        self.put_notes(name)
        r = winlaunch.run_script(BIN / "squad-respawn", [name], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        renames = [l.split()[2:] for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent rename")]
        self.assertTrue(renames)
        for arg in (a for pair in renames for a in pair):
            self.assertRegex(arg, r"^[a-z][a-z0-9_-]{0,31}$")

    def test_a_failing_spawn_renames_the_old_agent_back(self):
        stub = self.root / "plugin"
        (stub / "bin").mkdir(parents=True)
        for f in ("squad-respawn", "squad-usage", "squad-label", "squadlabel.py", "squadio.py", "squadtranscript.py"):
            shutil.copy(BIN / f, stub / "bin" / f)
        (stub / "bin" / "squad-spawn").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (stub / "bin" / "squad-spawn").chmod(0o755)
        r = winlaunch.run_script(stub / "bin" / "squad-respawn", ["dev-1"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 1)
        renames = [l.split() for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent rename")]
        self.assertEqual(renames[1][2:], [renames[0][3], "dev-1"])
        self.assertNotIn("pane close", self.log.read_text(encoding="utf-8"))

    def test_warns_when_notes_are_over_100_lines(self):
        self.put_notes("dev-1", text="line\n" * 101)
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("101 lines", r.stderr)
        self.assertIn("squad-process rule NOTE-1", r.stderr)  # AC4: the pointer is a command that exists
        self.assertNotIn("→ Notes", r.stderr)

    def test_missing_notes_refuse_with_one_line_and_start_nothing(self):
        (self.squad / "roles" / "dev-1.notes.md").unlink()
        r = self.respawn()
        self.assertEqual(r.returncode, 1)
        lines = r.stderr.strip().splitlines()
        self.assertEqual(len(lines), 1, r.stderr)
        self.assertIn("dev-1.notes.md", lines[0])
        self.assertIn("NOTE-1", lines[0])
        self.assertFalse(self.log.exists() and self.log.read_text(encoding="utf-8").strip())  # no rename, no spawn, no close

    def test_notes_older_than_10_minutes_warn_and_go_on(self):
        notes = self.put_notes("dev-1")
        old = notes.stat().st_mtime - 11 * 60
        os.utime(notes, (old, old))
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("11 min old", r.stderr)
        self.assertIn("agent start dev-1", self.log.read_text(encoding="utf-8"))
        self.put_notes("dev-1")  # touched now: no warning
        self.assertNotIn("10 minutes", self.respawn().stderr)

    def test_force_skips_the_old_notes_warning(self):
        notes = self.squad / "roles" / "dev-1.notes.md"
        old = notes.stat().st_mtime - 60 * 60
        os.utime(notes, (old, old))
        r = self.respawn("--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("10 minutes", r.stderr)

    def test_force_skips_the_missing_notes_check(self):
        (self.squad / "roles" / "dev-1.notes.md").unlink()
        r = self.respawn("--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("agent start dev-1", self.log.read_text(encoding="utf-8"))

    def test_dry_run_is_unchanged_without_notes(self):
        (self.squad / "roles" / "dev-1.notes.md").unlink()
        r = self.respawn("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would run: herdr agent rename dev-1", r.stdout)
        self.assertIn("dev-1.notes.md is missing", r.stderr)  # said on stderr, not refused
        self.assertIn("NOTE-1", r.stderr)

    def test_an_unknown_flag_prints_usage_and_exits_2_without_starting_anything(self):
        r = self.respawn("--dryrun")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Usage: squad-respawn", r.stderr)
        self.assertFalse(self.log.exists() and self.log.read_text(encoding="utf-8").strip())

    # --- the respawn event in usage-events.jsonl (task 17) ---
    def events(self, home=None):
        path = (home or self.squad) / "usage-events.jsonl"
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def failing_spawn_stub(self):
        """A plugin copy whose squad-spawn fails: the run gets past every refusal and stops at the spawn."""
        stub = self.root / "plugin"
        (stub / "bin").mkdir(parents=True)
        for f in ("squad-respawn", "squad-usage", "squad-label", "squadlabel.py", "squadio.py", "squadtranscript.py"):
            shutil.copy(BIN / f, stub / "bin" / f)
        (stub / "bin" / "squad-spawn").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (stub / "bin" / "squad-spawn").chmod(0o755)
        return stub / "bin" / "squad-respawn"

    def test_a_respawn_appends_one_event_line_before_the_spawn(self):  # AC1, T1, T2
        events = self.squad / "usage-events.jsonl"
        events.write_bytes(b'{"keep":"me"}\n')
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        old, line = events.read_bytes().split(b"\n", 1)[0], self.events()[1]
        self.assertEqual(old, b'{"keep":"me"}')  # appended, never rewritten
        ev = json.loads(line)
        self.assertRegex(ev["ts"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
        self.assertEqual((ev["rule"], ev["agent"], ev["role"]), ("respawn", "dev-1", "dev"))
        self.assertEqual(len(self.events()), 2)

    def test_no_event_when_the_run_is_refused_or_a_dry_run(self):  # AC2: missing notes, no live agent, --dry-run
        (self.squad / "roles" / "dev-1.notes.md").unlink()
        self.assertEqual(self.respawn().returncode, 1)  # refused: notes missing
        self.put_notes("dev-1")
        self.env["DEAD"] = "dev-1"
        r = self.respawn()
        self.assertEqual(r.returncode, 1)  # refused: no live agent
        del self.env["DEAD"]
        self.assertEqual(self.respawn("--dry-run").returncode, 0)
        self.assertEqual(self.events(), [])

    def test_a_spawn_that_fails_leaves_the_event(self):  # T4: the line comes before the squad-spawn call
        r = winlaunch.run_script(self.failing_spawn_stub(), ["dev-1"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 1)
        self.assertEqual([json.loads(l)["rule"] for l in self.events()], ["respawn"])

    def test_an_unwritable_log_warns_once_and_the_respawn_goes_on(self):  # T5
        (self.squad / "usage-events.jsonl").mkdir()
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr.count("could not write the respawn event"), 1)
        self.assertIn("agent start dev-1", self.log.read_text(encoding="utf-8"))

    def test_a_held_lock_does_not_hang_the_event_and_the_line_is_written_without_flock(self):  # T3: the mkdir-lock branch
        tools = self.root / "tools"
        tools.mkdir()
        for name in ("bash", "sh", "env", "basename", "ls", "jq", "date", "find", "stat", "wc", "tr", "sed", "dirname", "readlink", "sleep",
                     "mkdir", "rmdir", "cat", "python3", "awk", "grep", "git", "head", "tail", "cut", "sort", "mv", "rm", "uname", "id"):
            found = shutil.which(name)
            if found:
                (tools / name).symlink_to(found)
        shutil.copy(self.root / "fakebin" / "herdr", tools / "herdr")
        env = dict(self.env, PATH=str(tools))
        self.assertIsNone(shutil.which("flock", path=str(tools)))
        (self.squad / "usage-events.jsonl.lock").mkdir()  # a writer that never lets go
        start = time.monotonic()
        r = winlaunch.run_script(self.failing_spawn_stub(), ["dev-1"], env=env, text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertLess(time.monotonic() - start, 15)
        self.assertEqual(r.returncode, 1, r.stderr)  # the stub spawn fails; the line is already there
        self.assertEqual([json.loads(l)["rule"] for l in self.events()], ["respawn"])
        self.assertNotIn("could not write", r.stderr)

    def test_the_hook_and_the_manager_guard_still_read_a_file_with_the_respawn_line(self):  # AC3, T6
        events = self.squad / "usage-events.jsonl"
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        events.write_text(json.dumps({"ts": now, "agent": "dev-1", "role": "dev", "session": "sid-1", "rule": "fresh", "action": "a"}) + "\n"
                          + json.dumps({"ts": now, "agent": "dev-1", "role": "manager", "session": "sid-1", "rule": "manager-x", "action": "a"}) + "\n",
                          encoding="utf-8")
        self.assertEqual(self.respawn().returncode, 0)
        self.assertEqual(len(self.events()), 3)  # hook line, guard line, respawn line (it has no session)
        guard = load_cli("squad-manager-guard")
        self.assertEqual(guard.seen_keys(str(events), "sid-1"), {"manager-x"})
        cfg = self.root / "cfg"
        (cfg / "projects" / "-cwd").mkdir(parents=True)
        for sid in ("sid-1", "sid-2"):  # both over the respawn line (first action at 60k, now 130k)
            rows = [{"type": "assistant", "timestamp": now, "effort": "medium", "message": {"id": m, "model": "claude-sonnet-5-5",
                     "content": [{"type": "tool_use", "name": "Write", "input": {}}] if m == "first" else [],
                     "usage": {"input_tokens": 2, "cache_read_input_tokens": ctx, "cache_creation_input_tokens": 0, "output_tokens": 10}}}
                    for m, ctx in (("first", 60_000), ("last", 130_000))]
            (cfg / "projects" / "-cwd" / f"{sid}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
        hook_env = dict(self.env, CLAUDE_CONFIG_DIR=str(cfg), SQUAD_NAME="dev-1", SQUAD_ROLE="dev")

        def hook(sid):
            return winlaunch.run_script(BIN / "squad-usage-hook", input=json.dumps({"hook_event_name": "Stop", "session_id": sid}),
                                        text=True, encoding="utf-8", env=hook_env, capture_output=True, timeout=10)
        self.assertEqual(hook("sid-1").returncode, 0)  # already logged for this session: deduped
        self.assertEqual(hook("sid-2").returncode, 2)  # a session not yet logged still fires
        self.assertEqual(len(self.events()), 4)

    def scoped(self):
        """Turn the test squad into a per-scope squad with scope sc1 and goal g1."""
        head = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
        sc, g = self.squad / "scopes" / "sc1", self.squad / "goals" / "g1"
        sc.mkdir(parents=True)
        g.mkdir(parents=True)
        self.put_notes("t-dev-sc1-1", sc)
        self.put_notes("t-mgr-g1", g)
        (sc / "scope.md").write_text("# Scope\n\ngoal:\nteam: ba\n", encoding="utf-8")
        (sc / "roster.md").write_text(head + "| t-dev-sc1-1 | dev | sc1 | task 1 | live | old-sid |\n", encoding="utf-8")
        (g / "roster.md").write_text(head + "| t-mgr-g1 | manager |  |  | live | old-g |\n", encoding="utf-8")
        self.env.update(SCOPE_DIR=str(sc))
        return sc, g

    def test_scope_agent_respawns_in_its_scope_worktree_with_scope_env(self):
        sc, _ = self.scoped()
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/t/sc1/t-dev-sc1-1", cwd=repo)
        r = winlaunch.run_script(BIN / "squad-respawn", ["t-dev-sc1-1"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log.read_text(encoding="utf-8").splitlines()
        self.assertIn(f"tab create --cwd {Path(wt).as_posix()} --label 🤖 Dev --no-focus", " ".join(log))
        self.assertIn(f"SCOPE_DIR={Path(sc).as_posix()}", " ".join(log))
        self.assertFalse(any("worktree add" in l for l in log))
        sid = re.search(r"--session-id (\S+)", next(l for l in log if l.startswith("agent start"))).group(1)
        self.assertIn(f"| t-dev-sc1-1 | dev | sc1 | task 1 | live | {sid} |", (sc / "roster.md").read_text(encoding="utf-8"))
        self.assertIn("SCOPE_DIR/roles/t-dev-sc1-1.notes.md", next(l for l in log if l.startswith("agent prompt")))

    def test_goal_manager_respawns_with_goal_env(self):
        _, g = self.scoped()
        self.env.pop("SCOPE_DIR")
        self.env.update(GOAL_DIR=str(g))
        r = winlaunch.run_script(BIN / "squad-respawn", ["t-mgr-g1"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        log = " ".join(self.log.read_text(encoding="utf-8").splitlines())
        self.assertIn(f"GOAL_DIR={Path(g).as_posix()}", log)
        self.assertNotIn("SCOPE_DIR", log)
        self.assertIn("| t-mgr-g1 | manager |", (g / "roster.md").read_text(encoding="utf-8"))

    def test_flat_squad_finds_the_oldest_worktree_layout(self):
        # squad-board's early layout: .worktrees/<agent>, branch squad/<agent>
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        wt = self.root / ".worktrees" / "dev-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/dev-1", cwd=repo)
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log.read_text(encoding="utf-8")
        self.assertIn(f"tab create --cwd {Path(wt).as_posix()} --label 🤖 Dev", log)
        self.assertNotIn("worktree add", log)

    def test_unknown_agent_fails(self):
        r = winlaunch.run_script(BIN / "squad-respawn", ["ghost"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertNotEqual(r.returncode, 0)


class RespawnPinnedTest(RespawnTest):
    """D7: a scope pinned below 0.6.0 is respawned by the pin's own squad-respawn (its scope.md still says `size:`)."""

    def pinned(self, version="0.5.2", stub=True):
        sc, _ = self.scoped()
        (self.squad / "process.local.md").write_text("", encoding="utf-8")
        sha = "b" * 40
        rt = self.squad / "_runtime" / f"{version}-{sha[:12]}"
        (rt / ".claude-plugin").mkdir(parents=True)
        (rt / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "squad", "version": version}), encoding="utf-8")
        self.record = self.root / "stub.log"
        if stub:
            (rt / "bin").mkdir()
            (rt / "bin" / "squad-respawn").write_text(
                f'#!/usr/bin/env bash\necho "squad-respawn $* SCOPE_DIR=$SCOPE_DIR" >> "{self.record}"\n', encoding="utf-8")
            (rt / "bin" / "squad-respawn").chmod(0o755)
        (sc / "scope.md").write_text(f"# Scope\n\ngoal:\nsize: L\nqa-b: yes\nplugin: {version} {sha}\n", encoding="utf-8", newline="")
        return sc

    def run_respawn(self, *args, env=None):
        return winlaunch.run_script(BIN / "squad-respawn", ["t-dev-sc1-1", *args], env=env or self.env, text=True,
                              encoding="utf-8", capture_output=True, timeout=20)

    def calls(self):
        return self.record.read_text(encoding="utf-8").splitlines() if self.record.exists() else []

    def test_pin_0_5_2_hands_off_from_the_po_shell_and_from_an_agent_session(self):
        sc = self.pinned()
        before = (sc / "scope.md").read_bytes()
        for env in (self.env, dict(self.env, SQUAD_NAME="t-dev-sc1-1", SQUAD_ROLE="dev")):
            self.assertEqual(self.run_respawn(env=env).returncode, 0)
        self.assertEqual(self.calls(), [f"squad-respawn t-dev-sc1-1 SCOPE_DIR={sc}"] * 2)
        self.assertFalse(self.log.exists())  # the new engine made no herdr call of its own
        self.assertEqual((sc / "scope.md").read_bytes(), before)

    def test_the_hand_off_passes_the_dry_run_flag(self):
        self.pinned()
        r = self.run_respawn("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would hand off to the pinned runtime", r.stdout)
        self.assertEqual(self.calls(), [])

    def test_a_runtime_without_squad_respawn_refuses_with_a_warning_and_renames_nothing(self):
        self.pinned(stub=False)
        r = self.run_respawn()
        self.assertEqual(r.returncode, 1)
        self.assertIn("warning:", r.stderr)
        self.assertIn("no bin/squad-respawn", r.stderr)
        self.assertFalse(self.log.exists())

    def test_a_dry_run_without_the_pins_squad_respawn_also_warns_and_exits_1(self):
        self.pinned(stub=False)
        r = self.run_respawn("--dry-run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no bin/squad-respawn", r.stderr)
        self.assertNotIn("would hand off", r.stdout)

    def test_a_composed_scope_with_size_and_no_pin_gets_the_converter_pointer_not_the_pin_text(self):
        sc = self.pinned(stub=False)
        (sc / "scope.md").write_text("# Scope\n\nname: s\nsize: M\n", encoding="utf-8")
        r = self.run_respawn()
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertRegex(r.stderr, r"scope\.md:\d+: old format `size:`")
        self.assertIn("one `team:` line", r.stderr)
        self.assertNotIn("needs a pin", r.stderr)
        self.assertFalse(self.log.exists())

    def test_pin_0_6_0_does_not_hand_off(self):
        sc = self.pinned("0.6.0")
        (sc / "scope.md").write_text("# Scope\n\ngoal:\nteam: ba\nplugin: 0.6.0 " + "b" * 40 + "\n", encoding="utf-8")
        r = self.run_respawn("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("hand off", r.stdout)
        self.assertEqual(self.calls(), [])

    @unittest.skipIf(os.name == "nt", "os.symlink needs Developer Mode or admin (WinError 1314)")
    def test_a_runtime_that_is_this_script_is_not_handed_to_again(self):
        self.pinned(stub=False)
        rt = next((self.squad / "_runtime").iterdir())
        (rt / "bin").mkdir()
        (rt / "bin" / "squad-respawn").symlink_to(BIN / "squad-respawn")
        r = self.run_respawn("--dry-run")
        self.assertNotIn("hand off", r.stdout)  # no exec loop: the guard falls through to the normal path


for _n in dir(RespawnTest):  # reuse the fixture only: the inherited tests run once, in RespawnTest
    if _n.startswith("test_") and _n not in RespawnPinnedTest.__dict__:
        setattr(RespawnPinnedTest, _n, None)


if __name__ == "__main__":
    unittest.main()
