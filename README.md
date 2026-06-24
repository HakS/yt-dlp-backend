# Configuration (env vars)

The server reads two optional environment variables; both have defaults so it
runs out of the box on a typical macOS/Homebrew setup:

- `FFMPEG_DIR` — directory containing `ffmpeg` (default `/opt/homebrew/bin`).
- `WHISPERX_PYTHON` — absolute path to the Python interpreter that has whisperx
  + torch installed (default `python3`). `/transcribe` will fail if this points
  at an interpreter without whisperx. On `barbabook` this is the dedicated pyenv
  interpreter, e.g.:

  ```bash
  export WHISPERX_PYTHON="$HOME/.pyenv/versions/3.11.13/bin/python"
  python app.py
  ```

Set it in your shell profile or a launch wrapper so the value isn't hard-coded
in the source.

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
