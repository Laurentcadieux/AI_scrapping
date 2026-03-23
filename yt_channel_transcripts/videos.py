from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from yt_dlp import YoutubeDL


@dataclass(frozen=True)
class VideoRef:
    video_id: str
    title: str


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
        out.append(VideoRef(video_id=str(vid), title=title))
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
        out.append(VideoRef(video_id=str(vid), title=title))
    return out
