"""
Run this ONCE locally to get your Google OAuth refresh token.
No local server needed — just copy/paste a code from your browser.

Usage:
  source venv/bin/activate
  python3 get_refresh_token.py
"""

import urllib.parse
import urllib.request
import json

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID") or input("Enter your Google Client ID: ").strip()
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET") or input("Enter your Google Client Secret: ").strip()
REDIRECT_URI = "http://localhost:8080"
SCOPE = "https://www.googleapis.com/auth/calendar"

# Step 1: Build auth URL
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent",
}
auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

print("\n=== Google OAuth Setup ===\n")
print("1. Open this URL in your browser:\n")
print(auth_url)
print("\n2. Log in with lucashazan@gmail.com and approve access.")
print("3. You'll be redirected to localhost:8080 (it will fail to load — that's OK).")
print("4. Copy the full URL from your browser's address bar and paste it below.\n")

redirected_url = input("Paste the full redirect URL here: ").strip()

# Parse the code from the URL
parsed = urllib.parse.urlparse(redirected_url)
code = urllib.parse.parse_qs(parsed.query).get("code", [None])[0]

if not code:
    print("\n❌ Could not find authorization code in URL. Make sure you copied the full URL.")
    exit(1)

# Step 2: Exchange code for tokens
token_data = urllib.parse.urlencode({
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=token_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"\n❌ Token exchange failed: {e.read().decode()}")
    exit(1)

refresh_token = tokens.get("refresh_token")
if not refresh_token:
    print("\n❌ No refresh token returned. Make sure you included 'prompt=consent'.")
    exit(1)

print("\n✅ Success! Add this to Railway:\n")
print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
