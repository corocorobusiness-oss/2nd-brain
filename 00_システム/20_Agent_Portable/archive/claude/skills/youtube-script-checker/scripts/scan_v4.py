#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube スクリプト チェッカー v5
8層スキャンでポリシー違反を検出する
v5変更点:
  - 「死」の1文字検知対応（len<2ガード撤廃→専用FP処理）
  - 死/殺す の活用形を網羅的に追加
  - ボロカスをFPから削除し侮辱語として検知
  - 金柑頭/陰キャ/ジェノサイド/老いぼれ/ボロカス追加
  - 2chニックネーム（フロカス/ブリカス/フラカス/アメカス）FP対応
  - L1マッチングを正規表現ベースに変更（活用形展開）
"""

import re
import csv
import json
import sys

# =============================================================
# L1: NGワード辞書 (カテゴリ, パターン, 表示名, 重大度)
# パターンは正規表現。活用形もここで網羅する。
# =============================================================
L1_WORDS = []

def _add(cat, words, sev="🔴"):
    """単純な文字列マッチ用（従来互換）"""
    for w in words:
        L1_WORDS.append({"cat": cat, "word": w, "pat": re.escape(w), "sev": sev})

def _add_re(cat, pattern, display_name, sev="🔴"):
    """正規表現パターン用"""
    L1_WORDS.append({"cat": cat, "word": display_name, "pat": pattern, "sev": sev})

# ── ヘイト/民族蔑称 ──
_add("ヘイト/民族", ["チョン", "支那人", "支那", "土人", "ニガー", "三国人",
    "不逞鮮人", "鮮人", "劣等民族", "蛮族", "未開人", "原住民", "毛唐", "鬼畜米英"])

# ── 障害者差別 ──
_add("障害者差別", ["めくら", "つんぼ", "びっこ", "かたわ", "片輪", "ガイジ", "池沼",
    "キチガイ", "気違い", "基地外", "知障", "身障", "聾唖", "精神異常者"])

# ── 性差別 ──
_add("性差別", ["ま〜ん", "マンさん", "肉便器", "ヤリマン", "ビッチ", "淫売", "売女"])

# ── LGBTQ差別 ──
_add("LGBTQ差別", ["ホモ", "オカマ", "おなべ", "レズ"], sev="🟡")

# ── 侮辱/罵倒 🔴 ──
_add("侮辱/罵倒", ["クソ", "くっそ", "クッソ", "糞", "ゴミ", "クズ", "カス",
    "ボンクラ", "外道", "畜生", "畜将", "ぐう畜", "ボロカス"], sev="🔴")

# ── 侮辱/罵倒 🟡 ──
_add("侮辱/罵倒", ["野郎", "太鼓持ち", "三流", "無能", "ハゲ", "禿", "ブス"], sev="🟡")

# ── チャンネル固有禁止 ──
_add("CH固有禁止", ["アホ", "バカ", "馬鹿", "デブ"], sev="🔴")

# ── 死 関連（チャンネル固有禁止・最重要）──
# 「死」は1文字だが絶対禁止。活用形を正規表現で網羅。
_add_re("CH固有禁止/死", r"死ぬ", "死ぬ", sev="🔴")
_add_re("CH固有禁止/死", r"死んだ", "死んだ", sev="🔴")
_add_re("CH固有禁止/死", r"死んで", "死んで", sev="🔴")
_add_re("CH固有禁止/死", r"死に(かけ|方|様|際|場所|目|物狂い|体|絶え|至)", "死に〜", sev="🔴")
_add_re("CH固有禁止/死", r"死な[いかくけせば]", "死な〜", sev="🔴")
_add_re("CH固有禁止/死", r"死ね[ばよ]?", "死ね", sev="🔴")
_add_re("CH固有禁止/死", r"死の[うび]", "死の〜", sev="🔴")
_add_re("CH固有禁止/死", r"死に?た[いがく]?", "死にた〜", sev="🔴")
_add_re("CH固有禁止/死", r"死す", "死す", sev="🔴")
_add_re("CH固有禁止/死", r"死した", "死した", sev="🔴")
_add_re("CH固有禁止/死", r"死去", "死去", sev="🔴")
_add_re("CH固有禁止/死", r"死亡", "死亡", sev="🔴")
_add_re("CH固有禁止/死", r"死因", "死因", sev="🔴")
_add_re("CH固有禁止/死", r"死体", "死体", sev="🔴")
_add_re("CH固有禁止/死", r"死者", "死者", sev="🔴")
_add_re("CH固有禁止/死", r"死傷", "死傷", sev="🔴")
_add_re("CH固有禁止/死", r"死闘", "死闘", sev="🟡")  # 歴史文脈で使用可能性あり
_add_re("CH固有禁止/死", r"死守", "死守", sev="🟡")  # 軍事用語
_add_re("CH固有禁止/死", r"戦死", "戦死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"病死", "病死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"横死", "横死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"討ち?死に?", "討死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"溺死", "溺死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"餓死", "餓死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"焼死", "焼死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"憤死", "憤死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"頓死", "頓死", sev="🟡")  # 歴史用語
_add_re("CH固有禁止/死", r"刺死", "刺死", sev="🟡")  # 歴史用語
# 汎用「死」キャッチオール（上記に該当しなかったものを拾う）
_add_re("CH固有禁止/死", r"(?<!必)(?<!決)(?<!九)(?<!瀕)(?<!致)(?<!生)(?<!起)(?<!活)死(?!守|闘|角|力|中|地|後|語|線|球|蔵|海|活)", "死(汎用)", sev="🔴")

# ── 殺す 関連（活用形展開）──
_add_re("暴力/残虐", r"殺[すしせさ]", "殺す活用", sev="🔴")
_add_re("暴力/残虐", r"殺し[たてに]", "殺し〜", sev="🔴")
_add_re("暴力/残虐", r"殺され", "殺され", sev="🔴")
_add_re("暴力/残虐", r"殺そう", "殺そう", sev="🔴")
_add_re("暴力/残虐", r"ぶっ殺", "ぶっ殺", sev="🔴")
_add_re("暴力/残虐", r"殺害", "殺害", sev="🔴")
_add_re("暴力/残虐", r"殺戮", "殺戮", sev="🔴")
_add("暴力/残虐", ["撫切り", "撫切りに", "皆殺し", "虐殺", "ジェノサイド",
    "磔", "串刺し", "斬首", "打ち首", "釜茹で", "火あぶり", "血祭り"], sev="🔴")

# ── グラフィック暴力 ──
_add("グラフィック暴力", ["人肉", "食人", "カニバリ", "臓器", "内臓", "脳漿"], sev="🔴")

# ── 下品表現 ──
_add("下品表現", ["脱糞", "排泄", "うんこ", "うんち", "おしっこ", "ちんこ", "まんこ"], sev="🟡")

# ── 性的表現 ──
_add("性的表現", ["レイプ", "強姦", "輪姦", "近親相姦", "痴漢", "盗撮"], sev="🔴")

# ── 児童安全 ──
_add("児童安全", ["ロリコン", "ショタコン", "ペドフィリア", "児童ポルノ"], sev="🔴")

# =============================================================
# L4: 誤検知除外パターン (NGワード → 除外条件の正規表現)
# =============================================================
L4_FP = {
    "おし": [r"狂おし", r"教おし", r"推おし", r"おしい", r"おして", r"おした",
             r"おしゃれ", r"おしまい", r"おしえ", r"おしゃべり", r"おしぼり",
             r"うっとおし"],
    "ホモ": [r"ホモ・サピエンス"],
    "レズ": [r"プレゼ"],
    "めくら": [r"めくらまし"],
    "ハゲ": [r"ハゲしい", r"ハゲます", r"剥げ", r"激しい"],
    "禿": [r"禿頭(?!を|が|の|は)"],  # 禿頭は歴史用語として文脈次第
    "カス": [r"カステラ", r"カスタム", r"カスタマー", r"カスケード", r"ポンカス",
             r"フロカス", r"ブリカス", r"フラカス", r"アメカス", r"スカスカ", r"ダマスカス"],
    # 注意: ボロカスは侮辱語なのでFPに入れない
    "ゴミ": [r"ゴミ箱"],
    "無能": [r"無能力者"],
    "支那": [r"支那そば", r"支那料理"],  # 料理名は許容
    "殺す活用": [r"必殺", r"殺到", r"殺風景", r"殺気", r"相殺", r"抹殺"],
    "殺し〜": [r"必殺", r"殺到", r"殺風景", r"殺気", r"相殺", r"抹殺"],
    "殺され": [r"必殺", r"殺到", r"殺風景", r"殺気", r"相殺", r"抹殺"],
}

# 死の誤検知除外（複合語として許容するパターン）
L4_FP_DEATH = [
    r"必死", r"決死", r"九死", r"瀕死", r"致死", r"生死",
    r"起死", r"活死", r"死角", r"死力", r"死中", r"死地",
    r"死後の世界", r"死語", r"死線", r"死球", r"死蔵",
    r"死海", r"死活",
]

# =============================================================
# L2: 差別的トロープパターン (正規表現)
# =============================================================
L2_PATTERNS = [
    {"group": "民族/劣等主張", "pat": r"(朝鮮人?|韓国人?|中国人?|黒人|白人|[ァ-ヴ]+人)[はがも].{0,10}(劣|低い|低能|馬鹿|アホ|下等|未開)"},
    {"group": "非人間化/動物", "pat": r"(朝鮮人?|韓国人?|中国人?|黒人|女|男|障害者?)[はがも].{0,10}(ゴキブリ|虫|害虫|寄生虫|豚|犬|猿|ネズミ|病気)"},
    {"group": "非人間化/病気", "pat": r"(朝鮮人?|韓国人?|中国人?|黒人|女|障害者?)[はがも].{0,10}(病気|異常|欠陥|狂)"},
    {"group": "優位性主張", "pat": r"(日本人?|大和民族|白人)[はがの].{0,10}(優れ|優秀|上等|至上|最高)"},
    {"group": "女性蔑視", "pat": r"女[はがの].{0,10}(劣|低い|馬鹿|アホ|感情的|論理的.{0,3}ない)"},
    {"group": "障害者蔑視", "pat": r"障害者?[はがの].{0,10}(役立たず|負担|排除|不要|邪魔)"},
    {"group": "排除主張", "pat": r"(朝鮮人?|韓国人?|中国人?|外国人?)[はを].{0,10}(追い出|出ていけ|帰れ|排除)"},
]

# =============================================================
# L3: 悪意ある表現パターン
# =============================================================
L3_PATTERNS = [
    {"cat": "暴力称賛", "pat": r"(殺し|虐殺|処刑|攻撃).{0,10}(正しかった|仕方ない|当然|よかった|最高)"},
    {"cat": "暴力称賛", "pat": r"(起こって|死んで|殺されて).{0,5}(よかった|嬉しい|ざまあ)"},
    {"cat": "非人間化", "pat": r"(人間じゃない|人間以下|人外|獣|亜人)"},
    {"cat": "排除正当化", "pat": r"(出ていけ|帰れ|消えろ|排斥|隔離).{0,5}(すべき|しろ|べき)"},
    {"cat": "陰謀論", "pat": r"(ユダヤ|在日|フリーメイソン).{0,10}(支配|陰謀|操って)"},
]

# =============================================================
# L5: 辞書外マニュアル検知
# =============================================================
L5_A_INSULTS = [
    ("性格終わってる", "🟡"), ("性格悪", "🟡"), ("ろくでもない", "🟡"),
    ("チンケ", "🟡"), ("ショボ", "🟡"), ("ダサ", "🟡"), ("ウザ", "🟡"),
    ("キモ", "🟡"), ("タヌキ親父", "🟡"), ("小物", "🟡"),
    ("老害", "🟡"), ("老害化", "🟡"),       # 年齢差別（エイジズム）
    ("老いぼれ", "🟡"),                      # 年齢差別
    ("金柑頭", "🟡"),                        # 身体侮辱（ハゲいじり）
    ("キンカン頭", "🟡"),                    # 身体侮辱（カナ表記）
    ("陰キャ", "🟡"),                        # 侮辱
    ("陽キャ", "⚪"),                         # 監視のみ
    ("頭おかしい", "🟡"),                    # 侮辱
    ("マジキチ", "🔴"),                      # 精神障害蔑称派生
    ("ゴミ人間", "🔴"),                      # 非人間化
    ("人間以下", "🔴"),                      # 非人間化
    ("クズの極み", "🔴"),                    # 極度の侮辱
]
L5_B_GENDER = [
    (r"女性は.{1,10}(劣|低い|感情的|論理的.{0,3}ない)", "🔴"),
    (r"好きな女やる", "🟡"),
    (r"孕ませ", "🟡"),
    (r"身ごもらせて返却", "🟡"),
]
L5_C_ETHNIC = [
    (r"朝鮮.{0,5}(汚|臭|嫌|キモ|消え)", "🔴"),
    (r"蝦夷.{0,5}(野蛮|未開|土人)", "🔴"),
]
L5_D_YOUTUBE_AI = [
    (r"ﾊﾞｷｰ|ﾊﾞｷﾊﾞｷ", "🟡"),  # 暴力擬音
    (r"オラオラ[ァ！]", "🟡"),   # 威圧叫び
    (r"ごおおお", "🟡"),          # 威圧叫び
]

# =============================================================
# 伏字検知パターン
# =============================================================
CENSORED_PATTERNS = [
    r"ガ[〇○]ジ", r"ホ[〇○]", r"ク[〇○]", r"ア[〇○]", r"バ[〇○]",
    r"デ[〇○]", r"キ[〇○]", r"[〇○]にかけ", r"[〇○]んだ",
    r"[〇○]した", r"[〇○]してえ", r"カッ[〇○]", r"ﾊﾅｸ[〇○]",
    r"撃[〇○]", r"味方撃[〇○]",
    r"[\w][〇○◯●■□][\w]?",  # 汎用パターン
    r"[〇○◯●■□]",            # 単独の伏字文字
]


def check_fp(word, context):
    """L4: 誤検知チェック"""
    # 通常の誤検知除外
    if word in L4_FP:
        for fp_pat in L4_FP[word]:
            if re.search(fp_pat, context):
                return True
    # 死関連の特別誤検知除外
    if "死" in word or word.startswith("死") or "CH固有禁止/死" in word:
        for fp_pat in L4_FP_DEATH:
            if re.search(fp_pat, context):
                return True
    return False


def scan_l1(text):
    """L1: NGワード直接マッチ（正規表現対応）"""
    hits = []
    seen_positions = set()  # 同じ位置の重複ヒットを防ぐ
    for entry in L1_WORDS:
        pat = entry["pat"]
        try:
            for m in re.finditer(pat, text):
                pos_key = f"{m.start()}:{m.end()}"
                # 同じ位置で既により長いマッチがあればスキップ
                if pos_key in seen_positions:
                    continue
                ctx_s = max(0, m.start() - 20)
                ctx_e = min(len(text), m.end() + 20)
                ctx = text[ctx_s:ctx_e].replace('\n', ' ')
                # 誤検知チェック
                is_fp = check_fp(entry["word"], ctx)
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


def scan_l2(text):
    """L2: 差別的トロープ"""
    hits = []
    for entry in L2_PATTERNS:
        try:
            for m in re.finditer(entry["pat"], text):
                ctx_s = max(0, m.start() - 20)
                ctx_e = min(len(text), m.end() + 20)
                hits.append({
                    "group": entry["group"], "matched": m.group(),
                    "severity": "🔴",
                    "context": text[ctx_s:ctx_e].replace('\n', ' ')
                })
        except:
            pass
    return hits


def scan_l3(text):
    """L3: 悪意ある表現"""
    hits = []
    for entry in L3_PATTERNS:
        try:
            for m in re.finditer(entry["pat"], text):
                ctx_s = max(0, m.start() - 20)
                ctx_e = min(len(text), m.end() + 20)
                hits.append({
                    "category": entry["cat"], "matched": m.group(),
                    "severity": "🔴",
                    "context": text[ctx_s:ctx_e].replace('\n', ' ')
                })
        except:
            pass
    return hits


def scan_l5(text):
    """L5: 辞書外マニュアル検知"""
    hits = []
    # Layer A: 侮辱
    for word, sev in L5_A_INSULTS:
        for m in re.finditer(re.escape(word), text):
            ctx_s = max(0, m.start() - 20)
            ctx_e = min(len(text), m.end() + 20)
            hits.append({
                "layer": "A_侮辱", "word": word, "matched": word,
                "severity": sev,
                "context": text[ctx_s:ctx_e].replace('\n', ' ')
            })
    # Layer B: ジェンダー
    for pat, sev in L5_B_GENDER:
        for m in re.finditer(pat, text):
            ctx_s = max(0, m.start() - 20)
            ctx_e = min(len(text), m.end() + 20)
            hits.append({
                "layer": "B_ジェンダー", "word": pat, "matched": m.group(),
                "severity": sev,
                "context": text[ctx_s:ctx_e].replace('\n', ' ')
            })
    # Layer C: 民族
    for pat, sev in L5_C_ETHNIC:
        for m in re.finditer(pat, text):
            ctx_s = max(0, m.start() - 20)
            ctx_e = min(len(text), m.end() + 20)
            hits.append({
                "layer": "C_民族", "word": pat, "matched": m.group(),
                "severity": sev,
                "context": text[ctx_s:ctx_e].replace('\n', ' ')
            })
    # Layer D: YouTube AI
    for pat, sev in L5_D_YOUTUBE_AI:
        for m in re.finditer(pat, text):
            ctx_s = max(0, m.start() - 20)
            ctx_e = min(len(text), m.end() + 20)
            hits.append({
                "layer": "D_YouTube_AI", "word": pat, "matched": m.group(),
                "severity": sev,
                "context": text[ctx_s:ctx_e].replace('\n', ' ')
            })
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


def scan_censored(text):
    """伏字チェック"""
    hits = []
    seen = set()
    for pat in CENSORED_PATTERNS:
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
                if '台詞' in h:
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

    dialogues = read_csv(sys.argv[1])
    if not dialogues:
        print(json.dumps({"error": "有効な台詞データが見つかりません"}))
        sys.exit(1)

    full_text = "\n".join(dialogues)

    # 8層スキャン
    l1 = scan_l1(full_text)
    l2 = scan_l2(full_text)
    l3 = scan_l3(full_text)
    l5 = scan_l5(full_text)
    l6 = scan_l6(l1 + l5)
    censored = scan_censored(full_text)

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
