import json
import os
import re
import datetime

LEDGER_PATH = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production\app\data\channel_ledger.json"

def normalize_string(s):
    """Strips special characters and whitespace for fuzzy signature matching."""
    if not s:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

def load_ledger():
    if not os.path.exists(LEDGER_PATH):
        return {"channel_handle": "@CinePulseFlix", "history": []}
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading ledger: {e}")
        return {"channel_handle": "@CinePulseFlix", "history": []}

def save_ledger(data):
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def is_duplicate(track_name, artist="", video_id="", clip_start=None, clip_end=None):
    """
    Checks if a song or video footage has already been used on @CinePulseFlix.
    Returns: (bool is_dup, str reason)
    """
    ledger = load_ledger()
    norm_song = normalize_string(track_name)
    norm_artist = normalize_string(artist)
    target_sig = f"{norm_song}_{norm_artist}"

    for entry in ledger.get("history", []):
        entry_video_id = entry.get("source_video_id", "")
        entry_sig = entry.get("normalized_signature", "")
        entry_song = normalize_string(entry.get("track_name", ""))

        # 1. Exact Video ID Match
        if video_id and entry_video_id and video_id == entry_video_id:
            # Check if specific timestamp overlaps
            if clip_start is not None and clip_end is not None:
                for seg in entry.get("clip_segments", []):
                    s_start = seg.get("start_sec", 0)
                    s_end = seg.get("end_sec", 0)
                    # Check for overlap
                    if not (clip_end <= s_start or clip_start >= s_end):
                        return True, f"Duplicate clip segment [{clip_start}s-{clip_end}s] overlaps with previously used scene [{s_start}s-{s_end}s] from video '{entry.get('track_name')}' (used on {entry.get('first_rendered_date')})"
            return True, f"Video ID '{video_id}' ({entry.get('track_name')}) has already been featured on {entry.get('first_rendered_date')}."

        # 2. Same Song Signature Match
        if norm_song and (norm_song in entry_sig or entry_song in target_sig or norm_song == entry_song):
            return True, f"Song '{track_name}' by '{artist}' has already been uploaded to @CinePulseFlix on {entry.get('first_rendered_date')}."

    return False, "Clean: No duplicates found. Approved for production."

def register_used_clip(language, track_name, artist, video_id, source_url, clip_start, clip_end, scene_desc=""):
    """
    Permanently registers a finished clip in the ledger to prevent future duplicates.
    """
    ledger = load_ledger()
    norm_sig = f"{normalize_string(track_name)}_{normalize_string(artist)}"
    
    new_entry = {
        "id": f"entry-{len(ledger.get('history', [])) + 1:03d}",
        "language": language.lower(),
        "track_name": track_name,
        "artist": artist,
        "normalized_signature": norm_sig,
        "source_video_id": video_id,
        "source_url": source_url,
        "clip_segments": [
            {
                "start_sec": float(clip_start),
                "end_sec": float(clip_end),
                "duration": round(float(clip_end) - float(clip_start), 2),
                "scene_description": scene_desc
            }
        ],
        "first_rendered_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "status": "approved"
    }
    
    ledger.setdefault("history", []).append(new_entry)
    save_ledger(ledger)
    print(f"✅ Registered in deduplication ledger: '{track_name}' by {artist} [{clip_start}s-{clip_end}s]")
    return True

if __name__ == '__main__':
    # Test deduplication engine
    print("Testing deduplication engine...")
    dup, reason = is_duplicate("Tauba Tauba", "Karan Aujla", "LK7-_dgAVQE")
    print(f"Check 1 (Tauba Tauba): Duplicate={dup} -> {reason}")

    dup2, reason2 = is_duplicate("Pushpa 2 Mass Anthem", "Devi Sri Prasad", "XYZ12345")
    print(f"Check 2 (Pushpa 2): Duplicate={dup2} -> {reason2}")
