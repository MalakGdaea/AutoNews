from agent.monitor import get_top_stories
from agent.writer import write_script, write_caption
from db.models import mark_story_used
import os

def run_pipeline(limit: int = 3):
    print("\n🤖 AutoNews Agent Starting...\n")

    # Step 1 — Get top stories
    stories = get_top_stories(limit=limit)

    if not stories:
        print("😴 No fresh stories found. Try again later.")
        return []

    results = []

    for story in stories:
        print(f"\n{'='*50}")
        print(f"📰 Processing: {story['title'][:70]}")
        print(f"{'='*50}")

        # Step 2 — Write script
        script = write_script(story["title"], story["description"])
        if not script:
            continue

        # Step 3 — Write caption
        caption = write_caption(story["title"])

        # Step 4 — Mark story as used
        mark_story_used(story["url"], story["title"])

        result = {
            "title": story["title"],
            "script": script,
            "caption": caption,
            "url": story["url"]
        }

        results.append(result)

        # Print result
        print(f"\n📜 SCRIPT:\n{script}")
        print(f"\n📱 CAPTION:\n{caption}")

    print(f"\n✅ Pipeline complete — {len(results)} scripts ready")
    return results

if __name__ == "__main__":
    run_pipeline(limit=2)