#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""script-fix-metrics 集計レポート（月次・read-only）

fix_metrics.jsonl と台本執筆ルール.mdのタグを読み、「ルールの効き」を
ダッシュボード（台本ルール効き.md）へ全再生成する。

- 仕様正本: 00_システム/20_Agent_Portable/specs/script-fix-metrics-設計書.md
- 書き込みはダッシュボードmdの1ファイルのみ。JSONL・ルールブック・台帳へは一切書かない
- 壊れた行はスキップして警告に出す（黙って捨てない）
- 記録漏れ（台帳の出荷数との差）は必ず表示する（欠測の自己申告）

使い方:
  python3 fix_metrics_report.py                     # 既定パスで生成
  python3 fix_metrics_report.py --stdout            # ファイルに書かず標準出力のみ
  python3 fix_metrics_report.py --file test.jsonl --out /tmp/report.md
"""
import argparse
import datetime
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

TAG_LINE_RE = re.compile(r"\[([RF]\d+)\|([^\]]+)\]\s*(.*)")
VAULT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RULES = VAULT_ROOT / "03_知識ベース" / "YouTube・コンテンツ制作" / "台本執筆ルール.md"
DEFAULT_OUT = VAULT_ROOT / "03_知識ベース" / "YouTube・コンテンツ制作" / "台本ルール効き.md"
DEFAULT_FILE = os.environ.get(
    "FIX_METRICS_FILE",
    str(Path.home() / "Projects" / "youtube" / "eval" / "fix_metrics.jsonl"),
)
DEFAULT_LEDGER = str(Path.home() / ".claude" / "skills" / "neta-forge" / "data" / "video_ledger.json")


def load_rules(rules_path):
    """ルールブックから {ID: (執行者タグ, 見出し40字)} を抽出"""
    rules = {}
    p = Path(rules_path)
    if not p.exists():
        return rules
    for line in p.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        # ルール定義行のみ対象（見出し or 太字箇条書き）。凡例・引用行の例示タグは拾わない
        if not (stripped.startswith("#") or stripped.startswith("- **[")):
            continue
        m = TAG_LINE_RE.search(stripped)
        if not m:
            continue
        rid, tag, rest = m.group(1), m.group(2).strip(), m.group(3)
        title = re.sub(r"[*`#>]", "", rest).strip()
        title = re.split(r"[（(：:]", title)[0].strip() or "(無題)"
        if rid not in rules:
            rules[rid] = (tag, title[:40])
    return rules


def load_records(path):
    records, broken = [], []
    p = Path(path)
    if not p.exists():
        return records, broken, False
    with open(p, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("type") not in ("shipment", "fix_event") or not r.get("folder"):
                    raise ValueError("type/folder不正")
                records.append(r)
            except (json.JSONDecodeError, ValueError, AttributeError) as e:
                broken.append((i, str(e)[:60]))
    return records, broken, True


def count_ledger_published(ledger_path, since):
    """video_ledger.json から since以降の公開/出荷済み件数を数える（スキーマ非依存の防御的走査）"""
    p = Path(ledger_path)
    if not p.exists():
        return None, "台帳ファイルなし（%s）" % p
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return None, "台帳が読めない: %s" % str(e)[:60]
    hits = []

    def walk(node):
        if isinstance(node, dict):
            status = str(node.get("status", ""))
            if status in ("published", "script_done", "shipped"):
                date = ""
                for k in ("published_at", "publish_date", "date", "公開日", "公開予定"):
                    if node.get(k):
                        date = str(node[k])[:10]
                        break
                hits.append((status, date))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    if not hits:
        return None, "台帳から出荷/公開エントリを抽出できず（スキーマ確認要）"
    published = [h for h in hits if h[0] == "published" and (not h[1] or h[1] >= since)]
    return len(published), None


def med(xs):
    return statistics.median(xs) if xs else 0


def build_report(records, broken, rules, jsonl_found, jsonl_path, ledger_path):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ships = sorted([r for r in records if r["type"] == "shipment"], key=lambda r: r.get("date", ""))
    fixes = [r for r in records if r["type"] == "fix_event"]

    L = []
    L.append("# 台本ルール効き（script-fix-metrics）")
    L.append("")
    L.append("> 自動生成: %s　／　`python3 00_システム/20_Agent_Portable/scripts/fix_metrics_report.py` で再生成。" % now)
    L.append("> 数字の正本＝`%s`。ルールの正本＝[[台本執筆ルール]]。**このレポートは提案のみ・何も自動変更しない**。" % jsonl_path)
    L.append("> 設計: `00_システム/20_Agent_Portable/specs/script-fix-metrics-設計書.md`")
    L.append("")

    if not jsonl_found:
        L.append("⚠️ **記録ファイルが存在しない**（%s）。Phase 1の記録開始待ち。" % jsonl_path)
        return "\n".join(L) + "\n"

    # 1. 修正コスト推移
    L.append("## 📉 修正コスト推移（1本あたり修正ラウンド）")
    L.append("")
    if not ships:
        L.append("> 出荷記録なし。")
    else:
        by_month = defaultdict(list)
        for s in ships:
            total = int(s.get("rounds_ai_regen", 0)) + int(s.get("rounds_owner_fix", 0))
            by_month[s.get("date", "")[:7]].append(s)
        L.append("| 月 | n | 総ラウンド中央値 | AI再生成中央値 | 池田さん指摘中央値 |")
        L.append("|---|---:|---:|---:|---:|")
        for month in sorted(by_month):
            g = by_month[month]
            L.append("| %s | %d | %.1f | %.1f | %.1f |" % (
                month, len(g),
                med([int(x.get("rounds_ai_regen", 0)) + int(x.get("rounds_owner_fix", 0)) for x in g]),
                med([int(x.get("rounds_ai_regen", 0)) for x in g]),
                med([int(x.get("rounds_owner_fix", 0)) for x in g])))
        last3 = ships[-3:]
        L.append("")
        L.append("- 直近3本移動中央値（北極星・下がり続けるのが目標）: **%.1f**" %
                 med([int(x.get("rounds_ai_regen", 0)) + int(x.get("rounds_owner_fix", 0)) for x in last3]))
    L.append("")

    # 2. ルール別違反ランキング
    ship_v = defaultdict(int)
    fix_v = defaultdict(int)
    folders_v = defaultdict(set)
    for s in ships:
        for rid in s.get("rule_violations", []):
            ship_v[rid] += 1
            folders_v[rid].add(s["folder"])
    for f in fixes:
        for rid in f.get("rule_violations", []):
            fix_v[rid] += 1
            folders_v[rid].add(f["folder"])
    all_ids = sorted(set(ship_v) | set(fix_v), key=lambda r: -(ship_v[r] + fix_v[r]))

    L.append("## 🔁 ルール別違反ランキング")
    L.append("")
    if not all_ids:
        L.append("> 違反記録なし。")
    else:
        L.append("| ルール | 執行者 | 出荷前違反 | 出荷後違反 | 動画数 |")
        L.append("|---|---|---:|---:|---:|")
        for rid in all_ids:
            tag, title = rules.get(rid, ("⚠️未知/廃止ID", "—"))
            L.append("| %s %s | %s | %d | %d | %d |" % (rid, title, tag, ship_v[rid], fix_v[rid], len(folders_v[rid])))
    L.append("")

    # 3. 機械化候補
    L.append("## ⚙️ 機械化候補（提案のみ・prose/LLMタグで違反2回以上）")
    L.append("")
    cands = [rid for rid in all_ids
             if (rules.get(rid, ("", ""))[0].startswith(("prose", "LLM")))
             and (ship_v[rid] + fix_v[rid]) >= 2]
    if cands:
        for rid in cands:
            tag, title = rules[rid]
            L.append("- **%s %s**（%s・違反%d回）→ §4.8 / qa への機械チェック追加を検討。機械化したらタグ更新までがセット" %
                     (rid, title, tag, ship_v[rid] + fix_v[rid]))
    else:
        L.append("> 該当なし。")
    L.append("")

    # 4. 効いてないルール
    L.append("## 🧟 効いてないルール（提案のみ・2本以上の動画で再発）")
    L.append("")
    zombies = [rid for rid in all_ids if len(folders_v[rid]) >= 2]
    if zombies:
        for rid in zombies:
            tag, title = rules.get(rid, ("⚠️未知/廃止ID", "—"))
            L.append("- **%s %s**（%s・%d本で違反）→ ルールの書き方が悪い/ゲート未反映の疑い。表現の見直し or 機械化を検討" %
                     (rid, title, tag, len(folders_v[rid])))
    else:
        L.append("> 該当なし。")
    L.append("")

    # 5. ID化候補
    L.append("## 🆕 ID化候補（新種の指摘が2回以上＝ルール昇格の審議対象）")
    L.append("")
    cand_count = defaultdict(int)
    for r in records:
        for c in r.get("new_rule_candidates", []):
            cand_count[re.sub(r"\s+", "", c)] += 1
    promoted = {k: v for k, v in cand_count.items() if v >= 2}
    if promoted:
        for k, v in sorted(promoted.items(), key=lambda kv: -kv[1]):
            L.append("- 「%s」（%d回）→ 台本執筆ルール.mdへF系IDで追加を検討（池田さん承認制）" % (k, v))
    else:
        L.append("> 該当なし（1回だけの指摘: %d件を監視中）。" % sum(1 for v in cand_count.values() if v == 1))
    L.append("")

    # 6. 記録漏れ・データ品質
    L.append("## 🕳️ 記録漏れ・データ品質（欠測の自己申告）")
    L.append("")
    since = ships[0]["date"] if ships else datetime.date.today().isoformat()
    pub_count, err = count_ledger_published(ledger_path, since)
    if err:
        L.append("- ⚠️ 台帳突合スキップ: %s" % err)
    else:
        diff = pub_count - len(ships)
        mark = "✅" if diff <= 0 else "⚠️"
        L.append("- %s 台帳の公開 %d本 vs 出荷記録 %d本（%s以降）→ 記録漏れ疑い **%d本**" %
                 (mark, pub_count, len(ships), since, max(diff, 0)))
    if broken:
        for lineno, e in broken:
            L.append("- ⚠️ 壊れた行をスキップ: %d行目（%s）" % (lineno, e))
    else:
        L.append("- ✅ 壊れた行なし")
    L.append("- 記録数: shipment %d / fix_event %d" % (len(ships), len(fixes)))
    L.append("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="script-fix-metrics 集計レポート（read-only）")
    ap.add_argument("--file", default=DEFAULT_FILE)
    ap.add_argument("--rules", default=str(DEFAULT_RULES))
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--stdout", action="store_true", help="ファイルに書かず標準出力のみ")
    args = ap.parse_args()

    rules = load_rules(args.rules)
    records, broken, found = load_records(args.file)
    report = build_report(records, broken, rules, found, args.file, args.ledger)

    if args.stdout:
        print(report)
    else:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report, encoding="utf-8")
        print("✅ 生成: %s（shipment %d / fix_event %d / 壊れた行 %d）" % (
            args.out,
            sum(1 for r in records if r["type"] == "shipment"),
            sum(1 for r in records if r["type"] == "fix_event"),
            len(broken)))


if __name__ == "__main__":
    main()
