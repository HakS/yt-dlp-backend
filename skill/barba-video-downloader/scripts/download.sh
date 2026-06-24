#!/usr/bin/env bash
# Download video/audio from a URL via the barbabook media service.
#
# Usage:
#   download.sh <url> [outtmpl] [format|--audio]
#
# Examples:
#   download.sh "https://youtu.be/XXXX"
#   download.sh "https://youtu.be/XXXX" clip.mp4
#   download.sh "https://www.instagram.com/reel/XXXX/" reel.mp4
#   download.sh "https://youtu.be/XXXX" song.m4a --audio
#
# The server names/saves the file (Content-Disposition). On connection failure
# the backend is unreachable (off the home network or server down).
set -euo pipefail

BASE="http://barbabook.local:5001"

if [ $# -lt 1 ]; then
  echo "usage: download.sh <url> [outtmpl] [format|--audio]" >&2
  exit 2
fi

URL="$1"
OUTTMPL="${2:-}"
FMT="${3:-}"

args=(--data-urlencode "url=${URL}")
[ -n "$OUTTMPL" ] && args+=(--data-urlencode "outtmpl=${OUTTMPL}")

if [ "$FMT" = "--audio" ] || [ "$FMT" = "audio" ]; then
  args+=(--data-urlencode "x=")
elif [ -n "$FMT" ]; then
  args+=(--data-urlencode "format=${FMT}")
fi

# -OJ lets the server name the file; --fail-with-body surfaces error JSON on 4xx/5xx.
curl --fail-with-body -OJ -G "${BASE}/download" "${args[@]}"
