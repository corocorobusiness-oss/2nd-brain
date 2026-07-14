#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""click-learning-loop 実測取得（Mac mini専用・YouTube Analytics API）

click_ledger.jsonl の publish 行に対し、公開7日窓と累計の実測
（views / videoThumbnailImpressions / videoThumbnailImpressionsClickRate / averageViewPercentage）
を type=stats 行として自動追記する。

- 認証: ~/.config/youtube-revenue/token_2ch.json（neta-forge subscriber_signal.py と同一）
- サムネ指標は 2026-01-15 にAnalytics API v2へ正式追加されたmetric。
  APIに拒否された場合は views,averageViewPercentage へフォールバックし、CTR手動転記待ちを警告する
- ⚠️ 初回はMac側で必ず `--dry-run`（この環境ではAPI実行未検証のため）
- READ ONLY against YouTube。書くのは click_ledger.jsonl への追記のみ

使い方:
  python3 fetch_click_stats.py --dry-run   # 取得内容を表示のみ
  python3 fetch_click_stats.py             # stats行を追記
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

SCHEMA = 1
JST_OFFSET = datetime.timedelta(hours=9)
ANALYTICS_LAG_DAYS = 3
DEFAULT_LEDGER = Path.home() / "Projects" / "youtube" / "eval" / "click_ledger.jsonl"
DEFAULT_TOKEN = Path.home() / ".config" / "youtube-revenue" / "token_2ch.json"
DEFAULT_VIDEOS = Path.home() / ".claude" / "skills" / "neta-research" / "data" / "channel_videos.json"
FULL_METRICS = "views,videoThumbnailImpressions,videoThumbnailImpressionsClickRate,averageViewPercentage"
FALLBACK_METRICS = "views,averageViewPercentage"


def norm(s):
    return re.sub(r"[\s　]+", "", s or "")


def load_ledger(path):
    pubs, stats_done, broken = [], set(), []
    if not Path(path).exists():
        return pubs, stats_done, broken
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                broken.append((i, str(e)[:50]))
                continue
            if r.get("type") == "publish":
                pubs.append(r)
            elif r.get("type") == "stats" and r.get("source") == "api":
                stats_done.add((r.get("folder"), r.get("window")))
    return pubs, stats_done, broken


def match_video(pub, videos):
    """channel_videos.json とタイトル/テーマ照合で video_id を解決"""
    t = norm(pub.get("title"))
    theme = norm(pub.get("theme"))
    for v in videos:
        vt = norm(v.get("title", ""))
        if t and (vt.startswith(t[:20]) or t.startswith(vt[:20])):
            return v
    for v in videos:
        if theme and theme in norm(v.get("title", "")):
            return v
    return None


def yt_analytics(token_path):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build as build_service
    td = json.loads(Path(token_path).read_text())
    creds = Credentials(
        token=td["token"], refresh_token=td["refresh_token"],
        token_uri=td["token_uri"], client_id=td["client_id"],
        client_secret=td["client_secret"], scopes=td["scopes"],
    )
    creds.refresh(Request())
    return build_service("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)


def query(yta, video_id, start, end, metrics):
    return yta.reports().query(
        ids="channel==MINE", startDate=start.isoformat(), endDate=end.isoformat(),
        metrics=metrics, filters="video==%s" % video_id,
    ).execute()


def row_to_stats(resp, metrics):
    cols = [h["name"] for h in resp.get("columnHeaders", [])]
    rows = resp.get("rows") or []
    vals = dict(zip(cols, rows[0])) if rows else {}
    return {
        "views": vals.get("views"),
        "thumb_impressions": vals.get("videoThumbnailImpressions"),
        "thumb_ctr": vals.get("videoThumbnailImpressionsClickRate"),
        "avg_view_pct": vals.get("averageViewPercentage"),
    }


def main():
    ap = argparse.ArgumentParser(description="click_ledger へ実測CTR/初動を自動追記（READ ONLY対YouTube）")
    ap.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--videos", default=str(DEFAULT_VIDEOS))
    ap.add_argument("--dry-run", action="store_true", help="追記せず表示のみ（初回必須）")
    args = ap.parse_args()

    pubs, stats_done, broken = load_ledger(args.ledger)
    for lineno, err in broken:
        print("⚠️ 壊れた行をスキップ: %d行目（%s）" % (lineno, err))
    if not pubs:
        print("publish記録なし。まず click_ledger.py publish で記録してから。")
        return

    if not Path(args.videos).exists():
        print("❌ channel_videos.json が見つからない: %s" % args.videos)
        sys.exit(2)
    videos = json.loads(Path(args.videos).read_text())
    if isinstance(videos, dict):
        videos = videos.get("videos", [])

    today = (datetime.datetime.utcnow() + JST_OFFSET).date()
    yta = None
    metrics_in_use = FULL_METRICS
    appended, unresolved, skipped_young = 0, [], []

    for pub in pubs:
        folder = pub["folder"]
        pub_date = datetime.date.fromisoformat(pub["date"])
        if (today - pub_date).days < ANALYTICS_LAG_DAYS:
            skipped_young.append(folder)
            continue
        v = match_video(pub, videos)
        if not v:
            unresolved.append(folder)
            continue
        video_id = v.get("id") or v.get("video_id") or v.get("videoId")
        if not video_id:
            unresolved.append(folder + "(id欠落)")
            continue

        windows = []
        d7_end = min(pub_date + datetime.timedelta(days=6), today - datetime.timedelta(days=ANALYTICS_LAG_DAYS))
        if ("d1-7" not in [w for f, w in stats_done if f == folder]) and d7_end >= pub_date:
            windows.append(("d1-7", pub_date, d7_end))
        windows.append(("cum", pub_date, today))

        for window, start, end in windows:
            if (folder, window) in stats_done and window == "d1-7":
                continue
            if yta is None:
                yta = yt_analytics(args.token)
            try:
                resp = query(yta, video_id, start, end, metrics_in_use)
            except Exception as e:  # metric未対応等 → フォールバック1回
                if metrics_in_use == FULL_METRICS:
                    print("⚠️ サムネ指標が拒否された（%s）→ views/維持率のみで続行。CTRは手動転記待ち" % str(e)[:80])
                    metrics_in_use = FALLBACK_METRICS
                    resp = query(yta, video_id, start, end, metrics_in_use)
                else:
                    raise
            stats = row_to_stats(resp, metrics_in_use)
            rec = {"schema": SCHEMA, "type": "stats",
                   "date": today.isoformat(), "folder": folder, "video_id": video_id,
                   "window": window, "source": "api", "note": ""}
            rec.update(stats)
            line = json.dumps(rec, ensure_ascii=False)
            if args.dry_run:
                print("[dry-run] %s" % line)
            else:
                with open(args.ledger, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
                appended += 1

    print("---")
    print("追記 %d行%s / 未解決 %s / 3日未満スキップ %s" % (
        appended, "（dry-run）" if args.dry_run else "",
        unresolved or "なし", skipped_young or "なし"))
    if metrics_in_use == FALLBACK_METRICS:
        print("⚠️ CTRはAPIで取れていない → click_ledger.py stats で手動転記が必要")


if __name__ == "__main__":
    main()
