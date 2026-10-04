#!/bin/bash
# One-command cleanup using the best chain found so far (see FINDINGS.md).
#
# Usage: scripts/pipeline.sh <input audio or video> <output.wav> [ai|dsp]
#   ai  (default) Resemble Enhance -> warm chain -> -16 LUFS. Needs .venv-resemble.
#                 Slow: a few minutes per 2-minute clip on an Apple Silicon CPU.
#   dsp           Warm chain -> -16 LUFS only. FFmpeg alone, seconds, no AI, no downloads.
#
# Intermediate files are kept in .cache/tmp/pipeline/ so each stage can be heard on its own.
set -euo pipefail

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
fi
in="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
out_dir="$(mkdir -p "$(dirname "$2")" && cd "$(dirname "$2")" && pwd)"
out="$out_dir/$(basename "$2")"
mode="${3:-ai}"
case "$mode" in ai|dsp) ;; *) echo "mode must be 'ai' or 'dsp', got '$mode'" >&2; exit 1 ;; esac
[ -f "$in" ] || { echo "input not found: $in" >&2; exit 1; }

cd "$(dirname "$0")/.."
source scripts/env.sh
work=".cache/tmp/pipeline"
mkdir -p "$work"

# Zoom and most recorders give fake stereo (identical channels), so fold to mono at 48 kHz.
echo "[1/3] extracting mono 48 kHz audio"
ffmpeg -nostdin -hide_banner -loglevel error -y -i "$in" -vn -ac 1 -ar 48000 -c:a pcm_s16le "$work/01_source.wav"
stage="$work/01_source.wav"

if [ "$mode" = ai ]; then
  if [ ! -x .venv-resemble/bin/python ]; then
    echo ".venv-resemble not found. Set it up (see README), or run with 'dsp'." >&2
    exit 1
  fi
  # lambd 0.9 = strong denoise/dereverb before enhancing. It won the echo test while
  # still sounding like the real person; 0.1 (the script default) left the room in.
  echo "[2/3] Resemble Enhance (lambd 0.9, tau 0.5)"
  .venv-resemble/bin/python scripts/run_resemble.py "$stage" "$work/02_resemble.wav" 0.9 0.5
  stage="$work/02_resemble.wav"
else
  echo "[2/3] skipping AI enhancement (dsp mode)"
fi

echo "[3/3] warm chain + loudness to -16 LUFS"
scripts/chain_warm.sh "$stage" "$out"
echo "done -> $out"
