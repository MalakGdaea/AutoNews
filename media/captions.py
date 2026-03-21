import textwrap
import re

# --- CONFIGURATION ---
# 30 characters is the "Sweet Spot" for a single line on vertical video.
# If text still exits the frame, lower this to 25.
SINGLE_LINE_MAX_CHARS = 30 
CAPTION_START_DELAY = 0.35

def caption_chunks_by_chars(script: str, max_chars: int = SINGLE_LINE_MAX_CHARS) -> list[str]:
    """
    Splits the script into a list of strings. Each string is a single line 
    that does not exceed the max_chars limit.
    """
    if not script:
        return []
    # textwrap.wrap handles the logic of not breaking words in half
    return textwrap.wrap(script, width=max_chars, break_long_words=False)

def escape_drawtext(text: str) -> str:
    """
    Cleans text and escapes special characters for the FFmpeg drawtext filter.
    """
    if not text:
        return ""

    # Normalize problematic unicode characters to standard ASCII
    replacements = {
        "\u2026": "...",  # ellipsis
        "\u2018": "'",    # left single quote
        "\u2019": "'",    # right single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2013": "-",    # en dash
        "\u2014": "-",    # em dash
        "\u00a0": " ",    # non-breaking space
        "\u200b": "",     # zero-width space
        "\ufeff": "",     # BOM
        "\r": "",         # carriage return
    }

    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Remove ALL non-printable/control characters
    text = re.sub(r"[^\x20-\x7E\n]", "", text)

    # Convert to ASCII only (removes emojis, unsupported glyphs)
    text = text.encode("ascii", errors="ignore").decode("ascii")

    # Clean extra spaces
    text = " ".join(text.split())

    # Escape specifically for FFmpeg's parsing engine
    text = text.replace("\\", "\\\\")  # escape backslashes
    text = text.replace(":", "\\:")    # escape colons
    text = text.replace("%", "\\%")    # escape %

    return text

def caption_text(chunk: str) -> str:
    """
    Processes a single chunk of text for display.
    """
    escaped_text = escape_drawtext(chunk)
    return escaped_text.strip()

def caption_schedule(total_duration: float, chunk_count: int, start_delay: float = CAPTION_START_DELAY) -> list[tuple[float, float]]:
    """
    Calculates the start and end timestamps for each subtitle chunk.
    """
    if chunk_count <= 0 or total_duration <= 0:
        return []

    # Leave a small buffer at the very end
    active_duration = max(0.1, total_duration - start_delay - 0.1)
    part_duration = active_duration / chunk_count

    slots = []
    for i in range(chunk_count):
        start_time = start_delay + (i * part_duration)
        end_time = min(total_duration - 0.05, start_time + part_duration)
        if end_time > start_time:
            slots.append((start_time, end_time))
    return slots

# --- EXAMPLE USAGE ---
# script = "This is a long sentence that we want to keep on one single line per screen."
# video_len = 10.0
#
# chunks = caption_chunks_by_chars(script)
# schedule = caption_schedule(video_len, len(chunks))
#
# for i, chunk in enumerate(chunks):
#     display_text = caption_text(chunk)
#     start, end = schedule[i]
#     print(f"[{start:.2f}s - {end:.2f}s]: {display_text}")