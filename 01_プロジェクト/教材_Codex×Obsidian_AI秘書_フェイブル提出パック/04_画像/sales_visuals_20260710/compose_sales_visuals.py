from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FONT_DIR = Path("/System/Library/Fonts")
BOLD_FONT = next(FONT_DIR.glob("*W7.ttc"))
REGULAR_FONT = next(FONT_DIR.glob("*W4.ttc"))
MONO_FONT = FONT_DIR / "Menlo.ttc"


def font(path: Path, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size, index=index)


def fitted_font(draw: ImageDraw.ImageDraw, text: str, path: Path, max_size: int, max_width: int, min_size: int = 18) -> ImageFont.FreeTypeFont:
    for size in range(max_size, min_size - 1, -1):
        candidate = font(path, size)
        if draw.textbbox((0, 0), text, font=candidate)[2] <= max_width:
            return candidate
    return font(path, min_size)


def centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, text_font: ImageFont.FreeTypeFont, fill: tuple[int, int, int], stroke_width: int = 0, stroke_fill: Optional[tuple[int, int, int]] = None) -> None:
    left, top, right, bottom = box
    bbox = draw.textbbox((0, 0), text, font=text_font, stroke_width=stroke_width)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = left + (right - left - width) / 2 - bbox[0]
    y = top + (bottom - top - height) / 2 - bbox[1]
    draw.text((x, y), text, font=text_font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def title_banner(image: Image.Image, title: str) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((310, 18, 1362, 104), radius=18, fill=(3, 4, 12, 222), outline=(150, 101, 255, 230), width=3)
    title_font = fitted_font(draw, title, BOLD_FONT, 54, 980, 38)
    centered_text(draw, (330, 24, 1342, 98), title, title_font, (255, 255, 255), stroke_width=2, stroke_fill=(20, 12, 42))
    image.alpha_composite(overlay)


def make_bonus_pack() -> None:
    image = Image.open(ROOT / "14-bonus-pack-base.png").convert("RGBA")
    title_banner(image, "そのまま使える8大テンプレート特典")
    draw = ImageDraw.Draw(image)
    labels = [
        "AGENTS.md",
        "profile.md",
        "goals.md",
        "rules.md",
        "workflows.md",
        "デイリーノート",
        "プロンプト集",
        "安全チェックリスト",
    ]
    boxes = [
        (272, 357, 470, 420),
        (582, 357, 782, 420),
        (894, 357, 1092, 420),
        (1204, 357, 1402, 420),
        (272, 748, 470, 810),
        (582, 748, 782, 810),
        (894, 748, 1092, 810),
        (1204, 748, 1402, 810),
    ]
    for label, box in zip(labels, boxes):
        face = MONO_FONT if label.endswith(".md") else BOLD_FONT
        label_font = fitted_font(draw, label, face, 28, box[2] - box[0] - 10, 19)
        centered_text(draw, box, label, label_font, (25, 24, 41))
    image.convert("RGB").save(ROOT / "14-bonus-pack-title.png", quality=96)


def make_price() -> None:
    image = Image.open(ROOT / "15-release-price-base.png").convert("RGBA")
    draw = ImageDraw.Draw(image)
    title_font = font(BOLD_FONT, 60)
    centered_text(draw, (480, 220, 1190, 320), "リリース記念価格", title_font, (30, 27, 48))

    price_font = font(BOLD_FONT, 156)
    centered_text(draw, (455, 330, 1218, 560), "1,580円", price_font, (105, 63, 218), stroke_width=1, stroke_fill=(72, 39, 160))

    line_y = 584
    draw.rounded_rectangle((604, line_y, 1068, line_y + 4), radius=2, fill=(144, 100, 245))
    note_font = fitted_font(draw, "購入後の追記・改善は追加料金なし", BOLD_FONT, 36, 760, 28)
    centered_text(draw, (458, 612, 1216, 692), "購入後の追記・改善は追加料金なし", note_font, (45, 42, 61))
    image.convert("RGB").save(ROOT / "15-release-price-title.png", quality=96)


def make_product_bundle() -> None:
    image = Image.open(ROOT / "16-product-bundle-base.png").convert("RGBA")
    title_banner(image, "購入後に受け取れるもの")
    draw = ImageDraw.Draw(image)
    labels = [
        "Day 0〜7 実践ロードマップ",
        "8大テンプレート特典",
        "コピペ用プロンプト集",
        "安全運用チェックリスト",
    ]
    boxes = [
        (293, 362, 790, 449),
        (929, 362, 1360, 449),
        (275, 700, 765, 800),
        (913, 700, 1380, 800),
    ]
    for label, box in zip(labels, boxes):
        max_width = 390 if label == "Day 0〜7 実践ロードマップ" else box[2] - box[0] - 24
        max_size = 30 if label == "Day 0〜7 実践ロードマップ" else 34
        label_font = fitted_font(draw, label, BOLD_FONT, max_size, max_width, 22)
        centered_text(draw, box, label, label_font, (28, 27, 43))
    image.convert("RGB").save(ROOT / "16-product-bundle-title.png", quality=96)


def make_contact_sheet() -> None:
    files = [
        ROOT / "14-bonus-pack-title.png",
        ROOT / "15-release-price-title.png",
        ROOT / "16-product-bundle-title.png",
    ]
    canvas = Image.new("RGB", (1672, 1060), (5, 6, 14))
    draw = ImageDraw.Draw(canvas)
    thumb_size = (806, 454)
    positions = [(20, 20), (846, 20), (20, 535)]
    captions = ["14  8大特典", "15  リリース記念価格", "16  教材セット内容"]
    caption_font = font(BOLD_FONT, 28)
    for path, pos, caption in zip(files, positions, captions):
        thumb = Image.open(path).convert("RGB").resize(thumb_size, Image.Resampling.LANCZOS)
        canvas.paste(thumb, pos)
        draw.text((pos[0] + 8, pos[1] + 464), caption, font=caption_font, fill=(238, 238, 247))
    draw.rounded_rectangle((846, 535, 1652, 989), radius=12, outline=(68, 57, 105), width=2)
    centered_text(draw, (866, 555, 1632, 969), "販売ページ用 3枚", font(BOLD_FONT, 42), (168, 145, 235))
    canvas.save(ROOT / "contact-sheet-sales-3-title.jpg", quality=92)


if __name__ == "__main__":
    make_bonus_pack()
    make_price()
    make_product_bundle()
    make_contact_sheet()
