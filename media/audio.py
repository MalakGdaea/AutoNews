from elevenlabs.client import ElevenLabs
from elevenlabs import save
from config import ELEVENLABS_API_KEY, OUTPUT_DIR
import os

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# ElevenLabs voice ID — "Onyx"-like deep male voice equivalent is "Adam" or "George"
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "onwK4e9ZLuTAKqWW03F9")  # Daniel (deep, narration)
MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

def generate_voiceover(script: str, filename: str) -> str:
    """Convert script text to MP3 voiceover using ElevenLabs TTS."""
    print(f"🎙️  Generating voiceover...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp3")

    try:
        audio = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=script,
            model_id=MODEL_ID,
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        )

        save(audio, output_path)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"✅ Voiceover saved → {output_path} ({size_kb:.1f} KB)")
        return output_path

    except Exception as e:
        print(f"❌ Voiceover error: {e}")
        return None