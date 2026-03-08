import os
import re
import textwrap

import ffmpeg
import requests

from config import OUTPUT_DIR

BACKGROUND_PATH = "media/backgrounds/channel_bg.mp4"
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# Caption style (lower-third, readable)
CAPTION_Y = 1260
CAPTION_FONT_SIZE = 50
CAPTION_WORDS_PER_CHUNK = 2
CAPTION_START_DELAY = 0.45
CAPTION_SIDE_PADDING = 70

# Headline style (modern, bold, animated)
HEADLINE_Y = 430
HEADLINE_FONT_SIZE = 68
HEADLINE_MAX_ITEMS = 4
HEADLINE_FADE_TIME = 0.28
HEADLINE_HOLD_TIME = 1.9


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


def _format_caption_chunk(text: str, line_width: int = 18, max_lines: int = 2) -> str:
    cleaned = " ".join(text.split())
    lines = textwrap.wrap(cleaned, width=line_width)
    if not lines:
        return ""
    return _escape_drawtext("\n".join(lines[:max_lines]))


def _chunk_weight(text: str) -> float:
    words = text.split()
    punctuation_bonus = sum(text.count(p) for p in [",", ".", "?", "!", ":", ";"]) * 0.35
    return max(1.0, len(words) + punctuation_bonus)


def _contains_emphasis(text: str) -> bool:
    words = re.findall(r"\b[A-Za-z]{3,}\b", text)
    return any(word.isupper() for word in words) or ("!" in text) or ("?" in text)


def _split_sentences(script: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", script.strip())
    return [p.strip() for p in parts if p.strip()]


def _headline_from_sentence(sentence: str, max_words: int = 6) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9'\-\s]", "", sentence)
    words = cleaned.split()
    if not words:
        return ""
    return " ".join(words[:max_words]).upper()


def _build_headlines(script: str) -> list[str]:
    sentences = _split_sentences(script)
    candidates = []
    for sentence in sentences:
        if len(sentence.split()) < 4:
            continue
        h = _headline_from_sentence(sentence)
        if h and h not in candidates:
            candidates.append(h)
        if len(candidates) >= HEADLINE_MAX_ITEMS:
            break
    return candidates


def _fade_alpha_expr(start: float, end: float, fade_time: float = HEADLINE_FADE_TIME) -> str:
    fade_in_end = start + fade_time
    fade_out_start = end
    fade_out_end = end + fade_time
    return (
        f"if(lt(t,{start:.2f}),0,"
        f"if(lt(t,{fade_in_end:.2f}),(t-{start:.2f})/{fade_time:.2f},"
        f"if(lt(t,{fade_out_start:.2f}),1,"
        f"if(lt(t,{fade_out_end:.2f}),({fade_out_end:.2f}-t)/{fade_time:.2f},0))))"
    )


def _fade_up_y_expr(start: float, base_y: int = HEADLINE_Y, rise_px: int = 22) -> str:
    return f"{base_y}+{rise_px}-{rise_px}*clip((t-{start:.2f})/{HEADLINE_FADE_TIME:.2f},0,1)"


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

        # Core channel overlays
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

        # Animated headlines for key moments
        if script:
            headlines = _build_headlines(script)
            if headlines:
                timeline_start = 0.8
                timeline_end = max(timeline_start + 1.0, duration - 0.8)
                step = (timeline_end - timeline_start) / max(len(headlines), 1)
                for i, headline in enumerate(headlines):
                    start = timeline_start + (i * step)
                    end = min(start + HEADLINE_HOLD_TIME, duration - 0.4)
                    if end <= start:
                        continue
                    alpha_expr = _fade_alpha_expr(start, end)
                    y_expr = _fade_up_y_expr(start)
                    bg_video = (
                        bg_video.filter(
                            "drawbox",
                            x=120,
                            y=HEADLINE_Y - 16,
                            w=840,
                            h=95,
                            color="0x000000@0.28",
                            t="fill",
                            enable=f"between(t,{start:.2f},{end + HEADLINE_FADE_TIME:.2f})",
                        )
                        .drawtext(
                            text=_escape_drawtext(headline),
                            fontcolor="0xFFE08A",
                            fontsize=HEADLINE_FONT_SIZE,
                            x="(w-text_w)/2",
                            y=y_expr,
                            font="Sans Bold",
                            borderw=3,
                            bordercolor="0x111111",
                            alpha=alpha_expr,
                        )
                    )

        # Phrase-by-phrase lower-third captions
        if script:
            words = script.split()
            chunk_size = CAPTION_WORDS_PER_CHUNK
            chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]

            active_duration = max(0.0, duration - CAPTION_START_DELAY - 0.15)
            weights = [_chunk_weight(chunk) for chunk in chunks]
            total_weight = sum(weights) if weights else 1.0

            elapsed = CAPTION_START_DELAY
            for i, chunk in enumerate(chunks):
                text = _format_caption_chunk(chunk)
                if not text:
                    continue

                part_duration = active_duration * (weights[i] / total_weight)
                start_time = elapsed
                end_time = min(duration - 0.1, start_time + part_duration)
                elapsed = end_time

                is_emphasis = _contains_emphasis(chunk)
                font_color = "0xFFE08A" if is_emphasis else "white"
                box_color = "0x000000@0.60" if is_emphasis else "0x000000@0.46"
                font_size = CAPTION_FONT_SIZE + (4 if is_emphasis else 0)

                bg_video = bg_video.drawtext(
                    text=text,
                    fontcolor=font_color,
                    fontsize=font_size,
                    x="(w-text_w)/2",
                    y=CAPTION_Y,
                    font="Sans",
                    borderw=3,
                    bordercolor="0x101010",
                    box=1,
                    boxcolor=box_color,
                    boxborderw=14,
                    line_spacing=14,
                    alpha=f"if(lt(t,{start_time:.2f}),0,if(lt(t,{start_time + 0.10:.2f}),(t-{start_time:.2f})/0.10,1))",
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
                video_bitrate="4500k",
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
