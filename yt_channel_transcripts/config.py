from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml

INIT_PREFIX = "youtubeDOTcom_"


@dataclass(frozen=True)
class ChannelConfig:
    """One init file = one channel."""

    source_path: Path
    channel_url: str
    output_folder: str

    @property
    def transcript_dir(self) -> Path:
        from .paths import transcripts_root

        return transcripts_root() / self.output_folder


def _derive_output_folder(stem: str) -> str:
    if not stem.startswith(INIT_PREFIX):
        raise ValueError(
            f"Init filename must start with {INIT_PREFIX!r}, got {stem!r}"
        )
    rest = stem[len(INIT_PREFIX) :]
    # Allow youtubeDOTcom_SomeDOTName -> Some.Name in folder name
    return rest.replace("DOT", ".")


def load_channel_config(path: Path) -> ChannelConfig:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML in {path}: expected a mapping")

    url = data.get("channel_url")
    if not url or not isinstance(url, str):
        raise ValueError(f"{path}: missing or invalid 'channel_url'")

    output_folder = data.get("output_folder")
    if output_folder is None:
        output_folder = _derive_output_folder(path.stem)
    elif not isinstance(output_folder, str) or not output_folder.strip():
        raise ValueError(f"{path}: 'output_folder' must be a non-empty string")

    return ChannelConfig(
        source_path=path,
        channel_url=url.strip(),
        output_folder=output_folder.strip(),
    )


def discover_channel_configs(init_directory: Path) -> list[ChannelConfig]:
    if not init_directory.is_dir():
        return []
    configs: list[ChannelConfig] = []
    for p in sorted(init_directory.iterdir()):
        if p.suffix.lower() not in (".yaml", ".yml"):
            continue
        if not p.name.startswith(INIT_PREFIX):
            continue
        configs.append(load_channel_config(p))
    return configs


def _sanitize_folder_slug(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r'[<>:"/\\|?*\n\r\t]', "", s)
    s = re.sub(r"\s+", "_", s)
    s = s.strip("._")
    if not s:
        raise ValueError("Could not derive a non-empty folder name from the URL")
    return s[:200]


def derive_output_folder_from_channel_url(url: str) -> str:
    """
    Derive a transcript folder name from a YouTube channel URL
    (@handle, /channel/ID, /c/name, /user/name).
    """
    u = url.strip().rstrip("/")
    parsed = urlparse(u)
    host = (parsed.netloc or "").lower()
    if "youtube.com" not in host and "youtu.be" not in host:
        raise ValueError("URL must be a youtube.com channel URL")

    path = (parsed.path or "").strip("/")
    parts = [p for p in path.split("/") if p]

    if not parts and "youtu.be" in host:
        raise ValueError("Short youtu.be links are not supported; use a channel URL")

    if not parts:
        raise ValueError("Could not derive channel from URL path")

    if parts[0].startswith("@"):
        return _sanitize_folder_slug(parts[0][1:])

    if parts[0] == "channel" and len(parts) >= 2:
        return _sanitize_folder_slug(parts[1])

    if parts[0] in ("c", "user") and len(parts) >= 2:
        return _sanitize_folder_slug(parts[1])

    return _sanitize_folder_slug(parts[0])


def init_yaml_path_for_output_folder(output_folder: str) -> Path:
    from .paths import init_dir

    stem = output_folder.replace(".", "DOT")
    return init_dir() / f"{INIT_PREFIX}{stem}.yaml"


def write_channel_init_file(channel_url: str, output_folder: str) -> Path:
    """Create or overwrite init/<prefix><name>.yaml for pull and repeat runs."""
    from .paths import init_dir

    path = init_yaml_path_for_output_folder(output_folder)
    init_dir().mkdir(parents=True, exist_ok=True)
    data = {
        "channel_url": channel_url.strip(),
        "output_folder": output_folder.strip(),
    }
    header = (
        "# Channel config — created/updated by: "
        "python -m yt_channel_transcripts init <URL>\n"
    )
    with path.open("w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return path
