"""Seam A, BRD-01: squad-board in replay mode, GET /state from squad files and logs."""
import json
import re
import subprocess
import sys
import unittest

from board_fixture import BIN, Fixture

TOP_KEYS = {"now", "iterations", "iteration", "selected_iteration", "pods", "columns", "rows",
            "bars", "tasks", "needs_you"}
COLUMN_KEYS = {"agent", "role", "pod", "status", "retired", "notes_path", "working_s", "blocked_s",
               "wakes", "context_tokens", "tokens_in", "tokens_out", "model"}
NOW = "2026-10-12T12:00:00Z"

MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}


class BoardCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)

    def start(self, **kw):
        kw.setdefault("now", NOW)
        return self.fx.start(**kw)

    def state(self, iteration=None, **kw):
        return self.start(**kw).state(iteration)

    def column(self, state, agent):
        return next(c for c in state["columns"] if c["agent"] == agent)

    def pod(self, state, name):
        return next(p for p in state["pods"] if p["name"] == name)


class StateContractTest(BoardCase):
    def test_top_level_and_column_keys_are_exactly_the_contract(self):
        self.fx.roster([MANAGER, {"agent": "dev-board-1"}])
        st = self.state()
        self.assertEqual(set(st), TOP_KEYS)
        for col in st["columns"]:
            self.assertEqual(set(col), COLUMN_KEYS)

    def test_column_defaults_without_events(self):
        self.fx.roster([{"agent": "dev-board-1", "role": "Developer"}])
        col = self.column(self.state(), "dev-board-1")
        self.assertEqual(col, {
            "agent": "dev-board-1", "role": "Developer", "pod": "board", "status": "idle",
            "retired": False, "notes_path": None, "working_s": 0, "blocked_s": 0, "wakes": 0,
            "context_tokens": None, "tokens_in": None, "tokens_out": None, "model": None})

    def test_stub_sections_give_empty_lists(self):
        self.fx.roster([MANAGER])
        st = self.state()
        for key in ("rows", "bars", "tasks", "needs_you"):
            self.assertEqual(st[key], [])

    def test_now_flag_is_echoed(self):
        self.fx.roster([MANAGER])
        self.assertEqual(self.state(now="2026-10-12T09:30:00Z")["now"], "2026-10-12T09:30:00Z")

    def test_now_defaults_to_latest_log_ts(self):
        self.fx.roster([MANAGER])
        self.fx.message(ts="2026-10-12T10:00:05.000Z")
        self.fx.activity(ts="2026-10-12T10:00:09.000Z")
        self.fx.message(ts="2026-10-12T10:00:07.000Z")
        self.assertEqual(self.state(now=None)["now"], "2026-10-12T10:00:09.000Z")

    def test_now_falls_back_to_wall_clock_when_logs_are_empty(self):
        self.fx.roster([MANAGER])
        now = self.state(now=None)["now"]
        self.assertRegex(now, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d")


class SquadReaderTest(BoardCase):
    def test_bold_size_cell_is_plain_text(self):
        self.fx.roster([{"agent": "dev-board-1"}])
        self.fx.scopes([{"scope": "board", "size": "**S + QA whitebox**"}])
        self.assertEqual(self.pod(self.state(), "board")["size"], "S + QA whitebox")

    def test_escaped_pipe_stays_in_its_cell(self):
        self.fx.roster([{"agent": "dev-board-1", "role": r"Dev \| QA", "scope": "board"}])
        col = self.column(self.state(), "dev-board-1")
        self.assertEqual(col["role"], "Dev | QA")
        self.assertEqual(col["pod"], "board")
        self.assertFalse(col["retired"])

    def test_backticks_and_bold_are_stripped_from_cells(self):
        self.fx.roster([{"agent": "`dev-board-1`", "role": "**Developer**"}])
        col = self.column(self.state(), "dev-board-1")
        self.assertEqual(col["role"], "Developer")

    def test_only_first_scopes_table_counts(self):
        self.fx.roster([{"agent": "dev-board-1"}])
        self.fx.scopes([{"scope": "board", "size": "S"}],
                       size_log=["| board | XL | x | none | 2026-10-12 | x |"])
        self.assertEqual(self.pod(self.state(), "board")["size"], "S")

    def test_only_the_first_roster_table_counts(self):
        self.fx.roster([MANAGER])
        with open(self.fx.root / "roster.md", "a") as f:
            f.write("\n## Old\n\n| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n"
                    "| dev-old | Developer | board | x | live |\n")
        self.assertEqual([c["agent"] for c in self.state()["columns"]], ["manager"])

    def test_roster_rows_with_an_empty_agent_role_or_scope_are_skipped(self):
        self.fx.write("roster.md", (
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n"
            "| manager | Manager | all | x | live |\n"
            "| only |\n"
            "| no-role |  | board | x | live |\n"
            "| no-scope | Developer |  | x | live |\n"
            "|  | Developer | board | x | live |\n"
            "| dev-board-1 | Developer | board | x | live |\n"))
        st = self.state()
        self.assertEqual([c["agent"] for c in st["columns"]], ["manager", "dev-board-1"])
        self.assertEqual([p["name"] for p in st["pods"]], ["all", "board"])

    def test_scope_cell_with_parenthetical_matches_scopes_row(self):
        self.fx.roster([{"agent": "dev-board-1", "scope": "board (S+QAW)"}])
        self.fx.scopes([{"scope": "board", "size": "S"}])
        st = self.state()
        self.assertEqual(self.column(st, "dev-board-1")["pod"], "board")
        self.assertEqual(self.pod(st, "board")["size"], "S")

    def test_live_roster_and_scopes_rows_verbatim(self):
        self.fx.write("roster.md", (
            "# Roster\n\n| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n"
            "| manager | Manager | all | process, scopes, roster, disputes | live |\n"
            "| tech-board | Tech Lead | board (S+QAW) | design, quality, security; plan, task order "
            "and tickets in `.scratch/squad-board/issues/` | live |\n"))
        self.fx.write("scopes.md", (
            "# Scopes\n\n| Scope | Size | Signals | Risk flags | PO confirmed | Pod (agents) |\n"
            "|---|---|---|---|---|---|\n"
            "| board | **S + QA whitebox** (exception, see process.md → Sizes; escalation #1) | about 10 "
            "tasks over 3 iterations; one repo | security: 127.0.0.1 bind and a token-guarded jump "
            "action that drives herdr | 2026-10-12 | tech-board, qaw-board, dev-board-N |\n"))
        self.fx.message(**{"from": "dev-board-3", "to": "manager"})
        st = self.state()
        self.assertEqual(self.pod(st, "board")["size"], "S + QA whitebox")
        self.assertEqual(self.pod(st, "board")["agents"], ["tech-board", "dev-board-3"])

    def test_escalations_with_pipes_and_empty_answers_do_not_break_state(self):
        self.fx.roster([MANAGER])
        self.fx.escalations([{"question": r"a \| b?"}, {"answer": "2026-10-12: A"}])
        srv = self.start()
        self.assertEqual(srv.state()["columns"][0]["agent"], "manager")
        srv.stop()
        self.assertEqual(srv.stderr(), "")

    def test_iteration_files_ignore_template_and_non_numeric_names(self):
        self.fx.roster([MANAGER])
        self.fx.iteration(1)
        self.fx.iteration(2)
        self.fx.write("iterations/TEMPLATE.md", "# Iteration <n>\n")
        self.fx.write("iterations/notes.md", "x")
        self.assertEqual(self.state()["iterations"], [1, 2])


class OrderAndPodsTest(BoardCase):
    def test_manager_first_then_pods_by_first_appearance_roster_order_inside(self):
        self.fx.roster([
            {"agent": "dev-board-1", "scope": "board"},
            {"agent": "tech-board", "role": "Tech Lead", "scope": "board"},
            MANAGER,
            {"agent": "ba-settings", "role": "BA", "scope": "settings"},
            {"agent": "dev-board-2", "scope": "board"},
        ])
        self.fx.scopes([{"scope": "board", "size": "S"}, {"scope": "settings", "size": "M"}])
        st = self.state()
        self.assertEqual([p["name"] for p in st["pods"]], ["all", "board", "settings"])
        self.assertEqual([p["agents"] for p in st["pods"]],
                         [["manager"], ["dev-board-1", "tech-board", "dev-board-2"], ["ba-settings"]])
        self.assertEqual([c["agent"] for c in st["columns"]],
                         ["manager", "dev-board-1", "tech-board", "dev-board-2", "ba-settings"])
        self.assertEqual([p["size"] for p in st["pods"]], [None, "S", "M"])
        self.assertEqual(set(st["pods"][0]), {"name", "size", "agents"})

    def test_manager_pod_size_is_null_even_if_scopes_lists_all(self):
        self.fx.roster([MANAGER])
        self.fx.scopes([{"scope": "all", "size": "XL"}])
        self.assertIsNone(self.pod(self.state(), "all")["size"])

    def test_pod_without_scopes_row_has_null_size(self):
        self.fx.roster([{"agent": "dev-x-1", "scope": "x"}])
        self.assertIsNone(self.pod(self.state(), "x")["size"])

    def test_retired_agent_keeps_its_column_flagged(self):
        self.fx.roster([MANAGER, {"agent": "dev-board-1", "status": "live"},
                        {"agent": "dev-board-2", "status": "retired"}])
        st = self.state()
        self.assertFalse(self.column(st, "dev-board-1")["retired"])
        self.assertTrue(self.column(st, "dev-board-2")["retired"])
        self.assertEqual(self.pod(st, "board")["agents"], ["dev-board-1", "dev-board-2"])


class UnknownAgentTest(BoardCase):
    def test_log_only_agent_joins_end_of_pod_matching_a_name_part(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"},
                        {"agent": "ba-settings", "role": "BA", "scope": "settings"}])
        self.fx.message(**{"from": "dev-board-3", "to": "manager"})
        st = self.state()
        self.assertEqual(self.pod(st, "board")["agents"], ["tech-board", "dev-board-3"])
        col = self.column(st, "dev-board-3")
        self.assertEqual((col["pod"], col["role"], col["retired"]), ("board", None, False))

    def test_log_only_agent_without_pod_match_goes_to_unlisted_pod_last(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"}])
        self.fx.activity(agent="stranger", status="working")
        st = self.state()
        self.assertEqual([p["name"] for p in st["pods"]], ["all", "board", "(unlisted)"])
        self.assertEqual(self.pod(st, "(unlisted)")["agents"], ["stranger"])
        self.assertIsNone(self.pod(st, "(unlisted)")["size"])
        col = self.column(st, "stranger")
        self.assertEqual((col["pod"], col["role"], col["status"]), ("(unlisted)", None, "working"))

    def test_several_unknown_agents_keep_order_of_first_appearance(self):
        self.fx.roster([MANAGER])
        self.fx.message(**{"from": "zed", "to": "amy"})
        self.assertEqual(self.pod(self.state(), "(unlisted)")["agents"], ["zed", "amy"])

    def test_first_matching_name_part_decides_the_pod(self):
        self.fx.roster([MANAGER, {"agent": "dev-board-1", "scope": "board"},
                        {"agent": "ba-settings", "role": "BA", "scope": "settings"}])
        self.fx.message(**{"from": "qa-settings-board", "to": "manager"})
        self.assertEqual(self.column(self.state(), "qa-settings-board")["pod"], "settings")

    def test_managers_pod_is_never_a_name_part_target(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"}])
        self.fx.activity(agent="dev-all-1", status="working")
        st = self.state()
        self.assertEqual(self.column(st, "dev-all-1")["pod"], "(unlisted)")
        self.assertEqual(self.pod(st, "all")["agents"], ["manager"])

    def test_unsafe_log_agent_name_gets_no_notes_path(self):
        self.fx.roster([MANAGER])
        self.fx.write("x.notes.md", "outside roles/\n")
        self.fx.activity(agent="../x", status="working")
        st = self.state()
        self.assertIsNone(self.column(st, "../x")["notes_path"])


class StatusTest(BoardCase):
    def test_status_comes_from_the_latest_activity_event(self):
        self.fx.roster([MANAGER, {"agent": "dev-board-1"}, {"agent": "dev-board-2"},
                        {"agent": "dev-board-3"}, {"agent": "dev-board-4"}])
        self.fx.activity(agent="manager", status="working")
        self.fx.activity(agent="dev-board-1", status="working")
        self.fx.activity(agent="dev-board-1", status="blocked")
        self.fx.activity(agent="dev-board-2", status="working")
        self.fx.activity(agent="dev-board-2", status="done")
        self.fx.activity(agent="dev-board-3", status="idle")
        st = self.state()
        self.assertEqual({c["agent"]: c["status"] for c in st["columns"]}, {
            "manager": "working", "dev-board-1": "blocked", "dev-board-2": "idle",
            "dev-board-3": "idle", "dev-board-4": "idle"})

    def test_latest_is_by_ts_not_by_file_order(self):
        self.fx.roster([MANAGER])
        self.fx.activity(ts="2026-10-12T10:05:00.000Z", status="working")
        self.fx.activity(ts="2026-10-12T10:01:00.000Z", status="blocked")
        self.assertEqual(self.column(self.state(), "manager")["status"], "working")

    def test_unknown_status_does_not_replace_the_last_known_one(self):
        self.fx.roster([MANAGER])
        self.fx.activity(status="working")
        self.fx.activity(status="unknown")
        self.assertEqual(self.column(self.state(), "manager")["status"], "working")

    def test_notes_path_only_when_the_file_exists(self):
        self.fx.roster([MANAGER, {"agent": "tech-board"}])
        self.fx.write("roles/tech-board.notes.md", "# notes\n")
        st = self.state()
        self.assertEqual(self.column(st, "tech-board")["notes_path"], "roles/tech-board.notes.md")
        self.assertIsNone(self.column(st, "manager")["notes_path"])


class IterationTest(BoardCase):
    def setUp(self):
        super().setUp()
        self.fx.roster([MANAGER])

    def test_highest_iteration_is_current_and_selected_by_default(self):
        for n in (2, 1, 3):
            self.fx.iteration(n)
        st = self.state()
        self.assertEqual((st["iterations"], st["iteration"], st["selected_iteration"]),
                         ([1, 2, 3], 3, 3))

    def test_iteration_query_selects_an_earlier_one(self):
        for n in (1, 2, 3):
            self.fx.iteration(n)
        st = self.state(iteration=2)
        self.assertEqual((st["iteration"], st["selected_iteration"]), (3, 2))

    def test_numeric_ordering_not_lexical(self):
        for n in (2, 10):
            self.fx.iteration(n)
        self.assertEqual(self.state()["iterations"], [2, 10])
        self.assertEqual(self.state()["iteration"], 10)

    def test_bad_or_unknown_iteration_is_400(self):
        self.fx.iteration(1)
        srv = self.start()
        for q in ("abc", "9", "", "-1", "+1", "1_0", "%201", "1.0", "1%0A", "1234567", "1%3B2",
                  "1&iteration=1", "1&iteration=2"):
            status, _, _ = srv.get("/state?iteration=" + q)
            self.assertEqual(status, 400, q)
        self.assertEqual(srv.get("/state?iteration=1")[0], 200)

    def test_no_iteration_files_gives_null_and_no_error(self):
        st = self.state()
        self.assertEqual((st["iterations"], st["iteration"], st["selected_iteration"]), ([], None, None))

    def test_iteration_query_without_files_is_400(self):
        status, _, _ = self.start().get("/state?iteration=1")
        self.assertEqual(status, 400)


class RobustnessTest(BoardCase):
    def assert_clean(self, srv):
        srv.stop()
        self.assertEqual(srv.stderr(), "")

    def test_bad_json_lines_are_skipped(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"}])
        self.fx.append_jsonl("messages.jsonl", "{not json")
        self.fx.append_jsonl("messages.jsonl", "[1, 2]")
        self.fx.append_jsonl("messages.jsonl", '"text"')
        self.fx.append_jsonl("messages.jsonl", "3")
        self.fx.append_jsonl("messages.jsonl", "null")
        self.fx.message(**{"from": "dev-board-3"})
        self.fx.append_jsonl("activity.jsonl", "{not json")
        self.fx.append_jsonl("activity.jsonl", "")
        self.fx.activity(agent="dev-board-4")
        srv = self.start()
        names = [c["agent"] for c in srv.state()["columns"]]
        self.assertEqual(names, ["manager", "tech-board", "dev-board-3", "dev-board-4"])
        self.assert_clean(srv)

    def test_missing_logs_give_a_well_formed_state(self):
        self.fx.roster([MANAGER, {"agent": "dev-board-1"}])
        srv = self.start()
        st = srv.state()
        self.assertEqual(set(st), TOP_KEYS)
        self.assertEqual(len(st["columns"]), 2)
        self.assert_clean(srv)

    def test_record_with_bad_ts_is_skipped(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"}])
        self.fx.message(ts="yesterday", **{"from": "ghost-a"})
        self.fx.message(ts=12345, **{"from": "ghost-b"})
        self.fx.message(ts=None, **{"from": "ghost-c"})
        self.fx.message(ts="2026-10-12T10:00:00", **{"from": "ghost-naive"})
        self.fx.append_jsonl("messages.jsonl", {"msg_id": "no-ts", "from": "ghost-d", "to": "manager"})
        self.fx.activity(ts="not-a-time", agent="ghost-e", status="working")
        srv = self.start()
        names = [c["agent"] for c in srv.state()["columns"]]
        self.assertEqual(names, ["manager", "tech-board"])
        self.assert_clean(srv)

    def test_repeated_msg_id_first_record_wins(self):
        self.fx.roster([MANAGER])
        self.fx.message(msg_id="dup", to="dev-board-3")
        self.fx.message(msg_id="dup", to="dev-board-4")
        srv = self.start()
        names = [c["agent"] for c in srv.state()["columns"]]
        self.assertIn("dev-board-3", names)
        self.assertNotIn("dev-board-4", names)
        self.assert_clean(srv)

    def test_odd_field_types_are_tolerated(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"}])
        self.fx.message(**{"from": 5, "to": ["a"], "unexpected": {"x": 1}})
        self.fx.message(type=3, text={"a": 1}, task=[], iteration="1", msg_id=7)
        self.fx.message(iteration="abc")
        self.fx.message(iteration=1.5)
        self.fx.activity(agent=None, status=7)
        srv = self.start()
        self.assertEqual([c["agent"] for c in srv.state()["columns"]], ["manager", "tech-board"])
        self.assert_clean(srv)

    def test_raw_u2028_inside_a_log_string_does_not_split_the_line(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"}])
        self.fx.message(**{"from": "dev-board-3"})
        with open(self.fx.root / "messages.jsonl", "ab") as f:
            f.write('{"ts":"2026-10-12T10:30:00.000Z","from":"a\u2028b","to":"manager"}\n'.encode("utf-8"))
        srv = self.start()
        self.assertIn("a\u2028b", [c["agent"] for c in srv.state()["columns"]])
        self.assert_clean(srv)

    def test_deeply_nested_json_line_is_skipped(self):
        self.fx.roster([MANAGER, {"agent": "tech-board", "role": "Tech Lead"}])
        self.fx.message(**{"from": "dev-board-3"})
        self.fx.append_jsonl("messages.jsonl", '{"a":' * 100000)
        self.fx.message(**{"from": "dev-board-4"})
        srv = self.start()
        names = [c["agent"] for c in srv.state()["columns"]]
        self.assertEqual(names, ["manager", "tech-board", "dev-board-3", "dev-board-4"])
        self.assert_clean(srv)

    def test_empty_fixture_folder_gives_empty_well_formed_state(self):
        srv = self.start()
        st = srv.state()
        self.assertEqual(set(st), TOP_KEYS)
        for key in ("iterations", "pods", "columns", "rows", "bars", "tasks", "needs_you"):
            self.assertEqual(st[key], [], key)
        self.assertEqual((st["iteration"], st["selected_iteration"]), (None, None))
        self.assert_clean(srv)

    def test_non_utf8_squad_file_does_not_crash(self):
        self.fx.roster([MANAGER])
        (self.fx.root / "scopes.md").write_bytes(b"| Scope | Size |\n|---|---|\n| all | \xff\xfe |\n")
        srv = self.start()
        self.assertEqual(srv.state()["columns"][0]["agent"], "manager")
        self.assert_clean(srv)

    def test_log_lines_with_invalid_utf8_are_skipped(self):
        self.fx.roster([MANAGER])
        with open(self.fx.root / "messages.jsonl", "wb") as f:
            f.write(b'{"ts":"2026-10-12T10:00:01Z","from":"\xff"}\n')
        self.fx.message(**{"from": "dev-board-3"})
        srv = self.start()
        self.assertIn("dev-board-3", [c["agent"] for c in srv.state()["columns"]])
        self.assert_clean(srv)


class RoutesTest(BoardCase):
    def setUp(self):
        super().setUp()
        self.fx.roster([MANAGER])
        self.srv = self.start()

    def test_startup_line_is_the_first_stdout_line(self):
        self.assertRegex(self.srv.startup_line, r"^squad-board: http://127\.0\.0\.1:\d+/$")
        self.assertIsNone(self.srv.token)

    def test_root_is_a_placeholder_html_page(self):
        status, headers, body = self.srv.get("/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "text/html; charset=utf-8")
        self.assertIn(b"<html", body.lower())

    def test_state_is_json_and_not_cached(self):
        status, headers, body = self.srv.get("/state")
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "application/json; charset=utf-8")
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertEqual(set(json.loads(body)), TOP_KEYS)

    def test_events_and_jump_are_not_implemented_yet(self):
        self.assertEqual(self.srv.get("/events")[0], 501)
        self.assertEqual(self.srv.post("/jump/manager")[0], 501)

    def test_other_paths_are_404(self):
        self.assertEqual(self.srv.get("/nope")[0], 404)
        self.assertEqual(self.srv.get("/state/x")[0], 404)
        self.assertEqual(self.srv.post("/state")[0], 404)
        self.assertEqual(self.srv.get("/../x")[0], 404)
        self.assertEqual(self.srv.get("/%2e%2e/x")[0], 404)
        self.assertEqual(self.srv.get("/roster.md")[0], 404)

    def test_state_reflects_files_written_after_start(self):
        self.assertEqual(len(self.srv.state()["columns"]), 1)
        self.fx.roster([MANAGER, {"agent": "dev-board-1"}])
        self.assertEqual(len(self.srv.state()["columns"]), 2)


class CommandLineTest(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(BIN)] + list(args), capture_output=True,
                              text=True, timeout=10)

    def test_replay_flag_is_required(self):
        res = self.run_cli()
        self.assertEqual(res.returncode, 2)
        self.assertIn("live mode arrives in iteration 2", res.stderr)

    def test_replay_dir_must_exist(self):
        res = self.run_cli("--replay", "/nonexistent-board-dir")
        self.assertEqual(res.returncode, 2)

    def test_missing_replay_dir_is_a_one_line_error(self):
        res = self.run_cli("--replay", "/nonexistent-board-dir")
        self.assertEqual(len(res.stderr.strip().splitlines()), 1)
        self.assertNotIn("Traceback", res.stderr)

    def test_bad_now_is_rejected(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        res = self.run_cli("--replay", str(fx.root), "--now", "tomorrow")
        self.assertEqual(res.returncode, 2)

    def test_busy_port_exits_1(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        srv = fx.start()
        res = self.run_cli("--replay", str(fx.root), "--port", str(srv.port))
        self.assertEqual(res.returncode, 1)


if __name__ == "__main__":
    unittest.main()
