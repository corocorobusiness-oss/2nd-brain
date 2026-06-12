#!/usr/bin/env python3
"""AI帳簿 集計・検証ツール（恒久運用）

2026_仕訳帳.csv を読み込み、以下を生成する:
  - レポート/2026_試算表.md   （月次損益・B/S残高・検証結果）
  - レポート/2026_総勘定元帳.csv （科目別の全仕訳明細＋残高）

検証内容:
  1. 全仕訳の貸借一致
  2. 普通預金の帳簿残高 = 銀行明細の最終残高
  3. freee試算表（移行時点）との照合 — 差異が「意図した補正」のみであること

実行: python3 ledger.py
"""
import csv
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL = os.path.join(BASE, "2026_仕訳帳.csv")
REPORT_DIR = os.path.join(BASE, "レポート")
BANK_CSV = os.path.join(BASE, "data", "2026_銀行明細_GMOあおぞら.csv")

# ---- 勘定科目マスタ ----
PL_INCOME = ["売上高", "雑収入"]
PL_EXPENSE = ["研修費", "通信費", "車両費", "消耗品費", "支払手数料", "減価償却費"]
BS_ASSET = ["普通預金(GMOあおぞら)", "短期貸付金", "車両運搬具", "事業主貸"]
BS_LIABILITY = ["未払金", "事業主借"]
BS_CAPITAL = ["元入金"]
ALL_ACCOUNTS = PL_INCOME + PL_EXPENSE + BS_ASSET + BS_LIABILITY + BS_CAPITAL

# 期首残高（2026-01-01、freee開始残高より）
OPENING = {
    "普通預金(GMOあおぞら)": 10385,
    "車両運搬具": 1032986,
    "元入金": -1043371,  # 貸方残高はマイナスで保持
}

# ---- freee試算表との照合用リファレンス（2026-06-10移行時点） ----
FREEE_TRIAL = {
    1: {"売上高": 115667, "雑収入": 6, "研修費": 2980, "車両費": 3245},
    2: {"売上高": 227261, "雑収入": 37, "研修費": 17580, "通信費": 790, "車両費": 7248},
    3: {"売上高": 235563, "雑収入": 1733, "通信費": 17855, "支払手数料": 75, "車両費": 15665},
    4: {"売上高": 133014, "通信費": 18161, "車両費": 13822},
    5: {"売上高": 65598, "研修費": 2682, "通信費": 17912, "車両費": 10552},
}
# 意図した補正（freee側の記帳漏れ＋スナップショット(6/10朝)以降に同期された分）: (月, 科目) -> 差額
EXPECTED_DIFF = {
    (4, "売上高"): 38246,   # Google AdSense 4/22 入金の計上漏れ
    (5, "売上高"): 28041 + 39888,  # AdSense 5/22 計上漏れ + Uber 5/26 入金（スナップショット後同期）
    (4, "雑収入"): 155,     # キャッシュバック 4/21
    (5, "雑収入"): 196,     # キャッシュバック 5/21
    (4, "通信費"): 790,     # ニコニコプレミアム 4/1
    (5, "通信費"): 790,     # ニコニコプレミアム 5/1
    (4, "支払手数料"): 75,  # 振込手数料 4/21
    (5, "車両費"): 3655,    # アポロ 5/29（スナップショット後同期）
}


def load_journal():
    rows = []
    with open(JOURNAL, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "no": int(r["No"]),
                "date": r["日付"],
                "dr": r["借方科目"], "dr_amt": int(r["借方金額"]),
                "cr": r["貸方科目"], "cr_amt": int(r["貸方金額"]),
                "desc": r["摘要"], "src": r["出所"],
            })
    return rows


def main():
    rows = load_journal()
    errors, notes = [], []

    # 1. 貸借一致・科目チェック
    for r in rows:
        if r["dr_amt"] != r["cr_amt"]:
            errors.append(f"仕訳No{r['no']}: 貸借不一致 {r['dr_amt']} != {r['cr_amt']}")
        for acct in (r["dr"], r["cr"]):
            if acct not in ALL_ACCOUNTS:
                errors.append(f"仕訳No{r['no']}: 未定義の科目「{acct}」")

    # 残高計算（借方プラス・貸方マイナス）
    balance = defaultdict(int)
    monthly = defaultdict(lambda: defaultdict(int))  # month -> acct -> 発生額
    postings = defaultdict(list)
    for acct, amt in OPENING.items():
        balance[acct] += amt
        postings[acct].append(("2026-01-01", "期首残高", amt if amt > 0 else 0, -amt if amt < 0 else 0, "開始残高"))

    for r in sorted(rows, key=lambda x: (x["date"], x["no"])):
        m = int(r["date"][5:7])
        balance[r["dr"]] += r["dr_amt"]
        balance[r["cr"]] -= r["cr_amt"]
        postings[r["dr"]].append((r["date"], r["desc"], r["dr_amt"], 0, r["src"]))
        postings[r["cr"]].append((r["date"], r["desc"], 0, r["cr_amt"], r["src"]))
        # 月次発生（PL科目: 収益は貸方発生、費用は借方発生）
        if r["dr"] in PL_EXPENSE or r["dr"] in PL_INCOME:
            monthly[m][r["dr"]] += r["dr_amt"] * (1 if r["dr"] in PL_EXPENSE else -1)
        if r["cr"] in PL_INCOME or r["cr"] in PL_EXPENSE:
            monthly[m][r["cr"]] += r["cr_amt"] * (1 if r["cr"] in PL_INCOME else -1)

    # 2. 銀行残高検証
    with open(BANK_CSV, encoding="utf-8") as f:
        bank_rows = list(csv.DictReader(f))
    bank_last = bank_rows[-1]
    book_bank = balance["普通預金(GMOあおぞら)"]
    if book_bank != int(bank_last["balance"]):
        errors.append(
            f"普通預金残高不一致: 帳簿 {book_bank:,} vs 明細 {int(bank_last['balance']):,}（{bank_last['date']}時点）")
    else:
        notes.append(f"✅ 普通預金残高 一致: ¥{book_bank:,}（銀行明細 {bank_last['date']} 時点）")

    # 3. freee照合
    recon_lines = []
    for m in sorted(FREEE_TRIAL):
        accts = set(FREEE_TRIAL[m]) | {a for a in monthly[m] if monthly[m][a]}
        for a in sorted(accts):
            ours = monthly[m].get(a, 0)
            freee = FREEE_TRIAL[m].get(a, 0)
            diff = ours - freee
            expected = EXPECTED_DIFF.get((m, a), 0)
            status = "一致" if diff == 0 else ("補正(想定どおり)" if diff == expected else "❌ 想定外差異")
            if diff != 0 or a in FREEE_TRIAL[m]:
                recon_lines.append((m, a, freee, ours, diff, status))
            if diff != 0 and diff != expected:
                errors.append(f"freee照合: {m}月 {a} 想定外差異 {diff:+,}（想定 {expected:+,}）")

    # ---- レポート出力 ----
    os.makedirs(REPORT_DIR, exist_ok=True)

    # 総勘定元帳
    with open(os.path.join(REPORT_DIR, "2026_総勘定元帳.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["科目", "日付", "摘要", "借方", "貸方", "残高", "出所"])
        for acct in ALL_ACCOUNTS:
            if acct not in postings:
                continue
            run = 0
            for date, desc, dr, cr, src in sorted(postings[acct], key=lambda x: x[0]):
                run += dr - cr
                w.writerow([acct, date, desc, dr or "", cr or "", run, src])

    # 試算表md
    months = sorted(monthly)
    lines = ["# 2026年 試算表（AI帳簿）", "",
             f"仕訳数: {len(rows)} 件 ｜ 生成: ledger.py", ""]
    lines.append("## 月次損益")
    lines.append("| 科目 | " + " | ".join(f"{m}月" for m in months) + " | 累計 |")
    lines.append("|" + "---|" * (len(months) + 2))
    total_income = total_expense = 0
    for a in PL_INCOME + PL_EXPENSE:
        vals = [monthly[m].get(a, 0) for m in months]
        s = sum(vals)
        if s == 0:
            continue
        if a in PL_INCOME:
            total_income += s
        else:
            total_expense += s
        lines.append(f"| {a} | " + " | ".join(f"{v:,}" for v in vals) + f" | **{s:,}** |")
    profits = [sum(monthly[m].get(a, 0) for a in PL_INCOME) - sum(monthly[m].get(a, 0) for a in PL_EXPENSE) for m in months]
    lines.append("| **利益** | " + " | ".join(f"**{p:,}**" for p in profits) + f" | **{total_income - total_expense:,}** |")

    lines += ["", "## B/S残高（仕訳反映後）", "| 科目 | 残高 |", "|---|---:|"]
    for a in BS_ASSET + BS_LIABILITY + BS_CAPITAL:
        b = balance[a]
        if b == 0:
            continue
        lines.append(f"| {a} | {abs(b):,}{'（貸方）' if b < 0 else ''} |")

    lines += ["", "## freee試算表との照合（移行検証）",
              "| 月 | 科目 | freee | Claude帳簿 | 差異 | 判定 |", "|---|---|---:|---:|---:|---|"]
    for m, a, fr, ours, diff, status in recon_lines:
        lines.append(f"| {m}月 | {a} | {fr:,} | {ours:,} | {diff:+,} | {status} |")

    lines += ["", "## 検証結果", ""]
    if errors:
        lines += [f"- ❌ {e}" for e in errors]
    else:
        lines.append("- ✅ 全チェック合格（貸借一致・銀行残高一致・freee照合OK）")
    lines += [f"- {n}" for n in notes]

    with open(os.path.join(REPORT_DIR, "2026_試算表.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines[-12:]))
    print(f"\nレポート出力: {REPORT_DIR}/2026_試算表.md, 2026_総勘定元帳.csv")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
