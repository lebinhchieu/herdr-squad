"""BRD-04: token figures in GET /state come from each agent's transcript.

Seam A only: the real `bin/squad-board --replay` process, assertions on HTTP.
All transcript content is synthetic.
"""
import json
import os
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board_fixture import Fixture  # noqa: E402

NULLS = {"context_tokens": None, "tokens_in": None, "tokens_out": None, "model": None}
KEYS = tuple(NULLS)
SID = "11111111-2222-3333-4444-555555555555"
SID2 = "66666666-7777-8888-9999-000000000000"


def reply(msg_id, inp, cache_create, cache_read, out, model="model-a", **extra):
    rec = {"type": "assistant",
           "message": {"id": msg_id, "model": model, "role": "assistant",
                       "usage": {"input_tokens": inp, "cache_creation_input_tokens": cache_create,
                                 "cache_read_input_tokens": cache_read, "output_tokens": out}}}
    rec.update(extra)
    return rec


def figures(state, agent):
    col = next(c for c in state["columns"] if c["agent"] == agent)
    return {k: col[k] for k in KEYS}


class TokenTestCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"},
                        {"agent": "dev-board-5"}, {"agent": "dev-board-6"}])
        self.fx.iteration(1)
        self.fx.herdr({"dev-board-5": SID})

    def tpath(self, root="claude", project="p", sid=SID):
        return self.fx.root / "replay" / root / "projects" / project / (sid + ".jsonl")

    def check(self, expected, agent="dev-board-5"):
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        state = server.state()
        self.assertEqual(figures(state, agent), expected)
        self.assertEqual(server.stderr(), "")
        return server

    def append_raw(self, path, data):
        with open(path, "ab") as f:
            f.write(data)


class TestTotals(TokenTestCase):
    def test_sums_last_context_and_last_model(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 100, 1000, 7, "model-a"),
                                                reply("m2", 20, 200, 2000, 9, "model-b")])
        self.check({"context_tokens": 2220, "tokens_in": 3330, "tokens_out": 16, "model": "model-b"})

    def test_duplicate_message_id_counts_once_last_line_wins_by_position(self):
        self.fx.transcript("claude", "p", SID, [reply("A", 1, 0, 0, 1, "model-a"),
                                                reply("B", 2, 0, 0, 2, "model-b"),
                                                reply("A", 5, 0, 0, 5, "model-c")])
        # A's last line (in 5, out 5) replaces its first; A is also the last reply by position
        self.check({"context_tokens": 5, "tokens_in": 7, "tokens_out": 7, "model": "model-c"})

    def test_synthetic_model_is_skipped_but_other_lines_are_ignored(self):
        self.fx.transcript("claude", "p", SID, [
            reply("m1", 10, 0, 0, 1, "model-a"),
            {"type": "user", "message": {"role": "user", "content": "hi",
                                         "usage": {"input_tokens": 999, "output_tokens": 999}}},
            {"type": "assistant", "message": {"id": "m-nousage", "model": "model-z", "content": []}},
            {"type": "system", "note": "x"},
            reply("m2", 3, 0, 0, 4, "<synthetic>")])
        self.check({"context_tokens": 3, "tokens_in": 13, "tokens_out": 5, "model": "model-a"})

    def test_reply_without_message_id_still_counts(self):
        rec = reply("x", 4, 0, 0, 6)
        del rec["message"]["id"]
        self.fx.transcript("claude", "p", SID, [rec, rec])
        self.check({"context_tokens": 4, "tokens_in": 8, "tokens_out": 12, "model": "model-a"})

    def test_other_agents_are_unaffected_by_a_bad_transcript(self):
        self.fx.herdr({"dev-board-5": SID, "dev-board-6": SID2})
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.fx.transcript("claude", "p", SID2, ["garbage", "\x00\x01{"])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        state = server.state()
        self.assertEqual(figures(state, "dev-board-5")["tokens_in"], 10)
        self.assertEqual(figures(state, "dev-board-6"), NULLS)
        self.assertEqual(figures(state, "manager"), NULLS)
        self.assertEqual(server.stderr(), "")


class TestNulls(TokenTestCase):
    def test_no_herdr_json(self):
        (self.fx.root / "replay" / "herdr.json").unlink()
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.check(NULLS)

    def test_herdr_json_is_garbage(self):
        self.fx.write("replay/herdr.json", "{not json")
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.check(NULLS)

    def test_herdr_json_has_odd_shapes(self):
        self.fx.write("replay/herdr.json", json.dumps({"agents": {
            "dev-board-5": ["x"], "dev-board-6": {"session_id": 7}}}))
        self.check(NULLS)

    def test_session_id_not_in_herdr_json(self):
        self.fx.herdr({"someone-else": SID})
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.check(NULLS)

    def test_transcript_missing(self):
        self.fx.write("replay/claude/projects/p/other.jsonl", "")
        self.check(NULLS)

    def test_bad_session_ids_are_rejected(self):
        # decoy files that an unvalidated id could reach through a path trick or a glob
        decoy = [reply("m1", 10, 0, 0, 1)]
        self.fx.transcript("claude", ".", "x", decoy)
        for name in ("a b", "*", "x" * 65, "a.jsonl"):
            self.fx.transcript("claude", "p", name, decoy)
        for bad in ("../x", "a b", "a.jsonl", "/etc/passwd", "a\x00b", "*", "", "x" * 65, "a\n", "x/../x"):
            with self.subTest(session_id=bad):
                self.fx.herdr({"dev-board-5": bad})
                server = self.fx.start(now="2026-10-12T12:00:00Z")
                self.assertEqual(figures(server.state(), "dev-board-5"), NULLS)
                self.assertEqual(server.stderr(), "")
                server.close()

    def test_all_garbage_file(self):
        self.fx.transcript("claude", "p", SID, ["not json", "{", "[1,2]", "42", '"str"', "null", ""])
        self.check(NULLS)

    def test_empty_file(self):
        self.fx.write("replay/claude/projects/p/%s.jsonl" % SID, "")
        self.check(NULLS)

    def test_file_with_no_usage_lines(self):
        self.fx.transcript("claude", "p", SID, [{"type": "user", "message": {"content": "hi"}},
                                                {"type": "assistant", "message": {"id": "m", "content": []}}])
        self.check(NULLS)

    def test_transcript_path_is_a_directory(self):
        self.tpath().mkdir(parents=True)
        self.check(NULLS)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read anything")
    def test_unreadable_file(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.tpath().chmod(0)
        self.check(NULLS)


class TestRoots(TokenTestCase):
    def test_transcript_under_any_claude_star_root(self):
        self.fx.transcript("claude-2", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.check({"context_tokens": 10, "tokens_in": 10, "tokens_out": 1, "model": "model-a"})

    def test_non_claude_folder_is_not_a_root(self):
        self.fx.transcript("other", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.check(NULLS)

    def test_same_file_through_two_roots_counts_once(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1), reply("m2", 20, 0, 0, 2)])
        (self.fx.root / "replay" / "claude-2").mkdir()
        os.symlink(self.fx.root / "replay" / "claude" / "projects",
                   self.fx.root / "replay" / "claude-2" / "projects")
        self.check({"context_tokens": 20, "tokens_in": 30, "tokens_out": 3, "model": "model-a"})

    def test_symlink_pointing_outside_replay_is_not_read(self):
        outside = Fixture()
        self.addCleanup(outside.close)
        outside.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        proj = self.fx.root / "replay" / "claude" / "projects" / "p"
        proj.mkdir(parents=True)
        os.symlink(outside.root / "replay" / "claude" / "projects" / "p" / (SID + ".jsonl"),
                   proj / (SID + ".jsonl"))
        self.check(NULLS)

    def test_project_folder_symlinked_outside_replay_is_not_read(self):
        outside = Fixture()
        self.addCleanup(outside.close)
        outside.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        projects = self.fx.root / "replay" / "claude" / "projects"
        projects.mkdir(parents=True)
        os.symlink(outside.root / "replay" / "claude" / "projects" / "p", projects / "p")
        self.check(NULLS)

    def test_herdr_json_symlinked_outside_replay_is_not_read(self):
        outside = Fixture()
        self.addCleanup(outside.close)
        outside.herdr({"dev-board-5": SID})
        (self.fx.root / "replay" / "herdr.json").unlink()
        os.symlink(outside.root / "replay" / "herdr.json", self.fx.root / "replay" / "herdr.json")
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.check(NULLS)


class TestIncremental(TokenTestCase):
    def test_appended_reply_grows_totals_by_exactly_that_reply(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1, "model-a")])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5"),
                         {"context_tokens": 10, "tokens_in": 10, "tokens_out": 1, "model": "model-a"})
        self.fx.append_jsonl("replay/claude/projects/p/%s.jsonl" % SID, reply("m2", 30, 0, 0, 4, "model-b"))
        self.assertEqual(figures(server.state(), "dev-board-5"),
                         {"context_tokens": 30, "tokens_in": 40, "tokens_out": 5, "model": "model-b"})
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 40)
        self.assertEqual(server.stderr(), "")

    def test_line_without_trailing_newline_is_not_counted_until_complete(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)
        self.append_raw(self.tpath(), json.dumps(reply("m2", 30, 0, 0, 4)).encode())
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)
        self.append_raw(self.tpath(), b"\n")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 40)
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 40)
        self.assertEqual(server.stderr(), "")

    def test_partial_line_completed_in_two_appends_is_parsed_whole(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        server.state()
        line = json.dumps(reply("m2", 30, 0, 0, 4)).encode()
        self.append_raw(self.tpath(), line[:20])
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)
        self.append_raw(self.tpath(), line[20:] + b"\n")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 40)

    def test_transcript_appearing_after_start_is_picked_up(self):
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5"), NULLS)
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)

    def test_duplicate_id_appended_in_a_later_read_replaces_the_earlier_line(self):
        self.fx.transcript("claude", "p", SID, [reply("X", 10, 0, 0, 1, "model-a")])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)
        self.fx.append_jsonl("replay/claude/projects/p/%s.jsonl" % SID, reply("X", 50, 0, 0, 9, "model-b"))
        self.assertEqual(figures(server.state(), "dev-board-5"),
                         {"context_tokens": 50, "tokens_in": 50, "tokens_out": 9, "model": "model-b"})
        self.fx.append_jsonl("replay/claude/projects/p/%s.jsonl" % SID, reply("Y", 2, 0, 0, 1, "model-a"))
        self.fx.append_jsonl("replay/claude/projects/p/%s.jsonl" % SID, reply("X", 7, 0, 0, 3, "model-c"))
        # X now sits after Y by position, so it is the last reply
        self.assertEqual(figures(server.state(), "dev-board-5"),
                         {"context_tokens": 7, "tokens_in": 9, "tokens_out": 4, "model": "model-c"})

    def test_shrunk_file_is_recomputed_from_scratch(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 100, 0, 0, 10), reply("m2", 200, 0, 0, 20)])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 300)
        self.fx.transcript("claude", "p", SID, [reply("n1", 3, 0, 0, 1)])
        self.assertEqual(figures(server.state(), "dev-board-5"),
                         {"context_tokens": 3, "tokens_in": 3, "tokens_out": 1, "model": "model-a"})
        self.assertEqual(server.stderr(), "")

    def test_file_truncated_keeping_the_same_first_bytes_is_recomputed(self):
        # The start of the file is unchanged, so only the smaller size can show it was cut.
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1), reply("m2", 20, 0, 0, 2),
                                                reply("m3", 30, 0, 0, 3)])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 60)
        data = self.tpath().read_bytes()
        first = data.index(b"\n") + 1
        self.assertGreater(first, 64)
        self.tpath().write_bytes(data[:first + 10])  # one whole reply plus the start of the next
        self.assertEqual(figures(server.state(), "dev-board-5"),
                         {"context_tokens": 10, "tokens_in": 10, "tokens_out": 1, "model": "model-a"})
        self.assertEqual(server.stderr(), "")

    def test_file_replaced_by_longer_different_content_is_recomputed(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 1, 0, 0, 1)])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 1)
        self.fx.transcript("claude", "p", SID, [reply("zz-%d" % i, 1000 + i, 0, 0, 1) for i in range(5)])
        self.assertEqual(figures(server.state(), "dev-board-5"),
                         {"context_tokens": 1004, "tokens_in": 5010, "tokens_out": 5, "model": "model-a"})

    def test_file_emptied_gives_nulls(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)
        self.tpath().write_text("")
        self.assertEqual(figures(server.state(), "dev-board-5"), NULLS)

    def test_file_deleted_gives_nulls(self):
        self.fx.transcript("claude", "p", SID, [reply("m1", 10, 0, 0, 1)])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        self.assertEqual(figures(server.state(), "dev-board-5")["tokens_in"], 10)
        self.tpath().unlink()
        self.assertEqual(figures(server.state(), "dev-board-5"), NULLS)
        self.assertEqual(server.stderr(), "")


class TestConcurrency(TokenTestCase):
    def test_parallel_state_requests_give_the_same_numbers(self):
        self.fx.herdr({"dev-board-5": SID, "dev-board-6": SID2})
        lines = [reply("m%d" % i, i, 0, 0, 1) for i in range(1, 400)]
        self.fx.transcript("claude", "p", SID, lines)
        self.fx.transcript("claude-2", "p", SID2, lines[:10])
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        results, errors = [], []

        def worker():
            try:
                state = server.state()
                results.append((figures(state, "dev-board-5"), figures(state, "dev-board-6")))
            except Exception as e:  # noqa: BLE001 - reported below
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(30)
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 8)
        want5 = {"context_tokens": 399, "tokens_in": 399 * 400 // 2, "tokens_out": 399, "model": "model-a"}
        want6 = {"context_tokens": 10, "tokens_in": 55, "tokens_out": 10, "model": "model-a"}
        for got in results:
            self.assertEqual(got, (want5, want6))
        self.assertEqual(server.stderr(), "")


class TestRobustLines(TokenTestCase):
    def test_invalid_utf8_line_is_skipped_others_counted(self):
        good = json.dumps(reply("m1", 10, 0, 0, 1)).encode()
        bad = b'{"type":"assistant","message":{"id":"b","usage":{"input_tokens":\xff\xfe5}}}'
        # invalid bytes inside a string value must not lose the reply
        inside = json.dumps(reply("m2", 20, 0, 0, 2)).replace("model-a", "mod\\u00e9l").encode()
        inside = inside.replace(b"mod", b"mod\xff")
        path = self.tpath()
        path.parent.mkdir(parents=True)
        path.write_bytes(good + b"\n" + bad + b"\n" + inside + b"\n")
        server = self.fx.start(now="2026-10-12T12:00:00Z")
        got = figures(server.state(), "dev-board-5")
        self.assertEqual((got["tokens_in"], got["tokens_out"]), (30, 3))
        self.assertEqual(server.stderr(), "")

    def test_one_megabyte_line_does_not_hang_and_counts(self):
        big = reply("big", 10, 0, 0, 1)
        big["padding"] = "x" * 1_000_000
        self.fx.transcript("claude", "p", SID, [big, reply("m2", 5, 0, 0, 2)])
        self.check({"context_tokens": 5, "tokens_in": 15, "tokens_out": 3, "model": "model-a"})

    def test_deeply_nested_line_does_not_crash(self):
        self.fx.transcript("claude", "p", SID, ['{"usage":' + "[" * 100000, reply("m1", 10, 0, 0, 1)])
        self.check({"context_tokens": 10, "tokens_in": 10, "tokens_out": 1, "model": "model-a"})

    def test_bad_usage_fields_count_as_zero_and_the_reply_still_counts(self):
        rec = reply("m1", "5", -3, 2.5, None, "model-x")
        rec2 = reply("m2", True, 7, 0, 4, "model-y")
        rec3 = reply("m3", 1, 0, 0, 1, "model-z")
        self.fx.transcript("claude", "p", SID, [rec, rec2, rec3])
        # m1 -> in 0 out 0; m2 -> in 7 out 4 (True is not a count); m3 -> in 1 out 1
        self.check({"context_tokens": 1, "tokens_in": 8, "tokens_out": 5, "model": "model-z"})

    def test_bad_usage_on_last_reply_gives_zero_context_not_a_crash(self):
        rec = reply("m1", 10, 0, 0, 1, "model-a")
        rec["message"]["usage"] = {"input_tokens": "lots"}
        self.fx.transcript("claude", "p", SID, [reply("m0", 4, 0, 0, 1), rec])
        self.check({"context_tokens": 0, "tokens_in": 4, "tokens_out": 1, "model": "model-a"})

    def test_usage_not_an_object_or_model_not_a_string(self):
        weird = reply("m1", 10, 0, 0, 1)
        weird["message"]["usage"] = [1, 2]
        odd_model = reply("m2", 6, 0, 0, 2, 42)
        self.fx.transcript("claude", "p", SID, [weird, odd_model])
        self.check({"context_tokens": 6, "tokens_in": 6, "tokens_out": 2, "model": None})

    def test_message_not_an_object(self):
        self.fx.transcript("claude", "p", SID, [{"type": "assistant", "message": "text"},
                                                reply("m1", 10, 0, 0, 1)])
        self.check({"context_tokens": 10, "tokens_in": 10, "tokens_out": 1, "model": "model-a"})

    def test_line_with_u2028_inside_a_string_is_one_line(self):
        rec = reply("m1", 10, 0, 0, 1)
        rec["note"] = "a b\u0085c"
        self.fx.transcript("claude", "p", SID, [json.dumps(rec, ensure_ascii=False), reply("m2", 5, 0, 0, 1)])
        self.check({"context_tokens": 5, "tokens_in": 15, "tokens_out": 2, "model": "model-a"})


if __name__ == "__main__":
    unittest.main()
