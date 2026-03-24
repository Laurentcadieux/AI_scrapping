from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from .paths import remote_fetch_config_path


@dataclass(frozen=True)
class RemoteFetchSettings:
    """Loaded from config/remote_fetch.yaml when enabled: true."""

    enabled: bool
    base_url: str
    function_key: str
    timeout_seconds: int
    fallback_to_local: bool


_cache: RemoteFetchSettings | None | Literal["unset"] = "unset"


def _load_settings() -> RemoteFetchSettings | None:
    path: Path = remote_fetch_config_path()
    if not path.is_file():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return None
    if not raw.get("enabled"):
        return None
    base = raw.get("base_url")
    if not base or not isinstance(base, str) or not base.strip():
        raise ValueError(
            f"{path}: remote_fetch.enabled is true but base_url is missing or empty"
        )
    key = raw.get("function_key")
    if key is not None and not isinstance(key, str):
        raise ValueError(f"{path}: function_key must be a string if set")
    timeout = raw.get("timeout_seconds", 60)
    if not isinstance(timeout, int) or timeout < 5:
        timeout = 60
    fb = raw.get("fallback_to_local", False)
    if not isinstance(fb, bool):
        fb = False
    return RemoteFetchSettings(
        enabled=True,
        base_url=base.strip().rstrip("/"),
        function_key=(key or "").strip(),
        timeout_seconds=timeout,
        fallback_to_local=fb,
    )


def get_remote_settings() -> RemoteFetchSettings | None:
    """
    Returns settings when config/remote_fetch.yaml exists and enabled: true.
    Cached for the lifetime of the process.
    """
    global _cache
    if _cache != "unset":
        return _cache
    _cache = _load_settings()
    return _cache


def reload_remote_settings() -> None:
    global _cache
    _cache = "unset"
