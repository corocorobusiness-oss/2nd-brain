#!/usr/bin/env python3
"""Read-only structural QA for a YukkuriMovieMaker 4 ``.ymmp`` project.

The input project is opened only in binary read mode.  Results are written to
``--report`` as JSON.  Exit codes are 0 for pass, 1 for a QA failure, and 2 for
usage/tool errors.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterable, Iterator, Mapping


SCHEMA_VERSION = 1
FILE_BACKED_TYPES = {"Image", "Video", "Audio"}
STAGES = ("pre_roundtrip", "post_roundtrip", "final")


class QaUsageError(Exception):
    """Invalid QA configuration or a tool-level error."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_sha256(value: Any) -> str:
    data = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest().upper()


def item_type(item: Mapping[str, Any]) -> str:
    raw = str(item.get("$type", "Unknown"))
    class_name = raw.split(",", 1)[0].rsplit(".", 1)[-1]
    return class_name[:-4] if class_name.endswith("Item") else class_name


def normalize_expected_type(value: str) -> str:
    class_name = value.split(",", 1)[0].rsplit(".", 1)[-1]
    return class_name[:-4] if class_name.endswith("Item") else class_name


def integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return None


def timespan_seconds(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    if not isinstance(value, str) or not value:
        return None
    match = re.fullmatch(
        r"(?:(?P<days>\d+)\.)?(?P<hours>\d+):(?P<minutes>\d{2}):"
        r"(?P<seconds>\d{2}(?:\.\d+)?)",
        value,
    )
    if not match:
        return None
    minutes = int(match.group("minutes"))
    seconds = float(match.group("seconds"))
    if minutes >= 60 or seconds >= 60:
        return None
    return (
        int(match.group("days") or 0) * 86400
        + int(match.group("hours")) * 3600
        + minutes * 60
        + seconds
    )


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def walk_file_paths(value: Any, pointer: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}/{key}"
            if key == "FilePath":
                yield child_pointer, child
            else:
                yield from walk_file_paths(child, child_pointer)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_file_paths(child, f"{pointer}/{index}")


def parse_assignment(value: str, label: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{label} must use LEFT=RIGHT syntax")
    left, right = value.rsplit("=", 1)
    if not left or not right:
        raise argparse.ArgumentTypeError(f"{label} must have non-empty LEFT and RIGHT")
    return left, right


def type_expectation(value: str) -> tuple[str, int]:
    left, right = parse_assignment(value, "--expect-type")
    try:
        count = int(right)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--expect-type count must be an integer") from exc
    if count < 0:
        raise argparse.ArgumentTypeError("--expect-type count must be non-negative")
    return normalize_expected_type(left), count


def path_mapping(value: str) -> tuple[str, str]:
    return parse_assignment(value, "--path-map")


def apply_path_maps(original: str, mappings: Iterable[tuple[str, str]]) -> str:
    original_folded = original.casefold()
    for source, target in mappings:
        trimmed = source.rstrip("/\\")
        folded = trimmed.casefold()
        exact = original_folded == folded
        child = (
            original_folded.startswith(folded)
            and len(original) > len(trimmed)
            and original[len(trimmed)] in "/\\"
        )
        if exact or child or (source.endswith(("/", "\\")) and original_folded.startswith(source.casefold())):
            remainder = original[len(source) :].lstrip("/\\")
            remainder = remainder.replace("\\", os.sep).replace("/", os.sep)
            return str(Path(target).expanduser() / remainder) if remainder else str(Path(target).expanduser())
    return original


def path_identity(path: str) -> str:
    return os.path.normcase(os.path.normpath(path)).casefold()


def add_check(
    report: dict[str, Any], code: str, status: str, message: str, **context: Any
) -> None:
    entry: dict[str, Any] = {"code": code, "status": status, "message": message}
    entry.update(context)
    report["checks"].append(entry)


def add_error(report: dict[str, Any], code: str, message: str, **context: Any) -> None:
    add_check(report, code, "FAIL", message, **context)


def add_warning(report: dict[str, Any], code: str, message: str, **context: Any) -> None:
    add_check(report, code, "WARN", message, **context)


def first_value(mapping: Mapping[str, Any], aliases: Iterable[str]) -> tuple[bool, Any]:
    for key in aliases:
        if key in mapping:
            return True, mapping[key]
    for container_name in ("properties", "raw", "item"):
        child = mapping.get(container_name)
        if isinstance(child, dict):
            for key in aliases:
                if key in child:
                    return True, child[key]
    return False, None


def actual_project_value(document: Mapping[str, Any], aliases: Iterable[str]) -> tuple[bool, Any]:
    found, value = first_value(document, aliases)
    if found:
        return found, value
    for key in ("Project", "Video", "VideoInfo", "Settings", "ProjectSettings"):
        child = document.get(key)
        if isinstance(child, dict):
            found, value = first_value(child, aliases)
            if found:
                return found, value
    return False, None


def baseline_items(reference: Mapping[str, Any]) -> list[Any] | None:
    direct = reference.get("items")
    if isinstance(direct, list):
        return direct
    timeline = reference.get("timeline")
    if isinstance(timeline, dict) and isinstance(timeline.get("items"), list):
        return timeline["items"]
    timelines = reference.get("timelines")
    if isinstance(timelines, list) and timelines:
        first = timelines[0]
        if isinstance(first, dict):
            candidate = first.get("items") or first.get("Items")
            if isinstance(candidate, list):
                return candidate
    return None


def compare_baseline(
    report: dict[str, Any],
    document: Mapping[str, Any],
    timeline: Mapping[str, Any],
    items: list[Mapping[str, Any]],
    reference: Mapping[str, Any],
) -> None:
    expected_items = baseline_items(reference)
    if expected_items is None:
        raise QaUsageError("reference_timeline.json has no supported items list")

    if len(expected_items) != len(items):
        add_error(
            report,
            "BASELINE_ITEM_COUNT",
            f"item count {len(items)} differs from baseline {len(expected_items)}",
            actual=len(items),
            expected=len(expected_items),
        )

    field_specs = (
        ("type", ("type", "$type", "item_type"), None),
        ("Frame", ("Frame", "frame", "start_frame"), ("Frame",)),
        ("Length", ("Length", "length", "length_frames"), ("Length",)),
        ("Layer", ("Layer", "layer"), ("Layer",)),
        ("CharacterName", ("CharacterName", "character_name", "speaker"), ("CharacterName",)),
        ("Serif", ("Serif", "serif", "text"), ("Serif",)),
        ("Hatsuon", ("Hatsuon", "hatsuon", "reading"), ("Hatsuon",)),
    )

    for sequence_index, expected in enumerate(expected_items):
        if not isinstance(expected, dict):
            raise QaUsageError(f"baseline item {sequence_index} is not an object")
        index_value = expected.get("index", sequence_index)
        index = integer(index_value)
        if index is None or index < 0:
            raise QaUsageError(f"baseline item {sequence_index} has invalid index")
        if index >= len(items):
            continue
        actual = items[index]
        for label, expected_aliases, actual_aliases in field_specs:
            present, wanted = first_value(expected, expected_aliases)
            if not present:
                continue
            if label == "type":
                got = item_type(actual)
                wanted = normalize_expected_type(str(wanted))
            else:
                got = actual.get(actual_aliases[0]) if actual_aliases else None
            if got != wanted:
                add_error(
                    report,
                    "BASELINE_ITEM_FIELD",
                    f"item {index} {label} differs from baseline",
                    item_index=index,
                    field=label,
                    actual=got,
                    expected=wanted,
                )

        present, wanted_hash = first_value(
            expected, ("item_sha256", "raw_sha256", "properties_sha256")
        )
        if present:
            got_hash = canonical_sha256(actual)
            if str(wanted_hash).upper() != got_hash:
                add_error(
                    report,
                    "BASELINE_ITEM_HASH",
                    f"item {index} canonical hash differs from baseline",
                    item_index=index,
                    actual=got_hash,
                    expected=str(wanted_hash).upper(),
                )

    project = reference.get("project")
    if isinstance(project, dict):
        project_specs = (
            ("width", ("width", "Width", "VideoWidth"), ("Width", "VideoWidth", "width")),
            ("height", ("height", "Height", "VideoHeight"), ("Height", "VideoHeight", "height")),
            ("fps", ("fps", "FPS", "FrameRate"), ("FPS", "FrameRate", "fps")),
        )
        for label, expected_aliases, actual_aliases in project_specs:
            present, wanted = first_value(project, expected_aliases)
            if not present:
                continue
            actual_present, got = actual_project_value(document, actual_aliases)
            if not actual_present or got != wanted:
                add_error(
                    report,
                    "BASELINE_PROJECT_FIELD",
                    f"project {label} differs from baseline",
                    field=label,
                    actual=got if actual_present else None,
                    expected=wanted,
                )

    reference_timeline = reference.get("timeline")
    if isinstance(reference_timeline, dict):
        present, wanted = first_value(reference_timeline, ("length", "Length", "length_frames"))
        if present and timeline.get("Length") != wanted:
            add_error(
                report,
                "BASELINE_TIMELINE_LENGTH",
                "timeline length differs from baseline",
                actual=timeline.get("Length"),
                expected=wanted,
            )


def empty_report(input_path: Path, stage: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "qa_ymmp",
        "input": {"path": str(input_path), "stage": stage},
        "status": "ERROR",
        "summary": {},
        "project": {},
        "timeline": {},
        "counts": {},
        "files": {},
        "baseline": {},
        "checks": [],
    }


def finalize_report(report: dict[str, Any]) -> int:
    errors = sum(check["status"] == "FAIL" for check in report["checks"])
    warnings = sum(check["status"] == "WARN" for check in report["checks"])
    report["summary"] = {
        "errors": errors,
        "warnings": warnings,
        "checks": len(report["checks"]),
    }
    report["status"] = "FAIL" if errors else "PASS"
    return 1 if errors else 0


def evaluate(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    input_path = Path(args.ymmp).expanduser().resolve(strict=True)
    if not input_path.is_file():
        raise QaUsageError(f"input is not a file: {input_path}")
    report = empty_report(input_path, args.stage)
    report["input"]["bytes"] = input_path.stat().st_size
    report["input"]["sha256"] = sha256_file(input_path)

    try:
        with input_path.open("r", encoding="utf-8-sig") as handle:
            document = json.load(handle)
    except (UnicodeError, json.JSONDecodeError) as exc:
        add_error(report, "PARSE", f"YMMP is not valid UTF-8 JSON: {exc}")
        return report, finalize_report(report)
    if not isinstance(document, dict):
        add_error(report, "PROJECT_OBJECT", "YMMP root must be a JSON object")
        return report, finalize_report(report)

    timelines = document.get("Timelines")
    if not isinstance(timelines, list) or not timelines:
        add_error(report, "TIMELINES", "project has no non-empty Timelines array")
        return report, finalize_report(report)

    selected_raw = document.get("SelectedTimelineIndex", 0)
    selected = integer(selected_raw)
    if selected is None or selected < 0 or selected >= len(timelines):
        add_error(
            report,
            "SELECTED_TIMELINE",
            "SelectedTimelineIndex is not a valid timeline index",
            value=selected_raw,
            timeline_count=len(timelines),
        )
        selected = 0

    timeline_index = args.timeline_index if args.timeline_index is not None else selected
    if timeline_index < 0 or timeline_index >= len(timelines):
        raise QaUsageError(
            f"--timeline-index {timeline_index} is outside 0..{len(timelines) - 1}"
        )
    if args.timeline_index is not None and args.timeline_index != selected:
        add_warning(
            report,
            "TIMELINE_OVERRIDE",
            "QA timeline override differs from SelectedTimelineIndex",
            selected=selected,
            inspected=args.timeline_index,
        )

    timeline = timelines[timeline_index]
    if not isinstance(timeline, dict):
        add_error(report, "TIMELINE_OBJECT", "selected timeline is not a JSON object")
        return report, finalize_report(report)
    raw_items = timeline.get("Items")
    if not isinstance(raw_items, list):
        add_error(report, "ITEMS", "selected timeline Items must be an array")
        return report, finalize_report(report)
    items: list[Mapping[str, Any]] = []
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            add_error(
                report, "ITEM_OBJECT", f"item {index} is not a JSON object", item_index=index
            )
            items.append({})
        else:
            items.append(raw_item)

    report["project"] = {
        "timeline_count": len(timelines),
        "selected_timeline_index": selected,
        "characters": len(document.get("Characters", []))
        if isinstance(document.get("Characters"), list)
        else None,
    }
    timeline_length = integer(timeline.get("Length"))
    if "Length" in timeline and (timeline_length is None or timeline_length < 0):
        add_error(report, "TIMELINE_LENGTH", "timeline Length must be a non-negative integer")
        timeline_length = None

    type_counts = Counter(item_type(item) for item in items)
    report["counts"] = {"items": len(items), "types": dict(sorted(type_counts.items()))}

    valid_intervals: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    layers: list[int] = []
    for index, item in enumerate(items):
        frame = integer(item.get("Frame"))
        length = integer(item.get("Length"))
        layer = integer(item.get("Layer"))
        if frame is None or frame < 0:
            add_error(
                report,
                "ITEM_FRAME",
                f"item {index} Frame must be an integer >= 0",
                item_index=index,
                value=item.get("Frame"),
            )
        if length is None or length < 1:
            add_error(
                report,
                "ITEM_LENGTH",
                f"item {index} Length must be an integer >= 1",
                item_index=index,
                value=item.get("Length"),
            )
        if layer is None or layer < 0:
            add_error(
                report,
                "ITEM_LAYER",
                f"item {index} Layer must be an integer >= 0",
                item_index=index,
                value=item.get("Layer"),
            )
        else:
            layers.append(layer)
        if frame is not None and frame >= 0 and length is not None and length >= 1:
            end = frame + length
            if timeline_length is not None and end > timeline_length:
                add_error(
                    report,
                    "ITEM_AFTER_TIMELINE",
                    f"item {index} ends after timeline Length",
                    item_index=index,
                    end=end,
                    timeline_length=timeline_length,
                )
            if layer is not None and layer >= 0:
                valid_intervals[layer].append((frame, end, index))

    actual_max_layer = max(layers, default=-1)
    declared_max_layer = integer(timeline.get("MaxLayer")) if "MaxLayer" in timeline else None
    report["timeline"] = {
        "index": timeline_index,
        "length": timeline_length,
        "item_count": len(items),
        "max_layer": actual_max_layer,
        "declared_max_layer": declared_max_layer,
    }
    if declared_max_layer is not None and actual_max_layer > declared_max_layer:
        add_error(
            report,
            "MAX_LAYER_DECLARATION",
            "an item layer exceeds timeline MaxLayer",
            actual=actual_max_layer,
            declared=declared_max_layer,
        )
    elif declared_max_layer is not None and declared_max_layer > actual_max_layer:
        add_warning(
            report,
            "MAX_LAYER_UNUSED",
            "timeline MaxLayer is higher than the highest used layer",
            actual=actual_max_layer,
            declared=declared_max_layer,
        )
    if args.expect_max_layer is not None and actual_max_layer != args.expect_max_layer:
        add_error(
            report,
            "EXPECTED_MAX_LAYER",
            "highest used layer differs from expectation",
            actual=actual_max_layer,
            expected=args.expect_max_layer,
        )

    overlap_count = 0
    for layer, intervals in sorted(valid_intervals.items()):
        previous_end = -1
        previous_index: int | None = None
        for start, end, index in sorted(intervals):
            if start < previous_end:
                overlap_count += 1
                add_warning(
                    report,
                    "LAYER_OVERLAP",
                    f"items {previous_index} and {index} overlap on layer {layer}",
                    layer=layer,
                    previous_item_index=previous_index,
                    item_index=index,
                    overlap_frames=previous_end - start,
                )
            if end > previous_end:
                previous_end = end
                previous_index = index
    report["timeline"]["overlap_warnings"] = overlap_count

    characters = document.get("Characters", [])
    character_names: list[str] = []
    if not isinstance(characters, list):
        add_error(report, "CHARACTERS", "Characters must be an array")
    else:
        for index, character in enumerate(characters):
            if not isinstance(character, dict) or not nonempty(character.get("Name")):
                add_error(
                    report,
                    "CHARACTER_NAME",
                    f"character {index} has no non-empty Name",
                    character_index=index,
                )
            else:
                character_names.append(str(character["Name"]))
        duplicates = sorted(name for name, count in Counter(character_names).items() if count > 1)
        for name in duplicates:
            add_error(
                report,
                "DUPLICATE_CHARACTER",
                f"character name is duplicated: {name}",
                character_name=name,
            )
    known_characters = set(character_names)

    for index, item in enumerate(items):
        if item_type(item) != "Voice":
            continue
        character_name = item.get("CharacterName")
        if not nonempty(character_name):
            add_error(
                report,
                "VOICE_CHARACTER",
                f"voice item {index} has no CharacterName",
                item_index=index,
            )
        elif str(character_name) not in known_characters:
            add_error(
                report,
                "UNKNOWN_CHARACTER",
                f"voice item {index} references an unknown character",
                item_index=index,
                character_name=character_name,
            )

        if not nonempty(item.get("Serif")):
            add_error(
                report,
                "VOICE_SERIF",
                f"voice item {index} has an empty Serif",
                item_index=index,
            )
        if "Hatsuon" not in item or not isinstance(item.get("Hatsuon"), str):
            add_error(
                report,
                "VOICE_HATSUON_TYPE",
                f"voice item {index} Hatsuon must be a string",
                item_index=index,
            )
        elif args.stage == "final" and not nonempty(item.get("Hatsuon")):
            add_error(
                report,
                "VOICE_HATSUON_EMPTY",
                f"final voice item {index} has an empty Hatsuon",
                item_index=index,
            )
        elif args.stage == "post_roundtrip" and not nonempty(item.get("Hatsuon")):
            add_warning(
                report,
                "VOICE_HATSUON_EMPTY",
                f"post-roundtrip voice item {index} has an empty Hatsuon",
                item_index=index,
            )

        voice_seconds = timespan_seconds(item.get("VoiceLength"))
        if voice_seconds is None:
            add_error(
                report,
                "VOICE_LENGTH_FORMAT",
                f"voice item {index} has an invalid VoiceLength",
                item_index=index,
                value=item.get("VoiceLength"),
            )
        elif args.stage in {"post_roundtrip", "final"} and voice_seconds <= 0:
            add_error(
                report,
                "VOICE_LENGTH_EMPTY",
                f"{args.stage} voice item {index} has zero VoiceLength",
                item_index=index,
                value=item.get("VoiceLength"),
            )

        if args.stage in {"post_roundtrip", "final"} and not nonempty(item.get("VoiceCache")):
            add_error(
                report,
                "VOICE_CACHE_EMPTY",
                f"{args.stage} voice item {index} has no VoiceCache",
                item_index=index,
            )

    file_records: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        references = list(walk_file_paths(item))
        if item_type(item) in FILE_BACKED_TYPES and not references:
            add_error(
                report,
                "FILEPATH_ABSENT",
                f"file-backed item {index} has no FilePath",
                item_index=index,
                item_type=item_type(item),
            )
        for pointer, raw_path in references:
            if not isinstance(raw_path, str) or not raw_path.strip():
                add_error(
                    report,
                    "FILEPATH_EMPTY",
                    f"item {index} has an empty/non-string FilePath",
                    item_index=index,
                    pointer=pointer,
                )
                continue
            effective = apply_path_maps(raw_path, args.path_map)
            exists = Path(effective).expanduser().is_file()
            record = {
                "item_index": index,
                "pointer": pointer,
                "original": raw_path,
                "effective": effective,
                "exists": exists,
            }
            file_records.append(record)
            if not exists:
                add_error(
                    report,
                    "FILE_MISSING",
                    f"referenced file does not exist: {effective}",
                    **record,
                )

    unique_files = {path_identity(record["effective"]) for record in file_records}
    missing_files = [record for record in file_records if not record["exists"]]
    report["files"] = {
        "occurrences": len(file_records),
        "unique": len(unique_files),
        "missing": len(missing_files),
        "records": file_records,
        "path_maps": [{"from": source, "to": target} for source, target in args.path_map],
    }
    if (
        args.expect_file_occurrences is not None
        and len(file_records) != args.expect_file_occurrences
    ):
        add_error(
            report,
            "EXPECTED_FILE_OCCURRENCES",
            "file reference occurrence count differs from expectation",
            actual=len(file_records),
            expected=args.expect_file_occurrences,
        )
    if args.expect_unique_files is not None and len(unique_files) != args.expect_unique_files:
        add_error(
            report,
            "EXPECTED_UNIQUE_FILES",
            "unique file reference count differs from expectation",
            actual=len(unique_files),
            expected=args.expect_unique_files,
        )

    for expected_type, expected_count in args.expect_type:
        actual = type_counts.get(expected_type, 0)
        if actual != expected_count:
            add_error(
                report,
                "EXPECTED_TYPE_COUNT",
                f"{expected_type} item count differs from expectation",
                item_type=expected_type,
                actual=actual,
                expected=expected_count,
            )

    if args.reference_timeline:
        reference_path = Path(args.reference_timeline).expanduser().resolve(strict=True)
        try:
            reference = json.loads(reference_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise QaUsageError(f"cannot read reference timeline JSON: {exc}") from exc
        if not isinstance(reference, dict):
            raise QaUsageError("reference timeline root must be a JSON object")
        report["baseline"] = {
            "path": str(reference_path),
            "sha256": sha256_file(reference_path),
        }
        before = len(report["checks"])
        compare_baseline(report, document, timeline, items, reference)
        report["baseline"]["mismatches"] = sum(
            check["status"] == "FAIL"
            for check in report["checks"][before:]
            if check["code"].startswith("BASELINE_")
        )

    return report, finalize_report(report)


def write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as handle:
            temporary_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ymmp", help="input .ymmp (read-only)")
    parser.add_argument("--report", required=True, help="output QA report JSON")
    parser.add_argument("--stage", choices=STAGES, default="final")
    parser.add_argument("--timeline-index", type=int)
    parser.add_argument("--path-map", action="append", type=path_mapping, default=[], metavar="FROM=TO")
    parser.add_argument(
        "--expect-type", action="append", type=type_expectation, default=[], metavar="TYPE=COUNT"
    )
    parser.add_argument("--expect-file-occurrences", type=int)
    parser.add_argument("--expect-unique-files", type=int)
    parser.add_argument("--expect-max-layer", type=int)
    parser.add_argument("--reference-timeline", help="optional reference_timeline.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    for label in ("expect_file_occurrences", "expect_unique_files", "expect_max_layer"):
        value = getattr(args, label)
        if value is not None and value < 0:
            parser.error(f"--{label.replace('_', '-')} must be non-negative")

    input_path = Path(args.ymmp).expanduser().resolve(strict=False)
    report_path = Path(args.report).expanduser().resolve(strict=False)
    if input_path == report_path:
        print("qa_ymmp: --report must not be the input YMMP", file=sys.stderr)
        return 2

    try:
        report, exit_code = evaluate(args)
    except (FileNotFoundError, PermissionError, QaUsageError, OSError) as exc:
        report = empty_report(input_path, args.stage)
        report["status"] = "ERROR"
        report["summary"] = {"errors": 1, "warnings": 0, "checks": 1}
        add_error(report, "TOOL_ERROR", str(exc))
        try:
            write_report(report_path, report)
        except OSError as report_exc:
            print(f"qa_ymmp: {exc}; report write failed: {report_exc}", file=sys.stderr)
            return 2
        print(f"qa_ymmp: {exc}", file=sys.stderr)
        return 2

    try:
        write_report(report_path, report)
    except OSError as exc:
        print(f"qa_ymmp: cannot write report: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "report": str(report_path)}, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
