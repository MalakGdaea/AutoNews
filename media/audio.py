from openai import OpenAI
from config import OPENAI_API_KEY, OUTPUT_DIR
import os

client = OpenAI(api_key=OPENAI_API_KEY)
TTS_SPEED = float(os.getenv("TTS_SPEED", "0.92"))

def generate_voiceover(script: str, filename: str) -> str:
    """Convert script text to MP3 voiceover using OpenAI TTS."""
    print(f"🎙️  Generating voiceover...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp3")

    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="onyx",
            input=script,
            speed=TTS_SPEED
        )

        response.stream_to_file(output_path)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"✅ Voiceover saved → {output_path} ({size_kb:.1f} KB)")
        return output_path

    except Exception as e:
        print(f"❌ Voiceover error: {e}")
        return None
