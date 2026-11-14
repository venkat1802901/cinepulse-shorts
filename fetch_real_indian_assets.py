import os
import subprocess
import json

workspace = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production\Autonomous_Editor_Workspace"
raw_dir = os.path.join(workspace, "raw_footage")
music_dir = os.path.join(workspace, "music_library")

os.makedirs(raw_dir, exist_ok=True)
os.makedirs(music_dir, exist_ok=True)

# 1. Download viral audio (Tauba Tauba Karan Aujla)
audio_out = os.path.join(music_dir, "tauba_tauba_audio.mp3")
if not os.path.exists(audio_out):
    print("Fetching trending Indian audio (Tauba Tauba)...")
    cmd_audio = [
        "python", "-m", "yt_dlp",
        "ytsearch1:Tauba Tauba Karan Aujla audio",
        "-x", "--audio-format", "mp3",
        "-o", os.path.join(music_dir, "tauba_tauba_audio.%(ext)s"),
        "--no-playlist", "--max-downloads", "1"
    ]
    subprocess.run(cmd_audio, check=True)
    print("Audio downloaded successfully!")
else:
    print("Audio already exists:", audio_out)

# 2. Download high-energy raw video footage (real human dance / swagger / car motion)
video_out = os.path.join(raw_dir, "real_raw_footage.mp4")
if not os.path.exists(video_out):
    print("Fetching raw motion video footage...")
    cmd_video = [
        "python", "-m", "yt_dlp",
        "ytsearch1:Vicky Kaushal Tauba Tauba dance performance 4k",
        "-f", "bestvideo[height<=1080][ext=mp4]/best[height<=1080]",
        "-o", video_out,
        "--no-playlist", "--max-downloads", "1"
    ]
    subprocess.run(cmd_video, check=True)
    print("Video downloaded successfully!")
else:
    print("Video already exists:", video_out)
