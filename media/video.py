import os
import re
import textwrap

import ffmpeg
import requests

from config import OUTPUT_DIR
from media.captions import caption_chunks_by_chars, caption_schedule, caption_text, escape_drawtext

BACKGROUND_PATH = "media/backgrounds/channel_bg.mp4"
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# Persistent header (shown for full video)
HEADER_BOX_X = 54
HEADER_BOX_Y = 150
HEADER_BOX_W = 972
HEADER_BOX_H = 220
HEADER_TITLE_SIZE = 42
HEADER_TITLE_WRAP = 40
HEADER_TITLE_MAX_LINES = 4
HEADER_PADDING_X = 24
HEADER_PADDING_Y = 18
HEADER_LINE_GAP = 10

# Lower-third captions
CAPTION_Y = 1550
CAPTION_FONT_SIZE = 42
CAPTION_LINE_SPACING = 14
CAPTION_BOX_PADDING = 12
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


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


# def _extract_main_point(script: str) -> str:
#     if not script.strip():
#         return "Top Story Update"
#     first_sentence = re.split(r"(?<=[.!?])\s+", script.strip())[0]
#     return first_sentence.rstrip(".,!?") if first_sentence else "Top Story Update"


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
        .drawtext(text="LIVE", fontcolor="white", fontsize=28, x=40, y=1778, font=FONT_REGULAR)
    )

def _add_persistent_header(video_stream, header_text: str):
    cleaned = " ".join(header_text.split())
    raw_lines = textwrap.wrap(cleaned, width=HEADER_TITLE_WRAP, break_long_words=False)
    if len(raw_lines) > HEADER_TITLE_MAX_LINES:
        raw_lines = raw_lines[:HEADER_TITLE_MAX_LINES]
        last = raw_lines[-1]
        if len(last) > 3:
            raw_lines[-1] = f"{last[:-3].rstrip()}..."
        else:
            raw_lines[-1] = "..."

    if not raw_lines:
        return video_stream

    line_height = HEADER_TITLE_SIZE + HEADER_LINE_GAP
    text_height = len(raw_lines) * line_height
    box_height = max(HEADER_BOX_H, text_height + (HEADER_PADDING_Y * 2))
    y_start = HEADER_BOX_Y + max(HEADER_PADDING_Y, (box_height - text_height) // 2)

    # Draw one unified red rectangle behind all lines
    video_stream = video_stream.filter(
        "drawbox",
        x=HEADER_BOX_X,
        y=HEADER_BOX_Y,
        w=HEADER_BOX_W,
        h=box_height,
        color="0xFF0000@0.85",
        t="fill",
    )

    # Draw each line on top
    for i, line in enumerate(raw_lines):
        y = y_start + (i * line_height)
        video_stream = video_stream.drawtext(
            text=escape_drawtext(line),
            fontcolor="white",
            fontsize=HEADER_TITLE_SIZE,
            x=HEADER_BOX_X + HEADER_PADDING_X,
            y=y,
            font=FONT_BOLD,
            borderw=2,
            bordercolor="0x101010",
        )

    return video_stream

def _add_captions(video_stream, script: str, duration: float):
    if not script.strip():
        return video_stream

    chunks = caption_chunks_by_chars(script, max_chars=35)
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
            boxborderw=CAPTION_BOX_PADDING,
            # line_spacing=CAPTION_LINE_SPACING,
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
        # header_point = _extract_main_point(script)
        bg_video = _add_persistent_header(bg_video, header_title)

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
           ).run(quiet=False, capture_stderr=False, overwrite_output=True)
        except ffmpeg.Error as ffmpeg_exc:
            stderr = ffmpeg_exc.stderr.decode("utf-8", errors="ignore") if ffmpeg_exc.stderr else "no stderr"
            print(f"FFmpeg FULL ERROR:\n{stderr}")
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