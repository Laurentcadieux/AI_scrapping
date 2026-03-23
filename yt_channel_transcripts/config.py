from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
