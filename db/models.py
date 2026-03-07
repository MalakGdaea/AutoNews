from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Check if story was already used ──────────────
def is_story_used(url: str) -> bool:
    try:
        result = supabase.table("used_stories") \
            .select("id") \
            .eq("url", url) \
            .execute()
        return len(result.data) > 0
    except:
        return False

# ── Mark story as used ────────────────────────────
def mark_story_used(url: str, title: str):
    try:
        supabase.table("used_stories").insert({
            "url": url,
            "title": title,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"DB error: {e}")

# ── Log a completed video post ────────────────────
def log_video(title: str, script: str, video_path: str, status: str = "saved"):
    try:
        supabase.table("videos").insert({
            "title": title,
            "script": script,
            "video_path": video_path,
            "status": status,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"DB log error: {e}")