import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def main():
    print("==================================================================")
    print("🔑 CINEPULSE 1-TIME YOUTUBE CLOUD TOKEN GENERATOR")
    print("==================================================================")

    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"\n❌ Missing '{CLIENT_SECRET_FILE}'!")
        print("\nPlease follow these 3 quick steps to get it (100% Free):")
        print("1. Go to https://console.cloud.google.com/ and create a project 'CinePulse'")
        print("2. Search 'YouTube Data API v3' and click ENABLE")
        print("3. Go to 'APIs & Services' -> 'Credentials' -> 'Create Credentials' -> 'OAuth client ID'")
        print("   - Type: Desktop app")
        print("   - Download the JSON file and save it as 'client_secret.json' in this folder:")
        print(f"     {CLIENT_SECRET_FILE}")
        print("\nOnce saved, run this script again!")
        return

    print("\n🌐 Opening browser for 1-time channel authorization...")
    print("👉 Sign in with your YouTube channel account (@CinePulseFlix) and click Allow.\n")

    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES
    )

    # access_type='offline' and prompt='consent' ensure a permanent refresh_token is issued
    creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

    creds_data = json.loads(creds.to_json())

    # Ensure client_id and client_secret are included in token JSON for standalone headless refresh
    with open(CLIENT_SECRET_FILE, "r", encoding="utf-8") as f:
        secret_raw = json.load(f)
        client_info = secret_raw.get("installed") or secret_raw.get("web") or {}
        creds_data["client_id"] = client_info.get("client_id", creds_data.get("client_id"))
        creds_data["client_secret"] = client_info.get("client_secret", creds_data.get("client_secret"))

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(creds_data, f, indent=2)

    compact_secret = json.dumps(creds_data)

    print("\n🎉 SUCCESS! Token generated successfully.")
    print("📁 Saved locally to:", TOKEN_FILE)
    print("\n==================================================================")
    print("📋 YOUR GITHUB SECRET VALUE (COPY THE TEXT BELOW):")
    print("==================================================================")
    print(compact_secret)
    print("==================================================================")
    print("\n👉 Now add this to your GitHub Repository:")
    print("1. Go to: https://github.com/venkat1802901/cinepulse-shorts/settings/secrets/actions")
    print("2. Click 'New repository secret'")
    print("3. Name: YOUTUBE_TOKEN_JSON")
    print("4. Secret: [Paste the JSON string from above]")
    print("5. Click 'Add secret'")
    print("\nThat's it! GitHub Actions can now publish to your channel forever with your laptop OFF!")

if __name__ == "__main__":
    main()
