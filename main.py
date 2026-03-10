import argparse
import os
import re
from typing import Dict, Optional

from agent.monitor import get_top_stories
from agent.writer import write_caption, write_script
from config import TIKTOK_ACCESS_TOKEN, TIKTOK_DRY_RUN
from db.models import log_video, mark_story_used
from media.audio import generate_voiceover
from media.storage import upload_video_to_storage
from media.video import generate_video
from tiktok.uploader import TikTokUploadError, upload_video


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:70]


def run_once(
    *,
    story_limit: int = 1,
    dry_run: Optional[bool] = None,
    privacy_level: str = "SELF_ONLY",
) -> Dict[str, str]:
    effective_dry_run = TIKTOK_DRY_RUN if dry_run is None else dry_run

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
        status="generated",
        video_url=storage_url,
    )

    try:
        upload_result = upload_video(
            video_path=video_path,
            caption=caption,
            hashtags=None,
            access_token=TIKTOK_ACCESS_TOKEN,
            dry_run=effective_dry_run,
            privacy_level=privacy_level,
            wait_for_completion=True,
        )
        status = upload_result.get("status", "uploaded")
        if upload_result.get("dry_run"):
            status = "upload_dry_run"

        log_video(
            title=title,
            script=script,
            video_path=storage_url or video_path,
            status=status,
            video_url=storage_url,
        )
        mark_story_used(story_url, title)

        # Clean up local video file
        os.remove(video_path)

        return {
            "title": title,
            "video_path": storage_url or video_path,
            "status": status,
            "caption": caption,
        }
    except TikTokUploadError as exc:
        error_status = f"upload_failed: {exc}"
        log_video(title=title, script=script, video_path=storage_url or video_path, status=error_status, video_url=storage_url)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoNews pipeline runner")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use TikTok uploader dry-run mode regardless of config.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Force live upload mode regardless of config.",
    )
    parser.add_argument(
        "--privacy",
        default="SELF_ONLY",
        help="TikTok privacy level (default: SELF_ONLY).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    effective_dry_run = None
    if args.dry_run and args.live:
        raise ValueError("Use either --dry-run or --live, not both.")
    if args.dry_run:
        effective_dry_run = True
    if args.live:
        effective_dry_run = False

    result = run_once(
        story_limit=1,
        dry_run=effective_dry_run,
        privacy_level=args.privacy,
    )
    print(f"Done: {result['status']} -> {result['video_path']}")


if __name__ == "__main__":
    main()
