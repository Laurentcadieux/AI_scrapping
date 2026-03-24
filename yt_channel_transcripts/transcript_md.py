from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from youtube_transcript_api import YouTubeTranscriptApi

from .remote_client import fetch_transcript_raw_remote
from .remote_config import get_remote_settings
from .videos import VideoRef, fetch_video_upload_date

TranscriptStatus = Literal["created", "exists", "no_transcript"]

_LANGS = ("en", "en-US", "en-GB", "en-IN")


def _safe_filename_component(s: str, max_len: int = 120) -> str:
    s = re.sub(r'[<>:"/\\|?*\n\r\t]', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return "untitled"
    return s[:max_len]


def _lines_from_transcript(items: list[Any]) -> list[str]:
    lines: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        t = item.get("text", "")
        if t:
            lines.append(str(t).replace("\n", " ").strip())
    return lines


def _raw_from_new_api(video_id: str) -> list[dict[str, Any]] | None:
    """youtube-transcript-api 1.x: YouTubeTranscriptApi().fetch(...) -> FetchedTranscript."""
    api = YouTubeTranscriptApi()
    if not hasattr(api, "fetch"):
        return None
    try:
        fetched = api.fetch(video_id, languages=list(_LANGS))
    except Exception:
        try:
            fetched = api.fetch(video_id)
        except Exception:
            return None
    if hasattr(fetched, "to_raw_data"):
        try:
            return fetched.to_raw_data()
        except Exception:
            return None
    return None


def _raw_from_legacy_api(video_id: str) -> list[dict[str, Any]] | None:
    """youtube-transcript-api 0.6.x: YouTubeTranscriptApi.get_transcript(...)."""
    get_tr = getattr(YouTubeTranscriptApi, "get_transcript", None)
    if not callable(get_tr):
        return None
    try:
        return get_tr(video_id, languages=list(_LANGS))
    except Exception:
        try:
            return get_tr(video_id)
        except Exception:
            return None


def _format_published_line(upload_date_ymd: str | None) -> str:
    if not upload_date_ymd or len(upload_date_ymd) != 8 or not upload_date_ymd.isdigit():
        return "- **Published:** Unknown"
    try:
        d = datetime.strptime(upload_date_ymd, "%Y%m%d").date()
        return f"- **Published:** {d.isoformat()}"
    except ValueError:
        return "- **Published:** Unknown"


def fetch_transcript_text(video_id: str) -> str | None:
    """
    Returns None if no transcript or on any failure (rate limits, blocks, bad payloads).
    Does not raise for YouTube/API errors so pull/init keep running. Config errors still
    surface from get_remote_settings() when the YAML is invalid.
    """
    remote = get_remote_settings()
    try:
        if remote is not None:
            data = fetch_transcript_raw_remote(video_id, remote)
            if data is not None:
                if not isinstance(data, list):
                    data = None
                if data is not None:
                    lines = _lines_from_transcript(data)
                    text = "\n\n".join(lines) if lines else None
                    if text is not None:
                        return text
            if not remote.fallback_to_local:
                return None

        data = _raw_from_new_api(video_id)
        if data is None:
            data = _raw_from_legacy_api(video_id)
        if not data:
            return None
        if not isinstance(data, list):
            return None
        lines = _lines_from_transcript(data)
        return "\n\n".join(lines) if lines else None
    except Exception:
        return None


def write_transcript_md(
    video: VideoRef,
    transcript_dir: Path,
    delay_sec: float = 0.35,
) -> tuple[Path, TranscriptStatus]:
    """
    Writes transcripts/<folder>/<video_id>_<title>.md
    """
    transcript_dir.mkdir(parents=True, exist_ok=True)
    safe = _safe_filename_component(video.title)
    path = transcript_dir / f"{video.video_id}_{safe}.md"

    if path.exists():
        return path, "exists"

    text = fetch_transcript_text(video.video_id)
    if delay_sec > 0:
        time.sleep(delay_sec)

    if text is None:
        return path, "no_transcript"

    published_ymd = video.upload_date
    if published_ymd is None:
        try:
            published_ymd = fetch_video_upload_date(video.video_id)
        except Exception:
            published_ymd = None

    watch = f"https://www.youtube.com/watch?v={video.video_id}"
    body = (
        f"# {video.title}\n\n"
        f"- **Video ID:** `{video.video_id}`\n"
        f"- **URL:** {watch}\n"
        f"{_format_published_line(published_ymd)}\n\n"
        f"---\n\n"
        f"{text}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path, "created"
