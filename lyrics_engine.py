import os
import re
import urllib.request
import urllib.parse
import json
import platform

def get_system_font():
    """Returns a universal bold font depending on OS."""
    if platform.system() == "Windows":
        return "Nirmala UI"
    return "DejaVu Sans"

def clean_track_name(raw_title):
    """Strips YouTube video fluff like '(Official Video)', '| Singer', 'Video Song', etc."""
    if not raw_title:
        return ""
    # Strip brackets/parentheses and contents like (Official Video), [4K], etc.
    t = re.sub(r'\(.*?\)|\[.*?\]', '', raw_title)
    # Split on pipe, hyphen, ft., feat.
    parts = re.split(r'\||-|ft\.|feat\.', t, flags=re.IGNORECASE)
    t = parts[0] if parts else t
    # Remove common video buzzwords
    t = re.sub(r'(?i)new song \d+|official video|video song|full video|lyrical video|music video', '', t)
    return t.strip()

def parse_lrc_content(synced_text):
    """Parses LRC format into a sorted list of (timestamp_seconds, text)."""
    parsed = []
    for line in synced_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)', line)
        if match:
            minutes = int(match.group(1))
            seconds = float(match.group(2))
            total_sec = minutes * 60 + seconds
            text = match.group(3).strip()
            # Skip empty lines or metadata lines like [by:...]
            if text and not text.startswith(('by:', 'ar:', 'ti:', 'al:')):
                parsed.append((total_sec, text))
    parsed.sort(key=lambda x: x[0])
    return parsed

def fetch_synced_lyrics(track_name, artist_name=""):
    """
    Fetches real synchronized song lyrics from LRCLIB.
    Searches both fuzzy query endpoint and direct get endpoint.
    Returns list of tuples: (timestamp_seconds, text)
    """
    clean_title = clean_track_name(track_name)
    queries = []
    if clean_title and artist_name:
        queries.append(f"{clean_title} {artist_name}")
    if clean_title:
        queries.append(clean_title)
    if track_name:
        queries.append(track_name)

    # 1. Search endpoint (best for fuzzy match across languages)
    for q in queries:
        try:
            url = f"https://lrclib.net/api/search?q={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=6) as resp:
                results = json.loads(resp.read().decode('utf-8'))
                for r in results:
                    synced = r.get('syncedLyrics')
                    if synced:
                        parsed = parse_lrc_content(synced)
                        if len(parsed) >= 4:
                            print(f"🎵 Found real synced lyrics for '{q}': {len(parsed)} lines ({r.get('trackName')} by {r.get('artistName')})")
                            return parsed
        except Exception:
            continue

    # 2. Direct get endpoint fallback
    try:
        url = f"https://lrclib.net/api/get?track_name={urllib.parse.quote(clean_title)}"
        if artist_name:
            url += f"&artist_name={urllib.parse.quote(artist_name)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            synced = data.get('syncedLyrics', '')
            if synced:
                return parse_lrc_content(synced)
    except Exception:
        pass

    return []

def get_complete_lyrical_section(track_name, artist_name="", min_duration=35.0, max_duration=58.0, target_duration=45.0):
    """
    Finds a complete lyrical sentence / hook section strictly between 35s and 58s.
    Guarantees no chopped or half-sentences: starts at the beginning of a line and ends at the finish of a line.
    Returns: (start_sec, duration, relative_lyrics_list)
    """
    lyrics = fetch_synced_lyrics(track_name, artist_name)

    if lyrics and len(lyrics) >= 4:
        candidates = []
        for i in range(len(lyrics)):
            start_t = lyrics[i][0]
            # Avoid the first 15 seconds if song has plenty of lines (intros are talk/silence)
            if start_t < 15.0 and len(lyrics) > 10:
                continue

            for j in range(i + 2, len(lyrics)):
                # End time is the start of the next line, or current line + 4.0s
                if j + 1 < len(lyrics):
                    end_t = lyrics[j + 1][0] + 0.3
                else:
                    end_t = lyrics[j][0] + 4.0

                # Pre-roll 0.4s so first syllable is clear
                actual_start = max(0.0, start_t - 0.4)
                dur = end_t - actual_start

                if min_duration <= dur <= max_duration:
                    selected_lines = lyrics[i:j + 1]
                    # Score by sentence count, closeness to target, and hook energy
                    score = len(selected_lines) * 15 - abs(dur - target_duration)
                    if 25.0 <= actual_start <= 90.0:
                        score += 35 # Chorus/hook sweet spot in Indian tracks
                    candidates.append((score, actual_start, dur, selected_lines))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_start, best_dur, best_lines = candidates[0]

            # Build relative lyrics starting from 0.0
            relative_lyrics = []
            for idx, line in enumerate(best_lines):
                l_start = max(0.0, line[0] - best_start)
                if idx + 1 < len(best_lines):
                    l_end = min(best_dur, best_lines[idx + 1][0] - best_start)
                else:
                    l_end = min(best_dur, l_start + 4.5)
                relative_lyrics.append((round(l_start, 2), round(l_end, 2), line[1]))

            print(f"✨ Selected complete lyrical section: {best_start:.1f}s to {best_start + best_dur:.1f}s (duration: {best_dur:.1f}s, {len(relative_lyrics)} complete sentences)")
            return round(best_start, 2), round(best_dur, 2), relative_lyrics

    # Fallback if no synced lyrics exist: 42.0s complete musical phrase (NO channel ads!)
    fallback_start = 32.0
    fallback_dur = 44.0
    return fallback_start, fallback_dur, []

def format_ass_time(seconds):
    """Formats seconds to ASS time format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

def generate_kinetic_ass(lyrics_slice, output_path, video_duration=45.0, song_title="", artist="", font_name=None):
    """
    Generates a high-impact ASS subtitle file with word-by-word karaoke glow styling.
    ONLY uses genuine song lyrics. Never includes channel promotional text.
    lyrics_slice: list of (rel_start_sec, rel_end_sec, text) relative to clip start (0.0).
    """
    if not font_name:
        font_name = get_system_font()

    ass_template = f"""[Script Info]
Title: Kinetic Song Lyrics
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KineticMain,{font_name},56,&H0000FFFF,&H40FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1.5,0,1,4.5,2.0,2,60,60,340,1
Style: TitleBadge,{font_name},48,&H00FFFFFF,&H00D7FF,&H00000000,&HA0000000,-1,0,0,0,100,100,2.0,0,1,3.5,2.0,8,60,60,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    # If genuine lyrics exist, burn them with karaoke glow
    if lyrics_slice:
        for item in lyrics_slice:
            start_t, end_t, text = item
            if start_t >= video_duration or end_t <= 0:
                continue
            start_t = max(0.0, start_t)
            end_t = min(video_duration, end_t)

            words = text.split()
            if not words:
                continue

            duration_cs = int((end_t - start_t) * 100)
            per_word_cs = max(15, duration_cs // len(words))

            karaoke_text = "".join([f"{{\\k{per_word_cs}}}{w} " for w in words]).strip()
            start_str = format_ass_time(start_t)
            end_str = format_ass_time(end_t)

            dialogue = f"Dialogue: 0,{start_str},{end_str},KineticMain,,0,0,0,,{{\\fad(120,150)}}{karaoke_text}"
            events.append(dialogue)
    else:
        # If no synced lyrics exist for this song, show ONLY a brief 4s clean song title badge at top (NO channel ads!)
        clean_name = clean_track_name(song_title) or "Trending Track"
        artist_display = f" • {artist}" if artist else ""
        badge_text = f"♪ {clean_name}{artist_display} ♪"
        dialogue = f"Dialogue: 0,0:00:01.00,0:00:05.50,TitleBadge,,0,0,0,,{{\\fad(250,300)}}{badge_text}"
        events.append(dialogue)

    full_ass = ass_template + "\n".join(events) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_ass)
    print(f"ASS subtitle generated: {output_path} ({len(events)} events)")
    return output_path
