#!/usr/bin/env python3
"""Re-authenticate YouTube API (token_2ch.json)."""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = "<REDACTED 2026-06-13: 実物は ~/.config/youtube-revenue/client_secret.json>"
CLIENT_SECRET = "<REDACTED 2026-06-13: 同上。Vaultに認証情報を置かないルール>"

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
print("ブラウザが開きます。corocoro.works1@gmail.com のブランドアカウント「世界史」でログインしてください。")
creds = flow.run_local_server(port=8099, prompt="consent")

token_data = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": list(creds.scopes),
}

with open("/Users/kojinn/.config/youtube-revenue/token_2ch.json", "w") as f:
    json.dump(token_data, f, indent=2)

print("Token saved! YouTube API再認証完了。")
