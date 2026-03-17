import os
import re
import sys
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from agent.brain import run_pipeline
from media.audio import generate_voiceover
from media.video import generate_video
from media.storage import upload_video_to_storage
from db.models import log_video, mark_story_used
from tiktok.uploader import TikTokUploadError, upload_video
from config import TIKTOK_ACCESS_TOKEN, TIKTOK_DRY_RUN

scheduler = BlockingScheduler()

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text[:50]

def run_full_pipeline():
    print(f"\n{'='*50}")
    print(f"🤖 Scheduler triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    try:
        # Step 1 — Get scripts from agent
        results = run_pipeline(limit=2)

        if not results:
            print("😴 No fresh stories — skipping this run")
            return

        for result in results:
            filename = slugify(result["title"])

            # Step 2 — Generate voiceover
            audio_path = generate_voiceover(result["script"], filename)
            if not audio_path:
                print(f"❌ Audio failed for: {result['title'][:50]}")
                continue

            # Step 3 — Generate video
            video_path = generate_video(
                audio_path=audio_path,
                filename=filename,
                script=result["script"],
                image_url=result.get("image_url")
            )
            if not video_path:
                print(f"❌ Video failed for: {result['title'][:50]}")
                continue

            # Clean up audio file
            os.remove(audio_path)

            # Step 4 — Upload to storage
            storage_url = upload_video_to_storage(video_path, filename)

            # Step 5 — Log to database (initial)
            log_video(
                title=result["title"],
                script=result["script"],
                video_path=storage_url or video_path,
                status="generated",
                video_url=storage_url
            )

            # Step 6 — Upload to TikTok
            try:
                upload_result = upload_video(
                    video_path=video_path,
                    caption=result["caption"],
                    hashtags=None,
                    access_token=TIKTOK_ACCESS_TOKEN,
                    dry_run=False,
                    privacy_level="SELF_ONLY",
                    wait_for_completion=True,
                )
                status = upload_result.get("status", "uploaded")
                if upload_result.get("dry_run"):
                    status = "upload_dry_run"

                log_video(
                    title=result["title"],
                    script=result["script"],
                    video_path=storage_url or video_path,
                    status=status,
                    video_url=storage_url,
                )
                mark_story_used(result.get("story_url"), result["title"])

                print(f"\n✅ Video uploaded: {status}")
            except TikTokUploadError as exc:
                error_status = f"upload_failed: {exc}"
                log_video(
                    title=result["title"],
                    script=result["script"],
                    video_path=storage_url or video_path,
                    status=error_status,
                    video_url=storage_url
                )
                print(f"❌ TikTok upload failed: {exc}")

            # Clean up local video file if uploaded successfully
            if storage_url:
                os.remove(video_path)

            print(f"\n✅ Video ready: {storage_url or video_path}")
            print(f"📱 Caption: {result['caption']}")

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()

def start_scheduler(interval_hours: int = 4):
    """
    Run pipeline every X hours.
    Default: every 4 hours = 6 videos/day
    """
    print(f"⏱️  Scheduler starting — running every {interval_hours} hours")
    print(f"📅 First run: immediately")
    print(f"Press CTRL+C to stop\n")

    # Run immediately on start
    run_full_pipeline()

    # Then run every X hours
    scheduler.add_job(
        run_full_pipeline,
        trigger=IntervalTrigger(hours=interval_hours),
        id='pipeline_job',
        name='AutoNews Pipeline',
        replace_existing=True
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n⛔ Scheduler stopped by user")
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler(interval_hours=4)
