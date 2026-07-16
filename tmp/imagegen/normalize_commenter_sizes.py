from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

from PIL import Image


CHARACTERS = (
    ("A_戦国武将", "A"),
    ("B_古代語り部", "B"),
    ("C_忍び", "C"),
    ("D_平安学者", "D"),
    ("E_幕末知識人", "E"),
)

EXPRESSIONS = (
    ("01", "真顔"),
    ("02", "怒り"),
    ("03", "困り"),
    ("04", "喜び"),
    ("05", "悲しみ"),
    ("06", "びっくり"),
)

CANVAS_SIZE = (1254, 1254)
TARGET_BODY_HEIGHT = 1040
TARGET_CENTER_X = 627
TARGET_BOTTOM_Y = 1170


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def find_child(parent: Path, expected_name: str, *, directory: bool) -> Path:
    matches = [
        child
        for child in parent.iterdir()
        if nfc(child.name) == expected_name
        and (child.is_dir() if directory else child.is_file())
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one match for {expected_name!r} in {parent}, got {matches}"
        )
    return matches[0]


def union_bbox(images: list[Image.Image]) -> tuple[int, int, int, int]:
    boxes = [image.getchannel("A").getbbox() for image in images]
    if any(box is None for box in boxes):
        raise RuntimeError("An input image is fully transparent")
    typed_boxes = [box for box in boxes if box is not None]
    return (
        min(box[0] for box in typed_boxes),
        min(box[1] for box in typed_boxes),
        max(box[2] for box in typed_boxes),
        max(box[3] for box in typed_boxes),
    )


def normalize_character(
    source_root: Path,
    target_root: Path,
    folder_name: str,
    prefix: str,
) -> None:
    source_folder = find_child(source_root, folder_name, directory=True)
    target_folder = target_root / folder_name
    target_folder.mkdir()

    sources: list[tuple[str, Path, Image.Image]] = []
    for number, expression in EXPRESSIONS:
        filename = f"{prefix}_{number}_{expression}.png"
        source_path = find_child(source_folder, filename, directory=False)
        image = Image.open(source_path).convert("RGBA")
        if image.size != CANVAS_SIZE:
            raise RuntimeError(f"Unexpected canvas size for {source_path}: {image.size}")
        sources.append((filename, source_path, image))

    left, top, right, bottom = union_bbox([item[2] for item in sources])
    source_width = right - left
    source_height = bottom - top
    scale = TARGET_BODY_HEIGHT / source_height
    target_width = round(source_width * scale)
    paste_x = round(TARGET_CENTER_X - target_width / 2)
    paste_y = TARGET_BOTTOM_Y - TARGET_BODY_HEIGHT

    for filename, source_path, image in sources:
        subject = image.crop((left, top, right, bottom))
        # Resize premultiplied RGBA to preserve clean antialiased transparent edges.
        subject = (
            subject.convert("RGBa")
            .resize((target_width, TARGET_BODY_HEIGHT), Image.Resampling.LANCZOS)
            .convert("RGBA")
        )
        # Remove sub-visible resampling specks while retaining the visible edge matte.
        clean_alpha = subject.getchannel("A").point(
            lambda value: 0 if value <= 4 else value
        )
        subject.putalpha(clean_alpha)
        output = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        output.alpha_composite(subject, (paste_x, paste_y))
        output.save(target_folder / filename, format="PNG", optimize=True)

    print(
        f"{folder_name}: source_union={(left, top, right, bottom)}, "
        f"scale={scale:.6f}, output_box={(paste_x, paste_y, paste_x + target_width, TARGET_BOTTOM_Y)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()

    if not args.source.is_dir():
        raise RuntimeError(f"Source folder does not exist: {args.source}")
    args.target.mkdir(parents=True, exist_ok=False)

    for folder_name, prefix in CHARACTERS:
        normalize_character(args.source, args.target, folder_name, prefix)


if __name__ == "__main__":
    main()
