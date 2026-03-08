from datetime import datetime

from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DEFAULT_TOPIC_CONFIG = {
    "primary_terms": [
        "iran",
        "israel",
        "gaza",
        "hamas",
        "hezbollah",
        "idf",
        "tehran",
    ],
    "secondary_terms": [
        "united states",
        "us",
        "u.s.",
        "america",
        "pentagon",
        "white house",
        "middle east",
        "red sea",
        "houthis",
        "syria",
        "lebanon",
        "iraq",
        "yemen",
        "missile",
        "drone",
        "strike",
        "retaliation",
        "ceasefire",
        "sanctions",
        "nuclear",
    ],
    "relevance_threshold": 5,
}


def is_story_used(url: str) -> bool:
    try:
        result = supabase.table("used_stories").select("id").eq("url", url).execute()
        return len(result.data) > 0
    except Exception:
        return False


def mark_story_used(url: str, title: str):
    try:
        supabase.table("used_stories").insert(
            {
                "url": url,
                "title": title,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as exc:
        print(f"DB error: {exc}")


def log_video(title: str, script: str, video_path: str, status: str = "saved"):
    try:
        supabase.table("videos").insert(
            {
                "title": title,
                "script": script,
                "video_path": video_path,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as exc:
        print(f"DB log error: {exc}")


def get_topic_config() -> dict:
    """Load topic targeting config from pipeline_settings.conflict_topics."""
    try:
        result = (
            supabase.table("pipeline_settings")
            .select("value")
            .eq("key", "conflict_topics")
            .limit(1)
            .execute()
        )
        if not result.data:
            return DEFAULT_TOPIC_CONFIG.copy()

        value = result.data[0].get("value") or {}
        primary = value.get("primary_terms") or DEFAULT_TOPIC_CONFIG["primary_terms"]
        secondary = value.get("secondary_terms") or DEFAULT_TOPIC_CONFIG["secondary_terms"]
        threshold = value.get("relevance_threshold", DEFAULT_TOPIC_CONFIG["relevance_threshold"])

        return {
            "primary_terms": [str(x).strip().lower() for x in primary if str(x).strip()],
            "secondary_terms": [str(x).strip().lower() for x in secondary if str(x).strip()],
            "relevance_threshold": int(threshold),
        }
    except Exception as exc:
        print(f"Topic config fallback: {exc}")
        return DEFAULT_TOPIC_CONFIG.copy()
