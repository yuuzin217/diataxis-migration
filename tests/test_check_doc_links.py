import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "diataxis-migration"
SKILL_SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from check_doc_links import check_repository, main


class CheckDocLinksTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def codes(self, report):
        return {finding["code"] for finding in report["findings"]}

    def test_valid_inline_image_and_reference_links(self):
        self.write(
            "README.md",
            "# Home\n\n"
            "[Guide](guide.md#api-reference) [Spec][spec] ![image](image.png)\n\n"
            "[spec]: <spec.md#current-state>\n",
        )
        self.write("guide.md", "## API Reference\n")
        self.write("spec.md", "## Current State\n")
        self.write("image.png", "fixture")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["links_checked"], 3)
        self.assertEqual(report["findings"], [])

    def test_external_urls_are_skipped_without_fetching(self):
        self.write("README.md", "[external](https://example.invalid/path)\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["external_links_skipped"], 1)
        self.assertEqual(report["links_checked"], 0)

    def test_broken_file_link_is_a_failure(self):
        self.write("README.md", "[missing](not-here.md)\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("missing-target", self.codes(report))
        self.assertIn("does not exist", report["findings"][0]["message"])

    def test_problem_makes_cli_return_nonzero(self):
        self.write("README.md", "[missing](not-here.md)\n")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([str(self.root)])
        self.assertEqual(result, 1)
        self.assertIn("STATUS: FAIL", stdout.getvalue())

    def test_missing_heading_anchor_is_a_failure(self):
        self.write("README.md", "[guide](guide.md#absent)\n")
        self.write("guide.md", "## Present\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("missing-anchor", self.codes(report))

    def test_duplicate_heading_numeric_anchor_resolves_without_failing(self):
        self.write("README.md", "[second setup](guide.md#setup-1)\n")
        self.write("guide.md", "## Setup\n\n## Setup\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertNotIn("duplicate-heading", self.codes(report))
        self.assertNotIn("missing-anchor", self.codes(report))

    def test_nonexistent_duplicate_heading_suffix_is_a_failure(self):
        self.write("README.md", "[third setup](guide.md#setup-2)\n")
        self.write("guide.md", "## Setup\n\n## Setup\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("missing-anchor", self.codes(report))

    def test_undefined_full_reference_link_is_a_failure(self):
        self.write("README.md", "[guide][missing]\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("undefined-reference", self.codes(report))

    def test_undefined_collapsed_reference_link_is_a_failure(self):
        self.write("README.md", "[guide][]\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("undefined-reference", self.codes(report))

    def test_undefined_reference_makes_cli_return_failure_code(self):
        self.write("README.md", "[guide][missing]\n")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([str(self.root)])
        self.assertEqual(result, 1)
        self.assertIn("undefined-reference", stdout.getvalue())

    def test_undefined_shortcut_text_is_not_misreported_as_a_link(self):
        self.write("README.md", "The word [guide] appears in prose.\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertNotIn("undefined-reference", self.codes(report))

    def test_unicode_path_and_heading(self):
        self.write("README.md", "[設定](docs/日本語.md#利用方法)\n")
        self.write("docs/日本語.md", "## 利用方法\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")

    def test_percent_encoded_path_space_and_unicode_anchor(self):
        self.write(
            "README.md",
            "[guide](guide%20space.md#caf%C3%A9) [spaced](<guide space.md#caf%C3%A9>)\n",
        )
        self.write("guide space.md", "## Café\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["links_checked"], 2)

    def test_links_and_headings_inside_fenced_or_inline_code_are_ignored(self):
        tick = chr(96)
        content = (
            "Text with {}[inline](missing.md#gone){} code.\n\n".format(tick, tick)
            + tick * 3
            + "markdown\n"
            + "[fenced](also-missing.md#gone)\n"
            + "## Fake heading\n"
            + tick * 3
            + "\n\n[real](target.md#real-heading)\n"
        )
        self.write("README.md", content)
        self.write("target.md", "## Real heading\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["links_checked"], 1)

    def test_empty_repository_is_clean(self):
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["documents_scanned"], 0)

    def test_horizontal_rules_are_not_reported_as_duplicate_empty_headings(self):
        self.write("README.md", "Intro\n\n---\n\nDetails\n\n---\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertNotIn("duplicate-heading", self.codes(report))

    def test_path_traversal_outside_repository_is_rejected(self):
        self.write("README.md", "[escape](../outside.md#private)\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("path-outside-root", self.codes(report))

    def test_symlink_escape_is_rejected_without_reading_target(self):
        outside_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temporary.cleanup)
        outside = Path(outside_temporary.name) / "outside.md"
        outside.write_text("# outside\n", encoding="utf-8")
        link = self.root / "outside-link.md"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not supported in this environment")
        self.write("README.md", "[escape](outside-link.md#outside)\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("path-outside-root", self.codes(report))

    def test_multiline_link_syntax_is_reported_as_not_verified(self):
        self.write("README.md", "[guide](\nmissing.md)\n")
        report = check_repository(self.root)
        self.assertEqual(report["status"], "NOT VERIFIED")
        self.assertTrue(any("Multiline Markdown" in note for note in report["limitations"]))

    def test_multiline_destination_before_title_is_not_verified(self):
        self.write("README.md", '[guide](missing.md\n "Title")\n')
        report = check_repository(self.root)
        self.assertEqual(report["status"], "NOT VERIFIED")
        self.assertNotIn("missing-target", self.codes(report))
        self.assertTrue(any("Multiline Markdown" in note for note in report["limitations"]))

    def test_multiline_link_line_break_positions_are_not_verified(self):
        for content in (
            "[guide](\nmissing.md \"Title\")\n",
            "[guide](missing.md \"Title\n\")\n",
            "[guide\nlabel](missing.md)\n",
        ):
            with self.subTest(content=content):
                self.write("README.md", content)
                report = check_repository(self.root)
                self.assertEqual(report["status"], "NOT VERIFIED")

    def test_unverified_syntax_makes_cli_return_nonzero(self):
        self.write("README.md", "[guide](\nmissing.md)\n")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([str(self.root)])
        self.assertEqual(result, 2)
        self.assertIn("STATUS: NOT VERIFIED", stdout.getvalue())

    def test_multiline_destination_before_title_makes_cli_return_not_verified_code(self):
        self.write("README.md", '[guide](missing.md\n "Title")\n')
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([str(self.root)])
        self.assertEqual(result, 2)
        self.assertIn("STATUS: NOT VERIFIED", stdout.getvalue())

    def test_html_anchor_is_not_misreported_as_a_missing_heading(self):
        self.write("README.md", "[anchor](guide.md#custom)\n")
        self.write("guide.md", '<h2 id="custom">Custom section</h2>\n')
        report = check_repository(self.root)
        self.assertEqual(report["status"], "NOT VERIFIED")
        self.assertNotIn("missing-anchor", self.codes(report))

    def test_installed_skill_copy_contains_runnable_verification_helpers(self):
        self.write("README.md", "# Fixture\n")
        installation_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(installation_temporary.cleanup)
        install_root = Path(installation_temporary.name) / "skills"
        install_root.mkdir()
        installed_skill = install_root / "diataxis-migration"
        shutil.copytree(SKILL_ROOT, installed_skill)

        inventory = subprocess.run(
            [
                sys.executable,
                str(installed_skill / "scripts" / "inventory_docs.py"),
                str(self.root),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        self.assertEqual(json.loads(inventory.stdout)["documents"], ["README.md"])

        checker = subprocess.run(
            [
                sys.executable,
                str(installed_skill / "scripts" / "check_doc_links.py"),
                str(self.root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(checker.returncode, 0, checker.stderr)
        self.assertIn("STATUS: PASS", checker.stdout)


if __name__ == "__main__":
    unittest.main()
