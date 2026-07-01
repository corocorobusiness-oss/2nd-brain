#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI tests for mask_slurs_v2.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CURRENT_SCRIPT = SCRIPT_DIR / "mask_slurs.py"
LEGACY_SCRIPT = SCRIPT_DIR / "mask_slurs_v1_legacy.py"
REFERENCE_SCRIPT = LEGACY_SCRIPT if LEGACY_SCRIPT.exists() else CURRENT_SCRIPT
V2_SCRIPT = SCRIPT_DIR / "mask_slurs_v2.py"

MASK = "【NG】"
TERM_A = "\u7279\u4e9c"
TERM_B = "\u9b3c\u755c\u7c73\u82f1"
EXCLUDED = "\u652f\u90a3\u305d\u3070"


class MaskSlursV2Test(unittest.TestCase):
    def run_cli(
        self,
        *args: str,
        input_text: str | None = None,
        script: Path = V2_SCRIPT,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_stdin_stdout_masks_slurs_and_preserves_allowed_context(self) -> None:
        source = f"安全な行\n{TERM_A} は伏せる\n{EXCLUDED} は残す\n"

        result = self.run_cli(input_text=source)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(MASK, result.stdout)
        self.assertNotIn(TERM_A, result.stdout)
        self.assertIn(EXCLUDED, result.stdout)
        self.assertIn("蔑称 1件", result.stderr)

    def test_v2_matches_v1_stdout_for_basic_stdin_case(self) -> None:
        source = f"{TERM_A}\n{TERM_B}\n{EXCLUDED}\n"

        old = self.run_cli(input_text=source, script=REFERENCE_SCRIPT)
        new = self.run_cli(input_text=source, script=V2_SCRIPT)

        self.assertEqual(old.returncode, 0, old.stderr)
        self.assertEqual(new.returncode, 0, new.stderr)
        self.assertEqual(new.stdout, old.stdout)

    def test_output_file_is_written_without_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "in.md"
            out = root / "out.md"
            src.write_text(f"本文 {TERM_A}\n", encoding="utf-8")

            result = self.run_cli(str(src), "-o", str(out))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(out.read_text(encoding="utf-8"), f"本文 {MASK}\n")
            self.assertIn(str(out), result.stderr)

    def test_in_place_output_is_supported_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.md"
            src.write_text(f"本文 {TERM_A}\n", encoding="utf-8")

            result = self.run_cli(str(src), "-o", str(src))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(src.read_text(encoding="utf-8"), f"本文 {MASK}\n")

    def test_existing_output_mode_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "in.md"
            out = root / "out.md"
            src.write_text(f"本文 {TERM_A}\n", encoding="utf-8")
            out.write_text("old\n", encoding="utf-8")
            out.chmod(0o640)

            result = self.run_cli(str(src), "-o", str(out))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(out.stat().st_mode & 0o777, 0o640)

    def test_dry_run_does_not_write_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "in.md"
            out = root / "out.md"
            src.write_text(f"本文 {TERM_A}\n", encoding="utf-8")

            result = self.run_cli(str(src), "-o", str(out), "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(out.exists())
            self.assertEqual(result.stdout, f"本文 {MASK}\n")
            self.assertIn("status: dry-run", result.stderr)

    def test_custom_replacement(self) -> None:
        source = f"{TERM_A}\n"

        result = self.run_cli("--replacement", "[MASKED]", input_text=source)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "[MASKED]\n")
        self.assertIn("[MASKED]", result.stderr)

    def test_replacement_is_literal_not_regex_template(self) -> None:
        source = f"{TERM_A}\n"

        result = self.run_cli("--replacement", "\\1", input_text=source)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "\\1\n")

    def test_empty_replacement_fails_close(self) -> None:
        result = self.run_cli("--replacement", "", input_text=f"{TERM_A}\n")

        self.assertEqual(result.returncode, 2)
        self.assertIn("replacement", result.stderr)

    def test_slur_replacement_fails_close(self) -> None:
        result = self.run_cli("--replacement", TERM_A, input_text=f"{TERM_B}\n")

        self.assertEqual(result.returncode, 2)
        self.assertIn("replacement", result.stderr)

    def test_missing_input_file_fails_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(str(Path(tmp) / "missing.md"))

            self.assertEqual(result.returncode, 2)
            self.assertIn("input file not found", result.stderr)

    def test_missing_output_directory_fails_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "in.md"
            src.write_text(f"{TERM_A}\n", encoding="utf-8")

            result = self.run_cli(str(src), "-o", str(root / "missing" / "out.md"))

            self.assertEqual(result.returncode, 2)
            self.assertIn("output directory not found", result.stderr)

    def test_missing_qa_check_fails_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("--qa-check", str(Path(tmp) / "missing.py"), input_text=f"{TERM_A}\n")

            self.assertEqual(result.returncode, 2)
            self.assertIn("qa_check.py not found", result.stderr)

    def test_direct_execution_help(self) -> None:
        result = subprocess.run(
            [str(V2_SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)

    def test_backward_compatible_mask_import_api(self) -> None:
        spec = importlib.util.spec_from_file_location("mask_slurs_v2_under_test", V2_SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        masked, count = module.mask(f"{TERM_A}\n{EXCLUDED}\n")

        self.assertEqual(masked, f"{MASK}\n{EXCLUDED}\n")
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
