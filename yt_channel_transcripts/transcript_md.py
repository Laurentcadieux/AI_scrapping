from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Literal

from youtube_transcript_api import YouTubeTranscriptApi

from .videos import VideoRef

TranscriptStatus = Literal["created", "exists", "no_transcript"]

_LANGS = ("en", "en-US", "en-GB", "en-IN")


def _safe_filename_component(s: str, max_len: int = 120) -> str:
    s = re.sub(r'[<>:"/\\|?*\n\r\t]', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return "untitled"
    return s[:max_len]


def _lines_from_transcript(items: list[dict]) -> list[str]:
    lines: list[str] = []
    for item in items:
        t = item.get("text", "")
        if t:
            lines.append(t.replace("\n", " ").strip())
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
        return fetched.to_raw_data()
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


def fetch_transcript_text(video_id: str) -> str | None:
    data = _raw_from_new_api(video_id)
    if data is None:
        data = _raw_from_legacy_api(video_id)
    if not data:
        return None
    lines = _lines_from_transcript(data)
    return "\n\n".join(lines) if lines else None


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

    watch = f"https://www.youtube.com/watch?v={video.video_id}"
    body = (
        f"# {video.title}\n\n"
        f"- **Video ID:** `{video.video_id}`\n"
        f"- **URL:** {watch}\n\n"
        f"---\n\n"
        f"{text}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path, "created"
