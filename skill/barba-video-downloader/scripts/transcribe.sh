#!/usr/bin/env bash
# Transcribe spoken audio from a URL via the barbabook media service.
#
# Usage:
#   transcribe.sh <url> [response_format] [model] [language]
#     response_format: text | segments (default) | full
#     model:           tiny | base | small (default) | medium | large-v3
#     language:        ISO-639-1 (e.g. en, es); omit to auto-detect
#
# Examples:
#   transcribe.sh "https://youtu.be/XXXX"
#   transcribe.sh "https://youtu.be/XXXX" text
#   transcribe.sh "https://youtu.be/XXXX" text base en
#
# Synchronous and possibly slow (CPU whisperx). On connection failure the
# backend is unreachable (off the home network or server down).
set -euo pipefail

BASE="http://barbabook.local:5001"

if [ $# -lt 1 ]; then
  echo "usage: transcribe.sh <url> [response_format] [model] [language]" >&2
  exit 2
fi

URL="$1"
RESP="${2:-segments}"
MODEL="${3:-}"
LANG="${4:-}"

args=(--data-urlencode "url=${URL}" --data-urlencode "response_format=${RESP}")
[ -n "$MODEL" ] && args+=(--data-urlencode "model=${MODEL}")
[ -n "$LANG" ] && args+=(--data-urlencode "language=${LANG}")

out="$(curl --fail-with-body -sS -G "${BASE}/transcribe" "${args[@]}")"

# Print just the transcript for text mode if jq is available; else raw JSON.
if [ "$RESP" = "text" ] && command -v jq >/dev/null 2>&1; then
  printf '%s\n' "$out" | jq -r '.text'
else
  printf '%s\n' "$out"
fi
