import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from tiktok.auth import TikTokAuthError, get_valid_access_token

TIKTOK_API_BASE = "https://open.tiktokapis.com"
MIN_CHUNK_BYTES = 5 * 1024 * 1024
MAX_CHUNK_BYTES = 64 * 1024 * 1024
DEFAULT_CHUNK_BYTES = 10 * 1024 * 1024


class TikTokUploadError(Exception):
    pass


def build_caption(caption: str, hashtags: Optional[List[str]] = None) -> str:
    tags = []
    for tag in hashtags or []:
        cleaned = tag.strip().replace(" ", "")
        if not cleaned:
            continue
        if not cleaned.startswith("#"):
            cleaned = f"#{cleaned}"
        tags.append(cleaned)

    if not tags:
        return caption.strip()

    body = caption.strip()
    return f"{body}\n\n{' '.join(tags)}".strip()


class TikTokUploader:
    def __init__(
        self,
        access_token: str,
        *,
        dry_run: bool = True,
        timeout_seconds: int = 60,
        poll_interval_seconds: int = 5,
        max_poll_seconds: int = 180,
    ):
        self.access_token = access_token
        self.dry_run = dry_run
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.max_poll_seconds = max_poll_seconds

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{TIKTOK_API_BASE}{path}"
        response = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        error = data.get("error", {})
        if error.get("code") not in (None, "", "ok"):
            raise TikTokUploadError(
                f"TikTok API error {error.get('code')}: {error.get('message')}"
            )
        return data

    def query_creator_info(self) -> Dict[str, Any]:
        return self._post_json("/v2/post/publish/creator_info/query/", {})

    @staticmethod
    def _choose_privacy(
        options: List[str],
        requested_privacy: Optional[str],
    ) -> str:
        if requested_privacy and requested_privacy in options:
            return requested_privacy
        if "SELF_ONLY" in options:
            return "SELF_ONLY"
        if options:
            return options[0]
        return "SELF_ONLY"

    @staticmethod
    def _get_chunk_params(file_size: int) -> Dict[str, int]:
        if file_size <= 0:
            raise TikTokUploadError("Video file is empty.")

        if file_size < MIN_CHUNK_BYTES:
            chunk_size = file_size
        else:
            chunk_size = min(max(DEFAULT_CHUNK_BYTES, MIN_CHUNK_BYTES), MAX_CHUNK_BYTES)
            if chunk_size > file_size:
                chunk_size = file_size

        total_chunks = math.ceil(file_size / chunk_size)
        if total_chunks > 1000:
            chunk_size = math.ceil(file_size / 1000)
            chunk_size = min(max(chunk_size, MIN_CHUNK_BYTES), MAX_CHUNK_BYTES)
            total_chunks = math.ceil(file_size / chunk_size)

        if total_chunks > 1000:
            raise TikTokUploadError("Video is too large for TikTok chunk upload limits.")

        return {"chunk_size": chunk_size, "total_chunks": total_chunks}

    def init_direct_post(
        self,
        *,
        video_path: str,
        caption: str,
        privacy_level: Optional[str] = None,
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False,
        cover_timestamp_ms: int = 1000,
    ) -> Dict[str, Any]:
        file_size = Path(video_path).stat().st_size
        chunk = self._get_chunk_params(file_size)

        creator_info = self.query_creator_info().get("data", {})
        privacy_options = creator_info.get("privacy_level_options", [])
        chosen_privacy = self._choose_privacy(privacy_options, privacy_level)

        payload = {
            "post_info": {
                "title": caption,
                "privacy_level": chosen_privacy,
                "disable_comment": disable_comment,
                "disable_duet": disable_duet,
                "disable_stitch": disable_stitch,
                "video_cover_timestamp_ms": cover_timestamp_ms,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": chunk["chunk_size"],
                "total_chunk_count": chunk["total_chunks"],
            },
        }
        response = self._post_json("/v2/post/publish/video/init/", payload)
        response["resolved_privacy_level"] = chosen_privacy
        response["resolved_chunk_size"] = chunk["chunk_size"]
        return response

    def upload_video_file(
        self,
        *,
        upload_url: str,
        video_path: str,
        chunk_size: int,
    ) -> None:
        total_size = Path(video_path).stat().st_size
        uploaded = 0

        with open(video_path, "rb") as file_obj:
            while uploaded < total_size:
                chunk = file_obj.read(chunk_size)
                if not chunk:
                    break

                start = uploaded
                end = uploaded + len(chunk) - 1
                headers = {
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {start}-{end}/{total_size}",
                }
                response = requests.put(
                    upload_url,
                    data=chunk,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )

                if response.status_code not in (201, 206):
                    raise TikTokUploadError(
                        f"Upload failed with status {response.status_code}: {response.text}"
                    )
                uploaded += len(chunk)

    def fetch_status(self, publish_id: str) -> Dict[str, Any]:
        payload = {"publish_id": publish_id}
        return self._post_json("/v2/post/publish/status/fetch/", payload)

    def publish_video(
        self,
        *,
        video_path: str,
        caption: str,
        privacy_level: Optional[str] = None,
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False,
        cover_timestamp_ms: int = 1000,
        wait_for_completion: bool = True,
    ) -> Dict[str, Any]:
        path = Path(video_path)
        if not path.exists():
            raise TikTokUploadError(f"Video not found: {video_path}")
        if path.suffix.lower() != ".mp4":
            raise TikTokUploadError("Only .mp4 is supported by this uploader.")

        if self.dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "status": "DRY_RUN",
                "video_path": str(path),
                "caption": caption,
                "privacy_level": privacy_level or "SELF_ONLY",
            }

        init = self.init_direct_post(
            video_path=str(path),
            caption=caption,
            privacy_level=privacy_level,
            disable_comment=disable_comment,
            disable_duet=disable_duet,
            disable_stitch=disable_stitch,
            cover_timestamp_ms=cover_timestamp_ms,
        )
        data = init.get("data", {})
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")
        chunk_size = init.get("resolved_chunk_size", DEFAULT_CHUNK_BYTES)

        if not publish_id:
            raise TikTokUploadError("Missing publish_id from TikTok init response.")
        if not upload_url:
            raise TikTokUploadError("Missing upload_url from TikTok init response.")

        self.upload_video_file(
            upload_url=upload_url,
            video_path=str(path),
            chunk_size=int(chunk_size),
        )

        result = {
            "ok": True,
            "dry_run": False,
            "publish_id": publish_id,
            "privacy_level": init.get("resolved_privacy_level"),
            "status": "UPLOADED",
        }

        if not wait_for_completion:
            return result

        deadline = time.time() + self.max_poll_seconds
        while time.time() < deadline:
            status_payload = self.fetch_status(publish_id).get("data", {})
            status = status_payload.get("status", "")
            result["status"] = status or "UNKNOWN"
            result["status_payload"] = status_payload

            if status in {"PUBLISH_COMPLETE", "PUBLISHED", "SUCCESS"}:
                return result
            if status == "FAILED":
                fail_reason = status_payload.get("fail_reason", "unknown")
                raise TikTokUploadError(f"TikTok publish failed: {fail_reason}")

            time.sleep(self.poll_interval_seconds)

        result["timed_out"] = True
        return result


def upload_video(
    video_path: str,
    caption: str,
    hashtags: Optional[List[str]] = None,
    *,
    access_token: Optional[str] = None,
    dry_run: bool = True,
    privacy_level: Optional[str] = "SELF_ONLY",
    disable_comment: bool = False,
    disable_duet: bool = False,
    disable_stitch: bool = False,
    wait_for_completion: bool = True,
) -> Dict[str, Any]:
    token = access_token or os.getenv("TIKTOK_ACCESS_TOKEN")
    if not token and not dry_run:
        try:
            token = get_valid_access_token()
        except TikTokAuthError as exc:
            raise TikTokUploadError(str(exc)) from exc
    if not token and not dry_run:
        raise TikTokUploadError(
            "Missing TIKTOK_ACCESS_TOKEN. Set it in env or pass access_token."
        )

    final_caption = build_caption(caption, hashtags)
    uploader = TikTokUploader(access_token=token or "", dry_run=dry_run)
    return uploader.publish_video(
        video_path=video_path,
        caption=final_caption,
        privacy_level=privacy_level,
        disable_comment=disable_comment,
        disable_duet=disable_duet,
        disable_stitch=disable_stitch,
        wait_for_completion=wait_for_completion,
    )
