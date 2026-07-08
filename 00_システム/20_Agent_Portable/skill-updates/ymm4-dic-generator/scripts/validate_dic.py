#!/usr/bin/env python3
"""validate_dic.py v2 — YMM4 dic の「形式チェック」＋「台本×dic 漏れ/誤読検出器」

v1 は dic 側の形式・重複・台本未出現しか見ていなかった。
v2 は逆方向、「台本にあるのに dic から漏れている高リスク語」と
「登録済みだが読みが間違っている語」を検出して FAIL にする（fail-close）。

判定は3段階:
  FAIL … 完了扱いにしてはいけない（漏れ・誤読固定・形式不正）
  WARN … 人間/エージェントが目視すべき候補（自動では止めない）
  INFO … 統計・カバレッジ

使い方:
  python3 validate_dic.py <ymm4_user.dic> --script <台本.csv|.txt> [--data-dir DIR] [--json report.json] [--strict-warn]

exit code: 0=PASS / 1=FAIL / 2=引数・入力エラー

data-dir（省略時はスキルの data/）に置く読み資産:
  known_readings.tsv   検証済みの安定読み（正解源）。台本に出たら登録必須＋読み照合
  bad_readings.tsv     二度と通してはいけない誤読（表記+読みの組で即FAIL）
  high_risk_terms.tsv  台本に出たら候補必須の高リスク語（must=FAIL / review=WARN）
  ignore_terms.tsv     候補抽出から外してよい一般語
"""

import argparse
import csv
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

KANJI = "々〆ヵヶ一-鿿㐀-䶿"
KANJI_CHAR_RE = re.compile(f"[{KANJI}]")
# 数詞＋助数詞（2回, 500部, 天文16年 の「16年」など）
NUM_COUNTER_RE = re.compile(f"[0-9０-９]{{1,4}}[{KANJI}]{{1,2}}")
# 読みに許す文字: ひらがな・長音・半角数字（打線読み「2ばんせかんど」のため）
READING_OK_RE = re.compile(r"^[0-9ぁ-ゖー]+$")

# 資産ファイルに無くても常に無視する超一般語（最小限）
BUILTIN_IGNORE = {
    "今日", "明日", "昨日", "今", "人", "時", "事", "物", "所",
    "自分", "本当", "最初", "最後", "理由", "結果", "意味", "全部",
    "普通", "確認", "場合", "説明", "情報", "内容", "相手", "最近",
    "世界", "人間", "感じ", "時間", "時代", "当時", "現在", "以上",
    "以下", "一番", "大事", "無理", "必要", "有名", "存在", "実際",
}


def load_tsv(path):
    """タブ区切り・#コメント行と空行を無視して行のリストを返す。"""
    rows = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        rows.append(line.split("\t"))
    return rows


def load_script_text(path):
    """台本を読み込み、セリフ本文のテキストを返す。

    - CSV でヘッダに「セリフ」列があればその列だけを使う
    - それ以外は全文をそのまま使う
    """
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".csv":
        try:
            rows = list(csv.reader(io.StringIO(raw)))
        except csv.Error:
            return raw
        if rows and "セリフ" in rows[0]:
            col = rows[0].index("セリフ")
            lines = [r[col] for r in rows[1:] if len(r) > col]
            return "\n".join(lines)
    return raw


class Findings:
    def __init__(self):
        self.fail = []
        self.warn = []
        self.info = {}

    def add_fail(self, code, message, **extra):
        self.fail.append({"code": code, "message": message, **extra})

    def add_warn(self, code, message, **extra):
        self.warn.append({"code": code, "message": message, **extra})


def parse_dic(path, findings):
    """dic をパースし、[{lineno, enabled, regex, surface, reading}] を返す。形式不正はFAIL。"""
    entries = []
    seen = {}
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if '"' in line:
            findings.add_fail("ascii_quote", f"L{lineno}: ASCIIダブルクォートを含む", line=lineno)
        cols = line.split("\t")
        if len(cols) != 6:
            findings.add_fail(
                "format_error", f"L{lineno}: カラム数が6でない（{len(cols)}）", line=lineno
            )
            continue
        c1, c2, surface, reading, c5, c6 = cols
        if c1 != "1":
            findings.add_fail("format_error", f"L{lineno}: カラム1（有効フラグ）が1でない", line=lineno)
        if c2 not in ("0", "1"):
            findings.add_fail("format_error", f"L{lineno}: カラム2（正規表現フラグ）が0/1でない", line=lineno)
        if c5 != "":
            findings.add_fail("format_error", f"L{lineno}: カラム5（備考）が空でない", line=lineno)
        if c6 != "1":
            findings.add_fail("format_error", f"L{lineno}: カラム6が1でない", line=lineno)
        if not surface:
            findings.add_fail("format_error", f"L{lineno}: 単語（カラム3）が空", line=lineno)
            continue
        if not reading:
            findings.add_fail("empty_reading", f"L{lineno}: {surface} の読みが空", surface=surface)
        elif KANJI_CHAR_RE.search(reading):
            findings.add_fail(
                "kanji_in_reading", f"L{lineno}: {surface} の読みに漢字が混入: {reading}", surface=surface
            )
        elif not READING_OK_RE.match(reading):
            findings.add_fail(
                "bad_reading_char",
                f"L{lineno}: {surface} の読みにひらがな・長音・数字以外の文字: {reading}",
                surface=surface,
            )
        # 全角括弧を含むエントリ（打線など）は正規表現フラグ必須
        if ("（" in surface or "）" in surface) and c2 != "1":
            findings.add_fail(
                "regex_flag_missing",
                f"L{lineno}: {surface} は全角括弧を含むためカラム2を1にする必要がある",
                surface=surface,
            )
        if surface in seen:
            findings.add_fail(
                "duplicate_surface",
                f"L{lineno}: {surface} が重複（初出L{seen[surface]}）",
                surface=surface,
            )
        else:
            seen[surface] = lineno
        entries.append(
            {"lineno": lineno, "enabled": c1, "regex": c2, "surface": surface, "reading": reading}
        )
    return entries


def covered_intervals(text, surfaces):
    """dic の各リテラル表層形が台本中で占める区間 [(start, end)] を返す。"""
    intervals = []
    for s in surfaces:
        start = 0
        while True:
            idx = text.find(s, start)
            if idx == -1:
                break
            intervals.append((idx, idx + len(s)))
            start = idx + 1
    return intervals


def segmentable(word, vocab):
    """word が vocab の語の連結で完全に説明できるか（例: 歴史学者 = 歴史+学者）。"""
    n = len(word)
    ok = [False] * (n + 1)
    ok[0] = True
    for i in range(n):
        if not ok[i]:
            continue
        for j in range(i + 1, n + 1):
            if word[i:j] in vocab:
                ok[j] = True
    return ok[n]


def term_resolved(text, term, dic_surfaces, intervals):
    """台本中の term が dic で解決済みか。

    - term 自体が dic にあれば解決
    - term の全出現位置が、より長い dic 表層形の出現区間に包含されていれば解決
      （例: 「天海」が全部「南光坊天海」の中でだけ出るなら 天海 単体は不要）
    """
    if term in dic_surfaces:
        return True
    start = 0
    while True:
        idx = text.find(term, start)
        if idx == -1:
            break
        end = idx + len(term)
        if not any(s <= idx and end <= e and (e - s) > len(term) for s, e in intervals):
            return False
        start = idx + 1
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="YMM4 dic validator v2（漏れ・誤読検出つき）")
    ap.add_argument("dic", help="検証する ymm4_user.dic")
    ap.add_argument("--script", help="台本ファイル（.csv はセリフ列 / それ以外は全文）")
    ap.add_argument("--data-dir", help="読み資産ディレクトリ（既定: スキルの data/）")
    ap.add_argument("--json", dest="json_out", help="JSONレポートの出力先")
    ap.add_argument("--strict-warn", action="store_true", help="WARNもFAIL扱いにする")
    args = ap.parse_args(argv)

    dic_path = Path(args.dic)
    if not dic_path.exists():
        print(f"ERROR: dic が見つからない: {dic_path}", file=sys.stderr)
        return 2

    data_dir = Path(args.data_dir) if args.data_dir else Path(__file__).resolve().parent.parent / "data"

    findings = Findings()
    entries = parse_dic(dic_path, findings)
    dic_readings = {}
    for e in entries:
        dic_readings.setdefault(e["surface"], e["reading"])
    dic_surfaces = set(dic_readings)

    # --- 読み資産のロード ---
    known = {}  # surface -> reading
    for row in load_tsv(data_dir / "known_readings.tsv"):
        if len(row) < 2:
            continue
        surface, reading = row[0], row[1]
        if surface in known and known[surface] != reading:
            findings.add_fail(
                "known_reading_conflict",
                f"known_readings 内で {surface} の読みが衝突: {known[surface]} / {reading}",
                surface=surface,
            )
        known[surface] = reading

    bad = set()  # (surface, reading)
    for row in load_tsv(data_dir / "bad_readings.tsv"):
        if len(row) >= 2:
            bad.add((row[0], row[1]))

    high_risk = {}  # surface -> (level, hint)
    for row in load_tsv(data_dir / "high_risk_terms.tsv"):
        if len(row) >= 2:
            high_risk[row[0]] = (row[1], row[2] if len(row) > 2 else "")

    ignore = set(BUILTIN_IGNORE)
    for row in load_tsv(data_dir / "ignore_terms.tsv"):
        if row:
            ignore.add(row[0])

    # --- 登録済み語の読み検証（台本なしでも実行） ---
    for surface, reading in dic_readings.items():
        if (surface, reading) in bad:
            findings.add_fail(
                "bad_reading_registered",
                f"{surface}={reading} は既知の誤読（bad_readings）。登録禁止",
                surface=surface,
                reading=reading,
            )
        if surface in known and known[surface] != reading:
            findings.add_fail(
                "wrong_known_reading",
                f"{surface} の読みが検証済み読みと不一致: dic={reading} / 正={known[surface]}",
                surface=surface,
                reading=reading,
                expected=known[surface],
            )

    # --- 台本×dic の突合 ---
    script_text = None
    if args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            print(f"ERROR: 台本が見つからない: {script_path}", file=sys.stderr)
            return 2
        script_text = load_script_text(script_path)
        text = unicodedata.normalize("NFC", script_text)
        literal_surfaces = [e["surface"] for e in entries if e["regex"] == "0"]
        intervals = covered_intervals(text, literal_surfaces)

        # required_if_present: known_readings＋high_risk(must) は台本に出たら登録必須
        required = {s: "known_readings" for s in known}
        for s, (level, _hint) in high_risk.items():
            if level == "must":
                required[s] = "high_risk(must)"
        for term, source in sorted(required.items()):
            if term in text and not term_resolved(text, term, dic_surfaces, intervals):
                findings.add_fail(
                    "missing_must",
                    f"台本に「{term}」が出ているのに dic 未登録（{source}）"
                    + (f"。正しい読み: {known[term]}" if term in known else ""),
                    surface=term,
                    source=source,
                )

        # review レベルの高リスク語は WARN
        for term, (level, hint) in sorted(high_risk.items()):
            if level != "must" and term in text and not term_resolved(text, term, dic_surfaces, intervals):
                findings.add_warn(
                    "missing_review_candidate",
                    f"高リスク候補「{term}」が dic 未登録" + (f"（{hint}）" if hint else ""),
                    surface=term,
                )

        # 候補抽出（全文スイープの機械版）:
        # dic のどのエントリにもカバーされない漢字の連続を洗い出し、
        # ignore 資産で説明できないものを WARN として出す。
        covered = bytearray(len(text))
        for s, e in intervals:
            covered[s:e] = b"\x01" * (e - s)
        runs = []
        cur = []
        for i, ch in enumerate(text):
            if KANJI_CHAR_RE.match(ch) and not covered[i]:
                cur.append(ch)
            elif cur:
                runs.append("".join(cur))
                cur = []
        if cur:
            runs.append("".join(cur))

        missing_single_kanji = []
        missing_candidates = []
        for cand in sorted(set(runs)):
            # required（known_readings）と high_risk は missing_must / missing_review_candidate
            # 側で報告済みのため二重報告しない
            if cand in required or cand in high_risk:
                continue
            if cand in ignore or cand in dic_surfaces or segmentable(cand, ignore):
                continue
            if len(cand) == 1:
                missing_single_kanji.append(cand)
            else:
                missing_candidates.append(cand)
        # 数詞＋助数詞（500部, 16年 など）で未カバーのもの
        num_candidates = []
        for m in NUM_COUNTER_RE.finditer(text):
            if any(not covered[i] for i in range(*m.span())) and m.group() not in ignore:
                num_candidates.append(m.group())
        for cand in sorted(set(num_candidates)):
            missing_candidates.append(cand)

        for cand in missing_single_kanji:
            findings.add_warn(
                "missing_single_kanji",
                f"台本の単漢字「{cand}」が dic 未登録（読み割れリスク。登録するか除外理由を記録する）",
                surface=cand,
            )
        for cand in missing_candidates:
            findings.add_warn("missing_candidate", f"候補「{cand}」が dic 未登録", surface=cand)

        # 前回台本の残骸（台本に出ない登録語）は WARN（正規表現エントリは除外）
        for e in entries:
            if e["regex"] == "0" and e["surface"] not in text:
                findings.add_warn(
                    "unused_entry", f"{e['surface']} は台本に出現しない（前回の残骸？）", surface=e["surface"]
                )

        findings.info["uncovered_kanji_runs"] = len(set(runs))
        findings.info["missing_candidates"] = len(missing_candidates)
        findings.info["missing_single_kanji"] = len(missing_single_kanji)

    findings.info["dic_entries"] = len(entries)
    findings.info["known_readings"] = len(known)
    findings.info["high_risk_terms"] = len(high_risk)

    # --- 集計・出力 ---
    fail_count = len(findings.fail)
    warn_count = len(findings.warn)
    result = "FAIL" if fail_count or (args.strict_warn and warn_count) else "PASS"

    summary = {
        "result": result,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "missing_must_candidates": sum(1 for f in findings.fail if f["code"] == "missing_must"),
        "wrong_known_readings": sum(1 for f in findings.fail if f["code"] == "wrong_known_reading"),
        "bad_readings_registered": sum(1 for f in findings.fail if f["code"] == "bad_reading_registered"),
        "conflicts": sum(1 for f in findings.fail if f["code"] == "known_reading_conflict"),
        "fail": findings.fail,
        "warn": findings.warn,
        "info": findings.info,
    }

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    for f in findings.fail:
        print(f"FAIL [{f['code']}] {f['message']}")
    for w in findings.warn:
        print(f"WARN [{w['code']}] {w['message']}")
    print(
        f"{result}: entries={len(entries)} fail={fail_count} warn={warn_count} "
        f"missing_must={summary['missing_must_candidates']} "
        f"wrong_known={summary['wrong_known_readings']}"
    )
    return 1 if result == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
