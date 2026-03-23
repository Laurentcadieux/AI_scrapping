from pathlib import Path


def project_root() -> Path:
    """Package lives in <root>/yt_channel_transcripts; project root is parent."""
    return Path(__file__).resolve().parent.parent


def init_dir() -> Path:
    return project_root() / "init"


def transcripts_root() -> Path:
    return project_root() / "transcripts"
