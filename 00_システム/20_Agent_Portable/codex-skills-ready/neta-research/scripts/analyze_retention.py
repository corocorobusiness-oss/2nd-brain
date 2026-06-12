#!/usr/bin/env python3
"""動画の視聴維持率（離脱ポイント）分析。

YouTube Analytics API の audienceWatchRatio を動画ごとに取得し、
どの区間（動画の何%地点）で離脱が大きいかを検出する。
台本構成（冒頭→解説→スレ→締め）の改善材料に使う。

Usage:
  python3 analyze_retention.py            # 直近90日の動画を分析
  python3 analyze_retention.py VIDEO_ID   # 特定動画
"""
import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path

DATA = Path("/Users/kabushikikaishakorokoro/.codex/skills/neta-research/data")
TOKEN_PATH = "/Users/kabushikikaishakorokoro/.config/youtube-revenue/token_2ch.json"
CS_PATH = "/Users/kabushikikaishakorokoro/.config/youtube-revenue/client_secret.json"
OUT_PATH = DATA / "retention_analysis.json"


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


def retention_curve(at, video_id):
    """elapsedVideoTimeRatio(0-1) → audienceWatchRatio のカーブを取得"""
    params = urllib.parse.urlencode({
        "ids": "channel==MINE", "startDate": "2024-01-01", "endDate": "2030-01-01",
        "metrics": "audienceWatchRatio",
        "dimensions": "elapsedVideoTimeRatio",
        "filters": f"video=={video_id}"})
    req = urllib.request.Request(
        f"https://youtubeanalytics.googleapis.com/v2/reports?{params}",
        headers={"Authorization": f"Bearer {at}"})
    with urllib.request.urlopen(req) as r:
        rows = json.load(r).get("rows", [])
    return [(float(a), float(b)) for a, b in rows]


def analyze(curve):
    """カーブから要約指標と離脱急増ポイントを抽出"""
    if not curve:
        return None
    # 区間ごとの落ち幅（前区間比）
    drops = []
    for i in range(1, len(curve)):
        pos, ratio = curve[i]
        prev = curve[i - 1][1]
        drops.append((pos, prev - ratio))
    drops.sort(key=lambda x: -x[1])
    seg = lambda lo, hi: [r for p, r in curve if lo <= p < hi]
    avg = lambda xs: sum(xs) / len(xs) if xs else 0
    return {
        "intro_hold": round(avg(seg(0.0, 0.05)), 3),     # 冒頭5%の維持
        "q1": round(avg(seg(0.0, 0.25)), 3),
        "q2": round(avg(seg(0.25, 0.5)), 3),
        "q3": round(avg(seg(0.5, 0.75)), 3),
        "q4": round(avg(seg(0.75, 1.0)), 3),
        "worst_drops": [{"at_percent": round(p * 100), "drop": round(d, 3)}
                        for p, d in drops[:3] if d > 0],
    }


def main():
    at = access_token()
    videos = json.loads((DATA / "channel_videos.json").read_text())

    if len(sys.argv) > 1:
        targets = [v for v in videos if v["id"] == sys.argv[1]]
    else:
        # 直近90日 + 再生数1,000以上（ノイズ回避）
        targets = [v for v in videos
                   if v["published"] >= "2026-03-08" and int(v["views"]) >= 1000]

    results = []
    for v in sorted(targets, key=lambda x: -int(x["views"])):
        curve = retention_curve(at, v["id"])
        a = analyze(curve)
        if not a:
            continue
        a.update({"id": v["id"], "title": v["title"][:50],
                  "views": int(v["views"]), "published": v["published"][:10]})
        results.append(a)
        print(f"{v['views']:>8,} | 冒頭{a['intro_hold']*100:3.0f}% | "
              f"Q1 {a['q1']*100:3.0f}% Q2 {a['q2']*100:3.0f}% "
              f"Q3 {a['q3']*100:3.0f}% Q4 {a['q4']*100:3.0f}% | "
              f"最大離脱: {a['worst_drops'][0]['at_percent'] if a['worst_drops'] else '-'}%地点 | "
              f"{v['title'][:32]}")

    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n{len(results)}本を {OUT_PATH} に保存")


if __name__ == "__main__":
    main()
