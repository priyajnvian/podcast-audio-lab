"""WPE dereverberation (NARA-WPE): classic signal processing, no AI, invents nothing.

Usage: .venv-dereverb/bin/python scripts/run_wpe.py <in.wav> <out.wav> [taps]
  taps: how far back WPE looks for echoes to subtract (default 20, ~107 ms at 48 kHz).
Loudness and EQ are applied afterwards by the shell scripts, not here.
"""
import sys

import numpy as np
import soundfile as sf
from nara_wpe.utils import istft, stft
from nara_wpe.wpe import wpe

# The package's usual settings are for 16 kHz (512/128). At 48 kHz, these keep a
# similar frame length in milliseconds, and taps are raised so the look-back window
# still covers the early part of a room's echo tail.
FRAME_SIZE = 1024
FRAME_SHIFT = 256
DELAY = 3
ITERATIONS = 5


def main(input_path, output_path, taps):
    audio, rate = sf.read(input_path, dtype="float64")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    spectrum = stft(audio[np.newaxis, :], size=FRAME_SIZE, shift=FRAME_SHIFT).transpose(2, 0, 1)
    cleaned = wpe(spectrum, taps=taps, delay=DELAY, iterations=ITERATIONS, statistics_mode="full")
    result = istft(cleaned.transpose(1, 2, 0), size=FRAME_SIZE, shift=FRAME_SHIFT)[0]
    sf.write(output_path, result[: len(audio)], rate)
    print(f"WPE (taps={taps}) -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 20)
