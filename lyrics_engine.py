import os
import re
import urllib.request
import urllib.parse
import json
import platform

def get_system_font():
    """Returns a universal bold font depending on OS."""
    if platform.system() == "Windows":
        return "Segoe UI"
    return "DejaVu Sans"

def fetch_synced_lyrics(track_name, artist_name=""):
    """
    Fetches synchronized lyrics from LRCLIB.
    Returns list of tuples: (timestamp_seconds, text)
    """
    try:
        query = f"track_name={urllib.parse.quote(track_name)}"
        if artist_name:
            query += f"&artist_name={urllib.parse.quote(artist_name)}"
        url = f"https://lrclib.net/api/get?{query}"
        req = urllib.request.Request(url, headers={'User-Agent': 'CinePulseVideoEngine/2.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            synced = data.get('syncedLyrics', '')
            if not synced:
                return []
            
            parsed = []
            for line in synced.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)', line)
                if match:
                    minutes = int(match.group(1))
                    seconds = float(match.group(2))
                    total_sec = minutes * 60 + seconds
                    text = match.group(3).strip()
                    if text:
                        parsed.append((total_sec, text))
            return parsed
    except Exception as e:
        print(f"Error fetching synced lyrics for {track_name}: {e}")
        return []

def format_ass_time(seconds):
    """Formats seconds to ASS time format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

def generate_kinetic_ass(lyrics_slice, output_path, video_duration=22.0, font_name=None):
    """
    Generates a high-impact ASS subtitle file with word-by-word karaoke glow styling.
    lyrics_slice: list of (rel_start_sec, rel_end_sec, text) relative to clip start (0.0).
    """
    if not font_name:
        font_name = get_system_font()

    ass_template = f"""[Script Info]
Title: CinePulse Kinetic Lyrics
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KineticMain,{font_name},58,&H0000FFFF,&H40FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1.5,0,1,4.5,2.0,2,60,60,320,1
Style: KineticAccent,{font_name},62,&H00D7FF,&H30FFFFFF,&H00000000,&H90000000,-1,0,0,0,105,105,2.0,0,1,5.0,3.0,2,60,60,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
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

    full_ass = ass_template + "\n".join(events) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_ass)
    print(f"Kinetic ASS generated: {output_path} ({len(events)} lyric lines)")
    return output_path
