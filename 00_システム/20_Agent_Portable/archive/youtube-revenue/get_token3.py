#!/usr/bin/env python3
"""OAuth token retrieval - manual flow with auth URL output."""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import Flow

SCOPES = [
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/yt-analytics-monetary.readonly',
]
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(CONFIG_DIR, 'client_secret.json')
TOKEN_FILE = os.path.join(CONFIG_DIR, 'token.json')
PORT = 8089
REDIRECT_URI = f'http://localhost:{PORT}/'

auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = parse_qs(urlparse(self.path).query)
        auth_code = query.get('code', [None])[0]
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><body>Authentication successful! You can close this window.</body></html>')

    def log_message(self, format, *args):
        pass

def main():
    flow = Flow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(access_type='offline', prompt='consent')

    print(f'AUTH_URL:{auth_url}', flush=True)

    server = HTTPServer(('localhost', PORT), CallbackHandler)
    server.handle_request()

    if not auth_code:
        print('ERROR: No auth code received', file=sys.stderr)
        sys.exit(1)

    flow.fetch_token(code=auth_code)
    creds = flow.credentials

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

    print(f'SUCCESS: Token saved to {TOKEN_FILE}', flush=True)

if __name__ == '__main__':
    main()
