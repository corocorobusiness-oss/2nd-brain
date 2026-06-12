#!/usr/bin/env python3
"""Fetch all videos from the 2ch歴史 YouTube channel with view counts.

Outputs: /Users/kabushikikaishakorokoro/.codex/skills/neta-research/data/channel_videos.json
"""
import json
import sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/Users/kabushikikaishakorokoro/.config/youtube-revenue/token_2ch.json"
OUT_PATH = Path("/Users/kabushikikaishakorokoro/.codex/skills/neta-research/data/channel_videos.json")


def load_youtube():
    with open(TOKEN_PATH) as f:
        td = json.load(f)
    creds = Credentials(
        token=td["token"], refresh_token=td["refresh_token"],
        token_uri=td["token_uri"], client_id=td["client_id"],
        client_secret=td["client_secret"], scopes=td["scopes"],
    )
    return build("youtube", "v3", credentials=creds)


def main():
    yt = load_youtube()
    ch = yt.channels().list(part="contentDetails,statistics,snippet", mine=True).execute()
    if not ch.get("items"):
        print("ERROR: no channel found for this token", file=sys.stderr)
        sys.exit(1)
    c = ch["items"][0]
    uploads = c["contentDetails"]["relatedPlaylists"]["uploads"]
    print(f"Channel: {c['snippet']['title']} ({c['statistics'].get('videoCount')} videos)")

    video_ids = []
    page = None
    while True:
        resp = yt.playlistItems().list(
            part="contentDetails,snippet", playlistId=uploads,
            maxResults=50, pageToken=page,
        ).execute()
        for it in resp.get("items", []):
            video_ids.append(it["contentDetails"]["videoId"])
        page = resp.get("nextPageToken")
        if not page:
            break
    print(f"Collected {len(video_ids)} video ids")

    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = yt.videos().list(
            part="snippet,statistics,contentDetails", id=",".join(batch)
        ).execute()
        for v in resp.get("items", []):
            videos.append({
                "id": v["id"],
                "title": v["snippet"]["title"],
                "published": v["snippet"]["publishedAt"],
                "description": v["snippet"].get("description", ""),
                "tags": v["snippet"].get("tags", []),
                "duration": v["contentDetails"]["duration"],
                "views": int(v["statistics"].get("viewCount", 0)),
                "likes": int(v["statistics"].get("likeCount", 0)),
                "comments": int(v["statistics"].get("commentCount", 0)),
            })

    videos.sort(key=lambda x: x["published"], reverse=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(videos, ensure_ascii=False, indent=2))
    print(f"Saved {len(videos)} videos to {OUT_PATH}")

    # quick summary
    vs = sorted([v["views"] for v in videos])
    n = len(vs)
    print(f"Total views: {sum(vs):,}")
    print(f"Median: {vs[n//2]:,}  Mean: {sum(vs)//n:,}  Max: {max(vs):,}  Min: {min(vs):,}")
    print(f"10k+ videos: {sum(1 for v in vs if v >= 10000)} / {n} ({sum(1 for v in vs if v >= 10000) / n * 100:.1f}%)")


if __name__ == "__main__":
    main()
