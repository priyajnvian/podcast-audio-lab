"""Option D: LavaSR bandwidth extension. Rebuilds the highs Zoom's codec cut off.

Usage: .venv-lavasr/bin/python scripts/run_lavasr.py <in.wav> <out.wav> [input_sr, default 24000]
Loudness is normalised afterwards by scripts/loudnorm.sh, not here.
"""
import sys

import soundfile as sf
import torch
from LavaSR.model import LavaEnhance2


def main(input_path, output_path, input_sr):
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = LavaEnhance2("YatharthS/LavaSR", device)
    # input_sr sets where the model starts inventing highs. 24 kHz keeps Zoom's real
    # content up to ~12 kHz. 16 kHz is closer to its VCTK training data but discards more.
    audio, _ = model.load_audio(input_path, input_sr=input_sr)
    # Denoise stays off: the diagnosis found almost no noise to remove.
    enhanced = model.enhance(audio, denoise=False, batch=True).cpu().numpy().squeeze()
    sf.write(output_path, enhanced, 48000)
    print(f"LavaSR ({device}) -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 24000)
