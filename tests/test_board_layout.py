"""Seam A, BRD-19: the board reads the per-scope squad layout (`scopes/`, `goals/`) as well as the flat one.

Every test runs the real `bin/squad-board --replay` on a per-scope folder built by `make_scoped`
and reads HTTP. The flat layout is covered by the older test files, which are unchanged.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from board_fixture import Fixture, make_scoped
from fake_herdr import FakeHerdr
from test_board_events import Stream
from test_board_recorder import base_env, launch, wait_until

NOW = "2026-10-12T12:00:00Z"

# The `/state` key list (design.md), the one place the shape test reads. A ticket that adds a state key
# adds it here.
TOP_KEYS = {"now", "iterations", "iteration", "selected_iteration", "pods", "columns", "rows", "bars",
            "tasks", "needs_you", "live"}
POD_KEYS = {"name", "size", "agents"}
COLUMN_KEYS = {"agent", "role", "pod", "status", "retired", "notes_path", "working_s", "blocked_s", "wakes",
               "context_tokens", "tokens_in", "tokens_out", "model"}
ROW_KEYS = {"message": {"id", "kind", "ts", "from", "to", "type", "task", "text", "msg_id"},
            "status": {"id", "kind", "ts", "agent", "status", "duration_s"},
            "gap": {"id", "kind", "ts", "seconds", "from_ts", "to_ts"}}
BAR_KEYS = {"agent", "start_row", "end_row", "start_ts", "end_ts", "self_start", "open", "duration_s", "blocked"}
SEGMENT_KEYS = {"start_row", "end_row", "start_ts", "end_ts", "duration_s"}
TASK_KEYS = {"id", "state", "returns", "last_ts", "last_type"}
NEEDS_KEYS = {"id", "kind", "text", "agent", "since"}


def keys_everywhere(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from keys_everywhere(value)
    elif isinstance(node, list):
        for item in node:
            yield from keys_everywhere(item)


class ScopedCase(unittest.TestCase):
    def setUp(self):
        self.fx = make_scoped()
        self.addCleanup(self.fx.close)

    def start(self, **kw):
        kw.setdefault("now", NOW)
        return self.fx.start(**kw)

    def state(self, iteration=None, **kw):
        return self.start(**kw).state(iteration)

    @staticmethod
    def pods(state):
        return dict((p["name"], p) for p in state["pods"])

    @staticmethod
    def texts(state):
        return [r["text"] for r in state["rows"] if r["kind"] == "message"]

    def msg(self, home, text, iteration=None, **kw):
        fields = {"from": kw.pop("sender", "x-dev-a"), "to": kw.pop("to", "x-qaw-a"), "text": text,
                  "iteration": iteration}
        fields.update(kw)
        return self.fx.message(_home=home, **fields)


class DetectTest(ScopedCase):
    def test_scopes_folder_means_per_scope_and_the_root_roster_is_ignored(self):
        self.fx.roster([{"agent": "stale-root", "scope": "stale"}])
        state = self.state()
        names = [c["agent"] for c in state["columns"]]
        self.assertNotIn("stale-root", names)
        self.assertIn("x-dev-a", names)

    def test_an_empty_scopes_folder_gives_an_empty_valid_state(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.write("roster.md", "| Agent | Role | Scope |\n|---|---|---|\n| stale | Manager | all |\n")
        (fx.root / "scopes").mkdir()
        state = fx.start(now=NOW).state()
        for key in ("pods", "columns", "rows", "bars", "tasks", "needs_you", "iterations"):
            self.assertEqual(state[key], [], key)
        self.assertIsNone(state["iteration"])

    def test_a_squad_without_scopes_stays_flat(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-board-1"}])
        pods = [p["name"] for p in fx.start(now=NOW).state()["pods"]]
        self.assertEqual(pods, ["all", "board"])


class PodsTest(ScopedCase):
    def test_pods_in_order_with_sizes_from_scope_md(self):
        state = self.state()
        self.assertEqual([p["name"] for p in state["pods"]], ["all", "g", "a", "b", "c"])
        self.assertEqual([p["size"] for p in state["pods"]], [None, None, "S + QA whitebox", "M", None])

    def test_managers_share_the_first_pod_in_home_order_and_the_goal_manager_has_a_column(self):
        pods = self.pods(self.state())
        self.assertEqual(pods["all"]["agents"], ["g-mgr", "c-mgr"])
        self.assertEqual(pods["g"]["agents"], ["g-coach"])  # a coach row with an empty Scope cell
        self.assertEqual(pods["a"]["agents"], ["x-dev-a", "x-qaw-a"])
        self.assertEqual(pods["c"]["agents"], ["c-dev"])

    def test_scope_cell_of_a_roster_row_is_ignored(self):
        self.fx.roster([{"agent": "x-dev-a", "scope": "somewhere-else"}], home="scopes/a")
        self.assertEqual(self.pods(self.state())["a"]["agents"], ["x-dev-a"])


class HiddenTest(ScopedCase):
    def test_closed_and_odd_folders_appear_nowhere(self):
        self.fx.message(_home="scopes/_done/x", **{"from": "gone-dev", "to": "gone-dev", "text": "hidden-text"})
        self.fx.activity(_home="goals/_done/y", agent="gone-mgr")
        self.fx.escalations([{"question": "hidden-q"}], home="scopes/_done/x")
        self.fx.roster([{"agent": "bad-dev", "scope": "bad"}], home="scopes/Bad_Name")
        self.fx.write("scopes/plain-file", "| Agent | Role |\n")
        os.symlink(str(self.fx.root / "scopes/a"), str(self.fx.root / "scopes/linked"))
        os.symlink(str(self.fx.root / "scopes/b"), str(self.fx.root / "goals/linked-goal"))
        text = json.dumps(self.state())
        for needle in ("gone-", "hidden-", "bad-dev", "Bad_Name", "linked"):
            self.assertNotIn(needle, text)
        self.assertEqual([p["name"] for p in self.state()["pods"]], ["all", "g", "a", "b", "c"])

    def test_a_symlinked_scopes_folder_is_not_followed(self):
        outside = Path(tempfile.mkdtemp(prefix="board-out-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(str(outside), ignore_errors=True))
        (outside / "z").mkdir()
        (outside / "z/roster.md").write_text("| Agent | Role |\n|---|---|\n| outsider | Developer |\n")
        fx = Fixture()
        self.addCleanup(fx.close)
        os.symlink(str(outside), str(fx.root / "scopes"))
        self.assertNotIn("outsider", json.dumps(fx.start(now=NOW).state()))


class LogsTest(ScopedCase):
    def test_messages_of_three_homes_merge_in_time_order(self):
        self.msg("scopes/a", "first", iteration=2)
        self.msg("goals/g", "second", sender="g-mgr", to="x-dev-a")
        self.msg("scopes/b", "third", iteration=1, sender="x-dev-b", to="x-dev-b")
        state = self.state()
        rows = [r for r in state["rows"] if r["kind"] == "message"]
        self.assertEqual([(r["text"], r["from"], r["to"]) for r in rows],
                         [("first", "x-dev-a", "x-qaw-a"), ("second", "g-mgr", "x-dev-a"),
                          ("third", "x-dev-b", "x-dev-b")])

    def test_one_msg_id_in_two_homes_shows_once(self):
        self.msg("scopes/a", "same", iteration=2, msg_id="dup")
        self.msg("goals/g", "same", msg_id="dup")
        self.assertEqual(self.texts(self.state()), ["same"])

    def pod_of(self, state, agent):
        return next(c["pod"] for c in state["columns"] if c["agent"] == agent)

    def test_an_unlisted_agent_joins_the_pod_named_in_its_name(self):
        self.fx.write("scopes/my-scope/scope.md", "size: S\n")
        self.fx.roster([{"agent": "m-dev", "scope": "my-scope"}], home="scopes/my-scope")
        for name in ("x-dev-my-scope-1", "x-dev-b", "nobody-here"):
            self.msg("scopes/a", "hi " + name, iteration=2, sender=name, to=name)
        state = self.state()
        self.assertEqual(self.pod_of(state, "x-dev-my-scope-1"), "my-scope")
        self.assertEqual(self.pod_of(state, "x-dev-b"), "b")
        self.assertEqual(self.pod_of(state, "nobody-here"), "(unlisted)")

    def test_ambiguous_names_longest_then_earliest(self):
        for scope in ("a", "a-b"):
            self.fx.write("scopes/%s/scope.md" % scope, "size: S\n")
            self.fx.roster([{"agent": "%s-dev" % scope, "scope": scope}], home="scopes/%s" % scope)
        for name in ("x-a-b-1", "x-b-a-1"):
            self.msg("scopes/a", "hi", iteration=2, sender=name, to=name)
        state = self.state()
        self.assertEqual(self.pod_of(state, "x-a-b-1"), "a-b")  # same position, longest wins
        self.assertEqual(self.pod_of(state, "x-b-a-1"), "b")    # earlier position wins over `a`

    def test_the_manager_pod_is_never_a_match(self):
        self.msg("scopes/a", "hi", iteration=2, sender="x-all-1", to="x-all-1")
        self.assertEqual(self.pod_of(self.state(), "x-all-1"), "(unlisted)")


class NeedsYouTest(ScopedCase):
    def test_escalations_of_two_scopes_stay_apart(self):
        self.fx.escalations([{"num": 1, "question": "qa?"}], home="scopes/a")
        self.fx.escalations([{"num": 1, "question": "qb?"}], home="scopes/b")
        items = [i for i in self.state()["needs_you"] if i["kind"] == "escalation"]
        self.assertEqual([(i["id"], i["text"]) for i in items],
                         [("escalation:a:1", "a: qa?"), ("escalation:b:1", "b: qb?")])

    def test_an_answered_row_in_one_scope_does_not_clear_the_other(self):
        self.fx.escalations([{"num": 1, "question": "qa?", "answer": "yes"}], home="scopes/a")
        self.fx.escalations([{"num": 1, "question": "qb?"}], home="scopes/b")
        self.assertEqual([i["id"] for i in self.state()["needs_you"]], ["escalation:b:1"])

    def test_an_idle_scope_manager_with_an_empty_check_in_is_listed_the_goal_manager_never(self):
        self.fx.iteration(1, home="scopes/c")
        self.fx.activity(_home="scopes/c", agent="c-mgr", status="idle", iteration=1)
        self.fx.activity(_home="goals/g", agent="g-mgr", status="idle", iteration=None)
        items = [i for i in self.state()["needs_you"] if i["kind"] == "manager_idle"]
        self.assertEqual([(i["id"], i["agent"]) for i in items], [("manager_idle:c:1", "c-mgr")])
        self.assertIn("c", items[0]["text"])

    def test_a_filled_check_in_gives_no_item(self):
        self.fx.iteration(1, "# 1\n\n## PO check-in\n- **Done:** all\n- **Next:** more\n", home="scopes/c")
        self.fx.activity(_home="scopes/c", agent="c-mgr", status="idle", iteration=1)
        self.assertEqual(self.state()["needs_you"], [])

    def test_a_blocked_agent_of_any_scope_is_listed(self):
        self.fx.activity(_home="scopes/b", agent="x-dev-b", status="blocked", iteration=1)
        items = self.state()["needs_you"]
        self.assertEqual([(i["kind"], i["agent"]) for i in items], [("blocked", "x-dev-b")])


class IterationsTest(ScopedCase):
    def build(self):
        self.msg("scopes/a", "a1", iteration=1)
        self.msg("scopes/a", "a2", iteration=2)
        self.msg("scopes/b", "b1", iteration=1, sender="x-dev-b", to="x-dev-b")
        self.msg("goals/g", "g0", sender="g-mgr", to="g-coach")
        self.fx.activity(_home="scopes/a", agent="x-dev-a", status="working", iteration=2)

    def test_the_union_of_numbers_and_each_scopes_own_current_iteration_by_default(self):
        self.build()
        state = self.state()
        self.assertEqual((state["iterations"], state["iteration"], state["selected_iteration"]), ([1, 2], 2, 2))
        self.assertEqual(self.texts(state), ["a2", "b1", "g0"])

    def test_an_explicit_number_shows_the_records_tagged_with_it_and_the_goal(self):
        self.build()
        state = self.state(1)
        self.assertEqual(self.texts(state), ["a1", "b1", "g0"])

    def test_an_unknown_iteration_is_a_400(self):
        status, _, _ = self.start().get("/state?iteration=3")
        self.assertEqual(status, 400)

    def test_totals_stay_whole_run(self):
        self.build()
        by_agent = dict((c["agent"], c) for c in self.state(1)["columns"])
        self.assertGreater(by_agent["x-dev-a"]["working_s"], 0)  # an iteration-2 bar, seen from iteration 1

    def test_a_record_without_a_tag_counts_as_its_scopes_lowest_iteration(self):
        self.msg("scopes/b", "untagged", iteration=None, sender="x-dev-b", to="x-dev-b")
        self.assertEqual(self.texts(self.state()), ["untagged"])


class NotesTest(ScopedCase):
    def test_notes_path_is_relative_to_the_squad_folder_and_null_when_missing(self):
        self.fx.write("scopes/c/roles/c-dev.notes.md", "scope notes")
        self.fx.write("goals/g/roles/g-mgr.notes.md", "goal notes")
        by_agent = dict((c["agent"], c["notes_path"]) for c in self.state()["columns"])
        self.assertEqual(by_agent["c-dev"], "scopes/c/roles/c-dev.notes.md")
        self.assertEqual(by_agent["g-mgr"], "goals/g/roles/g-mgr.notes.md")
        self.assertIsNone(by_agent["x-dev-a"])

    def test_the_route_serves_a_scoped_agents_notes_but_not_a_file_of_another_home(self):
        self.fx.write("scopes/a/roles/x-dev-a.notes.md", "mine")
        self.fx.write("scopes/b/roles/x-qaw-a.notes.md", "wrong home")
        srv = self.start()
        status, _, body = srv.get("/notes/x-dev-a?token=" + srv.token)
        self.assertEqual((status, body), (200, b"mine"))
        status, _, _ = srv.get("/notes/x-qaw-a?token=" + srv.token)
        self.assertEqual(status, 404)
        by_agent = dict((c["agent"], c["notes_path"]) for c in srv.state()["columns"])
        self.assertIsNone(by_agent["x-qaw-a"])


class WatchTest(ScopedCase):
    def test_a_new_scope_a_closed_scope_and_a_size_edit_each_make_an_event(self):
        srv = self.start()
        stream = Stream(srv)
        self.addCleanup(stream.close)
        self.assertIsNotNone(stream.state(5))

        def pods_of(state):
            return [(p["name"], p["size"]) for p in state["pods"]]

        self.fx.write("scopes/d/scope.md", "size: S\n")
        self.fx.roster([{"agent": "d-dev", "scope": "d"}], home="scopes/d")
        state = stream.state_where(lambda s: "d" in [p["name"] for p in s["pods"]])
        self.assertIsNotNone(state, "no event for a new scope")
        self.fx.write("scopes/d/scope.md", "size: M\n")
        self.assertIsNotNone(stream.state_where(lambda s: ("d", "M") in pods_of(s)), "no event for a size edit")
        os.rename(str(self.fx.root / "scopes/c"), str(self.fx.root / "scopes/_done/c"))
        self.assertIsNotNone(stream.state_where(lambda s: "c" not in [p["name"] for p in s["pods"]]),
                             "no event for a closed scope")


class RecorderTest(ScopedCase):
    def test_a_record_goes_to_the_log_of_the_agents_own_home(self):
        tmp = Path(tempfile.mkdtemp(prefix="board-layout-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(str(tmp), ignore_errors=True))
        (tmp / "home").mkdir()
        fake = FakeHerdr(tmp / "h.sock")
        self.addCleanup(fake.stop)
        panes = {}
        for name in ("x-dev-a", "g-mgr", "stranger"):
            panes[name] = "wA:p%d" % (len(panes) + 1)
            fake.add_pane(name, panes[name], "idle")
        fake.start()
        env = base_env(tmp / "home", fake.path, self.fx.root)
        srv = launch([], env, tmp)
        self.addCleanup(srv.close)
        fake.wait_ready()

        def lines(rel):
            path = self.fx.root / rel
            return [json.loads(x) for x in path.read_text().split("\n") if x] if path.exists() else []

        # the start-up sync recorded every rostered pane's status once
        wait_until(lambda: lines("scopes/a/activity.jsonl") and lines("goals/g/activity.jsonl"), "records")
        fake.emit_status(panes["stranger"], "working")  # first: handled before the others' records appear
        fake.emit_status(panes["x-dev-a"], "working")
        fake.emit_status(panes["g-mgr"], "working")
        wait_until(lambda: [r for r in lines("scopes/a/activity.jsonl") if r["status"] == "working"]
                   and [r for r in lines("goals/g/activity.jsonl") if r["status"] == "working"], "the events")
        a = lines("scopes/a/activity.jsonl")[-1]
        g = lines("goals/g/activity.jsonl")[-1]
        self.assertEqual((a["agent"], a["status"], a["iteration"]), ("x-dev-a", "working", 2))
        self.assertEqual((g["agent"], g["status"], g["iteration"]), ("g-mgr", "working", None))
        self.assertFalse((self.fx.root / "activity.jsonl").exists())
        for rel in ("scopes/a", "scopes/b", "scopes/c", "goals/g"):
            self.assertNotIn("stranger", (self.fx.root / rel / "activity.jsonl").read_text()
                             if (self.fx.root / rel / "activity.jsonl").exists() else "")


class ShapeTest(ScopedCase):
    def test_the_per_scope_state_has_only_the_designed_keys_and_no_home(self):
        self.msg("scopes/a", "hello", iteration=2)
        self.msg("goals/g", "gm", sender="g-mgr", to="g-coach")
        self.fx.activity(_home="scopes/a", agent="x-dev-a", status="blocked", iteration=2)
        self.fx.activity(_home="scopes/a", agent="x-dev-a", status="idle", iteration=2)
        self.fx.escalations([{"question": "q?"}], home="scopes/b")
        self.fx.message(_home="scopes/a", **{"from": "x-dev-a", "to": "x-qaw-a", "type": "HANDIN",
                                             "task": "T-1", "iteration": 2})
        state = self.state()
        self.assertEqual(set(state), TOP_KEYS)
        self.assertNotIn("home", list(keys_everywhere(state)))
        for pod in state["pods"]:
            self.assertEqual(set(pod), POD_KEYS)
        for col in state["columns"]:
            self.assertEqual(set(col), COLUMN_KEYS)
        for row in state["rows"]:
            self.assertEqual(set(row) - ROW_KEYS[row["kind"]], set(), row)
        for bar in state["bars"]:
            self.assertEqual(set(bar), BAR_KEYS)
            for seg in bar["blocked"]:
                self.assertEqual(set(seg), SEGMENT_KEYS)
        for task in state["tasks"]:
            self.assertEqual(set(task), TASK_KEYS)
        for item in state["needs_you"]:
            self.assertEqual(set(item), NEEDS_KEYS)
        self.assertTrue(state["rows"] and state["bars"] and state["tasks"] and state["needs_you"])


class RobustTest(ScopedCase):
    def ok(self, srv):
        srv.state()
        self.assertEqual(srv.stderr(), "")

    def test_a_home_without_a_roster_and_an_unreadable_scope_md(self):
        (self.fx.root / "scopes/empty").mkdir()
        (self.fx.root / "scopes/odd").mkdir()
        (self.fx.root / "scopes/odd/scope.md").mkdir()  # reading it raises
        (self.fx.root / "scopes/odd/roster.md").mkdir()
        srv = self.start()
        self.ok(srv)
        self.assertNotIn("empty", [p["name"] for p in srv.state()["pods"]])  # no agents, no pod

    def test_a_scope_that_vanishes_between_two_requests(self):
        srv = self.start()
        self.ok(srv)
        __import__("shutil").rmtree(str(self.fx.root / "scopes/b"))
        self.ok(srv)
        self.assertEqual([p["name"] for p in srv.state()["pods"]], ["all", "g", "a", "c"])


class SecurityTest(ScopedCase):
    def test_a_roster_agent_named_like_a_path_is_never_used_in_one(self):
        self.fx.roster([{"agent": "../x", "scope": "a"}, {"agent": "x-dev-a", "scope": "a"}], home="scopes/a")
        self.fx.write("scopes/a/x.notes.md", "outside roles/")  # what `roles/../x.notes.md` would be
        srv = self.start()
        by_agent = dict((c["agent"], c["notes_path"]) for c in srv.state()["columns"])
        self.assertIsNone(by_agent.get("../x"))
        for path in ("/notes/..%2Fx", "/notes/../x"):
            status, _, _ = srv.get(path + "?token=" + srv.token)
            self.assertIn(status, (400, 404))
        self.assertEqual(srv.stderr(), "")


if __name__ == "__main__":
    unittest.main()
