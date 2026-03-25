from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL
from tiktok.uploader import TikTokUploadError, upload_video

VIDEO_TABLE = "videos"


def _get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _split_caption_and_tags(raw_title: str) -> Tuple[str, List[str]]:
    hashtags = [tag.lower() for tag in re.findall(r"#[\w_]+", raw_title or "")]
    deduped: List[str] = []
    seen = set()
    for tag in hashtags:
        if tag in seen:
            continue
        seen.add(tag)
        deduped.append(tag)

    caption = re.sub(r"#[\w_]+", "", raw_title or "").strip()
    return caption or (raw_title or "Untitled"), deduped


def _download_to_temp(url: str) -> str:
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    tmp.write(chunk)
            return tmp.name


def _resolve_video_source(video_path: Optional[str], video_url: Optional[str]) -> Tuple[str, Optional[str]]:
    if video_path:
        if video_path.startswith("http://") or video_path.startswith("https://"):
            temp = _download_to_temp(video_path)
            return temp, temp

        local = Path(video_path)
        if local.exists() and local.is_file():
            return str(local), None

        project_root = Path(__file__).resolve().parent.parent
        candidate = (project_root / video_path).resolve()
        if candidate.exists() and candidate.is_file():
            return str(candidate), None

    if video_url:
        temp = _download_to_temp(video_url)
        return temp, temp

    raise FileNotFoundError("No accessible local file or downloadable URL found for this video.")


def upload_video_by_id(video_id: int) -> Dict[str, str]:
    supabase = _get_supabase()

    result = (
        supabase.table(VIDEO_TABLE)
        .select("id,title,video_path,video_url,status")
        .eq("id", video_id)
        .single()
        .execute()
    )
    row = result.data
    if not row:
        raise RuntimeError(f"Video {video_id} not found")

    current_status = str(row.get("status") or "").lower()
    if "publish" in current_status or "uploaded" in current_status:
        return {
            "id": str(video_id),
            "status": row.get("status") or "already_uploaded",
            "message": "Video is already uploaded/published.",
        }

    caption, hashtags = _split_caption_and_tags(row.get("title") or "")

    temp_file: Optional[str] = None
    source_path = ""
    try:
        source_path, temp_file = _resolve_video_source(row.get("video_path"), row.get("video_url"))

        supabase.table(VIDEO_TABLE).update({"status": "uploading"}).eq("id", video_id).execute()

        upload_result = upload_video(
            video_path=source_path,
            caption=caption,
            hashtags=hashtags,
            dry_run=False,
            privacy_level="SELF_ONLY",
            wait_for_completion=True,
        )

        final_status = upload_result.get("status") or "uploaded"
        supabase.table(VIDEO_TABLE).update({"status": final_status}).eq("id", video_id).execute()

        return {
            "id": str(video_id),
            "status": str(final_status),
            "message": "Video uploaded to TikTok.",
        }
    except TikTokUploadError as exc:
        error_status = f"upload_failed: {exc}"[:500]
        supabase.table(VIDEO_TABLE).update({"status": error_status}).eq("id", video_id).execute()
        raise
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual upload by video id")
    parser.add_argument("video_id", type=int, help="Video row id in Supabase videos table")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = upload_video_by_id(args.video_id)
    print(f"__JSON__{json.dumps(result)}")


if __name__ == "__main__":
    main()
