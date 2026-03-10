import textwrap

CAPTION_WORDS_PER_CHUNK = 8
CAPTION_START_DELAY = 0.35
CAPTION_WRAP_WIDTH = 28
CAPTION_MAX_LINES = 3


def escape_drawtext(text: str) -> str:
    escaped = text.replace("\\", "\\\\")
    escaped = escaped.replace(":", "\\:")
    escaped = escaped.replace("'", "\\'")
    escaped = escaped.replace("%", "\\%")
    return escaped


def caption_chunks(script: str, words_per_chunk: int = CAPTION_WORDS_PER_CHUNK) -> list[str]:
    words = script.split()
    return [" ".join(words[i : i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]


def caption_text(chunk: str, wrap_width: int = CAPTION_WRAP_WIDTH, max_lines: int = CAPTION_MAX_LINES) -> str:
    lines = textwrap.wrap(" ".join(chunk.split()), width=wrap_width)
    if not lines:
        return ""
    return escape_drawtext("\n".join(lines[:max_lines]))


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
