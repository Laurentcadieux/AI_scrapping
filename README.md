# YouTube channel transcripts

Python utilities to download **captions/transcripts** from every video on configured YouTube channels and save them as **Markdown** files. Intended to run on **Ubuntu** (or any OS with Python 3.10+).

## Layout (GitHub-friendly)

| Path | Purpose |
|------|--------|
| `yt_channel_transcripts/` | Application code only |
| `init/` | One YAML file per channel (config + channel URL) |
| `transcripts/` | Generated `.md` files (ignored by Git — not committed) |

Init files must be named `youtubeDOTcom_<ChannelName>.yaml`. The folder under `transcripts/` defaults to `<ChannelName>` (text after the prefix; use `DOT` in the filename where you want a `.` in the name, e.g. `SomeDOTChannel` → `Some.Channel`).

## Setup (Ubuntu)

```bash
cd /path/to/AI_scrapping
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: install `ffmpeg` if you extend this with media downloads (`yt-dlp` may suggest it for some operations).

## Commands

- **`init`** — List all videos on each channel in `init/`, fetch transcripts, write `transcripts/<channel>/VIDEOID_title.md`. Skips videos that already have a file; does not re-download existing IDs.
- **`pull`** — Same as above, but only for videos **uploaded in the last 7 days** (change with `--days N`).

```bash
python -m yt_channel_transcripts init
python -m yt_channel_transcripts pull
python -m yt_channel_transcripts pull --days 14
```

## Dependencies

- [youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/) — transcript text
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — channel video lists and date filtering
- PyYAML — init file parsing

## Notes

- Transcripts must exist on YouTube (auto-generated or manual). Videos without captions are skipped and counted in the summary.
- `pull` uses yt-dlp’s `dateafter` filter; very large channels may take longer on the first `pull` while metadata is resolved.
