import os
from datetime import datetime

from supabase import create_client

from config import (
    SUPABASE_KEY,
    SUPABASE_STORAGE_BUCKET,
    SUPABASE_STORAGE_PUBLIC,
    SUPABASE_STORAGE_SIGNED_EXPIRES,
    SUPABASE_URL,
)


def _get_storage_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials are missing.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_video_to_storage(local_path: str, filename: str) -> str | None:
    if not SUPABASE_STORAGE_BUCKET:
        print("Storage upload skipped: SUPABASE_STORAGE_BUCKET not set.")
        return None

    if not local_path or not os.path.exists(local_path):
        raise FileNotFoundError(f"Video file missing: {local_path}")

    client = _get_storage_client()
    ext = os.path.splitext(local_path)[1] or ".mp4"
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    object_name = f"videos/{filename}_{timestamp}{ext}"

    try:
        with open(local_path, "rb") as file_handle:
            client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
                object_name,
                file_handle,
                {"content-type": "video/mp4", "upsert": True},
            )
    except Exception as exc:
        print(f"Storage upload failed: {exc}")
        return None

    if SUPABASE_STORAGE_PUBLIC:
        return client.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(object_name)

    try:
        signed = client.storage.from_(SUPABASE_STORAGE_BUCKET).create_signed_url(
            object_name,
            SUPABASE_STORAGE_SIGNED_EXPIRES,
        )
        return signed.get("signedURL") or signed.get("signedUrl")
    except Exception as exc:
        print(f"Signed URL generation failed: {exc}")
        return None
