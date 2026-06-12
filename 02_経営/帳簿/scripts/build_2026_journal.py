#!/usr/bin/env python3
"""2026年仕訳帳の初期構築スクリプト（freee移行・一回限り）

銀行明細CSV（freee wallet_txnsから取得）を読み、勘定科目マッピングルールで
複式簿記の仕訳に変換して 2026_仕訳帳.csv を生成する。
銀行を通らない現金系経費（レシート払い）は EXTRA_ENTRIES で追加する。

実行: python3 build_2026_journal.py
"""
import csv
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_CSV = os.path.join(BASE, "data", "2026_銀行明細_GMOあおぞら.csv")
OUT_CSV = os.path.join(BASE, "2026_仕訳帳.csv")

BANK_ACCOUNT = "普通預金(GMOあおぞら)"

# 摘要パターン → (相手勘定科目, 摘要ラベル)
# 入金（income）: 借方=普通預金 / 貸方=相手科目
INCOME_RULES = [
    ("UBER EATS", ("売上高", "Uber Eats 売上入金")),
    ("デマエカン", ("売上高", "出前館 売上入金")),
    ("グーグル", ("売上高", "Google AdSense（YouTube）売上入金")),
    ("キャッシュバック", ("雑収入", "VISAデビット キャッシュバック")),
    ("ニコニコ", ("雑収入", "ニコニコプレミアム デビット取消返金")),
    ("利息", ("事業主借", "普通預金利息（個人帰属）")),
    ("ATM", ("事業主借", "ATM入金（個人資金の繰入）")),
]
# 出金（expense）: 借方=相手科目 / 貸方=普通預金
EXPENSE_RULES = [
    ("アポロステーション", ("車両費", "ガソリン代（アポロステーション）")),
    ("ENEOS", ("車両費", "ガソリン代（ENEOS）")),
    ("IDEMITSU", ("車両費", "ガソリン代（出光）")),
    ("CLAUDE.AI", ("通信費", "Claude AIサブスクリプション")),
    ("ANTHROPIC", ("通信費", "Claude AIサブスクリプション")),
    ("OPENAI", ("通信費", "ChatGPTサブスクリプション")),
    ("ニコニコ", ("通信費", "ニコニコプレミアム")),
    ("Brain", ("研修費", "Brain教材")),
    ("MERCARI", ("消耗品費", "メルカリ 事業用備品（品名は要追記）")),
    ("アピタ", ("消耗品費", "アピタ長岡店 事業用購入品")),
    ("振込手数料", ("支払手数料", "振込手数料")),
    ("ATM 利用手数料", ("事業主貸", "ATM手数料（私的出金に伴う）")),
    ("コロコロ", ("短期貸付金", "（株）コロコロへの貸付")),
    ("ダイシホクエツ", ("事業主貸", "第四北越銀行（個人口座）への資金移動")),
    ("ペイペイ", ("事業主貸", "PayPayチャージ")),
    ("ATM", ("事業主貸", "ATM出金（個人使用）")),
]

# 銀行を通らない仕訳（現金・レシート系、freee帳簿から特定済み）
# (日付, 借方科目, 貸方科目, 金額, 摘要)
EXTRA_ENTRIES = [
    ("2026-03-31", "車両費", "事業主借", 6000,
     "車両費 現金/PayPay払い（3月分・freee記帳より移行。レシート日付要確認）"),
    ("2026-05-12", "車両費", "事業主借", 3000,
     "出光 ガソリン 現金払い（レシートあり・freee記帳より移行）"),
]


def match(rules, description):
    for pat, result in rules:
        if pat in description:
            return result
    return None


def main():
    entries = []  # (date, 借方科目, 借方金額, 貸方科目, 貸方金額, 摘要, 出所)
    unmatched = []
    with open(BANK_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            date, side = row["date"], row["side"]
            amount = int(row["amount"])
            desc = row["description"]
            if side == "income":
                hit = match(INCOME_RULES, desc)
                if not hit:
                    unmatched.append(row)
                    continue
                acct, label = hit
                entries.append((date, BANK_ACCOUNT, amount, acct, amount, label, "銀行明細"))
            else:
                hit = match(EXPENSE_RULES, desc)
                if not hit:
                    unmatched.append(row)
                    continue
                acct, label = hit
                entries.append((date, acct, amount, BANK_ACCOUNT, amount, label, "銀行明細"))

    for date, dr, cr, amount, label in EXTRA_ENTRIES:
        entries.append((date, dr, amount, cr, amount, label, "現金経費"))

    entries.sort(key=lambda e: e[0])

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["No", "日付", "借方科目", "借方金額", "貸方科目", "貸方金額", "摘要", "出所"])
        for i, e in enumerate(entries, 1):
            w.writerow([i, *e])

    print(f"仕訳 {len(entries)} 件を {OUT_CSV} に出力")
    if unmatched:
        print(f"⚠️ ルール未マッチ {len(unmatched)} 件:")
        for r in unmatched:
            print(f"  {r['date']} {r['side']} {r['amount']} {r['description']}")


if __name__ == "__main__":
    main()
