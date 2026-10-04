#!/bin/bash
# Option A: plain DSP, no AI. Targets what the diagnosis found:
# boomy 250-500 Hz, weak 2-5 kHz presence, no air, quiet overall.
set -euo pipefail
cd "$(dirname "$0")/.."
in="${1:?usage: chain_a_ffmpeg.sh <in.wav> <out.wav>}"
out="${2:?usage: chain_a_ffmpeg.sh <in.wav> <out.wav>}"
filters="highpass=f=80:poles=2,\
equalizer=f=350:t=q:w=1.0:g=-3,\
equalizer=f=3200:t=q:w=1.0:g=4,\
treble=g=3:f=7000,\
acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=2,\
deesser=i=0.4:m=0.5:f=0.5"
scripts/loudnorm.sh "$in" "$out" "$filters"
