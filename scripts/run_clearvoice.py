"""ClearerVoice-Studio models.

Usage: .venv-clearvoice/bin/python scripts/run_clearvoice.py <in.wav> <out.wav> [model]
  model: MossFormer2_SR_48K (default, super-resolution, round 1 option C)
         MossFormer2_SE_48K (speech enhancement: noise and some reverb)
Loudness and EQ are applied afterwards by the shell scripts, not here.
"""
import os
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
TASK_FOR_MODEL = {
    "MossFormer2_SR_48K": "speech_super_resolution",
    "MossFormer2_SE_48K": "speech_enhancement",
}


def main(input_path, output_path, model_name):
    if model_name not in TASK_FOR_MODEL:
        sys.exit(f"Unknown model {model_name}. Choose one of: {', '.join(TASK_FOR_MODEL)}")
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    # ClearVoice downloads checkpoints into ./checkpoints relative to the working
    # directory, so run from the lab cache to keep them inside the lab.
    work_dir = LAB / ".cache" / "clearvoice"
    work_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)

    from clearvoice import ClearVoice

    model = ClearVoice(task=TASK_FOR_MODEL[model_name], model_names=[model_name])
    enhanced = model(input_path=str(input_path), online_write=False)
    model.write(enhanced, output_path=str(output_path))
    print(f"ClearVoice {model_name} -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "MossFormer2_SR_48K")
