from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .remote_config import RemoteFetchSettings


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _headers(settings: RemoteFetchSettings) -> dict[str, str]:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if settings.function_key:
        h["x-functions-key"] = settings.function_key
    return h


def _post_json(
    settings: RemoteFetchSettings, path: str, body: dict[str, Any]
) -> dict[str, Any] | None:
    url = _url(settings.base_url, path)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers=_headers(settings)
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return None
            out = json.loads(raw)
            return out if isinstance(out, dict) else None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def fetch_transcript_raw_remote(
    video_id: str, settings: RemoteFetchSettings
) -> list[dict[str, Any]] | None:
    """
    POST {base_url}/transcript with {"video_id": "..."}
    Expects {"ok": true, "raw": [...]} or {"ok": false}.
    """
    res = _post_json(settings, "transcript", {"video_id": video_id})
    if not res or not res.get("ok"):
        return None
    raw = res.get("raw")
    if isinstance(raw, list):
        return raw
    return None


def fetch_video_upload_date_remote(
    video_id: str, settings: RemoteFetchSettings
) -> str | None:
    """
    POST {base_url}/video_metadata with {"video_id": "..."}
    Expects {"ok": true, "upload_date": "YYYYMMDD"} or null upload_date.
    """
    res = _post_json(settings, "video_metadata", {"video_id": video_id})
    if not res or not res.get("ok"):
        return None
    ud = res.get("upload_date")
    if isinstance(ud, str) and len(ud) == 8 and ud.isdigit():
        return ud
    return None
