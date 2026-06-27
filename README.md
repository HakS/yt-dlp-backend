# Claude skill (barba-video-downloader)

This repo ships a Claude skill that lets a Claude session download and
transcribe media by talking to this service.

> **Only works on the home network.** The skill calls the service at
> `http://barbabook.local:5001/`, which is reachable **only when your machine is
> on the same Wi-Fi / LAN as `barbabook`** and the server is running.

---

## Install the skill (pick one)

### Option 1 — Download the zip (easiest, no terminal needed)

1. **[Download barba-video-downloader.skill](https://github.com/HakS/yt-dlp-backend/raw/main/barba-video-downloader.skill)**
2. In **Claude Desktop** → **Customize → Skills → Create skill** → upload the zip.
3. Restart your Claude session.

Done. The skill is active.

---

### Option 2 — One line in a terminal

```bash
git clone https://github.com/HakS/yt-dlp-backend /tmp/bvd && \
  mkdir -p ~/.claude/skills && \
  cp -R /tmp/bvd/skill/barba-video-downloader ~/.claude/skills/ && \
  rm -rf /tmp/bvd
```

---

### Option 3 — Ask Claude to install it

In a Claude session paste:

> Install the skill from https://github.com/HakS/yt-dlp-backend — copy the
> `skill/barba-video-downloader` folder into `~/.claude/skills/`.

---

After installing, restart/refresh your Claude session so it picks up the skill.
See `skill/barba-video-downloader/README.md` for usage details.

---

# Configuration (env vars)

The server reads two optional environment variables; both have defaults so it
runs out of the box on a typical macOS/Homebrew setup:

- `FFMPEG_DIR` — directory containing `ffmpeg` (default `/opt/homebrew/bin`).
- `WHISPERX_PYTHON` — absolute path to the Python interpreter that has whisperx
  + torch installed. When unset, the server probes a few candidates at startup
  (the `~/.pyenv/versions/3.11.13` interpreter, then `python3.11`, then
  `python3`) and uses the first one that can `import whisperx`, so it works out
  of the box on `barbabook`. Set this explicitly to override the probe or when
  whisperx lives elsewhere:

  ```bash
  export WHISPERX_PYTHON="$HOME/.pyenv/versions/3.11.13/bin/python"
  python app.py
  ```

---

# /download

Downloads video or audio from a URL via yt-dlp.

Query parameters:

| Param | Default | Notes |
|---|---|---|
| `url` | **required** | The media URL. |
| `outtmpl` | `%(title).16s.%(ext)s` | Output filename. |
| `format` | `bestvideo` | yt-dlp format string. |
| `x` | — | Empty flag → audio-only. |
| `download_sections` | — | Time range `H:MM:SS-H:MM:SS`. |
| `cookies_from_browser` | — | e.g. `chrome` for login-gated content. |

---

# /transcribe

Downloads ONLY the audio of a URL and transcribes it with whisperx. Returns
JSON in a token-cheap shape meant for AI agents.

Query parameters:

| Param | Default | Notes |
|---|---|---|
| `url` | **required** | The media URL. |
| `response_format` | `segments` | `text`, `segments`, or `full`. |
| `model` | `small` | `tiny`, `base`, `small`, `medium`, `large-v3`. |
| `language` | auto-detect | ISO-639-1 code, e.g. `en`. |
| `task` | `transcribe` | `translate` → English. |
| `cookies_from_browser` | — | Same as `/download`. |

Response shapes:
- `text`: `{ language, text }`
- `segments`: `{ language, duration, text, segments: [{ start, end, text }] }`
- `full`: raw whisperx JSON with word-level alignments
