import textwrap
import re

CAPTION_WORDS_PER_CHUNK = 8
CAPTION_START_DELAY = 0.35
CAPTION_WRAP_WIDTH = 28
CAPTION_MAX_LINES = 3


def escape_drawtext(text: str) -> str:
    if not text:
        return ""

    # Normalize problematic unicode characters
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

    # 🚨 Remove ALL control characters (critical fix)
    text = re.sub(r"[^\x20-\x7E\n]", "", text)

    # Convert to ASCII only (removes emojis, unsupported glyphs)
    text = text.encode("ascii", errors="ignore").decode("ascii")

    # Clean extra spaces
    text = " ".join(text.split())

    # Escape for FFmpeg drawtext
    text = text.replace("\\", "\\\\")  # escape backslashes
    text = text.replace(":", "\\:")    # escape colons
    text = text.replace("%", "\\%")    # escape %

    return text

def caption_chunks(script: str, words_per_chunk: int = CAPTION_WORDS_PER_CHUNK) -> list[str]:
    words = script.split()
    return [" ".join(words[i : i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]


def caption_text(chunk: str, wrap_width: int = CAPTION_WRAP_WIDTH, max_lines: int = CAPTION_MAX_LINES) -> str:
    # First escape the text, then wrap the escaped version
    escaped_text = escape_drawtext(chunk)
    lines = textwrap.wrap(escaped_text, width=wrap_width)
    if not lines:
        return ""
    return "\n".join(lines[:max_lines])


def caption_schedule(total_duration: float, chunk_count: int, start_delay: float = CAPTION_START_DELAY) -> list[tuple[float, float]]:
    if chunk_count <= 0 or total_duration <= 0:
        return []

    active_duration = max(0.1, total_duration - start_delay - 0.1)
    part_duration = active_duration / chunk_count

    slots = []
    for i in range(chunk_count):
        start_time = start_delay + i * part_duration
        end_time = min(total_duration - 0.05, start_time + part_duration)
        if end_time > start_time:
            slots.append((start_time, end_time))
    return slots
