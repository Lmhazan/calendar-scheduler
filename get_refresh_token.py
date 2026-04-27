"""
Run this ONCE locally to get your Google OAuth refresh token.
Then add it to your Railway environment variables.

Usage:
  pip install google-auth-oauthlib
  python get_refresh_token.py
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]

CLIENT_CONFIG = {
    "installed": {
        "client_id": input("Enter your Google Client ID: ").strip(),
        "client_secret": input("Enter your Google Client Secret: ").strip(),
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
creds = flow.run_local_server(port=0)

print("\n✅ Success! Add these to your Railway environment variables:\n")
print(f"GOOGLE_CLIENT_ID={CLIENT_CONFIG['installed']['client_id']}")
print(f"GOOGLE_CLIENT_SECRET={CLIENT_CONFIG['installed']['client_secret']}")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
