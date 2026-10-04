"""VoiceFixer: AI general speech restoration (noise, reverb, low bandwidth, clipping).

Usage: HOME="$LAB/.cache/home" .venv-dereverb/bin/python scripts/run_voicefixer.py <in.wav> <out.wav> [mode]
  mode: 0 (default, original model), 1 (adds preprocessing), 2 (for badly degraded audio)
VoiceFixer hard-codes its weights to ~/.cache/voicefixer, so HOME must point inside the lab
or it writes to the real home folder. The script refuses to run otherwise.
Loudness and EQ are applied afterwards by the shell scripts, not here.
"""
import os
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent


def main(input_path, output_path, mode):
    home = Path(os.path.expanduser("~")).resolve()
    if LAB not in home.parents:
        sys.exit(f"HOME is {home}, outside the lab. Run with HOME=\"{LAB}/.cache/home\".")

    from voicefixer import VoiceFixer

    fixer = VoiceFixer()
    fixer.restore(input=str(input_path), output=str(output_path), cuda=False, mode=mode)
    print(f"VoiceFixer (mode {mode}) -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
