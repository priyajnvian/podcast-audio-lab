"""Second opinion on how pleasant each file is for long listening.

UTMOS (1-5, higher is better): a model trained on human naturalness ratings. It only
sees 16 kHz audio, so it can't judge the "air" above 8 kHz.
Tone balance (dB relative to the 250 Hz-1 kHz body of the voice, voiced frames only):
  mud   150-400 Hz   too high = boomy, boxy
  harsh 2.5-5 kHz    too high = piercing, tiring over an hour
  sss   5-9 kHz      too high = sharp S sounds
  air   9-16 kHz     too low = dull, closed-in

Usage: .venv-resemble/bin/python scripts/score_quality.py <file.wav> [...]
"""
import sys

import librosa
import numpy as np
import torch

UTMOS_RATE = 16000
CHUNK_SECONDS = 10
BANDS = {"mud": (150, 400), "harsh": (2500, 5000), "sss": (5000, 9000), "air": (9000, 16000)}
BODY = (250, 1000)


def utmos_score(path, model):
    audio, _ = librosa.load(path, sr=UTMOS_RATE, mono=True)
    step = CHUNK_SECONDS * UTMOS_RATE
    # Skip near-silent chunks so the long pause doesn't drag every file down equally.
    voiced = [audio[i:i + step] for i in range(0, len(audio) - step + 1, step)
              if np.sqrt(np.mean(audio[i:i + step] ** 2)) > 0.01]
    if not voiced:
        print(f"note: {path} has no voiced {CHUNK_SECONDS} s chunk (too short or too quiet), "
              "so UTMOS is n/a", file=sys.stderr)
        return float("nan")
    with torch.no_grad():
        return np.mean([model(torch.from_numpy(c).unsqueeze(0), UTMOS_RATE).item() for c in voiced])


def tone_balance(path):
    audio, rate = librosa.load(path, sr=48000, mono=True)
    power = np.abs(librosa.stft(audio, n_fft=4096, hop_length=1024)) ** 2
    freqs = librosa.fft_frequencies(sr=rate, n_fft=4096)
    frame_energy = power.sum(axis=0)
    # Voiced frames only: silences would otherwise pull every band towards the noise floor.
    voiced = power[:, frame_energy > np.percentile(frame_energy, 40)]

    def band_db(low, high):
        mask = (freqs >= low) & (freqs < high)
        return 10 * np.log10(voiced[mask].mean() + 1e-20)

    body = band_db(*BODY)
    return {name: band_db(*edges) - body for name, edges in BANDS.items()}


def main(paths):
    model = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
    print(f"{'file':32} {'UTMOS':>6} " + " ".join(f"{b:>6}" for b in BANDS))
    for path in paths:
        tone = tone_balance(path)
        print(f"{path.split('/')[-1]:32} {utmos_score(path, model):6.2f} "
              + " ".join(f"{tone[b]:6.1f}" for b in BANDS))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
