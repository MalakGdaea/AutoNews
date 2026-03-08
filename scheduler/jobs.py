from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from agent.brain import run_pipeline
from media.audio import generate_voiceover
from media.video import generate_video
from db.models import log_video
import re
import os
from datetime import datetime

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

            # Step 4 — Log to database
            log_video(
                title=result["title"],
                script=result["script"],
                video_path=video_path,
                status="ready"
            )

            print(f"\n✅ Video ready: {video_path}")
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