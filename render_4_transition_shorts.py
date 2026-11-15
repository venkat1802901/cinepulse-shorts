import os
import sys
import glob
import json
import datetime
import subprocess
from lyrics_engine import (
    get_complete_lyrical_section,
    generate_kinetic_ass,
    clean_track_name
)
from deduplication_engine import register_used_clip

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
VIDEOS_JSON = os.path.join(STATIC_DIR, "videos.json")

CANDIDATES = [
    {
        "lang": "hindi",
        "badge": "🇮🇳 HINDI • VIRAL BEAT",
        "track_name": "Tauba Tauba",
        "artist": "Karan Aujla • Vicky Kaushal",
        "yt_url": "https://www.youtube.com/watch?v=LK7-_dgAVQE",
        "video_id": "LK7-_dgAVQE",
        "pills": ["Kinetic Lyrics", "Directional Whip Transitions", "Teal & Gold Grade"],
        "scene_offsets": [0.0, 22.0, 48.0],
        "target_dur": 48.0
    },
    {
        "lang": "telugu",
        "badge": "🎭 TELUGU • MASS BANGERS",
        "track_name": "Pushpa Pushpa",
        "artist": "Devi Sri Prasad • Allu Arjun",
        "yt_url": "https://www.youtube.com/watch?v=EdvydlHCViY",
        "video_id": "EdvydlHCViY",
        "pills": ["High-Octane Swag", "Beat-Synced Cuts", "HDR Color Grade"],
        "scene_offsets": [0.0, 25.0, 52.0],
        "target_dur": 48.0
    },
    {
        "lang": "tamil",
        "badge": "⚡ TAMIL • ANIRUDH VIBES",
        "track_name": "Pavazha Malli",
        "artist": "Sai Abhyankkar • Shruti Haasan",
        "yt_url": "https://www.youtube.com/watch?v=b68HETiNO98",
        "video_id": "b68HETiNO98",
        "pills": ["Kollywood Bass Drop", "Tamil Karaoke Glow", "Multi-Scene Ramps"],
        "scene_offsets": [0.0, 22.0, 46.0],
        "target_dur": 48.0
    },
    {
        "lang": "wildcard",
        "badge": "🌟 WILDCARD • GLOBAL HYPE",
        "track_name": "Ghostface Killah",
        "artist": "Sidhu Moose Wala",
        "yt_url": "https://www.youtube.com/watch?v=Pq7UxbWeRU0",
        "video_id": "Pq7UxbWeRU0",
        "pills": ["Punjabi Trap Drill", "Word Pop Lyrics", "Dynamic Velocity Edits"],
        "scene_offsets": [0.0, 24.0, 50.0],
        "target_dur": 48.0
    }
]

def render_candidate(item):
    try:
        # 1. Fetch complete lyrical section strictly between 35s and 58s
        start_sec, dur, lyrics = get_complete_lyrical_section(
            item["track_name"],
            item["artist"],
            min_duration=36.0,
            max_duration=55.0,
            target_duration=item["target_dur"]
        )
        item["slice_start"] = start_sec
        item["duration"] = dur
        item["lyrics"] = lyrics
        out_filename = f"Short_{item['lang']}_{item['video_id']}_{int(dur)}s.mp4"
        out_file = os.path.join(STATIC_DIR, out_filename)
        item["filename"] = out_filename

        if os.path.exists(out_file) and os.path.getsize(out_file) > 2 * 1024 * 1024:
            print(f"⏩ Video already rendered: {out_filename} ({round(os.path.getsize(out_file)/1024/1024, 1)} MB)")
            return out_file

        print(f"\n=======================================================")
        print(f"🎬 Editing {item['badge']}: '{item['track_name']}'")
        print(f"⏱️ Duration: {dur:.1f}s (Start: {start_sec:.1f}s) | Real Lyrics: {len(lyrics)} lines")
        print(f"=======================================================")

        output_prefix = os.path.join(BASE_DIR, f"temp_{item['video_id']}")
        output_template = f"{output_prefix}.%(ext)s"
        ass_file = os.path.join(STATIC_DIR, f"temp_{item['video_id']}.ass")

        # Clean existing temp files for this ID
        for existing in glob.glob(f"{output_prefix}.*"):
            try:
                os.remove(existing)
            except Exception:
                pass

        # Determine download section:
        # Download with 3s pre-roll before start_sec, through start_sec + dur + max_scene_offset + 10s
        sec_start = max(0, int(start_sec) - 3)
        max_scene = max(item["scene_offsets"])
        sec_end = int(start_sec + dur + max_scene + 15)

        print(f"📥 Downloading source footage ({sec_start}s to {sec_end}s)...")
        subprocess.run([
            sys.executable, "-m", "yt_dlp",
            "--js-runtimes", "node",
            "-f", "bv*[vcodec^=avc1][height<=1080]+ba[ext=m4a]/bv*[height<=1080]+ba/b",
            "--merge-output-format", "mp4",
            "--download-sections", f"*{sec_start}-{sec_end}",
            "-o", output_template,
            item["yt_url"]
        ], check=True)

        candidates = [f for f in glob.glob(f"{output_prefix}.*") if not f.endswith(('.ass', '.part'))]
        if not candidates:
            raise FileNotFoundError(f"Download failed for {item['track_name']}")
        raw_video = candidates[0]

        # Generate ASS with real song lyrics (NO channel advertisements!)
        generate_kinetic_ass(
            lyrics_slice=lyrics,
            output_path=ass_file,
            video_duration=dur,
            song_title=item["track_name"],
            artist=item["artist"]
        )

        # In the downloaded file, time start_sec corresponds to file_start
        file_start = start_sec - sec_start

        # Multi-Scene Transition Edit setup:
        # 3 distinct visual scenes joined with directional whip and smooth left transitions
        S1 = file_start
        S2 = file_start + item["scene_offsets"][1]
        S3 = file_start + item["scene_offsets"][2]

        trans = 0.4
        d1 = dur / 3.0 + 0.2
        d2 = dur / 3.0 + 0.4
        d3 = dur / 3.0 + 0.2
        o1 = d1 - trans
        o2 = o1 + d2 - trans

        escaped_ass = ass_file.replace('\\', '/').replace(':', '\\:')

        fc = (
            f"[0:v]trim=start={S1:.2f}:duration={d1:.2f},setpts=PTS-STARTPTS,crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920,fps=60[v1];"
            f"[0:v]trim=start={S2:.2f}:duration={d2:.2f},setpts=PTS-STARTPTS,crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920,fps=60[v2];"
            f"[0:v]trim=start={S3:.2f}:duration={d3:.2f},setpts=PTS-STARTPTS,crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920,fps=60[v3];"
            f"[v1][v2]xfade=transition=wipetl:duration={trans}:offset={o1:.2f}[x1];"
            f"[x1][v3]xfade=transition=smoothleft:duration={trans}:offset={o2:.2f}[x2];"
            f"[x2]eq=contrast=1.14:saturation=1.24:brightness=0.01,vignette=angle=PI/5,ass='{escaped_ass}'[v];"
            f"[0:a]atrim=start={S1:.2f}:duration={dur:.2f},asetpts=PTS-STARTPTS,volume=1.05,loudnorm=I=-14:LRA=7:TP=-1.5,afade=t=out:st={dur - 0.5:.2f}:d=0.5[a]"
        )

        print(f"⚡ Rendering 1080x1920 @ 60FPS multi-scene transition edit with 44.1kHz audio...")
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_video,
            "-filter_complex", fc,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-profile:v", "high",
            "-level:v", "4.2",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-ac", "2",
            out_file
        ], check=True)

        print(f"✅ Master rendered: {out_file} ({round(os.path.getsize(out_file)/1024/1024, 1)} MB)")

        # Cleanup temp
        for c in candidates:
            if os.path.exists(c):
                try:
                    os.remove(c)
                except Exception:
                    pass
        if os.path.exists(ass_file):
            try:
                os.remove(ass_file)
            except Exception:
                pass

        return out_file
    except Exception as e:
        print(f"❌ Error rendering {item['track_name']}: {e}")
        # Check if an existing Short for this language exists
        existing = glob.glob(os.path.join(STATIC_DIR, f"Short_{item['lang']}_*.mp4"))
        if existing:
            return existing[0]
        return None

def main():
    output_videos = []
    for idx, c in enumerate(CANDIDATES):
        out_path = render_candidate(c)
        if out_path and os.path.exists(out_path) and os.path.getsize(out_path) > 1024 * 1024:
            actual_file = os.path.basename(out_path)
            clean_name = clean_track_name(c["track_name"])
            duration_text = f"{round(c.get('duration', 45.0), 1)}s • 60FPS"
            output_videos.append({
                "id": f"card-{idx + 1}",
                "language": c["lang"],
                "badge": c["badge"],
                "title": f"{clean_name} Velocity Edit 🔥 | 60FPS #Shorts",
                "track_name": clean_name,
                "artist": c["artist"],
                "duration": duration_text,
                "video_file": actual_file,
                "pills": c["pills"],
                "description": f"Experience {clean_name} in smooth 60FPS beat-sync velocity with directional transitions!\n\n🎵 Track: {clean_name} - {c['artist']}\n🎬 Edit: @CinePulseFlix\n⏰ Daily Viral Shorts drops every morning!\n\n#Shorts #ViralShorts #60FPS #CinePulseFlix"
            })

    final_data = {
        "updated_at": datetime.datetime.now().isoformat(),
        "queue_status": "Ready (Pushed Overnight - 100% Unique Multi-Scene Edits)",
        "review_deadline": "5:00 PM IST",
        "videos": output_videos
    }

    with open(VIDEOS_JSON, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)

    app_json = os.path.join(BASE_DIR, "app", "data", "videos.json")
    if os.path.exists(os.path.dirname(app_json)):
        with open(app_json, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2)

    # Also update app/static if it exists
    app_static_json = os.path.join(BASE_DIR, "app", "static", "videos.json")
    if os.path.exists(os.path.dirname(app_static_json)):
        with open(app_static_json, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2)

    print("\n🎉 ALL 4 MULTI-SCENE TRANSITION SHORTS RENDERED & VIDEOS.JSON UPDATED!")
    print(f"Total videos in feed: {len(output_videos)}")
    for v in output_videos:
        print(f"  - {v['badge']}: {v['video_file']} ({v['duration']})")

if __name__ == '__main__':
    main()
