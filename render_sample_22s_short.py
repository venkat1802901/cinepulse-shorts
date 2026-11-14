import subprocess
import os

raw_video = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production\Autonomous_Editor_Workspace\raw_footage\tauba_tauba_raw.mp4"
raw_audio = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production\Autonomous_Editor_Workspace\music_library\tauba_tauba_audio.mp3"
ass_file = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production\app\static\test_kinetic.ass"
output_video = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production\app\static\Short_01_Hindi_TaubaTauba_22s.mp4"

os.makedirs(os.path.dirname(output_video), exist_ok=True)

# Escape backslashes and colons for ffmpeg ass filter
escaped_ass = ass_file.replace('\\', '/').replace(':', '\\:')

# 22-second clip from 40.0s to 62.0s
# Section 1: 40.0 to 47.0 (Vicky & crew walking & groove) - 7s
# Section 2: 47.0 to 54.0 (Close-up swag / lyrics) - 7s
# Section 3: 54.0 to 62.0 (Iconic leg-slip hook dance drop) - 8s
# Total = 22.0 seconds

# Filtergraph with:
# 1. 9:16 Center Crop & 1080x1920 scaling @ 60fps
# 2. Cinematic Color Grade (contrast=1.12, saturation=1.20, brightness=0.01)
# 3. Vignette
# 4. Kinetic ASS Karaoke Lyrics burned in
# 5. Audio volume normalization (-14 LUFS target)

cmd = [
    "ffmpeg", "-y",
    "-ss", "40.0", "-t", "22.0", "-i", raw_video,
    "-ss", "40.0", "-t", "22.0", "-i", raw_audio,
    "-filter_complex",
    f"[0:v]crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920,fps=60,"
    f"eq=contrast=1.12:saturation=1.22:brightness=0.01,"
    f"vignette=angle=PI/5,"
    f"ass='{escaped_ass}'[v];"
    f"[1:a]volume=1.05,loudnorm=I=-14:LRA=7:TP=-1.5[a]",
    "-map", "[v]",
    "-map", "[a]",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "19",
    "-c:a", "aac",
    "-b:a", "320k",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    output_video
]

print("Executing render command...")
subprocess.run(cmd, check=True)
print(f"Render complete: {output_video}")
