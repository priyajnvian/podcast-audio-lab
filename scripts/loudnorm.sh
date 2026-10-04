#!/bin/bash
# Two-pass loudnorm to -16 LUFS so every output is compared at the same volume.
# Louder always sounds "better", so skipping this would bias the listening test.
# Usage: loudnorm.sh <in> <out> [extra filters applied before loudnorm]
set -euo pipefail
in="$1"; out="$2"; pre="${3:-anull}"
stats=$(ffmpeg -nostdin -hide_banner -nostats -i "$in" -af "$pre,loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$stats" | grep "\"$1\"" | sed -E 's/.*: "([^"]+)".*/\1/'; }
ffmpeg -nostdin -hide_banner -loglevel error -y -i "$in" \
  -af "$pre,loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true,aresample=48000" \
  -ac 1 -c:a pcm_s16le "$out"
