#!/usr/bin/env python3
import html
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def fetch(video_id: str) -> str:
    player_url = (
        "https://www.youtube.com/youtubei/v1/player"
        "?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    )
    player_body = json.dumps({
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "20.10.38",
                "hl": "ja",
            }
        },
        "videoId": video_id,
    }).encode()
    player_req = urllib.request.Request(
        player_url,
        data=player_body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "com.google.android.youtube/20.10.38 (Linux; Android 14)",
        },
    )
    player = json.load(urllib.request.urlopen(player_req, timeout=30))
    tracks = (
        player.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    if not tracks:
        raise RuntimeError(f"captionTracks not found: {video_id}")
    caption_req = urllib.request.Request(
        tracks[0]["baseUrl"], headers={"User-Agent": "Mozilla/5.0"}
    )
    xml_bytes = urllib.request.urlopen(caption_req, timeout=30).read()
    root = ET.fromstring(xml_bytes)
    lines = []
    for paragraph in root.findall(".//p"):
        text = "".join(paragraph.itertext())
        text = html.unescape(text).replace("\n", " ").strip()
        if text:
            lines.append(text)
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: fetch_youtube_transcript.py VIDEO_ID OUT", file=sys.stderr)
        return 2
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fetch(sys.argv[1]), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
