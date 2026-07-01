#!/usr/bin/env python3
"""Append memo bullets to a daily note. v2 parallel implementation."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


JST = timezone(timedelta(hours=9))
MODERN_MEMO_HEADING = "## 💡 メモ / アイデア"
LEGACY_MEMO_HEADING = "### 💡 思いつきメモ / Inbox"
TARGET_HEADINGS = (MODERN_MEMO_HEADING, LEGACY_MEMO_HEADING)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class UserError(Exception):
    """Expected CLI error with a stable exit code."""


@dataclass(frozen=True)
class TargetPaths:
    root: Path
    template: Path
    daily_dir: Path
    note: Path


@dataclass(frozen=True)
class AppendResult:
    content: str
    heading: str
    duplicate_noop: bool


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def today_jst() -> str:
    return datetime.now(JST).date().isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a daily note from the template and append memo bullets."
    )
    parser.add_argument("text", nargs="?", help="Memo text to append.")
    parser.add_argument("--text", dest="text_opt", help="Memo text to append.")
    parser.add_argument("--date", default=today_jst(), help="YYYY-MM-DD. Default: today in JST.")
    parser.add_argument("--root", type=Path, default=repo_root(), help="Vault root.")
    parser.add_argument(
        "--template",
        type=Path,
        help="Template path. Default: 00_システム/Templates/Daily_Note_Template.md.",
    )
    parser.add_argument("--daily-dir", type=Path, help="Daily note directory. Default: 05_日誌.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned diff without writing.")
    parser.add_argument(
        "--create-section",
        action="store_true",
        help="Create the modern memo section when no target heading exists.",
    )
    parser.add_argument(
        "--allow-duplicate",
        action="store_true",
        help="Append bullets even when identical bullets already exist in the memo section.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def checked_date(value: str) -> str:
    if not DATE_PATTERN.match(value):
        raise UserError(f"--date must be YYYY-MM-DD: {value}")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise UserError(f"--date must be YYYY-MM-DD: {value}") from exc
    return value


def selected_text(args: argparse.Namespace) -> str:
    text = args.text_opt if args.text_opt is not None else args.text
    if text is None:
        raise UserError("memo text is required")
    return text


def resolve_paths(args: argparse.Namespace, date_value: str) -> TargetPaths:
    root = args.root.resolve()
    template = args.template or root / "00_システム" / "Templates" / "Daily_Note_Template.md"
    daily_dir = args.daily_dir or root / "05_日誌"
    return TargetPaths(root=root, template=template, daily_dir=daily_dir, note=daily_dir / f"{date_value}.md")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def memo_bullets(raw_text: str) -> list[str]:
    bullets = [f"- {line.strip()}" for line in raw_text.splitlines() if line.strip()]
    if not bullets:
        raise UserError("memo text is empty")
    return bullets


def detect_newline(content: str) -> str:
    return "\r\n" if "\r\n" in content else "\n"


def ensure_trailing_newline(content: str, newline: str) -> str:
    return content if content.endswith(("\n", "\r\n")) else content + newline


def find_target_heading(lines: list[str]) -> tuple[int | None, str | None]:
    for heading in TARGET_HEADINGS:
        for index, line in enumerate(lines):
            if line.strip() == heading:
                return index, heading
    return None, None


def next_heading_index(lines: list[str], heading_index: int) -> int:
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("#"):
            return index
    return len(lines)


def load_base_note(paths: TargetPaths, date_value: str) -> tuple[str, bool]:
    if paths.note.exists():
        return read_text(paths.note), True
    if not paths.template.exists():
        raise UserError(f"template not found: {paths.template}")
    content = read_text(paths.template).replace("{{date}}", date_value)
    return ensure_trailing_newline(content, detect_newline(content)), False


def append_to_memo_section(
    content: str,
    bullets: list[str],
    *,
    create_section: bool,
    allow_duplicate: bool,
) -> AppendResult:
    newline = detect_newline(content)
    lines = content.splitlines()
    heading_index, heading = find_target_heading(lines)

    if heading_index is None:
        if not create_section:
            raise UserError("target memo heading not found. Use --create-section to add it.")
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([MODERN_MEMO_HEADING, *bullets])
        return AppendResult(newline.join(lines) + newline, MODERN_MEMO_HEADING, False)

    end_index = next_heading_index(lines, heading_index)
    section_lines = {line.rstrip("\r\n") for line in lines[heading_index + 1 : end_index]}
    if not allow_duplicate:
        bullets = [bullet for bullet in bullets if bullet not in section_lines]
        if not bullets:
            return AppendResult(ensure_trailing_newline(content, newline), heading or MODERN_MEMO_HEADING, True)

    empty_bullet = re.compile(r"^\s*-\s*$")
    for index in range(heading_index + 1, end_index):
        if empty_bullet.match(lines[index]):
            lines[index : index + 1] = bullets
            return AppendResult(newline.join(lines) + newline, heading or MODERN_MEMO_HEADING, False)

    insert_at = end_index
    while insert_at > heading_index + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines[insert_at:insert_at] = bullets
    return AppendResult(newline.join(lines) + newline, heading or MODERN_MEMO_HEADING, False)


def unified_diff(before: str, after: str, note_path: Path, *, existed: bool) -> str:
    left = before if existed else ""
    return "".join(
        difflib.unified_diff(
            left.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{note_path} (before)",
            tofile=f"{note_path} (after)",
        )
    )


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    date_value = checked_date(args.date)
    paths = resolve_paths(args, date_value)
    bullets = memo_bullets(selected_text(args))
    before, existed = load_base_note(paths, date_value)
    result = append_to_memo_section(
        before,
        bullets,
        create_section=args.create_section,
        allow_duplicate=args.allow_duplicate,
    )

    print(f"target: {paths.note}")
    print(f"date: {date_value}")
    print(f"existed: {str(existed).lower()}")
    print(f"heading: {result.heading}")

    if result.duplicate_noop:
        print("status: duplicate-noop")
        return 0

    diff = unified_diff(before, result.content, paths.note, existed=existed)
    if args.dry_run:
        print("status: dry-run")
        print(diff or "(no changes)")
        return 0

    write_text(paths.note, result.content)
    print("status: written")
    if diff:
        print(diff)
    return 0


def main() -> int:
    try:
        return run()
    except UserError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
