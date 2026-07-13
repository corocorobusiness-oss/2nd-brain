#!/usr/bin/env python3
"""Create a safe, resumable YMM4 job scaffold.

This module intentionally uses only the Python standard library.  It never
overwrites an existing job file.  ``--resume`` only fills missing directories
and files; an existing input is accepted only when it is byte-identical to the
requested source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Iterable


SCHEMA_VERSION = 1
DEFAULT_ROOT = r"C:\YMM4-Jobs"

DIRECTORIES = (
    "input",
    "assets/images",
    "assets/videos",
    "assets/bgm",
    "assets/se",
    "assets/characters",
    "template",
    "work",
    "output",
    "reports",
)

INPUT_SPECS = (
    ("script", "input/script.csv"),
    ("dictionary", "input/pronunciation.dic"),
    ("reference", "input/reference.mp4"),
    ("master_template", "template/master_template.ymmp"),
)


class JobInitError(Exception):
    """A safe, user-correctable initialization error."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_component(value: str, label: str, *, job_id: bool = False) -> str:
    if not value or value in {".", ".."}:
        raise JobInitError(f"{label} must be a non-empty path component")
    if value != value.strip() or value.endswith((".", " ")):
        raise JobInitError(f"{label} must not have leading/trailing spaces or dots")
    if any(ord(char) < 32 for char in value):
        raise JobInitError(f"{label} contains a control character")
    if any(char in '<>:"/\\|?*' for char in value):
        raise JobInitError(f"{label} contains a path separator or invalid Windows character")
    if len(value) > 120:
        raise JobInitError(f"{label} is too long (maximum 120 characters)")
    if job_id and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise JobInitError(
            "job id must start with an ASCII letter or digit and contain only "
            "letters, digits, dot, underscore, or hyphen"
        )
    return value


def contained_job_path(root: Path, job_id: str) -> Path:
    root = root.expanduser().resolve(strict=False)
    job = (root / job_id).resolve(strict=False)
    try:
        common = Path(os.path.commonpath((str(root), str(job))))
    except ValueError as exc:
        raise JobInitError("job root and job path are on different volumes") from exc
    if common != root or job == root:
        raise JobInitError("refusing a job path outside the requested root")
    return job


def source_file(value: str | None, label: str) -> Path | None:
    if value is None:
        return None
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file():
        raise JobInitError(f"{label} source is not a file: {path}")
    return path


def copy_exclusive(source: Path, target: Path, *, resume: bool) -> str:
    source_hash = sha256_file(source)
    if target.exists():
        if not target.is_file():
            raise JobInitError(f"input target exists but is not a file: {target}")
        target_hash = sha256_file(target)
        if not resume:
            raise JobInitError(f"refusing to overwrite existing input: {target}")
        if target_hash != source_hash:
            raise JobInitError(
                f"resume input differs from existing target: {target} "
                f"(existing {target_hash}, source {source_hash})"
            )
        return "existing-identical"

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
    except FileExistsError as exc:
        raise JobInitError(f"input appeared concurrently; refusing to overwrite: {target}") from exc

    copied_hash = sha256_file(target)
    if copied_hash != source_hash:
        raise JobInitError(f"copied input failed SHA-256 verification: {target}")
    return "copied"


def describe_file(job_dir: Path, path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(job_dir).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_json_exclusive(path: Path, payload: dict[str, Any]) -> str:
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
    except FileExistsError:
        return "existing"
    return "created"


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise JobInitError(f"existing {label} is not readable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise JobInitError(f"existing {label} must contain a JSON object: {path}")
    return value


def verify_resume_metadata(
    path: Path,
    label: str,
    expected: Iterable[tuple[str, Any]],
) -> None:
    if not path.exists():
        return
    if not path.is_file():
        raise JobInitError(f"existing {label} is not a file: {path}")
    value = load_json_object(path, label)
    for key, wanted in expected:
        if value.get(key) != wanted:
            raise JobInitError(
                f"existing {label} does not match --resume option {key!r}: "
                f"{value.get(key)!r} != {wanted!r}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True, help="unique safe job id, e.g. JOB-2026-001")
    parser.add_argument("--name", required=True, help="human-readable job name")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"job root (default: {DEFAULT_ROOT})")
    parser.add_argument("--script", help="source CSV copied as input/script.csv")
    parser.add_argument("--dictionary", help="source DIC copied as input/pronunciation.dic")
    parser.add_argument("--reference", help="source MP4 copied as input/reference.mp4")
    parser.add_argument(
        "--master-template", help="source YMMP copied as template/master_template.ymmp"
    )
    parser.add_argument("--mode", choices=("replicate", "house_style"), default="replicate")
    parser.add_argument("--ymm4-version", default="unspecified")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="fill missing directories/files without replacing any existing file",
    )
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    job_id = validate_component(args.job_id, "job id", job_id=True)
    name = validate_component(args.name, "name")
    if args.width < 1 or args.height < 1 or args.fps <= 0:
        raise JobInitError("width, height, and fps must be positive")

    root = Path(args.root).expanduser().resolve(strict=False)
    if root.exists() and not root.is_dir():
        raise JobInitError(f"job root exists but is not a directory: {root}")
    job_dir = contained_job_path(root, job_id)

    sources = {
        "script": source_file(args.script, "script"),
        "dictionary": source_file(args.dictionary, "dictionary"),
        "reference": source_file(args.reference, "reference"),
        "master_template": source_file(args.master_template, "master template"),
    }

    if job_dir.exists() and not args.resume:
        raise JobInitError(f"job already exists; use --resume to fill missing files: {job_dir}")
    if job_dir.exists() and not job_dir.is_dir():
        raise JobInitError(f"job path exists but is not a directory: {job_dir}")

    state_path = job_dir / "reports" / "job_state.json"
    lock_path = job_dir / "reports" / "project.lock.json"
    if args.resume:
        expected = (("job_id", job_id), ("name", name), ("mode", args.mode))
        verify_resume_metadata(state_path, "job state", expected)
        verify_resume_metadata(lock_path, "project lock", expected)

    root.mkdir(parents=True, exist_ok=True)
    job_dir.mkdir(exist_ok=True)
    for relative in DIRECTORIES:
        (job_dir / relative).mkdir(parents=True, exist_ok=True)

    copy_actions: dict[str, str] = {}
    for role, relative in INPUT_SPECS:
        source = sources[role]
        if source is not None:
            copy_actions[role] = copy_exclusive(
                source, job_dir / relative, resume=args.resume
            )

    input_files: dict[str, dict[str, Any]] = {}
    for role, relative in INPUT_SPECS:
        target = job_dir / relative
        if target.exists():
            if not target.is_file():
                raise JobInitError(f"expected input path is not a file: {target}")
            input_files[role] = describe_file(job_dir, target)

    state = {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "name": name,
        "mode": args.mode,
        "status": "NEW",
        "paths": {
            "input": "input",
            "assets": "assets",
            "template": "template",
            "work": "work",
            "output": "output",
            "reports": "reports",
        },
    }
    lock = {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "name": name,
        "mode": args.mode,
        "ymm4_version": args.ymm4_version,
        "project": {
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
        },
        "inputs": input_files,
        "voice_engine": None,
        "voice_engine_version": None,
        "plugins": [],
        "fonts": [],
        "template_version": None,
        "style_rules_version": None,
        "asset_catalog_version": None,
    }

    state_action = write_json_exclusive(state_path, state)
    lock_action = write_json_exclusive(lock_path, lock)

    return {
        "status": "NEW",
        "job_dir": str(job_dir),
        "resume": bool(args.resume),
        "inputs": copy_actions,
        "job_state": state_action,
        "project_lock": lock_action,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except (JobInitError, FileNotFoundError, OSError) as exc:
        print(f"init_job: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
