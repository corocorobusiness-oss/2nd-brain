#!/usr/bin/env python3
"""Predict view count for a proposed neta title using feature_db.json.

Usage:
  python predict_score.py                         # scores existing stock sheet
  python predict_score.py "タイトル候補www"      # scores a single title
  python predict_score.py --stdin                 # reads titles from stdin, one per line

Combines era × category × title-pattern × hype-word means, then applies
boosters (大河連動, Google Trends rising, seasonal) if provided via CLI flags.
"""
import json
import re
import sys
import argparse
from pathlib import Path
from statistics import mean

DATA = Path("/Users/kabushikikaishakorokoro/.codex/skills/neta-research/data")
DB_PATH = DATA / "feature_db.json"

# Re-import feature extractors from build_feature_db.py
sys.path.insert(0, str(Path(__file__).parent))
from build_feature_db import (
    extract_era, extract_ng, extract_categories, extract_title_patterns,
    extract_hype, extract_subjects, NG_KEYWORDS, FAME_S, FAME_MINOR,
)


def load_db():
    return json.loads(DB_PATH.read_text())


def score_title(title: str, db: dict, taiga_linked: bool = False,
                trend_boost: bool = False, seasonal_boost: bool = False) -> dict:
    """Return prediction dict for a given title.

    Strategy:
      1. Check NG (modern war / world history) → reject.
      2. Pull expected views for each matched feature (era, category, pattern, hype).
      3. Combine via weighted mean: era 35%, category 25%, pattern 25%, hype 15%.
         If any feature has n<3 or is unknown, fall back to overall median.
      4. Apply boosters multiplicatively.
      5. Estimate 10k+ probability from empirical over_10k_rate of matched features.
    """
    t = title
    ng = extract_ng(t)
    if ng:
        return {"title": t, "reject": True, "reason": f"NG: {','.join(ng)}",
                "predicted_views": 0, "over_10k_prob": 0.0, "rank": "X"}

    era = extract_era(t)
    cats = extract_categories(t)
    patterns = extract_title_patterns(t)
    hypes = extract_hype(t)
    subjects = extract_subjects(t)

    overall_mean = db["overall"]["mean"]
    overall_p75 = db["overall"]["p75"]

    def lookup(bucket, key):
        v = db.get(bucket, {}).get(key)
        if v and v["n"] >= 3:
            return v["mean"], v["over_10k_rate"]
        return None

    # Prefer era×category combined stat if available (more specific)
    era_cat_key = f"{era}×{cats[0]}" if cats else era
    era_cat_hit = lookup("by_era_category", era_cat_key)

    era_hit = lookup("by_era", era)
    cat_hits = [lookup("by_category", c) for c in cats]
    cat_hits = [x for x in cat_hits if x]
    pat_hits = [lookup("by_title_pattern", p) for p in patterns]
    pat_hits = [x for x in pat_hits if x]
    hype_hits = [lookup("by_hype_word", w) for w in hypes]
    hype_hits = [x for x in hype_hits if x]

    components = []
    breakdown = {}
    if era_cat_hit:
        components.append((era_cat_hit[0], 0.45, f"{era_cat_key}={era_cat_hit[0]:,}"))
        breakdown["era_category"] = era_cat_hit[0]
    else:
        if era_hit:
            components.append((era_hit[0], 0.30, f"era:{era}={era_hit[0]:,}"))
            breakdown["era"] = era_hit[0]
        if cat_hits:
            avg = int(mean(c[0] for c in cat_hits))
            components.append((avg, 0.20, f"cat:{'/'.join(cats)}={avg:,}"))
            breakdown["category"] = avg

    if pat_hits:
        avg = int(mean(p[0] for p in pat_hits))
        components.append((avg, 0.25, f"pat:{'/'.join(patterns)}={avg:,}"))
        breakdown["title_pattern"] = avg
    if hype_hits:
        avg = int(mean(h[0] for h in hype_hits))
        components.append((avg, 0.10, f"hype:{'/'.join(hypes)}={avg:,}"))
        breakdown["hype_words"] = avg

    # Subject (person/event) component — strongest single predictor (2026-06-04 backtest).
    # n>=2 allowed because subjects repeat less than eras/categories.
    subj_hits = []
    for s in subjects:
        v = db.get("by_subject", {}).get(s)
        if v and v["n"] >= 2:
            subj_hits.append((s, v["mean"], v["over_10k_rate"]))
    if subj_hits:
        avg = int(mean(h[1] for h in subj_hits))
        components.append((avg, 0.40, f"subj:{'/'.join(h[0] for h in subj_hits)}={avg:,}"))
        breakdown["subject"] = avg

    if not components:
        base = overall_mean
        rationale = [f"no feature match → overall mean {overall_mean:,}"]
    else:
        total_w = sum(w for _, w, _ in components)
        base = int(sum(v * w for v, w, _ in components) / total_w)
        rationale = [r for _, _, r in components]

    # Fame-tier fallback: no per-subject data → use knowledge-based tier
    fame_mult = 1.0
    if not subj_hits:
        if any(kw in t for kw in FAME_S):
            fame_mult = 1.25
        elif any(kw in t for kw in FAME_MINOR):
            fame_mult = 0.75
    base = int(base * fame_mult)

    # Dead-feature penalty: a matched category/pattern with n>=3 that has NEVER
    # hit 10k (打線・if系・もし系 etc.) drags the whole title down hard.
    dead = []
    for bucket, keys in (("by_category", cats), ("by_title_pattern", patterns)):
        for k in keys:
            v = db.get(bucket, {}).get(k)
            if v and v.get("n", 0) >= 3 and v.get("over_10k_rate", 1) == 0:
                dead.append(k)
    if dead:
        base = int(base * 0.45)

    # Boosters
    predicted = base
    boost_applied = []
    if fame_mult != 1.0:
        boost_applied.append(f"知名度×{fame_mult}")
    if dead:
        boost_applied.append(f"死筋ペナルティ×0.45({'/'.join(dead)})")
    if taiga_linked:
        predicted = int(predicted * 1.6)
        boost_applied.append("大河連動×1.6")
    if trend_boost:
        predicted = int(predicted * 1.3)
        boost_applied.append("トレンド×1.3")
    if seasonal_boost:
        predicted = int(predicted * 1.2)
        boost_applied.append("季節×1.2")

    # 10k+ probability: blend empirical rates of matched features
    over_rates = []
    if era_cat_hit:
        over_rates.append(era_cat_hit[1])
    if era_hit:
        over_rates.append(era_hit[1])
    for c in cat_hits:
        over_rates.append(c[1])
    for p in pat_hits:
        over_rates.append(p[1])
    # subject rate counts double (strongest signal)
    for s in subj_hits:
        over_rates.extend([s[2], s[2]])
    prob = mean(over_rates) if over_rates else 0.25
    if dead:
        prob = min(prob, 0.15)
    # predicted_views sanity: if way above 10k, push prob up
    if predicted >= 30000:
        prob = min(0.95, prob + 0.25)
    elif predicted >= 10000:
        prob = min(0.90, prob + 0.15)
    elif predicted < 5000:
        prob = max(0.05, prob - 0.15)

    # Rank
    if predicted >= 50000 or (predicted >= 20000 and prob >= 0.5):
        rank = "S"
    elif predicted >= 15000 or prob >= 0.5:
        rank = "A"
    elif predicted >= 7000 or prob >= 0.3:
        rank = "B"
    else:
        rank = "C"

    return {
        "title": t,
        "era": era, "categories": cats, "patterns": patterns, "hypes": hypes,
        "predicted_views": predicted,
        "over_10k_prob": round(prob, 3),
        "rank": rank,
        "rationale": " / ".join(rationale + boost_applied),
        "breakdown": breakdown,
        "boost": boost_applied,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title", nargs="?")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--taiga", action="store_true", help="大河連動ブースター")
    ap.add_argument("--trend", action="store_true", help="トレンドブースター")
    ap.add_argument("--season", action="store_true", help="季節ブースター")
    args = ap.parse_args()

    db = load_db()

    titles = []
    if args.stdin:
        titles = [ln.strip() for ln in sys.stdin if ln.strip()]
    elif args.title:
        titles = [args.title]
    else:
        print("Usage: predict_score.py <title>  |  --stdin", file=sys.stderr)
        sys.exit(2)

    for t in titles:
        r = score_title(t, db, args.taiga, args.trend, args.season)
        if r.get("reject"):
            print(f"❌ REJECT: {t}  ({r['reason']})")
        else:
            print(f"[{r['rank']}] pred={r['predicted_views']:>7,}  p10k={r['over_10k_prob']*100:4.1f}%  "
                  f"{r['era']:8s}/{'+'.join(r['categories'])[:15]:15s}  {t}")
            print(f"       → {r['rationale']}")


if __name__ == "__main__":
    main()
