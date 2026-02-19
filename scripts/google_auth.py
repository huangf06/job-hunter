"""
Google OAuth Re-authorization Script
=====================================

Re-authorizes with expanded scopes (Calendar + Gmail).
Starts a local HTTP server to catch the OAuth redirect automatically.

Usage:
    python scripts/google_auth.py

After running, tokens in ~/.config/google-calendar-mcp/tokens.json will be
updated with both calendar and gmail.readonly scopes.
"""

import json
import http.server
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

TOKENS_PATH = Path.home() / ".config" / "google-calendar-mcp" / "tokens.json"
CREDENTIALS_PATH = Path.home() / ".config" / "gcp-oauth.keys.json"
TOKEN_KEY = "normal"

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
]

REDIRECT_PORT = 8914
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"


def main():
    # Load client credentials
    creds = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
    installed = creds.get("installed", creds.get("web", {}))
    client_id = installed["client_id"]
    client_secret = installed["client_secret"]
    token_uri = installed.get("token_uri", "https://oauth2.googleapis.com/token")

    # Build authorization URL
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={'+'.join(SCOPES)}"
        f"&access_type=offline"
        f"&prompt=consent"
    )

    # Catch the auth code via local HTTP server
    auth_code = None
    server_ready = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            qs = parse_qs(urlparse(self.path).query)
            if "code" in qs:
                auth_code = qs["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>Authorization successful!</h2><p>You can close this tab.</p>")
            else:
                error = qs.get("error", ["unknown"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h2>Authorization failed: {error}</h2>".encode())

        def log_message(self, format, *args):
            pass  # Suppress HTTP logs

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), Handler)
    server.timeout = 120  # 2 minute timeout

    def run_server():
        server_ready.set()
        while auth_code is None:
            server.handle_request()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    server_ready.wait()

    print(f"Opening browser for authorization...")
    print(f"  Scopes: calendar + gmail.readonly")
    print(f"  Listening on: {REDIRECT_URI}")
    print()
    webbrowser.open(auth_url)
    print("Waiting for authorization (2 min timeout)...")

    # Wait for auth code
    thread.join(timeout=120)

    if not auth_code:
        print("\nTimeout — no authorization received.")
        print(f"If browser didn't open, visit manually:\n{auth_url}")
        server.server_close()
        return

    print("Authorization code received. Exchanging for tokens...")

    # Exchange auth code for tokens
    resp = requests.post(token_uri, data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
    }, timeout=15)
    resp.raise_for_status()
    token_data = resp.json()

    # Build token entry (same format as MCP)
    new_entry = {
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "scope": token_data["scope"],
        "token_type": token_data["token_type"],
        "expiry_date": int(time.time() * 1000) + token_data["expires_in"] * 1000,
    }

    # Read-modify-write tokens file
    all_tokens = {}
    if TOKENS_PATH.exists():
        all_tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))

    all_tokens[TOKEN_KEY] = new_entry
    TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_PATH.write_text(json.dumps(all_tokens, indent=2), encoding="utf-8")

    print(f"\nTokens saved to: {TOKENS_PATH}")
    print(f"Scopes granted: {token_data['scope']}")
    print("Done! Calendar MCP and Gmail are both ready.")

    server.server_close()


if __name__ == "__main__":
    main()
