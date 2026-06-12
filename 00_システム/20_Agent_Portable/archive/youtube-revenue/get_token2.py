#!/usr/bin/env python3
"""YouTube Analytics OAuth token retrieval - prints URL for manual auth."""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/yt-analytics.readonly']
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(CONFIG_DIR, 'client_secret.json')
TOKEN_FILE = os.path.join(CONFIG_DIR, 'token.json')

def main():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    # Print URL and wait for callback
    import sys
    sys.stderr.write("Starting server on port 8088...\n")
    sys.stderr.flush()
    creds = flow.run_local_server(port=8088, open_browser=False, timeout_seconds=120)

    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes),
    }

    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)

    print(f'SUCCESS: Token saved to {TOKEN_FILE}')

if __name__ == '__main__':
    main()
