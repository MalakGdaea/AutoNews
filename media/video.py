import os
import textwrap

import ffmpeg
import requests

from config import OUTPUT_DIR

BACKGROUND_PATH = "media/backgrounds/channel_bg.mp4"
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
CAPTION_Y = 820
CAPTION_FONT_SIZE = 56


def download_image(url: str, filename: str) -> str:
    os.makedirs("media/temp", exist_ok=True)
    path = f"media/temp/{filename}.jpg"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
            print("News image downloaded")
            return path
        print("Image download failed -> using fallback")
        return None
    except Exception as e:
        print(f"Image error: {e} -> using fallback")
        return None


def get_audio_duration(audio_path: str) -> float:
    probe = ffmpeg.probe(audio_path)
    for stream in probe["streams"]:
        if stream.get("codec_type") == "audio":
            return float(stream["duration"])
    return float(probe["format"]["duration"])


def _escape_drawtext(text: str) -> str:
    escaped = text.replace("\\", "\\\\")
    escaped = escaped.replace(":", "\\:")
    escaped = escaped.replace("'", "\\'")
    escaped = escaped.replace("%", "\\%")
    return escaped


def _format_caption_chunk(text: str, line_width: int = 22, max_lines: int = 3) -> str:
    cleaned = " ".join(text.split())
    lines = textwrap.wrap(cleaned, width=line_width)
    if not lines:
        return ""
    return _escape_drawtext("\n".join(lines[:max_lines]))


def generate_video(audio_path: str, filename: str, script: str = "", image_url: str = None) -> str:
    print("Assembling video...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp4")

    try:
        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file missing: {audio_path}")

        duration = get_audio_duration(audio_path)
        print(f"Duration: {duration:.1f}s")

        image_path = download_image(image_url, filename) if image_url else None

        if image_path:
            print("Background: news image")
            bg_video = (
                ffmpeg.input(image_path, loop=1, t=duration, framerate=30)
                .video.filter("scale", VIDEO_WIDTH, VIDEO_HEIGHT, force_original_aspect_ratio="increase")
                .filter("crop", VIDEO_WIDTH, VIDEO_HEIGHT)
                .filter(
                    "zoompan",
                    z="min(zoom+0.0005,1.05)",
                    d=int(duration * 30),
                    x="iw/2-(iw/zoom/2)",
                    y="ih/2-(ih/zoom/2)",
                    s=f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
                    fps=30,
                )
            )
        else:
            print("Background: channel default video")
            bg_video = (
                ffmpeg.input(BACKGROUND_PATH, stream_loop=-1, t=duration)
                .video.filter("scale", VIDEO_WIDTH, VIDEO_HEIGHT, force_original_aspect_ratio="increase")
                .filter("crop", VIDEO_WIDTH, VIDEO_HEIGHT)
            )

        bg_video = bg_video.filter("colorchannelmixer", rr=0.5, gg=0.5, bb=0.5)

        bg_video = (
            bg_video.drawtext(
                text="WORLD NEWS 24",
                fontcolor="white",
                fontsize=38,
                x="(w-text_w)/2",
                y=60,
                font="Sans",
                alpha=0.9,
            )
            .filter("drawbox", x=0, y=1750, w=VIDEO_WIDTH, h=80, color="0xCC0000@0.9", t="fill")
            .drawtext(
                text="BREAKING NEWS",
                fontcolor="white",
                fontsize=40,
                x="(w-text_w)/2",
                y=1770,
                font="Sans",
            )
            .drawtext(text="LIVE", fontcolor="white", fontsize=28, x=40, y=1778, font="Sans")
        )

        if script:
            words = script.split()
            chunk_size = 4
            chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
            chunk_duration = duration / max(len(chunks), 1)

            for i, chunk in enumerate(chunks):
                text = _format_caption_chunk(chunk)
                if not text:
                    continue
                start_time = i * chunk_duration
                end_time = start_time + chunk_duration
                bg_video = bg_video.drawtext(
                    text=text,
                    fontcolor="white",
                    fontsize=CAPTION_FONT_SIZE,
                    x="(w-text_w)/2",
                    y=CAPTION_Y,
                    font="Sans",
                    borderw=4,
                    bordercolor="black",
                    box=1,
                    boxcolor="black@0.5",
                    boxborderw=10,
                    line_spacing=18,
                    enable=f"between(t,{start_time:.2f},{end_time:.2f})",
                )

        audio = ffmpeg.input(audio_path).audio.filter("aresample", 44100).filter("volume", 1.2)

        (
            ffmpeg.output(
                bg_video,
                audio,
                output_path,
                vcodec="libx264",
                acodec="aac",
                **{"b:a": "192k"},
                ar=44100,
                ac=2,
                video_bitrate="4000k",
                r=30,
                pix_fmt="yuv420p",
                movflags="+faststart",
                t=duration,
                shortest=None,
                **{"y": None},
            ).run(quiet=True)
        )

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Video saved -> {output_path} ({size_mb:.1f} MB)")
        return output_path
    except Exception as e:
        print(f"Video error: {e}")
        import traceback

        traceback.print_exc()
        return None
