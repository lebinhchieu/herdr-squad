"""squad-report embed (ticket 04): script-safe JSON, one-file assembly, atomic write, plugin assets."""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "bin"))
import squadreport_embed as emb  # noqa: E402

PLANT = "</script><img src=x onerror=1> & http://evil.test/x    "


class Embed(unittest.TestCase):
    def test_json_for_script_round_trips_and_has_no_raw_markup(self):
        s = emb.json_for_script({"title": PLANT, "n": [1, 2]})
        self.assertEqual(json.loads(s), {"title": PLANT, "n": [1, 2]})
        for bad in ("<", ">", "&", " ", " ", "://"):
            self.assertNotIn(bad, s)
        self.assertNotIn("</script", s)

    def test_assemble_one_file_no_url_and_single_pass(self):
        tpl = "<style>__CSS__</style><script type=\"application/json\">__DATA__</script><script>__JS__</script>"
        out = emb.assemble(tpl, "b{}", "var a='__DATA__';", {"t": PLANT})
        self.assertNotIn("http://", out)
        self.assertNotIn("https://", out)
        self.assertEqual(out.count("</script>"), 2)
        self.assertIn("var a='__DATA__';", out)  # a placeholder inside a value is not replaced again
        blob = re.search(r'application/json">(.*?)</script>', out, re.S).group(1)
        self.assertEqual(json.loads(blob)["t"], PLANT)

    def test_atomic_write_replaces_and_leaves_no_temp(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "data.json")
            emb.atomic_write(p, "one\ntwoé")
            emb.atomic_write(p, "new\n")
            with open(p, "rb") as f:
                self.assertEqual(f.read(), b"new\n")
            self.assertEqual(os.listdir(os.path.dirname(p)), ["data.json"])

    def test_plugin_assets_read_from_given_root_and_default_is_plugin_dir(self):
        with tempfile.TemporaryDirectory() as d:
            for n, v in zip(emb.ASSET_FILES, ("T", "C", "J")):
                with open(os.path.join(d, n), "w", encoding="utf-8", newline="\n") as f:
                    f.write(v)
            self.assertEqual(emb.plugin_assets(d), ("T", "C", "J"))
        self.assertEqual(os.path.realpath(emb.assets_dir()), str((HERE.parent / "templates" / "report").resolve()))


if __name__ == "__main__":
    unittest.main()
