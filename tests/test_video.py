import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from media.video import generate_video

# Your test script
TEST_SCRIPT = """
An Iranian strike near an Israeli nuclear facility has raised fears of a wider regional conflict. 
The attack targeted infrastructure close to the Dimona reactor in the Negev desert. 
Israel has vowed retaliation as world leaders call for immediate de-escalation.
"""

TEST_TITLE = "Iran war shows norms of international conflicts have been overturned"
TEST_IMAGE_URL = None  # or paste a real image URL to test with image background

# Use a real audio file you already have, or create a silent dummy one
import subprocess, os

# Create a silent 30-second audio file for testing
DUMMY_AUDIO = "media/temp/test_audio.mp3"
os.makedirs("media/temp", exist_ok=True)
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
    "-t", "30",
    "-q:a", "9", "-acodec", "libmp3lame",
    DUMMY_AUDIO
], check=True)

# Generate the video
output = generate_video(
    audio_path=DUMMY_AUDIO,
    filename="test_video",
    script=TEST_SCRIPT,
    image_url=TEST_IMAGE_URL,
    title=TEST_TITLE,
)

print(f"\n✅ Test video saved to: {output}")