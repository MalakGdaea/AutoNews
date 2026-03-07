from dotenv import load_dotenv
import os

load_dotenv()

# AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Voice
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# News
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Database
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Output
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")