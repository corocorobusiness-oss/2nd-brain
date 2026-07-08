#!/usr/bin/env python3
"""動画別の収益単価（RPM）× 平均視聴時間の分析。

YouTube Analytics API から動画ごとの views / estimatedRevenue /
averageViewDuration を取得し、「平均視聴X分の動画は1000再生あたり¥いくら稼ぐか」
を集計する。尺・台本文字数の設計判断（台本執筆ルールR4）の収益裏付けに使う。

必要スコープ: yt-analytics-monetary.readonly（fetch_daily.py と同じ token_2ch.json でOK）

Usage:
  python3 analyze_rpm.py                # 全期間・再生1,000以上
  python3 analyze_rpm.py --days 180     # 直近180日に公開した動画のみ
  python3 analyze_rpm.py --min-views 500
"""
import argparse
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CONFIG = Path.home() / ".config" / "youtube-revenue"
TOKEN_PATH = CONFIG / "token_2ch.json"
CS_PATH = CONFIG / "client_secret.json"
OUT_PATH = DATA / "rpm_analysis.json"
RATE = 150  # USD -> JPY（fetch_daily.py と同一レート）


def access_token():
    tok = json.load(open(TOKEN_PATH))
    cs = json.load(open(CS_PATH))
    key = cs.get("installed", cs.get("web"))
    data = urllib.parse.urlencode({
        "client_id": tok.get("client_id") or key["client_id"],
        "client_secret": tok.get("client_secret") or key["client_secret"],
        "refresh_token": tok["refresh_token"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as r:
        return json.load(r)["access_token"]


def fetch_per_video(at):
    """動画別の views / 収益 / 平均視聴時間（上位200本）"""
    params = urllib.parse.urlencode({
        "ids": "channel==MINE", "startDate": "2023-01-01", "endDate": "2030-01-01",
        "metrics": "views,estimatedRevenue,estimatedMinutesWatched,averageViewDuration",
        "dimensions": "video", "sort": "-views", "maxResults": 200})
    req = urllib.request.Request(
        f"https://youtubeanalytics.googleapis.com/v2/reports?{params}",
        headers={"Authorization": f"Bearer {at}"})
    with urllib.request.urlopen(req) as r:
        res = json.load(r)
    cols = [c["name"] for c in res.get("columnHeaders", [])]
    if "estimatedRevenue" not in cols:
        raise SystemExit("estimatedRevenue が返ってこない。token_2ch.json のスコープに "
                         "yt-analytics-monetary.readonly が必要（reauth.py で再認証）")
    return [dict(zip(cols, row)) for row in res.get("rows", [])]


def iso_minutes(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return (h * 3600 + mi * 60 + s) / 60


def band(avg_min):
    if avg_min < 8: return "〜8分"
    if avg_min < 9: return "8〜9分"
    if avg_min < 10: return "9〜10分"
    if avg_min < 11: return "10〜11分"
    return "11分〜"


BAND_ORDER = ["〜8分", "8〜9分", "9〜10分", "10〜11分", "11分〜"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="直近N日に公開した動画に限定（0=全期間）")
    ap.add_argument("--min-views", type=int, default=1000)
    args = ap.parse_args()

    meta = {v["id"]: v for v in json.loads((DATA / "channel_videos.json").read_text())}
    at = access_token()
    rows = fetch_per_video(at)

    cutoff = ""
    if args.days:
        cutoff = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    videos = []
    for r in rows:
        v = meta.get(r["video"])
        views = int(r["views"])
        if views < args.min_views:
            continue
        published = (v or {}).get("published", "")[:10]
        if cutoff and published and published < cutoff:
            continue
        rev_usd = float(r["estimatedRevenue"])
        avg_min = float(r["averageViewDuration"]) / 60
        videos.append({
            "id": r["video"],
            "title": (v or {}).get("title", "(channel_videos.json未収載)")[:50],
            "published": published,
            "duration_min": round(iso_minutes((v or {}).get("duration")), 1) if v else None,
            "views": views,
            "revenue_usd": round(rev_usd, 2),
            "avg_view_min": round(avg_min, 2),
            "rpm_jpy": round(rev_usd / views * 1000 * RATE),
            "band": band(avg_min),
        })

    videos.sort(key=lambda x: x["avg_view_min"])
    print(f"{'平均視聴':>7} {'尺(分)':>6} {'RPM¥':>6} {'再生':>8} {'収益$':>8}  タイトル")
    for x in videos:
        d = f"{x['duration_min']:.1f}" if x["duration_min"] else "  —"
        print(f"{x['avg_view_min']:6.2f}分 {d:>6} {x['rpm_jpy']:6,} {x['views']:8,} "
              f"{x['revenue_usd']:8.2f}  {x['title'][:30]}")

    # 平均視聴時間の帯ごとの集計（本数・RPM中央値/平均・収益シェア）
    total_rev = sum(x["revenue_usd"] for x in videos) or 1
    print(f"\n== 平均視聴時間帯ごとのRPM（{len(videos)}本・再生{args.min_views:,}以上）==")
    print(f"{'帯':>6} {'本数':>4} {'RPM中央値':>9} {'RPM平均':>8} {'収益シェア':>8}")
    summary = {}
    for b in BAND_ORDER:
        xs = [x for x in videos if x["band"] == b]
        if not xs:
            continue
        rpms = sorted(x["rpm_jpy"] for x in xs)
        med = rpms[len(rpms) // 2]
        mean = sum(rpms) / len(rpms)
        share = sum(x["revenue_usd"] for x in xs) / total_rev
        summary[b] = {"n": len(xs), "rpm_median_jpy": med,
                      "rpm_mean_jpy": round(mean), "revenue_share": round(share, 3)}
        print(f"{b:>6} {len(xs):4d} {med:8,}円 {mean:7,.0f}円 {share:7.1%}")

    OUT_PATH.write_text(json.dumps(
        {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
         "rate_usd_jpy": RATE, "min_views": args.min_views, "days": args.days,
         "bands": summary, "videos": videos},
        ensure_ascii=False, indent=2))
    print(f"\n{len(videos)}本を {OUT_PATH} に保存")


if __name__ == "__main__":
    main()
