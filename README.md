# YouTube channel transcripts

Python utilities to download **captions/transcripts** from every video on configured YouTube channels and save them as **Markdown** files. Intended to run on **Ubuntu** (or any OS with Python 3.10+).

## Layout (GitHub-friendly)

| Path | Purpose |
|------|--------|
| `yt_channel_transcripts/` | Application code only |
| `init/` | One YAML file per channel (written when you run `init` with a URL) |
| `transcripts/` | Generated `.md` files (ignored by Git — not committed) |

`init` saves `init/youtubeDOTcom_<Name>.yaml` and writes transcripts under `transcripts/<Name>/`. The `<Name>` defaults to a slug derived from the URL (e.g. `@JuliaMcCoy` → `JuliaMcCoy`). Override with `--output-folder` / `-o`.

## Setup (Ubuntu)

```bash
cd /path/to/AI_scrapping
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: install `ffmpeg` if you extend this with media downloads (`yt-dlp` may suggest it for some operations).

## Commands

- **`init <URL>`** — Saves the channel URL into `init/`, then lists all videos on that channel, fetches transcripts, and writes `transcripts/<channel>/VIDEOID_title.md`. Skips videos that already have a file.

```bash
python -m yt_channel_transcripts init "https://www.youtube.com/@JuliaMcCoy"
python -m yt_channel_transcripts init "https://www.youtube.com/@JuliaMcCoy" -o JuliaMcCoy
```

- **`pull`** — Uses every `init/youtubeDOTcom_*.yaml` and fetches transcripts only for videos **uploaded in the last 7 days** (change with `--days N`).

```bash
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
