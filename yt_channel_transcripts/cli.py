from __future__ import annotations

import argparse
import sys

from .config import (
    ChannelConfig,
    discover_channel_configs,
    derive_output_folder_from_channel_url,
    load_channel_config,
    write_channel_init_file,
)
from .paths import init_dir, transcripts_root
from .transcript_md import write_transcript_md
from .videos import list_all_videos_flat, list_videos_since


PULL_DAYS_DEFAULT = 7


def _run_channel_init(cfg: ChannelConfig) -> None:
    print(f"Channel: {cfg.output_folder} ({cfg.channel_url})")
    videos = list_all_videos_flat(cfg.channel_url)
    print(f"  Found {len(videos)} video(s)")
    created = 0
    existed = 0
    missing = 0
    for v in videos:
        _path, status = write_transcript_md(v, cfg.transcript_dir)
        if status == "created":
            created += 1
        elif status == "exists":
            existed += 1
        else:
            missing += 1
    print(
        f"  Summary: {created} new, {existed} already saved, {missing} without transcript"
    )
    print(f"  Output: {cfg.transcript_dir}")


def _run_init(channel_url: str, output_folder: str | None) -> int:
    try:
        folder = output_folder or derive_output_folder_from_channel_url(channel_url)
    except ValueError as e:
        print(f"init: {e}", file=sys.stderr)
        return 1

    path = write_channel_init_file(channel_url, folder)
    cfg = load_channel_config(path)
    transcripts_root().mkdir(parents=True, exist_ok=True)
    print(f"Saved config: {path}")
    _run_channel_init(cfg)
    return 0


def _run_pull(days: int) -> int:
    init_path = init_dir()
    configs = discover_channel_configs(init_path)
    if not configs:
        print(
            f"No channel configs found in {init_path}. "
            "Run: python -m yt_channel_transcripts init <CHANNEL_URL>",
            file=sys.stderr,
        )
        return 1

    transcripts_root().mkdir(parents=True, exist_ok=True)
    for cfg in configs:
        print(f"Channel: {cfg.output_folder} — uploads in last {days} day(s)")
        videos = list_videos_since(cfg.channel_url, days)
        print(f"  Found {len(videos)} video(s) in window")
        for v in videos:
            path, status = write_transcript_md(v, cfg.transcript_dir)
            if status == "created":
                print(f"  [new] {path.name}")
            elif status == "exists":
                print(f"  [have] {path.name}")
            else:
                print(f"  [no transcript] {v.video_id} — {v.title[:80]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube transcripts into Markdown (init = all videos, pull = recent window).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Register the channel URL in init/ and fetch transcripts for all videos.",
    )
    p_init.add_argument(
        "channel_url",
        help='YouTube channel URL, e.g. "https://www.youtube.com/@JuliaMcCoy"',
    )
    p_init.add_argument(
        "--output-folder",
        "-o",
        metavar="NAME",
        help="Folder name under transcripts/ (default: derived from the URL)",
    )

    p_pull = sub.add_parser(
        "pull",
        help="Fetch transcripts for videos uploaded in the last N days (default 7).",
    )
    p_pull.add_argument(
        "--days",
        type=int,
        default=PULL_DAYS_DEFAULT,
        help=f"Days to look back (default: {PULL_DAYS_DEFAULT})",
    )

    args = parser.parse_args(argv)
    if args.command == "init":
        return _run_init(args.channel_url, args.output_folder)
    if args.command == "pull":
        return _run_pull(args.days)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
