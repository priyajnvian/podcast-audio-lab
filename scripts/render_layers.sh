#!/bin/bash
# Render every step of the warm chain cumulatively (step N = steps 1..N applied), so
# each layer can be heard on its own. Every file is loudness-matched to -16 LUFS so
# you hear the tone change, not a volume change.
# Usage: render_layers.sh <in.wav> <out_dir> <prefix>
set -euo pipefail
cd "$(dirname "$0")/.."
in="$1"; out_dir="$2"; prefix="$3"
mkdir -p "$out_dir"
scripts/loudnorm.sh "$in" "$out_dir/${prefix}_step0_start.wav"
chain=""; step=0
while IFS='|' read -r key label filter; do
  step=$((step + 1))
  chain="${chain:+$chain,}$filter"
  scripts/loudnorm.sh "$in" "$out_dir/${prefix}_step${step}_${key}.wav" "$chain"
done < scripts/warm_filters.txt
