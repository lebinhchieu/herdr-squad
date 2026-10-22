"""squad-evidence: path, add and check (spec evidence-inline, "The tool")."""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
TOOL = BIN / "squad-evidence"
PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"


def png(tag):
    return PNG + tag.encode()  # distinct bytes per tag, still a tiny file


def tool(*args, cwd=None):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, encoding="utf-8",
                          cwd=cwd, env=env)


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
    return path


def text(path):
    with open(path, encoding="utf-8", newline="\n") as f:
        return f.read()


def tree(folder):
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.ticket = put(self.root / ".scratch/f/issues/03-x.md", "Status: ready\n\n# 03: The thing\n\nbody\n")
        self.folder = self.root / ".scratch/f/issues/03-x"
        self.ev = self.folder / "evidence.md"
        self.work = self.root / "work"


class PathTest(Base):
    def test_ticket_in_issues(self):
        r = tool("path", ".scratch/f/issues/03-x.md")
        self.assertEqual((r.returncode, r.stdout), (0, ".scratch/f/issues/03-x\n"))

    def test_task_file(self):
        r = tool("path", "tasks/T1.md")
        self.assertEqual((r.returncode, r.stdout), (0, "tasks/T1\n"))

    def test_not_md_is_usage_error(self):
        r = tool("path", "tasks/T1.txt")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")

    def test_no_args_is_usage_error(self):
        self.assertEqual(tool().returncode, 2)
        self.assertEqual(tool("add", str(self.ticket)).returncode, 2)


class AddTest(Base):
    def review(self, name="tl-review.md", body=None, **images):
        for n, tag in images.items():
            put(self.work / n.replace("_", "."), png(tag))
        return put(self.work / name, body or "")

    def add(self, review, heading="Tech Lead review", *extra):
        return tool("add", str(self.ticket), "--heading", heading, "--from", str(review), *extra)

    def test_copies_relative_and_absolute_images_and_rewrites_links(self):
        put(self.work / "shots/a.png", png("a"))
        absimg = put(self.root / "elsewhere/b.png", png("b"))
        rv = put(self.work / "tl-review.md",
                 f"# Review\n\nok\n\n## Findings\n\n![rel](shots/a.png)\n\n![abs]({absimg})\n")
        r = self.add(rv)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(tree(self.folder / "img"), {"a.png": png("a"), "b.png": png("b")})
        t = text(self.ev)
        self.assertIn("![rel](img/a.png)", t)
        self.assertIn("![abs](img/b.png)", t)
        self.assertIn("## Tech Lead review\n\n### Review\n", t)  # `# ` demoted to `###`
        self.assertIn("\n#### Findings\n", t)
        self.assertNotIn(str(absimg), t)
        self.assertEqual(tool("check", str(self.folder)).returncode, 0)

    def test_second_run_is_byte_identical(self):
        put(self.work / "a.png", png("a"))
        rv = put(self.work / "r.md", "# R\n\n![x](a.png)\n")
        self.add(rv)
        first = (text(self.ev), tree(self.folder / "img"))
        r = self.add(rv)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((text(self.ev), tree(self.folder / "img")), first)

    def test_name_clash_between_reviews_prefixes_the_second(self):
        put(self.work / "one/s.png", png("one"))
        put(self.work / "two/s.png", png("two"))
        r1 = put(self.work / "one/r.md", "![a](s.png)\n")
        r2 = put(self.work / "two/r.md", "![b](s.png)\n")
        self.add(r1, "Tech Lead review")
        self.add(r2, "QA whitebox")
        self.assertEqual(tree(self.folder / "img"), {"s.png": png("one"), "qa-whitebox-s.png": png("two")})
        t = text(self.ev)
        self.assertIn("![a](img/s.png)", t)
        self.assertIn("![b](img/qa-whitebox-s.png)", t)
        before = (t, tree(self.folder / "img"))
        self.add(r2, "QA whitebox")  # re-adding the second keeps its prefixed name
        self.assertEqual((text(self.ev), tree(self.folder / "img")), before)
        self.assertEqual(tool("check", str(self.folder)).returncode, 0)

    def test_missing_image_exits_2_and_writes_nothing(self):
        put(self.work / "a.png", png("a"))
        rv = put(self.work / "r.md", "![ok](a.png)\n\n![gone](nope.png)\n")
        r = self.add(rv)
        self.assertEqual(r.returncode, 2)
        self.assertIn("nope.png", r.stderr)
        self.assertFalse(self.folder.exists())

    def test_missing_image_leaves_an_existing_file_unchanged(self):
        rv = put(self.work / "r.md", "ok\n")
        self.add(rv)
        before = (text(self.ev), tree(self.folder))
        put(self.work / "r2.md", "![gone](nope.png)\n")
        self.assertEqual(self.add(self.work / "r2.md").returncode, 2)
        self.assertEqual((text(self.ev), tree(self.folder)), before)

    def test_creates_title_from_ticket(self):
        self.add(put(self.work / "r.md", "ok\n"), "Tech Lead review", "--sha", "a" * 40)
        t = text(self.ev)
        self.assertTrue(t.startswith("# Evidence: 03 The thing\nsha: " + "a" * 40 + "\n\n## Tech Lead review\n"), t)

    def test_title_without_a_title_line(self):
        put(self.ticket, "Status: ready\n\nno heading here\n")
        self.add(put(self.work / "r.md", "ok\n"))
        self.assertTrue(text(self.ev).startswith("# Evidence: 03\n\n## Tech Lead review\n"), text(self.ev))

    def test_title_keeps_a_title_not_starting_with_the_number(self):
        put(self.ticket, "# Add the thing\n")
        self.add(put(self.work / "r.md", "ok\n"))
        self.assertTrue(text(self.ev).startswith("# Evidence: 03 Add the thing\n"))

    def test_task_file_ticket(self):
        t = put(self.root / "tasks/T1.md", "# Do it\n")
        r = tool("add", str(t), "--heading", "H", "--from", str(put(self.work / "r.md", "x\n")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(text(self.root / "tasks/T1/evidence.md").startswith("# Evidence: T1 Do it\n"))

    def test_developers_behaviour_section_is_never_touched_or_reordered(self):
        behaviour = "## Behaviour\n\n### AC 1\n\nran `x`, saw y\n\n```\nout\n```\n"
        put(self.ev, "# Evidence: 03 The thing\nsha: " + "b" * 40 + "\n\n" + behaviour)
        self.add(put(self.work / "r1.md", "one\n"), "Tech Lead review")
        self.add(put(self.work / "r2.md", "two\n"), "QA whitebox")
        self.add(put(self.work / "r1.md", "one again\n"), "Tech Lead review")  # replace, not append
        t = text(self.ev)
        self.assertIn("\n\n" + behaviour + "\n## Tech Lead review\n\none again\n\n## QA whitebox\n\ntwo\n", t)
        self.assertEqual(t.count("## Tech Lead review"), 1)
        self.assertEqual(t.index("## Behaviour") < t.index("## Tech Lead review") < t.index("## QA whitebox"), True)

    def test_replacing_a_section_removes_images_only_it_used(self):
        put(self.work / "a.png", png("a"))
        self.add(put(self.work / "r.md", "![a](a.png)\n"))
        self.assertIn("a.png", tree(self.folder / "img"))
        self.add(put(self.work / "r.md", "no image now\n"))
        self.assertEqual(tree(self.folder / "img"), {})
        self.assertEqual(tool("check", str(self.folder)).returncode, 0)

    def test_fenced_block_is_not_demoted_or_rewritten(self):
        rv = put(self.work / "r.md", "# T\n\n```\n# not a heading\n![x](missing.png)\n```\n")
        r = self.add(rv)
        self.assertEqual(r.returncode, 0, r.stderr)
        t = text(self.ev)
        self.assertIn("```\n# not a heading\n![x](missing.png)\n```", t)

    def test_crlf_review_is_written_back_as_lf(self):
        put(self.work / "a.png", png("a"))
        rv = self.work / "r.md"
        rv.write_bytes(b"# R\r\n\r\nline\r\n![a](a.png)\r\n")
        self.assertEqual(self.add(rv).returncode, 0)
        self.assertNotIn(b"\r", self.ev.read_bytes())

    def test_utf8_survives(self):
        self.add(put(self.work / "r.md", "# Überprüfung ✓\n\nrésumé\n"))
        self.assertIn("Überprüfung ✓", text(self.ev))

    def test_root_resolves_a_relative_ticket(self):
        r = tool("add", ".scratch/f/issues/03-x.md", "--heading", "H", "--from", str(put(self.work / "r.md", "x\n")),
                 "--root", str(self.root), cwd=self.work)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.ev.exists())

    def test_missing_ticket_or_review_is_usage_error(self):
        self.assertEqual(tool("add", str(self.root / "nope.md"), "--heading", "H",
                              "--from", str(put(self.work / "r.md", "x\n"))).returncode, 2)
        self.assertEqual(tool("add", str(self.ticket), "--heading", "H", "--from", str(self.work / "no.md")).returncode, 2)


class CheckTest(Base):
    def make(self, body, imgs=None):
        put(self.ev, "# Evidence: 03 The thing\n\n## Behaviour\n\n" + body)
        for n, data in (imgs or {}).items():
            put(self.folder / "img" / n, data)

    def problems(self, *extra):
        r = tool("check", str(self.folder), *extra)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        lines = r.stdout.strip().split("\n")
        for ln in lines:
            self.assertRegex(ln, r"^.+:\d+: .+")  # file:line: problem
        return lines

    def test_clean_folder_passes(self):
        self.make("![shot](img/a.png)\n\n```\nimg/other.png is fine in a fence\n```\n", {"a.png": png("a")})
        r = tool("check", str(self.folder))
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertEqual(tool("check", str(self.ev)).returncode, 0)  # the file works as well as the folder

    def test_absolute_embed(self):
        self.make("![a](/tmp/a.png)\n")
        self.assertRegex(self.problems()[0], r"evidence\.md:5: .*absolute")

    def test_windows_absolute_embed(self):
        self.make("![a](C:\\x\\a.png)\n")
        self.assertRegex(self.problems()[0], r"absolute")

    def test_url_embed(self):
        self.make("![a](https://example.com/a.png)\n")
        self.assertRegex(self.problems()[0], r"evidence\.md:5: .*URL")

    def test_dotdot(self):
        self.make("![a](../a.png)\n")
        self.assertRegex(self.problems()[0], r"evidence\.md:5: .*\.\.")

    def test_empty_alt(self):
        self.make("![](img/a.png)\n", {"a.png": png("a")})
        self.assertRegex(self.problems()[0], r"evidence\.md:5: .*empty alt")

    def test_missing_target(self):
        self.make("![a](img/gone.png)\n")
        self.assertRegex(self.problems()[0], r"evidence\.md:5: .*missing")

    def test_non_image_extension(self):
        self.make("![a](img/notes.txt)\n", {"notes.txt": b"x"})
        self.assertRegex(" ".join(self.problems()), r"evidence\.md:5: .*not an image")

    def test_orphan_in_img(self):
        self.make("text only\n", {"a.png": png("a")})
        self.assertRegex(self.problems()[0], r"img/a\.png:\d+: .*orphan")

    def test_backticked_screenshot(self):
        self.make("see `img/a.png`\n", {"a.png": png("a")})
        ps = self.problems()
        self.assertTrue(any(re.search(r"evidence\.md:5: .*a\.png", p) for p in ps), ps)

    def test_linked_screenshot(self):
        self.make("see [the shot](img/a.png)\n", {"a.png": png("a")})
        ps = self.problems()
        self.assertTrue(any("evidence.md:5:" in p and "a.png" in p for p in ps), ps)

    def test_bare_file_name(self):
        self.make("saw home.png then left\n")
        self.assertRegex(self.problems()[0], r"evidence\.md:5: .*home\.png")

    def test_fence_may_name_an_image_but_text_after_it_may_not(self):
        self.make("```\nimg/a.png\n```\n\nafter a.png\n", {})
        ps = self.problems()
        self.assertEqual(len(ps), 1)
        self.assertIn("evidence.md:9:", ps[0])

    def test_tilde_fence_and_longer_fence(self):
        self.make("~~~\na.png\n~~~\n\n````\n```\nb.png\n```\n````\n")
        self.assertEqual(tool("check", str(self.folder)).returncode, 0)

    def test_image_over_one_mb(self):
        self.make("![big](img/big.png)\n", {"big.png": b"\0" * (1024 * 1024 + 1)})
        self.assertRegex(self.problems()[0], r"big\.png:\d+: .*1 MB")
        # exactly 1 MB is fine
        put(self.folder / "img/big.png", b"\0" * (1024 * 1024))
        self.assertEqual(tool("check", str(self.folder)).returncode, 0)

    def test_missing_evidence_md_is_usage_error(self):
        self.assertEqual(tool("check", str(self.root / "nothing")).returncode, 2)

    def test_crlf_evidence_file(self):
        self.make("![a](img/a.png)\n", {"a.png": png("a")})
        self.ev.write_bytes(self.ev.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(tool("check", str(self.folder)).returncode, 0)


class FolderResolutionTest(Base):
    def run_add(self):
        r = tool("add", str(self.ticket), "--heading", "H", "--from", str(put(self.work / "r.md", "x\n")))
        self.assertEqual(r.returncode, 0, r.stderr)

    def old(self):
        return Path(str(self.folder) + ".evidence")

    def test_nothing_exists_creates_new(self):
        self.run_add()
        self.assertTrue(self.ev.is_file())
        self.assertFalse(self.old().exists())

    def test_only_old_is_used_and_no_second_folder(self):
        put(self.old() / "evidence.md", "# Evidence: 03 The thing\n\n## Behaviour\n\nx\n")
        r = tool("path", str(self.ticket))
        self.assertEqual(r.stdout.strip(), str(self.old()))
        self.run_add()
        self.assertIn("## H", text(self.old() / "evidence.md"))
        self.assertFalse(self.folder.exists())

    def test_both_exist_new_wins(self):
        put(self.old() / "evidence.md", "# E\n")
        put(self.folder / "evidence.md", "# E\n")
        self.assertEqual(tool("path", str(self.ticket)).stdout.strip(), str(self.folder))

    def test_check_accepts_old_and_new_folder(self):
        for f in (self.old(), self.folder):
            put(f / "evidence.md", "# E\n\n## B\n\nx\n")
            self.assertEqual(tool("check", str(f)).returncode, 0)


class CheckBaseTest(Base):
    def git(self, *args):
        r = subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t",
                            "-c", "commit.gpgsign=false", *args], capture_output=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def setUp(self):
        super().setUp()
        self.git("init", "-q")
        put(self.root / ".scratch/f/issues/04-y.md", "# Y\n")
        put(self.root / "code.py", "x = 1\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-qm", msg)

    def test_evidence_only_diff_passes(self):
        put(self.folder / "evidence.md", "# E\n\n## B\n\n![a](img/a.png)\n")
        put(self.folder / "img/a.png", png("a"))
        put(self.root / ".scratch/f/issues/04-y/evidence.md", "# E\n")  # another ticket's folder is evidence too
        put(self.root / ".scratch/f/issues/05-z.evidence/evidence.md", "# E\n")  # old form
        self.commit("evidence")
        r = tool("check", str(self.folder), "--base", self.base)
        self.assertEqual((r.returncode, r.stdout.startswith("ok")), (0, True), r.stdout + r.stderr)

    def test_a_path_outside_an_evidence_folder_fails(self):
        put(self.folder / "evidence.md", "# E\n\n## B\n\nx\n")
        put(self.root / "code.py", "x = 2\n")
        put(self.root / "notes.evidence.md", "x\n")  # a file, not a folder, named like one
        self.commit("mixed")
        r = tool("check", str(self.folder), "--base", self.base)
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2, lines)
        self.assertRegex(lines[0], r"^code\.py:\d+: .*outside an evidence folder.*\*\.evidence/")
        self.assertRegex(lines[1], r"^notes\.evidence\.md:\d+: ")

    def test_other_files_in_the_ticket_folder_and_stemless_folders_fail(self):
        put(self.folder / "evidence.md", "# E\n\n## B\n\n![a](img/a/b.png)\n")
        put(self.folder / "img/a/b.png", png("a"))
        put(self.folder / "notes.txt", "x\n")
        put(self.root / "bin/x", "x\n")
        put(self.root / "docs/foo/evidence.md", "# E\n")
        self.commit("mixed")
        r = tool("check", str(self.folder), "--base", self.base)
        self.assertEqual(r.returncode, 1)
        bad = sorted(l.split(":")[0] for l in r.stdout.strip().split("\n"))
        self.assertEqual(bad, [".scratch/f/issues/03-x/notes.txt", "bin/x", "docs/foo/evidence.md"])

    def test_unknown_base_is_usage_error(self):
        put(self.folder / "evidence.md", "# E\n")
        self.assertEqual(tool("check", str(self.folder), "--base", "deadbeef" * 5).returncode, 2)


if __name__ == "__main__":
    unittest.main()
