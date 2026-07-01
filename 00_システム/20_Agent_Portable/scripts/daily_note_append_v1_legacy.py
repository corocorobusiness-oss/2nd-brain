#!/usr/bin/env python3
"""Create today's daily note if needed, then append a memo safely."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


JST = timezone(timedelta(hours=9))
DEFAULT_HEADINGS = (
    "## 💡 メモ / アイデア",
    "### 💡 思いつきメモ / Inbox",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_date() -> str:
    return datetime.now(JST).date().isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a daily note from the template and append memo bullets."
    )
    parser.add_argument("text", nargs="?", help="Memo text to append.")
    parser.add_argument("--text", dest="text_opt", help="Memo text to append.")
    parser.add_argument("--date", default=default_date(), help="YYYY-MM-DD. Default: today in JST.")
    parser.add_argument("--root", type=Path, default=repo_root(), help="Vault root for tests or alternate vaults.")
    parser.add_argument("--template", type=Path, help="Template path. Default: 00_システム/Templates/Daily_Note_Template.md.")
    parser.add_argument("--daily-dir", type=Path, help="Daily note directory. Default: 05_日誌.")
    parser.add_argument("--dry-run", action="store_true", help="Show the planned diff without writing.")
    parser.add_argument("--create-section", action="store_true", help="Create the modern memo section if no target heading exists.")
    parser.add_argument("--allow-duplicate", action="store_true", help="Allow appending bullets that already exist in the section.")
    return parser.parse_args()


def fail(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        fail(f"--date must be YYYY-MM-DD: {value}")
    return value


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def memo_bullets(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    bullets = [f"- {line}" for line in lines if line]
    if not bullets:
        fail("memo text is empty")
    return bullets


def find_heading(lines: list[str]) -> tuple[int | None, str | None]:
    for heading in DEFAULT_HEADINGS:
        for index, line in enumerate(lines):
            if line.strip() == heading:
                return index, heading
    return None, None


def section_end(lines: list[str], heading_index: int) -> int:
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("#"):
            return index
    return len(lines)


def normalize_line(line: str) -> str:
    return line.rstrip("\r\n")


def newline_for(content: str) -> str:
    return "\r\n" if "\r\n" in content else "\n"


def append_bullets(
    content: str, bullets: list[str], create_section: bool, check_duplicates: bool = True
) -> tuple[str, str, bool]:
    newline = newline_for(content)
    lines = content.splitlines()
    heading_index, heading = find_heading(lines)

    if heading_index is None:
        if not create_section:
            fail("target memo heading not found. Use --create-section to add it.")
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([DEFAULT_HEADINGS[0], *bullets])
        return newline.join(lines) + newline, DEFAULT_HEADINGS[0], False

    end_index = section_end(lines, heading_index)
    section_lines = [normalize_line(line) for line in lines[heading_index + 1 : end_index]]
    existing = set(section_lines)

    if check_duplicates:
        missing_bullets = [bullet for bullet in bullets if bullet not in existing]
        if not missing_bullets:
            return content if content.endswith(("\n", "\r\n")) else content + newline, heading or DEFAULT_HEADINGS[0], True
        bullets = missing_bullets

    empty_bullet_re = re.compile(r"^\s*-\s*$")
    for index in range(heading_index + 1, end_index):
        if empty_bullet_re.match(lines[index]):
            lines[index : index + 1] = bullets
            return newline.join(lines) + newline, heading or DEFAULT_HEADINGS[0], False

    insert_at = end_index
    while insert_at > heading_index + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines[insert_at:insert_at] = bullets
    return newline.join(lines) + newline, heading or DEFAULT_HEADINGS[0], False


def unified_diff(before: str, after: str, path: Path) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{path} (before)",
            tofile=f"{path} (after)",
        )
    )


def main() -> int:
    args = parse_args()
    date_value = validate_date(args.date)
    text = args.text_opt if args.text_opt is not None else args.text
    if text is None:
        fail("memo text is required")

    root = args.root.resolve()
    template_path = args.template or root / "00_システム" / "Templates" / "Daily_Note_Template.md"
    daily_dir = args.daily_dir or root / "05_日誌"
    note_path = daily_dir / f"{date_value}.md"
    bullets = memo_bullets(text)

    existed = note_path.exists()
    if existed:
        before = read_text(note_path)
    else:
        if not template_path.exists():
            fail(f"template not found: {template_path}")
        before = read_text(template_path).replace("{{date}}", date_value)
        if not before.endswith("\n"):
            before += "\n"

    after, heading, duplicate = append_bullets(
        before, bullets, args.create_section, check_duplicates=not args.allow_duplicate
    )

    print(f"target: {note_path}")
    print(f"date: {date_value}")
    print(f"existed: {str(existed).lower()}")
    print(f"heading: {heading}")
    if duplicate and not args.allow_duplicate:
        print("status: duplicate-noop")
        return 0

    diff = unified_diff("" if not existed else before, after, note_path)
    if args.dry_run:
        print("status: dry-run")
        print(diff or "(no changes)")
        return 0

    write_text(note_path, after)
    print("status: written")
    if diff:
        print(diff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
