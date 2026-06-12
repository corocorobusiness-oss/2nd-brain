#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube スクリプト チェッカー v4
8層スキャンでポリシー違反を検出する

【データ駆動設計】
全てのNGワード・パターン・誤検知除外は refs/data/*.tsv から動的にロードする。
Python コード内にはワードリストを一切ハードコードしない。
新しい単語やパターンを追加するには、該当する TSV ファイルに1行追加するだけでOK。

対応TSVファイル:
  refs/data/l1_words.tsv          - L1: NGワード辞書
  refs/data/l2_patterns.tsv       - L2: 差別的トロープパターン
  refs/data/l3_patterns.tsv       - L3: 悪意ある表現パターン
  refs/data/l4_false_positives.tsv - L4: 誤検知除外
  refs/data/l5_manual.tsv         - L5: 辞書外マニュアル検知
  refs/data/censored_patterns.tsv - 伏字検知パターン

使い方:
  python scan_v4.py <CSVファイルパス>
  python scan_v4.py <CSVファイルパス> --data-dir /path/to/refs/data
"""

import re
import csv
import json
import sys
import os

# =============================================================
# TSVローダー
# =============================================================

def _resolve_data_dir():
    """TSVデータディレクトリのパスを解決する"""
    # --data-dir オプションが指定されていればそれを使う
    for i, arg in enumerate(sys.argv):
        if arg == "--data-dir" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    # デフォルト: スクリプトの親ディレクトリから refs/data を探す
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "..", "refs", "data")


def _load_tsv(filepath):
    """TSVファイルを読み込み、行ごとのタブ区切りリストを返す。
    コメント行（#始まり）と空行は無視する。"""
    rows = []
    if not os.path.exists(filepath):
        print(json.dumps({"warning": f"TSVファイルが見つかりません: {filepath}"}), file=sys.stderr)
        return rows
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def load_l1_words(data_dir):
    """L1: NGワード辞書をTSVからロードする"""
    words = []
    for cols in _load_tsv(os.path.join(data_dir, "l1_words.tsv")):
        if len(cols) < 4:
            continue
        cat, word, sev, typ = cols[0], cols[1], cols[2], cols[3]
        if typ == "plain":
            pat = re.escape(word)
        else:  # regex
            pat = word
        words.append({"cat": cat, "word": word, "pat": pat, "sev": sev})
    return words


def load_l2_patterns(data_dir):
    """L2: 差別的トロープパターンをTSVからロードする"""
    patterns = []
    for cols in _load_tsv(os.path.join(data_dir, "l2_patterns.tsv")):
        if len(cols) < 3:
            continue
        patterns.append({"group": cols[0], "pat": cols[1], "sev": cols[2]})
    return patterns


def load_l3_patterns(data_dir):
    """L3: 悪意ある表現パターンをTSVからロードする"""
    patterns = []
    for cols in _load_tsv(os.path.join(data_dir, "l3_patterns.tsv")):
        if len(cols) < 3:
            continue
        patterns.append({"cat": cols[0], "pat": cols[1], "sev": cols[2]})
    return patterns


def load_l4_false_positives(data_dir):
    """L4: 誤検知除外パターンをTSVからロードする"""
    fp = {}
    death_fp = []
    for cols in _load_tsv(os.path.join(data_dir, "l4_false_positives.tsv")):
        if len(cols) < 2:
            continue
        trigger, pattern = cols[0], cols[1]
        if trigger == "__DEATH__":
            death_fp.append(pattern)
        else:
            if trigger not in fp:
                fp[trigger] = []
            fp[trigger].append(pattern)
    return fp, death_fp


def load_l5_manual(data_dir):
    """L5: 辞書外マニュアル検知をTSVからロードする"""
    entries = {"A": [], "B": [], "C": [], "D": []}
    for cols in _load_tsv(os.path.join(data_dir, "l5_manual.tsv")):
        if len(cols) < 4:
            continue
        layer_key, word, sev, typ = cols[0], cols[1], cols[2], cols[3]
        # レイヤーキーの先頭1文字で振り分け（A_侮辱→A, B_ジェンダー→B, ...）
        key = layer_key[0] if layer_key else "A"
        entries.setdefault(key, []).append({"word": word, "sev": sev, "typ": typ, "layer": layer_key})
    return entries


def load_censored_patterns(data_dir):
    """伏字検知パターンをTSVからロードする"""
    patterns = []
    for cols in _load_tsv(os.path.join(data_dir, "censored_patterns.tsv")):
        if cols:
            patterns.append(cols[0])
    return patterns


# =============================================================
# スキャンエンジン
# =============================================================

def check_fp(word, context, l4_fp, l4_fp_death):
    """L4: 誤検知チェック"""
    if word in l4_fp:
        for fp_pat in l4_fp[word]:
            if re.search(fp_pat, context):
                return True
    if "死" in word or word.startswith("死") or "CH固有禁止/死" in word:
        for fp_pat in l4_fp_death:
            if re.search(fp_pat, context):
                return True
    return False


def scan_l1(text, l1_words, l4_fp, l4_fp_death):
    """L1: NGワード直接マッチ（正規表現対応）"""
    hits = []
    seen_positions = set()
    for entry in l1_words:
        pat = entry["pat"]
        try:
            for m in re.finditer(pat, text):
                pos_key = f"{m.start()}:{m.end()}"
                if pos_key in seen_positions:
                    continue
                ctx_s = max(0, m.start() - 20)
                ctx_e = min(len(text), m.end() + 20)
                ctx = text[ctx_s:ctx_e].replace('\n', ' ')
                is_fp = check_fp(entry["word"], ctx, l4_fp, l4_fp_death)
                if not is_fp:
                    seen_positions.add(pos_key)
                    hits.append({
                        "word": entry["word"], "category": entry["cat"],
                        "severity": entry["sev"], "context": ctx,
                        "matched": m.group(), "is_fp": False
                    })
        except re.error:
            pass
    return hits


def scan_l2(text, l2_patterns):
    """L2: 差別的トロープ"""
    hits = []
    for entry in l2_patterns:
        try:
            for m in re.finditer(entry["pat"], text):
                ctx_s = max(0, m.start() - 20)
                ctx_e = min(len(text), m.end() + 20)
                hits.append({
                    "group": entry["group"], "matched": m.group(),
                    "severity": entry.get("sev", "🔴"),
                    "context": text[ctx_s:ctx_e].replace('\n', ' ')
                })
        except re.error:
            pass
    return hits


def scan_l3(text, l3_patterns):
    """L3: 悪意ある表現"""
    hits = []
    for entry in l3_patterns:
        try:
            for m in re.finditer(entry["pat"], text):
                ctx_s = max(0, m.start() - 20)
                ctx_e = min(len(text), m.end() + 20)
                hits.append({
                    "category": entry["cat"], "matched": m.group(),
                    "severity": entry.get("sev", "🔴"),
                    "context": text[ctx_s:ctx_e].replace('\n', ' ')
                })
        except re.error:
            pass
    return hits


def scan_l5(text, l5_entries):
    """L5: 辞書外マニュアル検知"""
    hits = []
    for key in ["A", "B", "C", "D"]:
        for entry in l5_entries.get(key, []):
            word = entry["word"]
            sev = entry["sev"]
            typ = entry["typ"]
            layer = entry["layer"]
            pat = word if typ == "regex" else re.escape(word)
            try:
                for m in re.finditer(pat, text):
                    ctx_s = max(0, m.start() - 20)
                    ctx_e = min(len(text), m.end() + 20)
                    hits.append({
                        "layer": layer, "word": word, "matched": m.group(),
                        "severity": sev,
                        "context": text[ctx_s:ctx_e].replace('\n', ' ')
                    })
            except re.error:
                pass
    return hits


def scan_l6(all_hits):
    """L6: 頻度カウンター"""
    freq = {}
    for h in all_hits:
        w = h.get("word", h.get("matched", ""))
        if w:
            freq[w] = freq.get(w, 0) + 1
    warnings = []
    for w, c in freq.items():
        if c >= 5:
            warnings.append({"word": w, "count": c, "severity": "🟡"})
    return warnings


def scan_censored(text, censored_patterns):
    """伏字チェック"""
    hits = []
    seen = set()
    for pat in censored_patterns:
        try:
            for m in re.finditer(pat, text):
                ctx_s = max(0, m.start() - 20)
                ctx_e = min(len(text), m.end() + 20)
                ctx = text[ctx_s:ctx_e].replace('\n', ' ')
                key = f"{m.group()}:{m.start()}"
                if key not in seen:
                    seen.add(key)
                    hits.append({
                        "matched": m.group(), "severity": "🔴",
                        "context": ctx
                    })
        except re.error:
            pass
    return hits


def read_csv(filepath):
    """CSV読み込み"""
    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return []
            col_idx = 1
            for i, h in enumerate(header):
                if 'セリフ' in h or '台詞' in h:
                    col_idx = i
                    break
            for row in reader:
                if len(row) > col_idx and row[col_idx]:
                    lines.append(row[col_idx])
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
    return lines


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "CSVファイルパスを指定してください"}))
        sys.exit(1)

    csv_path = sys.argv[1]

    # データディレクトリ解決 & 全データロード
    data_dir = _resolve_data_dir()
    l1_words = load_l1_words(data_dir)
    l2_patterns = load_l2_patterns(data_dir)
    l3_patterns = load_l3_patterns(data_dir)
    l4_fp, l4_fp_death = load_l4_false_positives(data_dir)
    l5_entries = load_l5_manual(data_dir)
    censored_pats = load_censored_patterns(data_dir)

    # ロード結果サマリー
    load_summary = {
        "data_dir": data_dir,
        "l1_words_loaded": len(l1_words),
        "l2_patterns_loaded": len(l2_patterns),
        "l3_patterns_loaded": len(l3_patterns),
        "l4_fp_triggers": len(l4_fp),
        "l4_death_fp": len(l4_fp_death),
        "l5_entries_loaded": sum(len(v) for v in l5_entries.values()),
        "censored_patterns_loaded": len(censored_pats),
    }

    # CSV読み込み
    dialogues = read_csv(csv_path)
    if not dialogues:
        print(json.dumps({"error": "有効な台詞データが見つかりません", "load_summary": load_summary}))
        sys.exit(1)

    full_text = "\n".join(dialogues)

    # 8層スキャン
    l1 = scan_l1(full_text, l1_words, l4_fp, l4_fp_death)
    l2 = scan_l2(full_text, l2_patterns)
    l3 = scan_l3(full_text, l3_patterns)
    l5 = scan_l5(full_text, l5_entries)
    l6 = scan_l6(l1 + l5)
    censored = scan_censored(full_text, censored_pats)

    # カウント
    red = (sum(1 for h in l1 if h["severity"] == "🔴") +
           len(l2) + len(l3) +
           sum(1 for h in l5 if h["severity"] == "🔴") +
           sum(1 for h in censored if h["severity"] == "🔴"))
    yellow = (sum(1 for h in l1 if h["severity"] == "🟡") +
              sum(1 for h in l5 if h["severity"] == "🟡") +
              len(l6))

    verdict = "FAIL" if red > 0 else ("WARN" if yellow > 0 else "PASS")

    result = {
        "load_summary": load_summary,
        "summary": {"total_lines": len(dialogues), "total_chars": len(full_text)},
        "l1_hits": l1,
        "l2_hits": l2,
        "l3_hits": l3,
        "l5_hits": l5,
        "l6_warnings": l6,
        "censored_hits": censored,
        "verdict": verdict,
        "red_count": red,
        "yellow_count": yellow
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
