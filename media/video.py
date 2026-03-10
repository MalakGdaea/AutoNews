import os
import re
import textwrap

import ffmpeg
import requests

from config import OUTPUT_DIR
from media.captions import caption_chunks, caption_schedule, caption_text, escape_drawtext

BACKGROUND_PATH = "media/backgrounds/channel_bg.mp4"
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# Persistent header (shown for full video)
HEADER_BOX_X = 70
HEADER_BOX_Y = 160
HEADER_BOX_W = 940
HEADER_BOX_H = 190
HEADER_TITLE_SIZE = 48
HEADER_POINT_SIZE = 40
HEADER_TITLE_WRAP = 28
HEADER_POINT_WRAP = 36
HEADER_TITLE_MAX_LINES = 2
HEADER_POINT_MAX_LINES = 2

# Lower-third captions
CAPTION_Y = 1270
CAPTION_FONT_SIZE = 48
FONT_REGULAR = "DejaVu Sans"
FONT_BOLD = "DejaVu Sans Bold"


def download_image(url: str, filename: str) -> str:
    os.makedirs("media/temp", exist_ok=True)
    path = f"media/temp/{filename}.jpg"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
            print("News image downloaded")
            return path
        print("Image download failed -> using fallback")
        return None
    except Exception as exc:
        print(f"Image error: {exc} -> using fallback")
        return None


def get_audio_duration(audio_path: str) -> float:
    probe = ffmpeg.probe(audio_path)
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "audio":
            return float(stream["duration"])
    return float(probe["format"]["duration"])


def _clean_title_from_filename(filename: str) -> str:
    return " ".join(filename.replace("_", " ").split()).title()


def _extract_main_point(script: str, max_words: int = 9) -> str:
    if not script.strip():
        return "Top Story Update"
    first_sentence = re.split(r"(?<=[.!?])\s+", script.strip())[0]
    words = first_sentence.split()
    short = " ".join(words[:max_words]).strip()
    return short.rstrip(".,!?") if short else "Top Story Update"


def _header_text(text: str, *, wrap_width: int, max_lines: int) -> tuple[str, int]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ("", 0)
    lines = textwrap.wrap(cleaned, width=wrap_width)
    trimmed = lines[:max_lines]
    return (escape_drawtext("\n".join(trimmed)), len(trimmed))


def _build_background(duration: float, image_path: str | None):
    if image_path:
        print("Background: news image")
        return (
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

    if os.path.exists(BACKGROUND_PATH):
        print("Background: channel default video")
        return (
            ffmpeg.input(BACKGROUND_PATH, stream_loop=-1, t=duration)
            .video.filter("scale", VIDEO_WIDTH, VIDEO_HEIGHT, force_original_aspect_ratio="increase")
            .filter("crop", VIDEO_WIDTH, VIDEO_HEIGHT)
        )

    print("Background: fallback color (missing channel_bg.mp4)")
    return (
        ffmpeg.input(f"color=c=#111111:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r=30", f="lavfi", t=duration)
        .video
    )


def _add_branding(video_stream):
    return (
        video_stream.filter("colorchannelmixer", rr=0.5, gg=0.5, bb=0.5)
        .drawtext(
            text="WORLD NEWS 24",
            fontcolor="white",
            fontsize=36,
            x="(w-text_w)/2",
            y=70,
            font=FONT_REGULAR,
            alpha=0.9,
        )
        .filter("drawbox", x=0, y=1750, w=VIDEO_WIDTH, h=80, color="0xCC0000@0.9", t="fill")
        .drawtext(
            text="BREAKING NEWS",
            fontcolor="white",
            fontsize=38,
            x="(w-text_w)/2",
            y=1770,
            font=FONT_REGULAR,
        )
        .drawtext(text="LIVE", fontcolor="white", fontsize=28, x=40, y=1778, font="Sans")
    )


def _add_persistent_header(video_stream, title: str, main_point: str):
    title_text, title_lines = _header_text(
        title,
        wrap_width=HEADER_TITLE_WRAP,
        max_lines=HEADER_TITLE_MAX_LINES,
    )
    point_text, point_lines = _header_text(
        main_point,
        wrap_width=HEADER_POINT_WRAP,
        max_lines=HEADER_POINT_MAX_LINES,
    )

    title_y = HEADER_BOX_Y + 28
    line_gap = 6
    point_y = title_y + (max(1, title_lines) * (HEADER_TITLE_SIZE + line_gap)) + 8

    return (
        video_stream.filter(
            "drawbox",
            x=HEADER_BOX_X,
            y=HEADER_BOX_Y,
            w=HEADER_BOX_W,
            h=HEADER_BOX_H,
            color="0x000000@0.45",
            t="fill",
        )
        .drawtext(
            text=title_text,
            fontcolor="0xFFE08A",
            fontsize=HEADER_TITLE_SIZE,
            x=HEADER_BOX_X + 28,
            y=title_y,
            font=FONT_BOLD,
            borderw=2,
            bordercolor="0x101010",
            line_spacing=10,
        )
        .drawtext(
            text=point_text,
            fontcolor="white",
            fontsize=HEADER_POINT_SIZE,
            x=HEADER_BOX_X + 28,
            y=point_y,
            font=FONT_REGULAR,
            borderw=2,
            bordercolor="0x101010",
            line_spacing=8,
        )
    )


def _add_captions(video_stream, script: str, duration: float):
    if not script.strip():
        return video_stream

    chunks = caption_chunks(script)
    schedule = caption_schedule(duration, len(chunks))

    for chunk, (start_time, end_time) in zip(chunks, schedule):
        text = caption_text(chunk)
        if not text:
            continue

        video_stream = video_stream.drawtext(
            text=text,
            fontcolor="white",
            fontsize=CAPTION_FONT_SIZE,
            x="(w-text_w)/2",
            y=CAPTION_Y,
            font=FONT_REGULAR,
            borderw=3,
            bordercolor="0x101010",
            box=1,
            boxcolor="0x000000@0.50",
            boxborderw=14,
            line_spacing=12,
            enable=f"between(t,{start_time:.2f},{end_time:.2f})",
        )

    return video_stream


def generate_video(
    audio_path: str,
    filename: str,
    *,
    script: str = "",
    image_url: str | None = None,
    title: str = "",
) -> str:
    print("Assembling video...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp4")

    try:
        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file missing: {audio_path}")

        duration = get_audio_duration(audio_path)
        print(f"Duration: {duration:.1f}s")

        image_path = download_image(image_url, filename) if image_url else None
        bg_video = _build_background(duration, image_path)
        bg_video = _add_branding(bg_video)

        header_title = title or _clean_title_from_filename(filename)
        header_point = _extract_main_point(script)
        bg_video = _add_persistent_header(bg_video, header_title, header_point)

        bg_video = _add_captions(bg_video, script, duration)

        audio = ffmpeg.input(audio_path).audio.filter("aresample", 44100).filter("volume", 1.2)

        try:
            ffmpeg.output(
                bg_video,
                audio,
                output_path,
                vcodec="libx264",
                acodec="aac",
                **{"b:a": "192k"},
                ar=44100,
                ac=2,
                video_bitrate="4500k",
                r=30,
                pix_fmt="yuv420p",
                movflags="+faststart",
                t=duration,
                shortest=None,
                **{"y": None},
            ).run(quiet=True, capture_stderr=True)
        except ffmpeg.Error as ffmpeg_exc:
            try:
                stderr = ffmpeg_exc.stderr.decode("utf-8", errors="ignore")
            except Exception:
                stderr = str(ffmpeg_exc)
            print(f"FFmpeg stderr: {stderr}")
            raise
        finally:
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as exc:
                    print(f"Temp image cleanup failed: {exc}")

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Video saved -> {output_path} ({size_mb:.1f} MB)")
        return output_path
    except Exception as exc:
        print(f"Video error: {exc}")
        import traceback

        traceback.print_exc()
        return None
