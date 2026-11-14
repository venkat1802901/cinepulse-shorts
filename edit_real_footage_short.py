import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_vignette(width, height, strength=0.45):
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    xx, yy = np.meshgrid(x, y)
    radius = np.sqrt(xx**2 + yy**2) / np.sqrt(2)
    vignette = 1.0 - strength * (radius ** 1.8)
    return np.clip(vignette, 0.25, 1.0)[:, :, np.newaxis]

def apply_cinematic_color_grade(img_bgr):
    # img_bgr is float32 in [0, 1]
    b = img_bgr[:, :, 0]
    g = img_bgr[:, :, 1]
    r = img_bgr[:, :, 2]
    
    # Warm golden/amber tone mapping in midtones & highlights
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    warm_mask = np.clip((lum - 0.25) * 1.5, 0, 1)
    r += warm_mask * 0.07
    g += warm_mask * 0.02
    
    # Deep contrast curve
    graded = np.clip(np.dstack([b, g, r]), 0, 1)
    graded = 0.5 * (1.0 + np.sin((graded - 0.5) * np.pi))
    return graded

def render_lyrical_overlay(frame_bgr, line_words, current_time, font_path, base_font_size=68, y_ratio=0.78):
    if not line_words:
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    pil_img = Image.fromarray(cv2.cvtColor((frame_bgr * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert("RGBA")
    txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    normal_font = ImageFont.truetype(font_path, base_font_size)
    active_font = ImageFont.truetype(font_path, int(base_font_size * 1.18))
    
    word_metrics = []
    space_w = normal_font.getlength("  ")
    total_w = 0
    
    for word, t_start, t_end in line_words:
        is_active = (t_start <= current_time <= t_end)
        font = active_font if is_active else normal_font
        w_len = font.getlength(word)
        h_len = base_font_size * 1.3
        word_metrics.append((word, t_start, t_end, is_active, font, w_len, h_len))
        total_w += w_len + space_w
    total_w -= space_w
    
    start_x = (w - total_w) / 2
    cur_x = start_x
    center_y = int(h * y_ratio)
    
    for word, t_start, t_end, is_active, font, w_len, h_len in word_metrics:
        if current_time < t_start:
            text_color = (255, 255, 255, 100)
            shadow_color = (0, 0, 0, 90)
            glow = False
            y_offset = 0
        elif is_active:
            # Active word: Radiant Gold with energetic bounce
            progress = (current_time - t_start) / max(0.001, (t_end - t_start))
            bounce = np.sin(progress * np.pi) * 8.0
            text_color = (255, 215, 0, 255)
            shadow_color = (0, 0, 0, 255)
            glow = True
            y_offset = -int(bounce)
        else:
            text_color = (255, 255, 255, 240)
            shadow_color = (0, 0, 0, 220)
            glow = False
            y_offset = 0
            
        draw_y = center_y - h_len / 2 + y_offset
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx*dx + dy*dy <= 18:
                    draw.text((cur_x + dx, draw_y + dy), word, font=font, fill=shadow_color)
        if glow:
            for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
                draw.text((cur_x + dx, draw_y + dy), word, font=font, fill=(255, 160, 0, 180))
        draw.text((cur_x, draw_y), word, font=font, fill=text_color)
        cur_x += w_len + space_w
        
    composed = Image.alpha_composite(pil_img, txt_layer)
    res_bgr = cv2.cvtColor(np.array(composed.convert("RGB")), cv2.COLOR_RGB2BGR)
    return res_bgr.astype(np.float32) / 255.0

def crop_to_vertical_9_16(frame_1080p, center_x_ratio=0.5):
    # frame_1080p is (1080, 1920, 3)
    # We want 9:16 -> (1920, 1080) vertical!
    # Height is 1080, so 9:16 vertical width = 1080 * 9 / 16 = 607.5 px
    # Or scale height to 1920, meaning scale factor = 1920 / 1080 = 1.777
    # Scaled width = 1920 * 1.777 = 3413 px.
    # Cropping 1080 px from center of 3413 gives perfect 1080x1920 full-screen vertical!
    h, w = frame_1080p.shape[:2]
    # Resize frame so height is 1920
    scaled_w = int(w * (1920.0 / h))
    scaled = cv2.resize(frame_1080p, (scaled_w, 1920), interpolation=cv2.INTER_LANCZOS4)
    
    # Calculate crop center
    cx = int(scaled_w * center_x_ratio)
    x1 = max(0, min(scaled_w - 1080, cx - 540))
    x2 = x1 + 1080
    return scaled[:, x1:x2]

def main():
    workspace = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production\Autonomous_Editor_Workspace"
    raw_video = os.path.join(workspace, "raw_footage", "tauba_tauba_raw.mp4")
    raw_audio = os.path.join(workspace, "music_library", "tauba_tauba_audio.mp3")
    exports_dir = os.path.join(workspace, "exports")
    font_path = r"C:\Windows\Fonts\impact.ttf"
    
    cap = cv2.VideoCapture(raw_video)
    fps_in = cap.get(cv2.CAP_PROP_FPS)
    print(f"Reading raw footage: {raw_video} (Input FPS: {fps_in:.2f})")
    
    # We will assemble a 14.0 second high-energy edit:
    # Segment 1 (0.0s - 3.5s): Hook swagger walk (starts at 36.5s in raw video)
    # Segment 2 (3.5s - 7.5s): The iconic footwork slide (starts at 42.2s in raw video)
    # Segment 3 (7.5s - 14.0s): High-energy chorus drop & climax (starts at 52.0s in raw video)
    
    segments = [
        {"raw_start_s": 36.5, "dur_s": 3.5, "speed": 1.0, "center_x": 0.50},
        {"raw_start_s": 42.2, "dur_s": 4.0, "speed": 1.0, "center_x": 0.52},
        {"raw_start_s": 52.0, "dur_s": 6.5, "speed": 1.0, "center_x": 0.50}
    ]
    
    target_fps = 30
    total_duration = 14.0
    total_frames = int(total_duration * target_fps)
    
    temp_raw_out = os.path.join(exports_dir, "temp_edited_video.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(temp_raw_out, fourcc, target_fps, (1080, 1920))
    vignette = create_vignette(1080, 1920, strength=0.42)
    
    # Lyrical timing for the 14-second edit
    lyrics = [
        (0.2, 3.4, [
            ("HUSN", 0.3, 1.1),
            ("TERA...", 1.1, 1.9),
            ("KILLER", 1.9, 2.6),
            ("LOOKS", 2.6, 3.3)
        ]),
        (3.5, 7.4, [
            ("TAUBA", 3.6, 4.4),
            ("TAUBA!", 4.4, 5.3),
            ("THAT", 5.3, 6.0),
            ("VIRAL", 6.0, 6.7),
            ("SLIDE", 6.7, 7.4)
        ]),
        (7.5, 11.2, [
            ("CHARCHA", 7.6, 8.4),
            ("TERA", 8.4, 9.1),
            ("HAR", 9.1, 9.7),
            ("TARAF!", 9.7, 11.1)
        ]),
        (11.3, 14.0, [
            ("TAUBA", 11.4, 12.3),
            ("TAUBA!", 12.3, 13.8)
        ])
    ]
    
    print(f"Beginning frame-by-frame professional edit ({total_frames} frames @ 30 FPS)...")
    
    # Extract frames from segment 1, 2, 3
    assembled_frames = []
    
    for seg_idx, seg in enumerate(segments):
        start_frame = int(seg["raw_start_s"] * fps_in)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        num_seg_frames = int(seg["dur_s"] * target_fps)
        step = fps_in / target_fps  # frame skip to convert 60fps to 30fps
        
        print(f"Editing Segment {seg_idx+1}: {seg['dur_s']}s from {seg['raw_start_s']}s raw footage...")
        for i in range(num_seg_frames):
            target_f = start_frame + int(i * step)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_f)
            ret, frame = cap.read()
            if not ret:
                break
                
            # Crop to vertical 9:16 (1080x1920)
            vert_frame = crop_to_vertical_9_16(frame, center_x_ratio=seg["center_x"])
            assembled_frames.append(vert_frame)
            
    cap.release()
    print(f"Extracted and cropped {len(assembled_frames)} real full-motion frames!")
    
    # Now apply transitions, color grading, film grain, and kinetic typography
    for f_idx in range(min(total_frames, len(assembled_frames))):
        t = f_idx / target_fps
        frame = assembled_frames[f_idx].astype(np.float32) / 255.0
        
        # Transition 1: Flash & speed whip at 3.5s (frames 100-110)
        if 3.4 <= t <= 3.75:
            flash = (0.35 - abs(t - 3.55)) / 0.35
            frame = np.clip(frame + flash * 0.45, 0, 1)
            
        # Transition 2: Drop impact flash + chromatic split at 7.5s (frames 220-230)
        if 7.4 <= t <= 7.8:
            flash = (0.4 - abs(t - 7.6)) / 0.4
            shift = int(flash * 12)
            if shift > 0:
                frame[:, :, 2] = np.roll(frame[:, :, 2], shift, axis=1) # Red split
                frame[:, :, 0] = np.roll(frame[:, :, 0], -shift, axis=1) # Blue split
            frame = np.clip(frame + flash * 0.5, 0, 1)

        # Apply Bollywood Warm Grade & Vignette
        graded = apply_cinematic_color_grade(frame)
        graded = graded * vignette
        
        # 35mm fine film grain
        grain = np.random.normal(0, 0.012, (1920, 1080, 1)).astype(np.float32)
        final_frame = np.clip(graded + grain, 0, 1)
        
        # Overlay kinetic lyrics
        active_line = None
        for l_start, l_end, words in lyrics:
            if l_start <= t < l_end:
                active_line = words
                break
        if active_line:
            final_frame = render_lyrical_overlay(final_frame, active_line, current_time=t, font_path=font_path, base_font_size=68, y_ratio=0.78)
            
        frame_u8 = (final_frame * 255.0).astype(np.uint8)
        writer.write(frame_u8)
        
        if (f_idx + 1) % 60 == 0:
            print(f"Rendered {f_idx + 1}/{total_frames} frames ({int((f_idx+1)/total_frames*100)}%)...")
            
    writer.release()
    print("Video frame generation completed successfully!")
    
    # Multiplex with real audio track from 41.5s to 55.5s (14s)
    final_audio_master = os.path.join(exports_dir, "Short_REAL_FOOTAGE_TaubaTauba_Audio_Master.mp4")
    final_visual_noaudio = os.path.join(exports_dir, "Short_REAL_FOOTAGE_TaubaTauba_Visual_NoAudio.mp4")
    
    # 1. Clean Visual Master
    cmd_noaudio = f'ffmpeg -y -i "{temp_raw_out}" -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.2 -crf 18 -r 30 "{final_visual_noaudio}"'
    os.system(cmd_noaudio)
    
    # 2. Master with synced real audio
    cmd_audio = f'ffmpeg -y -i "{temp_raw_out}" -ss 00:00:41.5 -t 14.0 -i "{raw_audio}" -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.2 -crf 18 -r 30 -c:a aac -b:a 320k -shortest "{final_audio_master}"'
    os.system(cmd_audio)
    
    if os.path.exists(temp_raw_out):
        os.remove(temp_raw_out)
        
    print("\n=== FINAL DELIVERABLES READY ===")
    print(f"1. Real Footage Audio Master: {final_audio_master}")
    print(f"2. Real Footage Visual-Only Master: {final_visual_noaudio}")

if __name__ == '__main__':
    main()
