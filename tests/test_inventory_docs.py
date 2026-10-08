import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.inventory_docs import inventory, main


class InventoryDocsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_inventory_is_sorted_unicode_aware_and_excludes_generated_dirs(self):
        (self.root / "zeta.md").write_text("# Z\n", encoding="utf-8")
        nested = self.root / "docs"
        nested.mkdir()
        (nested / "日本語.md").write_text("# 記録\n", encoding="utf-8")
        (nested / "a.markdown").write_text("# A\n", encoding="utf-8")
        for directory in (".git", "build", "node_modules", "vendor"):
            excluded = self.root / directory
            excluded.mkdir()
            (excluded / "ignored.md").write_text("ignored", encoding="utf-8")

        expected = ["docs/a.markdown", "docs/日本語.md", "zeta.md"]
        self.assertEqual(inventory(self.root), expected)
        self.assertEqual(inventory(self.root), expected)

    def test_empty_repository_returns_empty_list(self):
        self.assertEqual(inventory(self.root), [])

    def test_json_cli_is_machine_readable_and_does_not_modify_files(self):
        source = self.root / "日本語.md"
        source.write_text("# 変更しない\n", encoding="utf-8")
        before = source.read_bytes()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([str(self.root), "--format", "json"])
        self.assertEqual(result, 0)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"count": 1, "documents": ["日本語.md"]},
        )
        self.assertEqual(source.read_bytes(), before)

    def test_does_not_follow_symlinked_directories(self):
        outside_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temporary.cleanup)
        outside = Path(outside_temporary.name)
        (outside / "outside.md").write_text("outside", encoding="utf-8")
        link = self.root / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not supported in this environment")
        self.assertEqual(inventory(self.root), [])


if __name__ == "__main__":
    unittest.main()
