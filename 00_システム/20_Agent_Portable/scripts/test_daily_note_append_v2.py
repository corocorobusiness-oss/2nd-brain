#!/usr/bin/env python3
"""CLI tests for daily_note_append_v2.py."""

from __future__ import annotations

import subprocess
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
V1_SCRIPT = SCRIPT_DIR / "daily_note_append.py"
V2_SCRIPT = SCRIPT_DIR / "daily_note_append_v2.py"
TEMPLATE_TEXT = """# {{date}}

## 💡 メモ / アイデア
- 
"""


class DailyNoteAppendV2Test(unittest.TestCase):
    def make_root(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="daily-note-v2-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        template = root / "00_システム" / "Templates" / "Daily_Note_Template.md"
        template.parent.mkdir(parents=True)
        template.write_text(TEMPLATE_TEXT, encoding="utf-8")
        return root

    def run_cli(self, root: Path, *args: str, script: Path = V2_SCRIPT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), "--root", str(root), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def note(self, root: Path, date_value: str) -> Path:
        return root / "05_日誌" / f"{date_value}.md"

    def test_create_new_note_and_replace_placeholder(self) -> None:
        root = self.make_root()
        result = self.run_cli(root, "--date", "2026-07-05", "hello")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status: written", result.stdout)
        content = self.note(root, "2026-07-05").read_text(encoding="utf-8")
        self.assertIn("# 2026-07-05", content)
        self.assertIn("- hello", content)
        self.assertNotIn("- \n", content)

    def test_duplicate_and_partial_multiline(self) -> None:
        root = self.make_root()
        first = self.run_cli(root, "--date", "2026-07-05", "--text", "A\nB")
        self.assertEqual(first.returncode, 0, first.stderr)

        duplicate = self.run_cli(root, "--date", "2026-07-05", "--text", "A\nB")
        self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
        self.assertIn("status: duplicate-noop", duplicate.stdout)

        partial = self.run_cli(root, "--date", "2026-07-05", "--text", "B\nC")
        self.assertEqual(partial.returncode, 0, partial.stderr)
        content = self.note(root, "2026-07-05").read_text(encoding="utf-8")
        self.assertEqual(content.count("- B"), 1)
        self.assertEqual(content.count("- C"), 1)

    def test_legacy_heading(self) -> None:
        root = self.make_root()
        note = self.note(root, "2026-07-06")
        note.parent.mkdir(parents=True)
        note.write_text("# 2026-07-06\n\n### 💡 思いつきメモ / Inbox\n- old\n\n## Next\nbody\n", encoding="utf-8")
        result = self.run_cli(root, "--date", "2026-07-06", "legacy")
        self.assertEqual(result.returncode, 0, result.stderr)
        content = note.read_text(encoding="utf-8")
        self.assertLess(content.index("- legacy"), content.index("## Next"))

    def test_missing_heading_requires_create_section(self) -> None:
        root = self.make_root()
        note = self.note(root, "2026-07-07")
        note.parent.mkdir(parents=True)
        note.write_text("# 2026-07-07\n\nbody\n", encoding="utf-8")
        before = note.read_text(encoding="utf-8")

        failed = self.run_cli(root, "--date", "2026-07-07", "memo")
        self.assertEqual(failed.returncode, 2)
        self.assertIn("target memo heading not found", failed.stderr)
        self.assertEqual(note.read_text(encoding="utf-8"), before)

        created = self.run_cli(root, "--date", "2026-07-07", "--create-section", "memo")
        self.assertEqual(created.returncode, 0, created.stderr)
        content = note.read_text(encoding="utf-8")
        self.assertIn("## 💡 メモ / アイデア", content)
        self.assertIn("- memo", content)

    def test_dry_run_does_not_write_new_note(self) -> None:
        root = self.make_root()
        result = self.run_cli(root, "--date", "2026-07-08", "--dry-run", "dry")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status: dry-run", result.stdout)
        self.assertFalse(self.note(root, "2026-07-08").exists())

    def test_empty_text_fails(self) -> None:
        root = self.make_root()
        result = self.run_cli(root, "--date", "2026-07-09", "--text", "")
        self.assertEqual(result.returncode, 2)
        self.assertIn("memo text is empty", result.stderr)

    def test_basic_output_matches_v1(self) -> None:
        root_v1 = self.make_root()
        root_v2 = self.make_root()
        v1 = self.run_cli(root_v1, "--date", "2026-07-10", "--text", "same\nmemo", script=V1_SCRIPT)
        v2 = self.run_cli(root_v2, "--date", "2026-07-10", "--text", "same\nmemo", script=V2_SCRIPT)
        self.assertEqual(v1.returncode, 0, v1.stderr)
        self.assertEqual(v2.returncode, 0, v2.stderr)
        self.assertEqual(
            self.note(root_v1, "2026-07-10").read_text(encoding="utf-8"),
            self.note(root_v2, "2026-07-10").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
