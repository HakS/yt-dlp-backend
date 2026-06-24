# Claude skill (barba-video-downloader)

This repo ships a Claude skill in `skill/barba-video-downloader/` that lets a
Claude session download and transcribe media by talking to this service. Install
it into `~/.claude/skills/` so Claude can use it.

> **Only works on the local network.** The skill calls the service at
> `http://barbabook.local:5001/`, which is reachable **only when your machine is
> on the same Wi-Fi / LAN as `barbabook`** and the server is running. Off the
> network, the skill still loads but every command fails to connect — this is
> expected, not a bug.

**Option 1 — ask Claude (easiest).** In a Claude session, paste:

> Install the skill from https://github.com/HakS/yt-dlp-backend — copy the
> `skill/barba-video-downloader` folder into `~/.claude/skills/`.

**Option 2 — one line in a terminal:**

```bash
git clone https://github.com/HakS/yt-dlp-backend /tmp/bvd && \
  mkdir -p ~/.claude/skills && \
  cp -R /tmp/bvd/skill/barba-video-downloader ~/.claude/skills/ && \
  rm -rf /tmp/bvd
```

If you already have the repo cloned, just copy the folder:

```bash
mkdir -p ~/.claude/skills && \
  cp -R skill/barba-video-downloader ~/.claude/skills/
```

**Option 3 — upload in the app:** download this repo as a ZIP, unzip it, then in
Claude Desktop go to **Customize → Skills → Create skill** and upload the
`barba-video-downloader` folder (zipped).

After installing, restart/refresh your Claude session so it picks up the skill.
To update later, re-run any option to overwrite with the latest version. See
`skill/barba-video-downloader/README.md` for usage details.

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

  Note: a bare `python3` in a server's minimal PATH often resolves to Homebrew's
  Python (no whisperx), which is why the probe avoids that as the default.

# Examples of usage

```
http://127.0.0.1:5000/download?
url=
https://www.youtube.com/watch?v=mSevVBCAe6Y
&download_sections=*
0:1:1-
0:1:10
&outtmpl=video.webm
&format=bestvideo





http://127.0.0.1:5000/download?
url=
https://www.youtube.com/shorts/lkO95SCW40I
&format=bestvideo

http://127.0.0.1:5000/download?
url=
https://www.youtube.com/shorts/rpLlhfO2Llo
&outtmpl=video.mp4
&format=bestvideo

http://127.0.0.1:5000/download?
url=
https://www.youtube.com/watch?v=0_GEzVYOkYg
&x
&outtmpl=audio.opus



http://127.0.0.1:5000/download?
url=  
https://www.youtube.com/watch?v=Q5OMHwYcgpE
&download_sections=*
0:3:21-
0:3:50
&outtmpl=flamenco.opus
&x
  



http://127.0.0.1:5000/download?
url=
https://www.instagram.com/p/DGu_b-yK-gj/
&outtmpl=tal.mp3

http://127.0.0.1:5000/download?
url=
https://www.youtube.com/watch?v=hBBOjCiFcuo

http://127.0.0.1:5000/download?
url=
https://www.youtube.com/watch?v=U_LXkVU1MLs
&format=bestaudio


https://www.youtube.com/watch?v=0aHl15zQOsg&list=PLs-YFAlH63L-TER_jnvnTxnrfQJcqyvZW&index=2
```

# /transcribe

Downloads ONLY the audio of a URL and transcribes it with whisperx (run
out-of-process against the local pyenv install). Returns JSON in a token-cheap
shape meant for AI agents.

Query parameters:

- `url` (required) — the media URL.
- `response_format` — `segments` (default), `text`, or `full`.
  - `segments`: `{ language, duration, text, segments: [{ start, end, text }] }`
  - `text`: `{ language, text }` (cheapest — transcript only)
  - `full`: raw whisperx JSON, including word-level alignments
- `model` — Whisper model name (default `small`; e.g. `base`, `medium`, `large-v3`).
- `language` — language code (e.g. `en`); omit to auto-detect.
- `task` — `transcribe` (default) or `translate` (X → English).
- `cookies_from_browser` — same form as `/download`, for gated sources.

```
# Default: timestamped segments + full text
http://127.0.0.1:5001/transcribe?url=https://www.youtube.com/watch?v=mSevVBCAe6Y

# Just the transcript text, faster model
http://127.0.0.1:5001/transcribe?url=https://www.youtube.com/watch?v=mSevVBCAe6Y&response_format=text&model=base

# Full whisperx JSON with word-level timestamps, forced language
http://127.0.0.1:5001/transcribe?url=https://www.youtube.com/watch?v=mSevVBCAe6Y&response_format=full&language=en
```
