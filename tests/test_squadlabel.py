"""squadlabel: the label rule, the label store, and number assignment."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import squadlabel as sl  # noqa: E402


class BuildLabelTest(unittest.TestCase):
    def test_every_role_with_and_without_number_and_title(self):
        for role, name in sl.ROLE_NAMES.items():
            emoji = "🦀" if role == "manager" else "🤖"
            for number, title, tail in [(None, "", ""), (2, "", " 2"), (None, "T-1 x", " · T-1 x"), (3, "T-1 x", " 3 · T-1 x")]:
                self.assertEqual(sl.build_label(role, number, title), f"{emoji} {name}{tail}")

    def test_unknown_role_is_title_cased(self):
        self.assertEqual(sl.build_label("data-wrangler"), "🤖 Data Wrangler")

    def test_blank_whitespace_and_multiline_titles(self):
        self.assertEqual(sl.build_label("dev", None, ""), "🤖 Dev")
        self.assertEqual(sl.build_label("dev", None, "  \n\t "), "🤖 Dev")
        self.assertEqual(sl.build_label("dev", 1, "  a\n\nb \t c\x07\x1b[0m "), "🤖 Dev 1 · a b c[0m")

    def test_cut_at_32_code_points(self):
        exact = "🤖 Dev · " + "x" * 24
        self.assertEqual(len(exact), 32)
        self.assertEqual(sl.build_label("dev", None, "x" * 24), exact)
        cut = sl.build_label("dev", None, "x" * 25)
        self.assertEqual(cut, "🤖 Dev · " + "x" * 23 + "…")
        self.assertEqual(len(cut), 32)

    def test_spec_example(self):
        self.assertEqual(sl.build_label("qa-blackbox", None, "TAB-05 integration live check"),
                         "🤖 QA Blackbox · TAB-05 integrat…")

    def test_board_labels(self):
        self.assertEqual((sl.BOARD_LABEL, sl.LEGACY_BOARD_LABEL), ("📋 Board", "board"))


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "a"
        self.other = Path(self.tmp.name) / "b"

    def tearDown(self):
        self.tmp.cleanup()

    def test_round_trip_and_no_tmp_left(self):
        sl.write_entry(self.home, "dev-1", "dev", 2, "TAB-02 ü")
        self.assertEqual(sl.read_entry(self.home, "dev-1"), {"role": "dev", "number": 2, "title": "TAB-02 ü"})
        self.assertEqual([p.name for p in (self.home / "labels").iterdir()], ["dev-1.json"])

    def test_missing_and_bad_json_give_none(self):
        self.assertIsNone(sl.read_entry(self.home, "dev-1"))
        (self.home / "labels").mkdir(parents=True)
        (self.home / "labels" / "dev-1.json").write_text("{not json")
        self.assertIsNone(sl.read_entry(self.home, "dev-1"))
        (self.home / "labels" / "dev-1.json").write_text("[1]")
        self.assertIsNone(sl.read_entry(self.home, "dev-1"))

    def test_bad_names_refused_before_any_path(self):
        for bad in ("../x", "A b", "", "x" * 33, "-a"):
            with self.assertRaises(ValueError):
                sl.write_entry(self.home, bad, "dev", None, "")
            self.assertIsNone(sl.read_entry(self.home, bad))
        self.assertFalse(self.home.exists())

    def test_homes_are_separate(self):
        sl.write_entry(self.home, "dev-1", "dev", None, "")
        self.assertIsNone(sl.read_entry(self.other, "dev-1"))


class AssignNumberTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, name, role="dev", number=None):
        sl.write_entry(self.home, name, role, number, "")

    def test_no_peer_gives_none(self):
        self.assertEqual(sl.assign_number(self.home, "d1", "dev", {"d1"}), (None, []))

    def test_one_live_peer_becomes_1_and_new_is_2(self):
        self.add("d1")
        self.assertEqual(sl.assign_number(self.home, "d2", "dev", {"d1", "d2"}), (2, [("d1", 1)]))
        self.assertEqual(sl.read_entry(self.home, "d1")["number"], 1)

    def test_three_agents_get_1_2_3(self):
        self.add("d1")
        n2, _ = sl.assign_number(self.home, "d2", "dev", {"d1"})
        self.add("d2", number=n2)
        n3, changed = sl.assign_number(self.home, "d3", "dev", {"d1", "d2"})
        self.assertEqual((n2, n3, changed), (2, 3, []))

    def test_other_roles_are_not_peers(self):
        self.add("q1", role="qa-whitebox")
        self.assertEqual(sl.assign_number(self.home, "d1", "dev", {"q1"}), (None, []))

    def test_retired_peer_is_ignored_and_never_rewritten(self):
        self.add("d1")
        f = Path(self.home, "labels", "d1.json")
        before = f.read_text()
        self.assertEqual(sl.assign_number(self.home, "d2", "dev", {"d2"}), (None, []))
        self.assertEqual(f.read_text(), before)

    def test_numbers_never_move(self):
        self.add("d2", number=2)  # Dev 1 retired
        self.assertEqual(sl.assign_number(self.home, "d3", "dev", {"d2"}), (3, []))

    def test_respawn_keeps_its_number(self):
        self.add("d1", number=1)
        self.add("d2", number=2)
        self.assertEqual(sl.assign_number(self.home, "d2", "dev", {"d1", "d2"}), (2, []))

    def test_unnumbered_peer_gets_smallest_free(self):
        self.add("d1", number=1)
        self.add("d3")
        self.assertEqual(sl.assign_number(self.home, "d4", "dev", {"d1", "d3"}), (3, [("d3", 2)]))


if __name__ == "__main__":
    unittest.main()
