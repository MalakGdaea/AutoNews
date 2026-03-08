import ffmpeg
import os
import requests
from config import OUTPUT_DIR

BACKGROUND_PATH = "media/backgrounds/channel_bg.mp4"

def download_image(url: str, filename: str) -> str:
    os.makedirs("media/temp", exist_ok=True)
    path = f"media/temp/{filename}.jpg"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
            print(f"✅ News image downloaded")
            return path
        else:
            print(f"⚠️  Image download failed → using fallback")
            return None
    except Exception as e:
        print(f"⚠️  Image error: {e} → using fallback")
        return None

def get_audio_duration(audio_path: str) -> float:
    probe = ffmpeg.probe(audio_path)
    for stream in probe['streams']:
        if stream['codec_type'] == 'audio':
            return float(stream['duration'])
    return float(probe['format']['duration'])

def generate_video(audio_path: str, filename: str, script: str = "", image_url: str = None) -> str:
    print(f"🎬 Assembling video...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp4")

    try:
        duration = get_audio_duration(audio_path)
        print(f"   Duration: {duration:.1f}s")

        # ── Background ──────────────────────────────
        image_path = None
        if image_url:
            image_path = download_image(image_url, filename)

        if image_path:
            print(f"   Background: news image")
            bg_video = (
                ffmpeg
                .input(image_path, loop=1, t=duration, framerate=30)
                .video
                .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
                .filter('crop', 1080, 1920)
                .filter('zoompan',
                    z='min(zoom+0.0005,1.05)',
                    d=int(duration * 30),
                    x='iw/2-(iw/zoom/2)',
                    y='ih/2-(ih/zoom/2)',
                    s='1080x1920',
                    fps=30
                )
            )
        else:
            print(f"   Background: channel default video")
            bg_video = (
                ffmpeg
                .input(BACKGROUND_PATH, stream_loop=-1, t=duration)
                .video
                .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
                .filter('crop', 1080, 1920)
            )

        # ── Dark overlay ─────────────────────────────
        bg_video = bg_video.filter('colorchannelmixer', rr=0.5, gg=0.5, bb=0.5)

        # ── Overlays ─────────────────────────────────
        bg_video = (
            bg_video
            .drawtext(
                text='WORLD NEWS 24',
                fontcolor='white',
                fontsize=38,
                x='(w-text_w)/2',
                y=60,
                font='Sans',
                alpha=0.9
            )
            .filter('drawbox',
                x=0, y=1750, w=1080, h=80,
                color='0xCC0000@0.9',
                t='fill'
            )
            .drawtext(
                text='BREAKING NEWS',
                fontcolor='white',
                fontsize=40,
                x='(w-text_w)/2',
                y=1770,
                font='Sans'
            )
            .drawtext(
                text='● LIVE',
                fontcolor='white',
                fontsize=28,
                x=40,
                y=1778,
                font='Sans'
            )
        )

        # ── Captions ─────────────────────────────────
        if script:
            words = script.split()
            chunk_size = 5
            chunks = [' '.join(words[i:i+chunk_size])
                     for i in range(0, len(words), chunk_size)]
            chunk_duration = duration / len(chunks)

            for i, chunk in enumerate(chunks):
                start_time = i * chunk_duration
                end_time = start_time + chunk_duration
                bg_video = bg_video.drawtext(
                    text=chunk,
                    fontcolor='white',
                    fontsize=58,
                    x='(w-text_w)/2',
                    y=860,
                    font='Sans',
                    borderw=4,
                    bordercolor='black',
                    box=1,
                    boxcolor='black@0.5',
                    boxborderw=10,
                    enable=f'between(t,{start_time:.2f},{end_time:.2f})'
                )

        # ── Merge video + audio ───────────────────────
        audio = ffmpeg.input(audio_path)

        (
            ffmpeg
            .output(
                bg_video,
                audio.audio,
                output_path,
                vcodec='libx264',
                acodec='aac',
                **{'b:a': '192k'},
                ar=44100,
                ac=2,
                video_bitrate='4000k',
                r=30,
                t=duration,
                **{'y': None}
            )
            .run(quiet=True)
        )

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Video saved → {output_path} ({size_mb:.1f} MB)")
        return output_path

    except Exception as e:
        print(f"❌ Video error: {e}")
        import traceback
        traceback.print_exc()
        return None