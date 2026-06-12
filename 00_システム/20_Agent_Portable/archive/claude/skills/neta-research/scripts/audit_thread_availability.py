#!/usr/bin/env python3
"""既存ネタストックの棚卸しユーティリティ。

neta-research 側のスレ可用性チェックが「推定ヒット数」ベースだった頃に書かれた
既存行を再監査するために使う。以下を出力する:

1. Q列（候補スレURL）が空で、かつ O列が ✕ 以外のネタ一覧
   → Claude が neta-research スキル内でこのネタ名を順に実URL収集して Q列 を埋める

2. Q列に URL が入っているが本数が 3 未満のネタ一覧
   → 即除外候補（O列を ✕ に変えても良い）

Usage:
    python3 audit_thread_availability.py           # 一覧表示
    python3 audit_thread_availability.py --json    # JSON出力（Claudeがパイプライン処理する用）
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = Path("/Users/kojinn/.config/google-sheets/token.json")
SHEET_ID = "1K_K7gs6l3n4GHixDT_iB_crpb2_ShXSnwRuqa8MOUAo"
RANGE = "ネタストック!A:Q"

COL = {
    "num": 0, "name": 1, "era": 2, "category": 3, "taiga": 4,
    "timing": 5, "status": 6, "pattern": 7, "script_url": 8, "memo": 9,
    "predicted": 10, "prob10k": 11, "rationale": 12, "scored_at": 13,
    "availability": 14, "availability_memo": 15, "thread_urls": 16,
}


def _service():
    data = json.loads(TOKEN_PATH.read_text())
    creds = Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )
    return build("sheets", "v4", credentials=creds)


def _cell(row: list[str], idx: int) -> str:
    return row[idx] if idx < len(row) else ""


def classify(rows: list[list[str]]) -> dict:
    needs_url_collection: list[dict] = []
    insufficient_urls: list[dict] = []
    ok: list[dict] = []
    rejected: list[dict] = []

    for sheet_row_idx, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
        if not row or not _cell(row, COL["name"]).strip():
            continue
        status = _cell(row, COL["status"])
        if status not in ("", "ストック"):
            # 制作中・公開済みは監査対象外
            continue
        availability = _cell(row, COL["availability"])
        urls_raw = _cell(row, COL["thread_urls"])
        urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]

        entry = {
            "sheet_row": sheet_row_idx,
            "num": _cell(row, COL["num"]),
            "name": _cell(row, COL["name"]),
            "era": _cell(row, COL["era"]),
            "availability": availability,
            "url_count": len(urls),
            "urls": urls,
        }
        if availability == "✕":
            rejected.append(entry)
        elif not urls:
            needs_url_collection.append(entry)
        elif len(urls) < 3:
            insufficient_urls.append(entry)
        else:
            ok.append(entry)

    return {
        "needs_url_collection": needs_url_collection,
        "insufficient_urls": insufficient_urls,
        "ok": ok,
        "rejected": rejected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="JSON出力（パイプライン用）")
    args = parser.parse_args()

    service = _service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=RANGE
    ).execute()
    rows = result.get("values", [])
    report = classify(rows)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"=== ネタストック棚卸し結果 ===")
    print(f"総行数: {len(rows) - 1}（ヘッダ除く）")
    print()

    print(f"■ Q列URL収集が必要（{len(report['needs_url_collection'])}件）")
    print("  → neta-researchで実URL収集を実行し、3本未満なら✕に更新")
    for e in report["needs_url_collection"]:
        print(f"    [行{e['sheet_row']}] {e['name']} ({e['era']}, 可用性:{e['availability']})")
    print()

    print(f"■ URL不足（3本未満）（{len(report['insufficient_urls'])}件）")
    print("  → 追加収集 or ✕に更新")
    for e in report["insufficient_urls"]:
        print(f"    [行{e['sheet_row']}] {e['name']} (URL:{e['url_count']}本)")
    print()

    print(f"■ 収集OK（3本以上）（{len(report['ok'])}件）")
    for e in report["ok"][:5]:
        print(f"    [行{e['sheet_row']}] {e['name']} (URL:{e['url_count']}本)")
    if len(report["ok"]) > 5:
        print(f"    ...他{len(report['ok']) - 5}件")
    print()

    print(f"■ 既に✕判定（{len(report['rejected'])}件）- 監査対象外")
    return 0


if __name__ == "__main__":
    sys.exit(main())
