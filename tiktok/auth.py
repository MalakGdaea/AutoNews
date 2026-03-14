from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import requests
from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL, TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET

TOKEN_TABLE = "tiktok_tokens"
TOKEN_ID = "primary"
EXPIRY_SAFETY_SECONDS = 300
TOKEN_ENDPOINT = "https://open.tiktokapis.com/v2/oauth/token/"


class TikTokAuthError(Exception):
    pass


def _get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise TikTokAuthError("Supabase credentials are missing.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_expired(expires_at: Optional[str]) -> bool:
    if not expires_at:
        return True
    ts = _parse_timestamp(expires_at)
    if not ts:
        return True
    return ts <= datetime.now(timezone.utc) + timedelta(seconds=EXPIRY_SAFETY_SECONDS)


def _refresh_token(refresh_token: str) -> Dict[str, Any]:
    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET:
        raise TikTokAuthError("Missing TikTok client credentials.")

    payload = {
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    response = requests.post(
        TOKEN_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    data = response.json()
    if response.status_code >= 400:
        message = data.get("error_description") or data.get("error") or response.text
        raise TikTokAuthError(f"TikTok refresh failed: {message}")
    return data


def get_valid_access_token() -> str:
    supabase = _get_supabase()
    result = supabase.table(TOKEN_TABLE).select("*").eq("id", TOKEN_ID).single().execute()
    row = result.data
    if not row:
        raise TikTokAuthError("No TikTok token record found. Run OAuth first.")

    access_token = row.get("access_token")
    refresh_token = row.get("refresh_token")

    if access_token and not _is_expired(row.get("expires_at")):
        return access_token

    if not refresh_token:
        raise TikTokAuthError("Missing refresh token. Run OAuth again.")

    refreshed = _refresh_token(refresh_token)

    expires_at = None
    refresh_expires_at = None
    if refreshed.get("expires_in"):
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=int(refreshed["expires_in"]))
        ).isoformat()
    if refreshed.get("refresh_expires_in"):
        refresh_expires_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=int(refreshed["refresh_expires_in"]))
        ).isoformat()

    update_payload = {
        "access_token": refreshed.get("access_token") or access_token,
        "refresh_token": refreshed.get("refresh_token") or refresh_token,
        "expires_at": expires_at or row.get("expires_at"),
        "refresh_expires_at": refresh_expires_at or row.get("refresh_expires_at"),
        "scope": refreshed.get("scope") or row.get("scope"),
        "token_type": refreshed.get("token_type") or row.get("token_type"),
        "open_id": refreshed.get("open_id") or row.get("open_id"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    supabase.table(TOKEN_TABLE).update(update_payload).eq("id", TOKEN_ID).execute()

    token = update_payload["access_token"]
    if not token:
        raise TikTokAuthError("Refresh succeeded but access token is missing.")
    return token
