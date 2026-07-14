#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""script-fix-metrics 記録CLI（台本修正メトリクス）

出荷1本ごと・出荷後の修正指示ごとに、修正コストとルール違反を
fix_metrics.jsonl へ「追記のみ」で記録する。

- 仕様正本: 00_システム/20_Agent_Portable/specs/script-fix-metrics-設計書.md
- ルールIDの正本: 03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md のインラインタグ [F05|機械:assemble_csv]
- 原則: 追記のみ（既存行の書き換え・削除はしない）／不正IDは追記せずエラー（fail-close）

使い方:
  出荷時（1本1行・必須）:
    python3 record_fix_metrics.py ship --folder 2026-07-03_中国大返し \
        --ai-regen 2 --owner-fix 1 --violations F04,F07 \
        --gate-fail qa_hard:字数 --gate-fail step45:講義臭:3 \
        --new-rule "解説直後の下スタート禁止" --note "..."
  出荷後に修正指示が来たら（都度1行）:
    python3 record_fix_metrics.py fix --folder 2026-07-03_中国大返し \
        --violations F07 --severity minor --note "退場レス1本カット指示"

保存先の既定は ~/Projects/youtube/eval/fix_metrics.jsonl。
環境変数 FIX_METRICS_FILE または --file で上書き可（テスト用）。
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

SCHEMA = 1
TAG_RE = re.compile(r"\[([RF]\d+)\|([^\]]+)\]")
SEVERITIES = ("minor", "major")

# このスクリプトはvault内に置かれる前提（マシン固有パスを書かない）
VAULT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RULES = VAULT_ROOT / "03_知識ベース" / "YouTube・コンテンツ制作" / "台本執筆ルール.md"
DEFAULT_FILE = os.environ.get(
    "FIX_METRICS_FILE",
    str(Path.home() / "Projects" / "youtube" / "eval" / "fix_metrics.jsonl"),
)


def die(msg):
    print("❌ %s（追記していません）" % msg, file=sys.stderr)
    sys.exit(2)


def load_rule_registry(rules_path):
    p = Path(rules_path)
    if not p.exists():
        die("ルールブックが見つからない: %s" % p)
    text = p.read_text(encoding="utf-8")
    reg = {}
    for m in TAG_RE.finditer(text):
        reg[m.group(1)] = m.group(2).strip()
    if not reg:
        die("ルールブックにID タグが1件もない（Phase 0未実施？）: %s" % p)
    return reg


def parse_violations(raw, registry):
    if not raw:
        return []
    ids = [v.strip() for v in raw.split(",") if v.strip()]
    unknown = [v for v in ids if v not in registry]
    if unknown:
        die("未知のルールID: %s（台本執筆ルール.mdのタグに存在しない。新種の指摘は --new-rule で文字列登録）"
            % ",".join(unknown))
    return ids


def parse_gate_fail(items):
    """--gate-fail gate:detail[:count] を辞書リストへ"""
    out = []
    for raw in items or []:
        parts = raw.split(":")
        if len(parts) == 2:
            gate, detail, count = parts[0], parts[1], 1
        elif len(parts) == 3:
            gate, detail = parts[0], parts[1]
            try:
                count = int(parts[2])
            except ValueError:
                die("--gate-fail のcountが数値でない: %s" % raw)
        else:
            die("--gate-fail は gate:detail[:count] 形式で: %s" % raw)
        if not gate or not detail:
            die("--gate-fail のgate/detailが空: %s" % raw)
        if count < 1:
            die("--gate-fail のcountは1以上: %s" % raw)
        out.append({"gate": gate, "detail": detail, "count": count})
    return out


def valid_date(s):
    try:
        datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        die("--date は YYYY-MM-DD 形式で: %s" % s)
    return s


def append_record(path, record):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with open(p, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print("✅ 追記: %s" % line)
    print("→ %s" % p)


def main():
    ap = argparse.ArgumentParser(description="script-fix-metrics 記録CLI（追記のみ）")
    ap.add_argument("--file", default=DEFAULT_FILE, help="記録先JSONL（既定: %s）" % DEFAULT_FILE)
    ap.add_argument("--rules", default=str(DEFAULT_RULES), help="ルールブックmd（ID照合用）")
    sub = ap.add_subparsers(dest="cmd")

    sp = sub.add_parser("ship", help="出荷時の記録（1本1行・必須）")
    sp.add_argument("--folder", required=True, help="案件フォルダ名（例: 2026-07-03_中国大返し）")
    sp.add_argument("--theme", default="", help="テーマ名（省略時folderから推定）")
    sp.add_argument("--date", default=datetime.date.today().isoformat(), help="出荷日 YYYY-MM-DD")
    sp.add_argument("--ai-regen", type=int, default=0, help="検品FAILによるAI再生成・修正サイクル数")
    sp.add_argument("--owner-fix", type=int, default=0, help="出荷前の池田さん指摘で直した回数")
    sp.add_argument("--violations", default="", help="違反ルールID（カンマ区切り 例: F04,F07）")
    sp.add_argument("--gate-fail", action="append", default=[],
                    help="ゲートFAIL gate:detail[:count]（繰り返し可）")
    sp.add_argument("--new-rule", action="append", default=[],
                    help="まだIDのない新種の指摘（文字列・繰り返し可）")
    sp.add_argument("--note", default="")

    fp = sub.add_parser("fix", help="出荷後の修正指示の記録（都度1行）")
    fp.add_argument("--folder", required=True)
    fp.add_argument("--date", default=datetime.date.today().isoformat())
    fp.add_argument("--violations", default="", help="違反ルールID（カンマ区切り）")
    fp.add_argument("--severity", default="minor", help="minor / major（major=差し替え級）")
    fp.add_argument("--new-rule", action="append", default=[])
    fp.add_argument("--note", default="")

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        sys.exit(2)

    registry = load_rule_registry(args.rules)

    if not args.folder.strip():
        die("--folder が空")
    date = valid_date(args.date)
    violations = parse_violations(args.violations, registry)

    if args.cmd == "ship":
        if args.ai_regen < 0 or args.owner_fix < 0:
            die("--ai-regen / --owner-fix は0以上")
        theme = args.theme or re.sub(r"^\d{4}-\d{2}-\d{2}_", "", args.folder.strip())
        record = {
            "schema": SCHEMA,
            "type": "shipment",
            "date": date,
            "folder": args.folder.strip(),
            "theme": theme,
            "rounds_ai_regen": args.ai_regen,
            "rounds_owner_fix": args.owner_fix,
            "gate_fails": parse_gate_fail(args.gate_fail),
            "rule_violations": violations,
            "new_rule_candidates": [s.strip() for s in args.new_rule if s.strip()],
            "note": args.note,
        }
    else:  # fix
        if args.severity not in SEVERITIES:
            die("--severity は minor / major のどちらか: %s" % args.severity)
        if not violations and not args.new_rule and not args.note:
            die("fix は --violations / --new-rule / --note のどれかが必要（空イベントは記録しない）")
        record = {
            "schema": SCHEMA,
            "type": "fix_event",
            "date": date,
            "folder": args.folder.strip(),
            "rule_violations": violations,
            "severity": args.severity,
            "new_rule_candidates": [s.strip() for s in args.new_rule if s.strip()],
            "note": args.note,
        }

    append_record(args.file, record)


if __name__ == "__main__":
    main()
