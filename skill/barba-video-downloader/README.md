# barba-video-downloader (Claude skill)

A Claude skill that lets your session **download videos/audio** (YouTube,
Instagram reels, TikTok, Pinterest, and more) and **transcribe** them to text —
by talking to the private media service running on the home machine `barbabook`.

> **Works only at home:** the service lives at `http://barbabook.local:5001/`,
> which is reachable **only when you're on the same Wi-Fi / home network** and
> the server is running. Off the network, the skill will load but its commands
> will fail to connect.

## Install (pick the easiest one)

**Option 1 — just ask Claude (easiest).** In your Claude session, paste:

> Install the skill from https://github.com/HakS/yt-dlp-backend — copy the
> `skill/barba-video-downloader` folder into `~/.claude/skills/`.

**Option 2 — one line in a terminal:**

```bash
git clone https://github.com/HakS/yt-dlp-backend /tmp/bvd && \
  mkdir -p ~/.claude/skills && \
  cp -R /tmp/bvd/skill/barba-video-downloader ~/.claude/skills/ && \
  rm -rf /tmp/bvd
```

**Option 3 — upload in the app:** download this repo as a ZIP, unzip it, then in
Claude Desktop go to **Customize → Skills → Create skill** and upload the
`barba-video-downloader` folder (zipped).

After installing, restart/refresh your Claude session so it picks up the skill.

## Using it

Just ask naturally, e.g.:
- "Download this YouTube video: <link>"
- "Save this Instagram reel as an mp4: <link>"
- "Grab the audio from this TikTok: <link>"
- "Transcribe this video to text: <link>"

## Updating

Re-run Option 1 or 2 to overwrite with the latest version.
