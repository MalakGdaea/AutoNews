from agent.monitor import get_top_stories
from agent.writer import write_script, write_caption
from media.audio import generate_voiceover
from media.video import generate_video
import re

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text[:50]

print("\n🚀 Running full pipeline test...\n")

# Step 1 — Get story
stories = get_top_stories(limit=1)
if not stories:
    print("❌ No fresh stories found")
    exit()

story = stories[0]
print(f"📰 Story: {story['title']}")
print(f"📅 Date: {story['published_at']}")
print(f"🖼️  Image: {story.get('image_url', 'None')}")

# Step 2 — Write script + caption
script = write_script(story["title"], story["description"])
caption = write_caption(story["title"])
filename = slugify(story["title"])

print(f"\n📜 SCRIPT:\n{script}")
print(f"\n📱 CAPTION:\n{caption}")

# Step 3 — Generate voiceover
audio_path = generate_voiceover(script, filename)

# Step 4 — Generate video
video_path = generate_video(
    audio_path=audio_path,
    filename=filename,
    script=script,
    image_url=story.get("image_url")
)

print(f"\n🎬 Video ready at: {video_path}")
print("\n✅ Full pipeline complete!")