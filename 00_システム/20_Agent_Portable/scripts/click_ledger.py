#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""click-learning-loop 記録CLI（クリック台帳・追記のみ）

サムネ・タイトルのクリック学習用。公開時・A/B終了時・差し替え時に1行ずつ記録する。
仕様正本: 00_システム/20_Agent_Portable/specs/click-learning-loop-設計書.md

使い方:
  公開時（必須・1本1行）:
    python3 click_ledger.py publish --folder 2026-07-03_中国大返し \
        --title "【2ch歴史】秀吉の中国大返しが..." --pred 16544 \
        --kirikuchi なぜ,黒幕 --thumb-badge "中国大返し" \
        --thumb-headline "230kmを10日←どう間に合った？" --thumb-sub "秀吉は本能寺を知ってた？/黒幕説の真相" \
        --ab-variant "A:現行" --ab-variant "B:数字なし逆説版"
  A/B終了時:
    python3 click_ledger.py ab --folder ... --winner A --note "数字入り大見出しが勝ち"
  CTR手動転記（APIフォールバック時のみ）:
    python3 click_ledger.py stats --folder ... --views 12000 --thumb-ctr 5.2 --window d1-7
  タイトル/サムネ差し替え時:
    python3 click_ledger.py touch --folder ... --kind rethumb --to "新見出し..."

保存先の既定: ~/Projects/youtube/eval/click_ledger.jsonl（環境変数 CLICK_LEDGER_FILE / --file で上書き可）
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

SCHEMA = 1
DEFAULT_FILE = os.environ.get(
    "CLICK_LEDGER_FILE",
    str(Path.home() / "Projects" / "youtube" / "eval" / "click_ledger.jsonl"),
)


def classify_title(title):
    """neta-forge subscriber_signal.py と同一regex（M11の型定義とズレさせない）"""
    if re.search(r"雑学|面白くなりすぎた|歴史オタクの雑学", title):
        return "広域雑学"
    if re.search(r"打線|ランキング|TOP|代表", title):
        return "打線/ランキング"
    if re.search(r"なぜ|理由|どうすれば|どうして|勝てた|取れなかった|天下取れ|滅亡|何をした|何した", title):
        return "なぜ/理由"
    if re.search(r"説|黒幕|闇|真実|ミステリー|祟り|暗殺|最期|死因|入れ替わ", title):
        return "闇/真実/説"
    if re.search(r"戦い|合戦|乱|変|大返し|関ヶ原|本能寺|応仁|元寇", title):
        return "事件/戦い"
    return "その他"


def die(msg):
    print("❌ %s（追記していません）" % msg, file=sys.stderr)
    sys.exit(2)


def valid_date(s):
    try:
        datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        die("--date は YYYY-MM-DD 形式で: %s" % s)
    return s


def append(path, record):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with open(p, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print("✅ 追記: %s" % line)
    print("→ %s" % p)


def main():
    ap = argparse.ArgumentParser(description="click-learning-loop 記録CLI（追記のみ）")
    ap.add_argument("--file", default=DEFAULT_FILE)
    sub = ap.add_subparsers(dest="cmd")

    pp = sub.add_parser("publish", help="公開時の記録（1本1行・必須）")
    pp.add_argument("--folder", required=True)
    pp.add_argument("--theme", default="")
    pp.add_argument("--date", default=datetime.date.today().isoformat())
    pp.add_argument("--title", required=True)
    pp.add_argument("--title-type", default="", help="省略時はタイトルから自動分類")
    pp.add_argument("--kirikuchi", default="", help="切り口タグ カンマ区切り（死因,なぜ,黒幕 等）")
    pp.add_argument("--thumb-badge", default="", help="サムネ上バッジ")
    pp.add_argument("--thumb-headline", default="", help="サムネ大見出し")
    pp.add_argument("--thumb-sub", default="", help="サムネ添え（/区切り）")
    pp.add_argument("--ab-variant", action="append", default=[], help='"ラベル:説明" 繰り返し可')
    pp.add_argument("--pred", type=int, default=0, help="neta-forge予測再生数")
    pp.add_argument("--series", default="", help="シリーズ名（怨霊/大河連動 等）")
    pp.add_argument("--note", default="")

    ab = sub.add_parser("ab", help="Test & Compare の結果記録")
    ab.add_argument("--folder", required=True)
    ab.add_argument("--date", default=datetime.date.today().isoformat())
    ab.add_argument("--winner", required=True, help="勝ったバリアントのラベル")
    ab.add_argument("--detail", default="", help="表示シェア等あれば")
    ab.add_argument("--note", default="", help="勝った理由の仮説を1行")

    st = sub.add_parser("stats", help="実測の手動転記（通常はfetch_click_statsが自動追記）")
    st.add_argument("--folder", required=True)
    st.add_argument("--date", default=datetime.date.today().isoformat())
    st.add_argument("--video-id", default="")
    st.add_argument("--window", default="d1-7", choices=["d1-7", "cum"])
    st.add_argument("--views", type=int, default=None)
    st.add_argument("--thumb-impressions", type=int, default=None)
    st.add_argument("--thumb-ctr", type=float, default=None, help="%%値（例 5.2）")
    st.add_argument("--avg-view-pct", type=float, default=None)
    st.add_argument("--note", default="")

    tc = sub.add_parser("touch", help="タイトル/サムネ差し替えの記録")
    tc.add_argument("--folder", required=True)
    tc.add_argument("--date", default=datetime.date.today().isoformat())
    tc.add_argument("--kind", required=True, choices=["retitle", "rethumb"])
    tc.add_argument("--from", dest="from_", default="")
    tc.add_argument("--to", default="")
    tc.add_argument("--note", default="")

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        sys.exit(2)
    if not args.folder.strip():
        die("--folder が空")
    date = valid_date(args.date)

    if args.cmd == "publish":
        variants = []
        for raw in args.ab_variant:
            if ":" not in raw:
                die('--ab-variant は "ラベル:説明" 形式で: %s' % raw)
            label, desc = raw.split(":", 1)
            variants.append({"label": label.strip(), "desc": desc.strip()})
        theme = args.theme or re.sub(r"^\d{4}-\d{2}-\d{2}_", "", args.folder.strip())
        rec = {
            "schema": SCHEMA, "type": "publish", "date": date,
            "folder": args.folder.strip(), "theme": theme,
            "title": args.title.strip(),
            "title_type": args.title_type or classify_title(args.title),
            "kirikuchi": [k.strip() for k in args.kirikuchi.split(",") if k.strip()],
            "thumb": {"badge": args.thumb_badge, "headline": args.thumb_headline, "sub": args.thumb_sub},
            "ab_variants": variants,
            "pred": args.pred, "series": args.series, "note": args.note,
        }
    elif args.cmd == "ab":
        rec = {"schema": SCHEMA, "type": "ab_result", "date": date,
               "folder": args.folder.strip(), "winner": args.winner.strip(),
               "detail": args.detail, "note": args.note}
    elif args.cmd == "stats":
        if args.views is None and args.thumb_ctr is None:
            die("stats は --views / --thumb-ctr のどちらかが必要")
        rec = {"schema": SCHEMA, "type": "stats", "date": date,
               "folder": args.folder.strip(), "video_id": args.video_id,
               "window": args.window, "views": args.views,
               "thumb_impressions": args.thumb_impressions,
               "thumb_ctr": args.thumb_ctr, "avg_view_pct": args.avg_view_pct,
               "source": "manual", "note": args.note}
    else:  # touch
        rec = {"schema": SCHEMA, "type": "touch", "date": date,
               "folder": args.folder.strip(), "kind": args.kind,
               "from": args.from_, "to": args.to, "note": args.note}

    append(args.file, rec)


if __name__ == "__main__":
    main()
