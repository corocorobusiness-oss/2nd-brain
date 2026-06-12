#!/usr/bin/env python3
"""Build feature DB from channel_videos.json.

Extracts features per video (era, category, title-pattern, keywords) and computes
per-feature view-count statistics. Outputs feature_db.json used by predict_score.py.
"""
import json
import re
import statistics
from pathlib import Path
from collections import defaultdict

DATA = Path("/Users/kabushikikaishakorokoro/.codex/skills/neta-research/data")
SRC = DATA / "channel_videos.json"
OUT = DATA / "feature_db.json"

# --- Feature extraction ---

ERA_KEYWORDS = {
    "縄文": ["縄文", "弥生", "卑弥呼", "邪馬台国"],
    "飛鳥奈良": ["聖徳太子", "蘇我", "大化", "天智", "天武", "壬申", "藤原不比等", "奈良", "平城京", "大仏"],
    "平安": ["平安", "藤原道長", "源氏物語", "紫式部", "清少納言", "平将門", "菅原道真", "陰陽師", "安倍晴明", "摂関", "院政"],
    "鎌倉": ["源頼朝", "北条", "元寇", "鎌倉", "承久", "執権", "源義経", "源範頼", "後鳥羽"],
    "室町": ["足利", "応仁", "一休", "室町", "南北朝", "建武", "後醍醐", "北山", "東山"],
    "戦国": ["信長", "秀吉", "家康", "武田", "上杉", "毛利", "長宗我部", "島津", "伊達政宗", "真田",
            "明智", "浅井", "朝倉", "斎藤", "織田", "豊臣", "徳川", "本能寺", "関ヶ原", "小谷",
            "比叡山", "三好", "足利義昭", "石田三成", "大谷吉継", "直江", "前田", "柴田", "丹羽",
            "黒田", "加藤清正", "福島正則", "戦国", "信玄", "謙信", "秀長", "宮部", "京極"],
    "江戸": ["徳川", "将軍", "赤穂", "吉良", "忠臣蔵", "鎖国", "大奥", "江戸", "綱吉", "吉宗",
            "田沼", "松平", "水戸", "生類憐み", "参勤交代", "吉原", "切腹", "新井白石", "家光"],
    "幕末": ["幕末", "坂本龍馬", "新選組", "土方", "近藤", "沖田", "黒船", "ペリー", "西郷",
            "大久保", "勝海舟", "吉田松陰", "高杉", "桂小五郎", "岩倉", "戊辰", "会津", "鳥羽伏見",
            "薩摩", "長州", "土佐", "桜田門", "安政"],
}

# NG: modern war / world history tags (for filtering)
NG_KEYWORDS = {
    "近代戦争": ["太平洋戦争", "日露", "日清", "ノルマンディー", "硫黄島", "特攻", "栗林", "東郷", "乃木", "203高地",
                "ミッドウェー", "バルジ", "ヒトラー", "スターリン", "真珠湾"],
    "世界史": ["三国志", "ローマ", "エジプト", "モンゴル", "シュメール", "ナポレオン", "フランス革命", "英仏"],
}

CATEGORY_KEYWORDS = {
    "if系": ["もし", "if", "たら", "だったら", "いれば"],
    "打線": ["打線", "で組ん", "ランキング", "ベスト", "ワースト"],
    "闇・裏話": ["闇", "裏", "ヤバ", "やばい", "狂", "地獄", "恐怖", "怖い", "残虐", "真実", "教科書に載"],
    "再評価": ["過大評価", "過小評価", "実は", "ガチで", "再評価", "無能", "有能", "じゃね", "〇〇説", "だった説"],
    "戦争・合戦": ["戦", "合戦", "の変", "城", "落城", "攻め", "征伐", "包囲", "焼き討ち", "侵攻", "防衛"],
    "人物": ["とかいう", "←こいつ", "←この人", "の生涯", "の最期", "って結局"],
    "文化・制度": ["雑学", "生活", "食事", "結婚", "恋愛", "給料", "制度", "風習", "文化"],
    "比較": ["vs", "VS", "どっち", "比較", "比べ"],
}

# Title patterns (tail-based)
TITLE_PATTERNS = [
    ("www/草系", re.compile(r"(www|WWW|草|ｗｗｗ|w$)")),
    ("〜じゃね/なんや", re.compile(r"(じゃね|なんや|なんや？|やろ|説\?|説？)")),
    ("〇〇とかいう△△", re.compile(r"とかいう")),
    ("←こいつ", re.compile(r"[←⇐]こいつ|←この")),
    ("〜件/〜件www", re.compile(r"件(www)?|件$")),
    ("もし系", re.compile(r"もし.*(たら|だったら|いれば|場合)")),
    ("打線/ランキング", re.compile(r"(打線|ランキング|ベスト|ワースト)")),
    ("雑学シリーズ", re.compile(r"雑学で.*面白くなり")),
    ("〜の真実/〜の闇", re.compile(r"真実|闇[がをに]")),
]

# Subject (person/event) keywords — fame is the strongest single predictor
# (2026-06-04 backtest: model missed 秀吉/関ヶ原 hits and overshot minor figures)
SUBJECT_KEYWORDS = {
    "豊臣秀吉": ["秀吉"],
    "豊臣秀長": ["秀長"],
    "織田信長": ["信長"],
    "徳川家康": ["家康"],
    "武田信玄": ["信玄", "武田"],
    "上杉謙信": ["謙信", "上杉"],
    "明智光秀": ["光秀", "明智"],
    "黒田官兵衛": ["官兵衛", "黒田"],
    "竹中半兵衛": ["半兵衛"],
    "伊達政宗": ["政宗", "伊達"],
    "真田": ["真田"],
    "石田三成": ["三成"],
    "柴田勝家": ["勝家", "柴田"],
    "浅井長政": ["長政", "浅井"],
    "毛利元就": ["毛利"],
    "お市の方": ["お市"],
    "卑弥呼": ["卑弥呼", "邪馬台国"],
    "聖徳太子": ["聖徳太子"],
    "坂本龍馬": ["龍馬"],
    "新選組": ["新選組", "土方", "沖田", "近藤勇"],
    "西郷隆盛": ["西郷"],
    "源頼朝": ["頼朝"],
    "源義経": ["義経"],
    "北条": ["北条"],
    "平将門": ["将門"],
    "藤原道長": ["道長"],
    "関ヶ原": ["関ヶ原"],
    "本能寺": ["本能寺"],
    "縄文人": ["縄文"],
}

# Knowledge-based fame tier fallback (used by predict_score when no per-subject data)
FAME_S = ["信長", "秀吉", "家康", "関ヶ原", "本能寺", "卑弥呼", "聖徳太子", "龍馬",
          "新選組", "義経", "信玄", "謙信", "縄文"]
FAME_MINOR = ["宮部", "京極", "大谷吉継", "直江", "丹羽", "新井白石", "三好", "斎藤",
              "朝倉", "長宗我部", "福島正則", "加藤清正", "半兵衛"]

# Hype words that correlate with views
HYPE_WORDS = [
    "ヤバ", "やば", "ガチ", "地獄", "闇", "狂", "凄", "すご", "絶", "最強", "最弱", "最恐",
    "草", "神", "無能", "有能", "過大", "過小", "真実", "本当", "実は", "謎", "衝撃",
    "まさか", "まじ", "あり得", "ありえ", "想像を絶", "現代じゃ", "教科書",
]


def extract_era(title: str) -> str:
    for era, kws in ERA_KEYWORDS.items():
        if any(kw in title for kw in kws):
            return era
    return "その他"


def extract_ng(title: str) -> list[str]:
    tags = []
    for tag, kws in NG_KEYWORDS.items():
        if any(kw in title for kw in kws):
            tags.append(tag)
    return tags


def extract_categories(title: str) -> list[str]:
    tags = []
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in title for kw in kws):
            tags.append(cat)
    return tags or ["その他"]


def extract_title_patterns(title: str) -> list[str]:
    tags = []
    for name, pat in TITLE_PATTERNS:
        if pat.search(title):
            tags.append(name)
    return tags or ["無パターン"]


def extract_hype(title: str) -> list[str]:
    return [w for w in HYPE_WORDS if w in title]


def extract_subjects(title: str) -> list[str]:
    return [s for s, kws in SUBJECT_KEYWORDS.items() if any(kw in title for kw in kws)]


def stats(values: list[int]) -> dict:
    if not values:
        return {"n": 0}
    v = sorted(values)
    n = len(v)
    return {
        "n": n,
        "mean": int(statistics.mean(v)),
        "median": v[n // 2],
        "max": max(v),
        "min": min(v),
        "p25": v[n // 4],
        "p75": v[3 * n // 4],
        "over_10k_rate": round(sum(1 for x in v if x >= 10000) / n, 3),
    }


def main():
    videos = json.loads(SRC.read_text())
    print(f"Loaded {len(videos)} videos")

    # Enrich each video
    for v in videos:
        t = v["title"]
        v["era"] = extract_era(t)
        v["ng_tags"] = extract_ng(t)
        v["categories"] = extract_categories(t)
        v["title_patterns"] = extract_title_patterns(t)
        v["hype_words"] = extract_hype(t)
        v["subjects"] = extract_subjects(t)

    # Aggregate
    by_era = defaultdict(list)
    by_category = defaultdict(list)
    by_pattern = defaultdict(list)
    by_hype = defaultdict(list)
    by_era_category = defaultdict(list)
    by_subject = defaultdict(list)

    for v in videos:
        by_era[v["era"]].append(v["views"])
        for c in v["categories"]:
            by_category[c].append(v["views"])
        for p in v["title_patterns"]:
            by_pattern[p].append(v["views"])
        for w in v["hype_words"]:
            by_hype[w].append(v["views"])
        for c in v["categories"]:
            by_era_category[f"{v['era']}×{c}"].append(v["views"])
        for s in v["subjects"]:
            by_subject[s].append(v["views"])

    db = {
        "overall": stats([v["views"] for v in videos]),
        "by_era": {k: stats(v) for k, v in by_era.items()},
        "by_category": {k: stats(v) for k, v in by_category.items()},
        "by_title_pattern": {k: stats(v) for k, v in by_pattern.items()},
        "by_hype_word": {k: stats(v) for k, v in by_hype.items() if len(v) >= 3},
        "by_era_category": {k: stats(v) for k, v in by_era_category.items() if len(v) >= 2},
        "by_subject": {k: stats(v) for k, v in by_subject.items() if len(v) >= 2},
        "video_count": len(videos),
        "videos_enriched": videos,
    }
    OUT.write_text(json.dumps(db, ensure_ascii=False, indent=2))
    print(f"Saved feature DB to {OUT}")

    print("\n=== TOP ERA ===")
    for era, s in sorted(db["by_era"].items(), key=lambda x: -x[1]["mean"]):
        print(f"  {era:8s} n={s['n']:3d}  mean={s['mean']:>7,}  median={s['median']:>6,}  10k+={s['over_10k_rate']*100:5.1f}%")
    print("\n=== TOP CATEGORY ===")
    for cat, s in sorted(db["by_category"].items(), key=lambda x: -x[1]["mean"]):
        print(f"  {cat:10s} n={s['n']:3d}  mean={s['mean']:>7,}  median={s['median']:>6,}  10k+={s['over_10k_rate']*100:5.1f}%")
    print("\n=== TOP TITLE PATTERN ===")
    for pat, s in sorted(db["by_title_pattern"].items(), key=lambda x: -x[1]["mean"]):
        print(f"  {pat:20s} n={s['n']:3d}  mean={s['mean']:>7,}  10k+={s['over_10k_rate']*100:5.1f}%")
    print("\n=== TOP HYPE WORDS (n>=3) ===")
    for w, s in sorted(db["by_hype_word"].items(), key=lambda x: -x[1]["mean"])[:15]:
        print(f"  {w:10s} n={s['n']:3d}  mean={s['mean']:>7,}  10k+={s['over_10k_rate']*100:5.1f}%")
    print("\n=== TOP SUBJECTS (n>=2) ===")
    for w, s in sorted(db["by_subject"].items(), key=lambda x: -x[1]["mean"]):
        print(f"  {w:10s} n={s['n']:3d}  mean={s['mean']:>7,}  10k+={s['over_10k_rate']*100:5.1f}%")


if __name__ == "__main__":
    main()
