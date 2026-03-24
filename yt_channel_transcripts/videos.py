from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from yt_dlp import YoutubeDL

from .remote_client import fetch_video_upload_date_remote
from .remote_config import get_remote_settings


@dataclass(frozen=True)
class VideoRef:
    video_id: str
    title: str
    """YYYYMMDD from YouTube when known; used for Markdown **Published** line."""
    upload_date: str | None = None


def parse_upload_date_from_entry(entry: dict[str, Any] | None) -> str | None:
    """Best-effort YYYYMMDD from a yt-dlp info dict."""
    if not entry:
        return None
    for key in ("upload_date", "release_date"):
        v = entry.get(key)
        if isinstance(v, str) and len(v) == 8 and v.isdigit():
            return v
    ts = entry.get("timestamp") or entry.get("release_timestamp")
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d")
        except (OSError, OverflowError, ValueError):
            return None
    return None


def fetch_video_upload_date(video_id: str) -> str | None:
    """One yt-dlp request for a single video (used when playlist entries lack a date)."""
    remote = get_remote_settings()
    if remote is not None:
        ud = fetch_video_upload_date_remote(video_id, remote)
        if ud is not None:
            return ud
        if not remote.fallback_to_local:
            return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "extract_flat": False,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return None
    return parse_upload_date_from_entry(info or {})


def _channel_videos_url(channel_url: str) -> str:
    u = channel_url.strip().rstrip("/")
    if u.endswith("/videos") or "/playlist?" in u:
        return u
    return f"{u}/videos"


def list_all_videos_flat(channel_url: str) -> list[VideoRef]:
    """Fast flat playlist: all video ids + titles (no per-video HTTP for metadata)."""
    url = _channel_videos_url(channel_url)
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "extract_flat": True,
    }
    out: list[VideoRef] = []
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        return out
    entries = info.get("entries") or []
    for e in entries:
        if not e:
            continue
        vid = e.get("id")
        if not vid:
            continue
        title = (e.get("title") or "untitled").strip()
        out.append(
            VideoRef(
                video_id=str(vid),
                title=title,
                upload_date=parse_upload_date_from_entry(e),
            )
        )
    return out


def list_videos_since(channel_url: str, days: int) -> list[VideoRef]:
    """
    Videos uploaded on or after (today - days), using yt-dlp dateafter filter.
    Uses full playlist extraction (slower than flat) so upload dates are honored.
    """
    url = _channel_videos_url(channel_url)
    dateafter = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "extract_flat": False,
        "dateafter": dateafter,
    }
    out: list[VideoRef] = []
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        return out
    entries = info.get("entries") or []
    for e in entries:
        if not e:
            continue
        vid = e.get("id")
        if not vid:
            continue
        title = (e.get("title") or "untitled").strip()
        out.append(
            VideoRef(
                video_id=str(vid),
                title=title,
                upload_date=parse_upload_date_from_entry(e),
            )
        )
    return out
