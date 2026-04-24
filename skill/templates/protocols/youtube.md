### YouTube fetch protocol

**Trigger:** inbox URL matches `youtube.com/watch?v=` or `youtu.be/`.
**Tool:** `yt-dlp`.

Steps:

1. `yt-dlp --dump-json <url>` — one call; captures description, chapters, title, channel, duration, upload date, video ID. No download.
2. Transcript: `yt-dlp --write-auto-sub --skip-download --sub-lang en-orig <url>`
   - Prefer `--sub-format srt` when available.
   - Fall back to `--sub-format vtt` if SRT unavailable.
   - Prefer `en-orig` (unprocessed captions) over `en` (auto-translated).
3. Parse subtitles:
   - **SRT format:** use standard cue text per block. Join consecutive cues that belong to the same sentence.
   - **VTT rolling-caption format:** each cue has 2 lines; the last line is live/partial. Strategy: take the **first clean line per cue** (strip `<c>` timing tags). Deduplicate consecutive identical lines. Group transcript text by chapter heading (from step 1 `--dump-json` chapters array).
4. Save to `raw/youtube/<video-id>-<slug>.md`.
5. **Fallback:** if no transcript track exists at all, flag the inbox line `<!-- fetch-failed:no-transcript -->` and skip (do not mark `[x]` or move to Completed).

**Guard:** if the video transcript would exceed 200k input tokens during ingest, surface to user before proceeding.

**Slug generation:** lowercase title, replace spaces/special chars with hyphens, truncate at 40 chars.

**Raw file format** (`raw/youtube/<video-id>-<slug>.md`):
```
# <title>

## Metadata
- Video ID: <id>
- Channel: <channel>
- Duration: <MM:SS or HH:MM:SS>
- Upload date: <YYYY-MM-DD>
- URL: <url>
- Fetched: <YYYY-MM-DD>

## Description
<full description text>

## Chapters
| # | Title | Timestamp |
|---|---|---|
<chapter rows>

## Transcript

### <Chapter 1 Title> (0:00)
<cleaned transcript text>

### <Chapter 2 Title> (MM:SS)
<cleaned transcript text>
...
```

**README.md row format** (`raw/youtube/README.md`):
`| raw/youtube/<video-id>-<slug>.md | <title> | <channel> | <duration> | <upload-date> | <YYYY-MM-DD> | |`
