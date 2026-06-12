#!/usr/bin/env python3
"""Fetch YouTube daily revenue and update Obsidian daily notes."""
import json
import re
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

VAULT = "/Users/kojinn/2nd-Brain"
TOKEN_PATH = "/Users/kojinn/.config/youtube-revenue/token_2ch.json"
RATE = 150  # USD to JPY

def get_credentials():
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"]
    )
    creds.refresh(Request())
    return creds

def fetch_revenue(creds, start_date, end_date):
    yta = build("youtubeAnalytics", "v2", credentials=creds)
    response = yta.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="estimatedRevenue,views,estimatedMinutesWatched",
        dimensions="day",
        sort="day"
    ).execute()
    return response.get("rows", [])

def update_daily_note(date_str, jpy, usd):
    note_path = os.path.join(VAULT, "05_日誌", f"{date_str}.md")
    if not os.path.exists(note_path):
        return False

    with open(note_path, "r") as f:
        content = f.read()

    # Check if YouTube already has a value (not just "円")
    yt_match = re.search(r'\| YouTube \| (.+?) \|', content)
    if yt_match:
        current = yt_match.group(1).strip()
        if current != "円" and current not in ("", "-"):
            return False  # Already has data

    # Update YouTube row
    content = re.sub(
        r'\| YouTube \| 円 \| \|',
        f'| YouTube | ¥{jpy:,} | ${usd:.2f} |',
        content
    )

    # Update total (add YouTube to existing delivery total)
    total_match = re.search(r'\| 合計 \| [¥￥]?([\d,]+)', content)
    if total_match:
        current_total = int(total_match.group(1).replace(",", ""))
        new_total = current_total + jpy
        content = re.sub(
            r'\| 合計 \| [¥￥]?[\d,]+ \|',
            f'| 合計 | ¥{new_total:,} |',
            content
        )

    with open(note_path, "w") as f:
        f.write(content)
    return True

def main():
    creds = get_credentials()

    # Fetch last 10 days (YouTube Analytics has 2-3 day delay)
    end = datetime.now()
    start = end - timedelta(days=10)

    rows = fetch_revenue(creds, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

    updated = []
    for row in rows:
        date_str, revenue_usd, views, minutes = row
        jpy = round(revenue_usd * RATE)
        if update_daily_note(date_str, jpy, revenue_usd):
            updated.append(f"{date_str}: ¥{jpy:,} (${revenue_usd:.2f})")

    if updated:
        print("Updated:")
        for u in updated:
            print(f"  {u}")
    else:
        print("No updates needed.")

if __name__ == "__main__":
    main()
