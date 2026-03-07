from agent.monitor import get_top_stories
from agent.writer import write_script, write_caption
from media.audio import generate_voiceover
import re

def slugify(text: str) -> str:
    """Convert title to safe filename."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text[:50]

print("\n🚀 Running full pipeline test...\n")

# Step 1 — Get a real news story
stories = get_top_stories(limit=1)

if not stories:
    print("❌ No fresh stories found — try again later")
    exit()

story = stories[0]
print(f"\n📰 Story: {story['title']}")
print(f"📅 Date: {story['published_at']}")

# Step 2 — Write real script
script = write_script(story["title"], story["description"])
if not script:
    print("❌ Script writing failed")
    exit()

print(f"\n📜 SCRIPT:\n{script}")

# Step 3 — Generate voiceover from real script
caption = write_caption(story["title"])
filename = slugify(story["title"])
audio_path = generate_voiceover(script, filename)

print(f"\n📱 CAPTION:\n{caption}")
print(f"\n🎧 Audio saved at: {audio_path}")
print("\n✅ Full pipeline test complete!")