"""
Azure Functions (Python) — proxy for transcript + video metadata so your laptop
does not hit YouTube directly at scale.

Deploy as a Python Function App; set auth to Function and pass the host key
in x-functions-key from the client config/remote_fetch.yaml.

Routes (relative to your /api base):
  POST /transcript      JSON {"video_id": "..."} -> {"ok": true, "raw": [...]}
  POST /video_metadata  JSON {"video_id": "..."} -> {"ok": true, "upload_date": "YYYYMMDD"}
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any

import azure.functions as func
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

app = func.FunctionApp()

_LANGS = ["en", "en-US", "en-GB", "en-IN", "en"]


def _parse_upload_date(info: dict[str, Any] | None) -> str | None:
    if not info:
        return None
    for key in ("upload_date", "release_date"):
        v = info.get(key)
        if isinstance(v, str) and len(v) == 8 and v.isdigit():
            return v
    ts = info.get("timestamp") or info.get("release_timestamp")
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d")
        except (OSError, OverflowError, ValueError):
            return None
    return None


@app.route(route="transcript", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def transcript(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return _json_response({"ok": False, "error": "invalid json"}, 400)
    if not isinstance(body, dict):
        return _json_response({"ok": False, "error": "expected object"}, 400)
    vid = body.get("video_id")
    if not vid or not isinstance(vid, str):
        return _json_response({"ok": False, "error": "missing video_id"}, 400)

    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(vid, languages=_LANGS)
    except Exception:
        try:
            fetched = api.fetch(vid)
        except Exception as e:
            return _json_response({"ok": False, "error": str(e)}, 200)

    if hasattr(fetched, "to_raw_data"):
        raw = fetched.to_raw_data()
    else:
        return _json_response({"ok": False, "error": "unexpected transcript shape"}, 200)
    return _json_response({"ok": True, "raw": raw}, 200)


@app.route(route="video_metadata", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def video_metadata(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return _json_response({"ok": False, "error": "invalid json"}, 400)
    if not isinstance(body, dict):
        return _json_response({"ok": False, "error": "expected object"}, 400)
    vid = body.get("video_id")
    if not vid or not isinstance(vid, str):
        return _json_response({"ok": False, "error": "missing video_id"}, 400)

    url = f"https://www.youtube.com/watch?v={vid}"
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
    except Exception as e:
        return _json_response({"ok": False, "error": str(e)}, 200)

    ud = _parse_upload_date(info or {})
    return _json_response({"ok": True, "upload_date": ud}, 200)


def _json_response(data: dict[str, Any], status: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data),
        status_code=status,
        mimetype="application/json",
        charset="utf-8",
    )


# Azure Functions Python v2: ensure app is exported
if __name__ == "__main__":
    print("Run with: func start", file=sys.stderr)
