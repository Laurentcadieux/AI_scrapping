from __future__ import annotations

import argparse
import sys

from .config import discover_channel_configs
from .paths import init_dir, transcripts_root
from .transcript_md import write_transcript_md
from .videos import list_all_videos_flat, list_videos_since


PULL_DAYS_DEFAULT = 7


def _run_init() -> int:
    init_path = init_dir()
    configs = discover_channel_configs(init_path)
    if not configs:
        print(
            f"No channel configs found in {init_path} "
            f"(expected files like youtubeDOTcom_<Name>.yaml).",
            file=sys.stderr,
        )
        return 1

    transcripts_root().mkdir(parents=True, exist_ok=True)
    for cfg in configs:
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
    return 0


def _run_pull(days: int) -> int:
    init_path = init_dir()
    configs = discover_channel_configs(init_path)
    if not configs:
        print(
            f"No channel configs found in {init_path}.",
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

    sub.add_parser("init", help="Fetch transcripts for all videos on each configured channel.")

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
        return _run_init()
    if args.command == "pull":
        return _run_pull(args.days)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
