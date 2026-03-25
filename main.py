import argparse
import os
import re
from typing import Dict

from agent.monitor import get_top_stories
from agent.writer import write_caption, write_script
from db.models import log_video, mark_story_used
from media.audio import generate_voiceover
from media.storage import upload_video_to_storage
from media.video import generate_video


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:70]


def run_once(
    *,
    story_limit: int = 1,
) -> Dict[str, str]:
    stories = get_top_stories(limit=story_limit)
    if not stories:
        raise RuntimeError("No fresh stories found.")

    story = stories[0]
    title = story["title"]
    description = story.get("description", "")
    image_url = story.get("image_url")
    story_url = story.get("url", "")

    print(f"Selected story: {title}")

    script = write_script(title, description)
    if not script:
        raise RuntimeError("Script generation failed.")

    caption = write_caption(title)
    filename = slugify(title)

    audio_path = generate_voiceover(script, filename)
    if not audio_path:
        raise RuntimeError("Voiceover generation failed.")

    video_path = generate_video(
        audio_path=audio_path,
        filename=filename,
        script=script,
        image_url=image_url,
        title=title,
    )
    if not video_path:
        raise RuntimeError("Video generation failed.")

    # Clean up audio file
    os.remove(audio_path)

    storage_url = upload_video_to_storage(video_path, filename)
    log_video(
        title=title,
        script=script,
        video_path=storage_url or video_path,
        status="ready_to_upload",
        video_url=storage_url,
    )

    mark_story_used(story_url, title)

    # Clean up local video file after storage upload.
    if storage_url:
        os.remove(video_path)

    return {
        "title": title,
        "video_path": storage_url or video_path,
        "status": "ready_to_upload",
        "caption": caption,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoNews pipeline runner")
    parser.add_argument(
        "--story-limit",
        type=int,
        default=1,
        help="Number of fresh stories to generate in one run (default: 1).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_once(
        story_limit=args.story_limit,
    )
    print(f"Done: {result['status']} -> {result['video_path']}")


if __name__ == "__main__":
    main()
