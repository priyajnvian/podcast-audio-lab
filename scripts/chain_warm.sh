#!/bin/bash
# "Warm" chain for long listening. Round 1 showed chain A's +4 dB at 3.2 kHz lifts the
# fatigue zone by ~6 dB and doesn't reduce mud at all. This one cuts mud properly,
# lifts presence gently and broadly, and uses slower compression so levels stay even
# without sounding squashed. Steps live in warm_filters.txt, shared with render_layers.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
in="$1"; out="$2"
filters=$(cut -d'|' -f3 scripts/warm_filters.txt | paste -sd, -)
scripts/loudnorm.sh "$in" "$out" "$filters"
