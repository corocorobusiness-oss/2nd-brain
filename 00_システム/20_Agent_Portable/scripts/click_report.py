#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""click-learning-loop 集計レポート（read-only）

click_ledger.jsonl を読み、サムネ・タイトルの「勝ちパターン」答え合わせを
ダッシュボード（サムネ・タイトル効き.md）へ全再生成する。
書き込みはダッシュボード1ファイルのみ。昇格は提案のみ（自動でルールブックを書き換えない）。

使い方:
  python3 click_report.py            # 既定パスで生成
  python3 click_report.py --stdout   # ファイルに書かず表示のみ
"""
import argparse
import datetime
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = VAULT_ROOT / "03_知識ベース" / "YouTube・コンテンツ制作" / "サムネ・タイトル効き.md"
DEFAULT_FILE = os.environ.get(
    "CLICK_LEDGER_FILE",
    str(Path.home() / "Projects" / "youtube" / "eval" / "click_ledger.jsonl"),
)


def load(path):
    recs, broken = [], []
    p = Path(path)
    if not p.exists():
        return recs, broken, False
    with open(p, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if not r.get("type") or not r.get("folder"):
                    raise ValueError("type/folder不正")
                recs.append(r)
            except (json.JSONDecodeError, ValueError) as e:
                broken.append((i, str(e)[:50]))
    return recs, broken, True


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def fmt(v, suffix=""):
    return ("%s%s" % (v, suffix)) if v is not None else "—"


def build(recs, broken, found, src):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    pubs = sorted([r for r in recs if r["type"] == "publish"], key=lambda r: r["date"])
    abs_ = [r for r in recs if r["type"] == "ab_result"]
    touches = [r for r in recs if r["type"] == "touch"]
    # 最新のd1-7 statsをfolderごとに
    d7 = {}
    for r in recs:
        if r["type"] == "stats" and r.get("window") == "d1-7":
            d7[r["folder"]] = r

    L = []
    L.append("# サムネ・タイトル効き（click-learning-loop）")
    L.append("")
    L.append("> 自動生成: %s　／　`python3 00_システム/20_Agent_Portable/scripts/click_report.py` で再生成。" % now)
    L.append("> 数字の正本＝`%s`。ルールの正本＝[[サムネ・タイトル勝ちパターン]]。**提案のみ・自動変更なし**。" % src)
    L.append("")
    if not found:
        L.append("⚠️ 台帳ファイルが存在しない（%s）。click_ledger.py publish で記録開始待ち。" % src)
        return "\n".join(L) + "\n"

    ctrs = [d7[f].get("thumb_ctr") for f in d7 if d7[f].get("thumb_ctr") is not None]
    ch_med = med(ctrs)

    # 1. 公開一覧
    L.append("## 📋 公開一覧（7日窓の実測）")
    L.append("")
    if not pubs:
        L.append("> publish記録なし。")
    else:
        L.append("| 公開日 | テーマ | 型 | サムネ大見出し | CTR(d7) | 再生(d7) | pred比 |")
        L.append("|---|---|---|---|---:|---:|---:|")
        for p in pubs:
            s = d7.get(p["folder"], {})
            views, pred = s.get("views"), p.get("pred") or 0
            ratio = ("%.0f%%" % (100.0 * views / pred)) if (views is not None and pred) else "—"
            L.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                p["date"], p.get("theme", ""), p.get("title_type", ""),
                (p.get("thumb") or {}).get("headline", ""),
                fmt(s.get("thumb_ctr"), "%"), fmt(views), ratio))
        L.append("")
        L.append("- チャンネルCTR中央値(d7): **%s**　／　北極星＝この移動中央値が上がり続けること" % fmt(ch_med, "%"))
    L.append("")

    # 2. 型別
    L.append("## 🎯 タイトル型別（実測が3本たまった型から意味を持つ）")
    L.append("")
    by_type = defaultdict(list)
    for p in pubs:
        s = d7.get(p["folder"], {})
        by_type[p.get("title_type", "その他")].append(s)
    if by_type:
        L.append("| 型 | n | CTR中央値 | 再生中央値 |")
        L.append("|---|---:|---:|---:|")
        for t, ss in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
            L.append("| %s | %d | %s | %s |" % (
                t, len(ss), fmt(med([s.get("thumb_ctr") for s in ss]), "%"),
                fmt(med([s.get("views") for s in ss]))))
    else:
        L.append("> データなし。")
    L.append("")

    # 3. 切り口別
    L.append("## 🔎 切り口タグ別")
    L.append("")
    by_kiri = defaultdict(list)
    for p in pubs:
        s = d7.get(p["folder"], {})
        for k in p.get("kirikuchi", []):
            by_kiri[k].append(s)
    if by_kiri:
        L.append("| 切り口 | n | CTR中央値 |")
        L.append("|---|---:|---:|")
        for k, ss in sorted(by_kiri.items(), key=lambda kv: -len(kv[1])):
            L.append("| %s | %d | %s |" % (k, len(ss), fmt(med([s.get("thumb_ctr") for s in ss]), "%")))
    else:
        L.append("> 切り口タグ付きの記録なし。")
    L.append("")

    # 4. A/Bテスト
    L.append("## 🧪 A/Bテスト（Test & Compare）")
    L.append("")
    with_ab = [p for p in pubs if p.get("ab_variants")]
    rate = ("%.0f%%" % (100.0 * len(with_ab) / len(pubs))) if pubs else "—"
    L.append("- 実施率: %s（%d/%d本が複数案で公開）" % (rate, len(with_ab), len(pubs)))
    if abs_:
        for a in abs_:
            L.append("- %s **%s** 勝者=%s %s%s" % (
                a["date"], a["folder"], a["winner"],
                a.get("detail", ""), ("｜仮説: " + a["note"]) if a.get("note") else ""))
    else:
        L.append("- 結果記録なし（テスト完了したら `click_ledger.py ab --winner ...`）")
    if touches:
        L.append("- 差し替え: %d件（%s）" % (len(touches), " / ".join("%s %s" % (t["kind"], t["folder"]) for t in touches)))
    L.append("")

    # 5. 昇格候補
    L.append("## 🏆 勝ちパターン昇格候補（提案のみ・中央値CTR超えで2勝）")
    L.append("")
    cands = []
    if ch_med is not None:
        for group, items in [("型", by_type), ("切り口", by_kiri)]:
            for name, ss in items.items():
                wins = [s for s in ss if s.get("thumb_ctr") is not None and s["thumb_ctr"] > ch_med]
                if len(wins) >= 2:
                    cands.append("- **%s「%s」が%d勝**（CTR中央値%s%% > ch中央値%s%%）→ [[サムネ・タイトル勝ちパターン]]の該当仮説を確定へ（祐馬さん承認）"
                                 % (group, name, len(wins), med([s.get("thumb_ctr") for s in wins]), ch_med))
    L.extend(cands or ["> 該当なし（実測CTRが2本以上たまってから判定）。"])
    L.append("")

    # 6. データ品質
    L.append("## 🕳️ 記録漏れ・データ品質")
    L.append("")
    waiting = [p["folder"] for p in pubs if p["folder"] not in d7]
    if waiting:
        L.append("- ⏳ 実測待ち（fetch_click_stats 未取得）: %s" % " / ".join(waiting))
    no_ctr = [f for f in d7 if d7[f].get("thumb_ctr") is None]
    if no_ctr:
        L.append("- ⚠️ CTR欠測（APIフォールバック中→手動転記が必要）: %s" % " / ".join(no_ctr))
    for lineno, e in broken:
        L.append("- ⚠️ 壊れた行をスキップ: %d行目（%s）" % (lineno, e))
    if not waiting and not no_ctr and not broken:
        L.append("- ✅ 欠測・破損なし")
    L.append("- 記録数: publish %d / stats(d1-7) %d / ab %d / touch %d" % (len(pubs), len(d7), len(abs_), len(touches)))
    L.append("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="click-learning-loop 集計レポート（read-only）")
    ap.add_argument("--file", default=DEFAULT_FILE)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()

    recs, broken, found = load(args.file)
    report = build(recs, broken, found, args.file)
    if args.stdout:
        print(report)
    else:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report, encoding="utf-8")
        print("✅ 生成: %s（レコード%d件 / 壊れた行%d）" % (args.out, len(recs), len(broken)))


if __name__ == "__main__":
    main()
