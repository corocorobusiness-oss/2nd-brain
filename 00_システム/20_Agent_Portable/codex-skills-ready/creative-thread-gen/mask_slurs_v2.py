#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mask protected-attribute slurs in corpus text before learning import."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


DEFAULT_REPLACEMENT = "【NG】"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_QA_CHECK = SCRIPT_DIR / "qa_check.py"


class CliError(Exception):
    """User-correctable CLI error."""


@dataclass(frozen=True)
class MaskResult:
    text: str
    count: int


def load_slur_pattern(qa_check_path: Path = DEFAULT_QA_CHECK):
    """Load SLUR_RE from qa_check.py so the detection source stays single."""
    if not qa_check_path.exists():
        raise CliError(f"qa_check.py not found: {qa_check_path}")

    spec = importlib.util.spec_from_file_location("qa_check_for_mask_v2", qa_check_path)
    if spec is None or spec.loader is None:
        raise CliError(f"cannot load qa_check.py: {qa_check_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pattern = getattr(module, "SLUR_RE", None)
    if pattern is None or not hasattr(pattern, "sub") or not hasattr(pattern, "findall"):
        raise CliError("qa_check.py does not expose a usable SLUR_RE")
    return pattern


def mask_text(text: str, pattern, replacement: str = DEFAULT_REPLACEMENT) -> MaskResult:
    """Return masked text and replacement count."""
    if replacement == "":
        raise CliError("--replacement cannot be empty")
    if pattern.search(replacement):
        raise CliError("--replacement cannot contain a slur matched by SLUR_RE")

    count = len(pattern.findall(text))
    return MaskResult(text=pattern.sub(lambda _match: replacement, text), count=count)


def mask(text: str) -> tuple[str, int]:
    """Backward-compatible import API from mask_slurs.py."""
    result = mask_text(text, load_slur_pattern())
    return result.text, result.count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mask protected-attribute slurs with the qa_check.py SLUR_RE pattern."
    )
    parser.add_argument("file", nargs="?", help="Input file. Reads stdin when omitted.")
    parser.add_argument("-o", "--out", help="Output file. Writes stdout when omitted.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the masked result and summary without writing the output file.",
    )
    parser.add_argument(
        "--replacement",
        default=DEFAULT_REPLACEMENT,
        help=f"Replacement text. Default: {DEFAULT_REPLACEMENT}",
    )
    parser.add_argument(
        "--qa-check",
        default=str(DEFAULT_QA_CHECK),
        help=argparse.SUPPRESS,
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def read_input(input_file: str | None, stdin: TextIO) -> str:
    if input_file:
        path = Path(input_file)
        if not path.exists():
            raise CliError(f"input file not found: {path}")
        if not path.is_file():
            raise CliError(f"input path is not a file: {path}")
        return path.read_text(encoding="utf-8")

    if stdin.isatty():
        raise CliError("provide an input file or pipe text to stdin")
    return stdin.read()


def atomic_write_text(path: Path, text: str) -> None:
    parent = path.parent
    if not parent.exists():
        raise CliError(f"output directory not found: {parent}")
    if path.exists() and path.is_dir():
        raise CliError(f"output path is a directory: {path}")
    mode = path.stat().st_mode & 0o777 if path.exists() else None

    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
        if mode is not None:
            os.chmod(tmp_name, mode)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def write_result(
    result: MaskResult,
    output_file: str | None,
    dry_run: bool,
    replacement: str,
    stdout: TextIO,
    stderr: TextIO,
) -> None:
    if dry_run:
        stdout.write(result.text)
        stderr.write(f"[mask] status: dry-run / 蔑称 {result.count}件を{replacement}化\n")
        return

    if output_file:
        path = Path(output_file)
        atomic_write_text(path, result.text)
        stderr.write(f"[mask] 蔑称 {result.count}件を{replacement}化 → {path}\n")
        return

    stdout.write(result.text)
    stderr.write(f"[mask] 蔑称 {result.count}件を{replacement}化\n")


def run(argv: list[str] | None = None, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int:
    args = parse_args(argv)
    pattern = load_slur_pattern(Path(args.qa_check))
    source = read_input(args.file, stdin)
    result = mask_text(source, pattern, args.replacement)
    write_result(result, args.out, args.dry_run, args.replacement, stdout, stderr)
    return 0


def main() -> int:
    try:
        return run()
    except (CliError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
