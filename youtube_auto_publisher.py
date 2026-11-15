import os
import sys
import json
import time
import urllib.request
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LEDGER_FILE = os.path.join(BASE_DIR, "app", "data", "published_ledger.json")
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
NTFY_TOPIC = "cinepulse_flx_venkat_channel"
ONLINE_FEED_URL = "https://venkat1802901.github.io/cinepulse-shorts/static/videos.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def load_published_ledger():
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_published_ledger(ledger):
    os.makedirs(os.path.dirname(LEDGER_FILE), exist_ok=True)
    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)

def fetch_feed():
    """Fetches video metadata from live GitHub Pages website (fallback to local)."""
    try:
        req = urllib.request.Request(
            f"{ONLINE_FEED_URL}?t={int(time.time())}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            log(f"🌐 Fetched live feed from website ({len(data.get('videos', []))} videos)")
            return data.get("videos", [])
    except Exception as e:
        log(f"⚠️ Could not fetch from online feed: {e}. Falling back to local videos.json...")
        local_path = os.path.join(STATIC_DIR, "videos.json")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                return json.load(f).get("videos", [])
        return []

def get_youtube_service():
    """Authenticates via OAuth 2.0 (local file or cloud environment secret) and returns the YouTube API service object."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        log("❌ Required libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        return None

    creds = None

    # 1. Check for GitHub Actions Cloud Secret environment variable
    cloud_token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if cloud_token_json:
        try:
            token_dict = json.loads(cloud_token_json)
            creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
            log("☁️ Loaded OAuth credentials from GitHub Cloud Secret (YOUTUBE_TOKEN_JSON)")
        except Exception as e:
            log(f"⚠️ Error parsing YOUTUBE_TOKEN_JSON: {e}")
            creds = None

    # 2. Check for local token.json file
    if not creds and os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            log("📁 Loaded OAuth credentials from local token.json")
        except Exception:
            creds = None

    # 3. Refresh or authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log("🔄 Refreshing expired OAuth token with permanent refresh_token...")
            creds.refresh(Request())
            # Save refreshed token locally if on laptop
            if os.path.exists(TOKEN_FILE):
                try:
                    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                except Exception:
                    pass
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                log(f"❌ Missing '{CLIENT_SECRET_FILE}' and YOUTUBE_TOKEN_JSON not set.")
                return None
            log("🔑 Starting 1-time OAuth authorization flow in browser...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

            with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
                token_out.write(creds.to_json())
            log("✅ OAuth token saved. Headless authentication is now perpetual!")

    return build("youtube", "v3", credentials=creds)

def notify_phone(title, message, click_url=None):
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "high",
                "Tags": "rocket,movie_camera",
                "Click": click_url or ""
            }
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

def upload_video_to_youtube(youtube, item, privacy_status="public"):
    from googleapiclient.http import MediaFileUpload

    # Locate the video file locally or download if hosted
    local_file = os.path.join(STATIC_DIR, item["video_file"])
    if not os.path.exists(local_file):
        # Try downloading from live website
        online_url = f"https://venkat1802901.github.io/cinepulse-shorts/static/{item['video_file']}"
        log(f"📥 Downloading video from {online_url}...")
        try:
            urllib.request.urlretrieve(online_url, local_file)
        except Exception as dl_err:
            log(f"❌ Failed to locate or download {item['video_file']}: {dl_err}")
            return None

    # Construct Shorts metadata
    title = item.get("title", f"{item.get('track_name')} Velocity Edit 🔥 #Shorts")
    if "#Shorts" not in title:
        title = f"{title} #Shorts"
    if len(title) > 100:
        title = title[:92] + " #Shorts"

    description = item.get("description", "")
    if "#Shorts" not in description:
        description += "\n\n#Shorts #ViralShorts #60FPS #CinePulseFlix"

    tags = ["Shorts", "ViralShorts", "60FPS", "CinePulseFlix", item.get("track_name", ""), item.get("artist", "")]

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "10", # 10 = Music, 24 = Entertainment
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    log(f"🚀 Uploading '{title}' ({privacy_status})...")
    media = MediaFileUpload(local_file, mimetype="video/mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log(f"  Uploading: {int(status.progress() * 100)}%")

    yt_id = response.get("id")
    shorts_url = f"https://youtube.com/shorts/{yt_id}"
    log(f"🎉 SUCCESS! Published to YouTube Shorts: {shorts_url}")

    notify_phone(
        title=f"🎬 Live on @CinePulseFlix!",
        message=f"'{item.get('track_name')}' was published to your channel!",
        click_url=shorts_url
    )

    return yt_id, shorts_url

def main():
    parser = argparse.ArgumentParser(description="Autonomous YouTube Shorts Publisher for CinePulse")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="Video privacy status")
    parser.add_argument("--dry-run", action="store_true", help="Inspect feed and test without uploading")
    parser.add_argument("--limit", type=int, default=2, help="Max videos to publish in this run (default: 2 daily)")
    args = parser.parse_args()

    log("==================================================================")
    log("🤖 CINEPULSE AUTONOMOUS YOUTUBE SHORTS PUBLISHER")
    log(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPLOAD'} | Privacy: {args.privacy} | Limit: {args.limit}")
    log("==================================================================")

    videos = fetch_feed()
    if not videos:
        log("No videos found in feed. Exiting.")
        return

    ledger = load_published_ledger()
    log(f"Found {len(ledger)} previously published videos in ledger.")

    unpublished = [v for v in videos if v["video_file"] not in ledger]
    log(f"Found {len(unpublished)} pending unpublished video(s).")

    if not unpublished:
        log("✅ All videos in current feed are already published to your channel!")
        return

    if args.dry_run:
        log("🔍 DRY RUN PREVIEW:")
        for idx, item in enumerate(unpublished[:args.limit]):
            log(f"  [{idx + 1}] {item.get('badge')}: {item.get('title')} ({item.get('video_file')})")
        log("Dry run complete. Run without --dry-run to upload.")
        return

    youtube = get_youtube_service()
    if not youtube:
        log("❌ Cannot proceed without YouTube authentication. See instructions above.")
        return

    published_count = 0
    for item in unpublished[:args.limit]:
        yt_id, shorts_url = upload_video_to_youtube(youtube, item, privacy_status=args.privacy)
        if yt_id:
            ledger[item["video_file"]] = {
                "youtube_id": yt_id,
                "shorts_url": shorts_url,
                "track_name": item.get("track_name"),
                "artist": item.get("artist"),
                "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "privacy": args.privacy
            }
            save_published_ledger(ledger)
            published_count += 1
            time.sleep(5) # Brief breathing room between uploads

    log(f"\n🎉 Done! Successfully published {published_count} new Short(s) to @CinePulseFlix.")

if __name__ == "__main__":
    main()
