---
name: barba-video-downloader
description: >-
  Download videos and audio from a URL — supports YouTube videos, Instagram
  reels, TikTok, and Pinterest (plus other yt-dlp-supported sites). Can clip a
  time section, extract audio-only, or transcribe spoken audio to text/subtitles.
  Use whenever the user wants to grab, save, rip, or clip a video / reel / short,
  or get a transcript or captions from a video or audio URL. Backed by a private
  yt-dlp + whisperx service on the local network (barbabook).
---

# Barba Video Downloader

A thin client over a private media service running on the home network at
**`http://barbabook.local:5001/`**. It can **download** video/audio from a URL
and **transcribe** spoken audio to text.

Supported platforms include **YouTube videos, Instagram reels, TikTok, and
Pinterest** — and most other sites yt-dlp handles. If a user shares a link from
any of these and wants to save it, clip it, pull the audio, or get a transcript,
this is the tool.

## Requirement (read first)

This only works when:
1. The machine is on the **same home Wi-Fi / LAN** as `barbabook`, and
2. The `barbabook` service is running.

If a `curl` call fails to connect (e.g. "Could not resolve host" or "Connection
refused"), the backend is **not reachable** — tell the user they're either off
the home network or the server isn't running. Don't retry endlessly.

## Downloading (video or audio)

`GET /download` returns the media file directly (binary, with the correct
filename). The preferred way is the helper script:

```bash
scripts/download.sh "<MEDIA_URL>"                 # best video, server names the file
scripts/download.sh "<MEDIA_URL>" clip.mp4        # custom output filename
scripts/download.sh "<MEDIA_URL>" song.m4a --audio   # audio-only
```

Raw `curl` equivalent (always URL-encode the URL — it has `&`/`?` in it, and let
the server name the file with `-OJ`):

```bash
curl -OJ -G "http://barbabook.local:5001/download" \
  --data-urlencode "url=<MEDIA_URL>" \
  --data-urlencode "outtmpl=video.mp4" \
  --data-urlencode "format=bestvideo"
```

Audio-only (the `x` flag forces bestaudio):

```bash
curl -OJ -G "http://barbabook.local:5001/download" \
  --data-urlencode "url=<MEDIA_URL>" \
  --data-urlencode "outtmpl=audio.m4a" \
  --data-urlencode "x="
```

Clip a time section (`H:MM:SS-H:MM:SS`):

```bash
curl -OJ -G "http://barbabook.local:5001/download" \
  --data-urlencode "url=<MEDIA_URL>" \
  --data-urlencode "download_sections=0:1:05-0:1:30" \
  --data-urlencode "outtmpl=clip.mp4"
```

### Parameters

| Param | Default | Notes |
|---|---|---|
| `url` | **required** | The media URL (YouTube / Instagram reel / TikTok / Pinterest / …). |
| `outtmpl` | `%(title).16s.%(ext)s` | Output filename (e.g. `clip.mp4`, `song.m4a`). |
| `format` | `bestvideo` | yt-dlp format. Use `bestaudio` or `best` as needed. |
| `x` | — | Empty flag (`x=`) → audio-only (same as `format=bestaudio`). |
| `download_sections` | — | Time range `H:MM:SS-H:MM:SS` to clip. |
| `cookies_from_browser` | — | e.g. `chrome` / `firefox` for login-gated content. |

Notes:
- Video is auto-transcoded to an Apple-compatible **H.265 MP4** unless it's audio-only.
- Instagram links get browser headers/cookies applied automatically server-side.

## Transcribing (speech → text)

`GET /transcribe` downloads the audio and runs whisperx, returning **JSON**.
It is **synchronous and can be slow** (CPU whisperx — up to ~30 min for long
audio). Prefer the script:

```bash
scripts/transcribe.sh "<MEDIA_URL>"                 # default: segments + full text
scripts/transcribe.sh "<MEDIA_URL>" text            # plain text only
scripts/transcribe.sh "<MEDIA_URL>" text base en    # faster model, force English
```

Raw `curl` for plain text:

```bash
curl -G "http://barbabook.local:5001/transcribe" \
  --data-urlencode "url=<MEDIA_URL>" \
  --data-urlencode "response_format=text" | jq -r .text
```

### Parameters

| Param | Default | Notes |
|---|---|---|
| `url` | **required** | The media URL. |
| `response_format` | `segments` | `text` (plain), `segments` (text + timed segments), or `full` (word-level timestamps). |
| `model` | `small` | `tiny`, `base`, `small`, `medium`, `large-v3`. Smaller = faster, less accurate. |
| `language` | auto-detect | ISO-639-1 code, e.g. `en`, `es`. Omit to auto-detect. |
| `task` | `transcribe` | `translate` translates non-English audio → English text. |
| `cookies_from_browser` | — | Same as download. |

### Response shapes
- `text`: `{ "language": "en", "text": "…" }`
- `segments`: adds `duration` and a `segments[]` array of `{ start, end, text }`.
- `full`: `segments[]` with per-`words[]` `{ word, start, end }` timings.

## Errors

On failure the API returns JSON `{ "error": "…" }` with status 400 or 500.
Surface the message to the user. Common cases: missing `url`,
`Download failed: …` (bad/unsupported URL), or a whisperx timeout on very long
audio (suggest a smaller `model` or clipping a section first).
