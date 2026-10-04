"""Option B: Resemble Enhance (denoise + generative voice restoration).

Usage: .venv-resemble/bin/python scripts/run_resemble.py <in.wav> <out.wav> [lambd] [tau]
  lambd: how strongly to denoise before enhancing (0..1, default 0.1, since there's little noise)
  tau:   prior temperature; higher is more "creative" restoration (0..1, default 0.5)
Loudness is normalised afterwards by scripts/loudnorm.sh, not here.
"""
import sys
import types
from pathlib import Path


def install_deepspeed_stub():
    # resemble-enhance imports DeepSpeed at module level for its training code, but
    # DeepSpeed won't build on macOS. Inference never calls it, so empty names suffice.
    def module(name, **attrs):
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        sys.modules[name] = mod
        return mod

    class Unavailable:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("DeepSpeed stub: training is not supported in this lab")

    def unavailable(*args, **kwargs):
        raise RuntimeError("DeepSpeed stub: training is not supported in this lab")

    module("deepspeed", DeepSpeedConfig=Unavailable, init_distributed=unavailable)
    module("deepspeed.accelerator", get_accelerator=unavailable)
    module("deepspeed.runtime")
    module("deepspeed.runtime.engine", DeepSpeedEngine=Unavailable)
    module("deepspeed.runtime.utils", clip_grad_norm_=unavailable)


def download_weights():
    # Fetch via huggingface_hub so the weights land in HF_HOME (inside the lab),
    # instead of the package's own git-lfs clone into site-packages.
    from huggingface_hub import snapshot_download

    repo = Path(snapshot_download("ResembleAI/resemble-enhance"))
    return repo / "enhancer_stage2"


def main(input_path, output_path, lambd, tau):
    install_deepspeed_stub()
    import soundfile as sf
    import torch

    # Newer torch defaults torch.load to weights_only=True, which rejects this
    # 2023 checkpoint format. The weights come from Resemble AI's official repo.
    original_load = torch.load
    torch.load = lambda *a, **k: original_load(*a, **{"weights_only": False, **k})

    from resemble_enhance.enhancer.inference import enhance

    run_dir = download_weights()
    # CPU first because it's guaranteed to work. MPS is untested with this model.
    device = "cpu"
    audio, sr = sf.read(input_path, dtype="float32")
    wav = torch.from_numpy(audio)
    enhanced, out_sr = enhance(wav, sr, device, nfe=64, solver="midpoint", lambd=lambd, tau=tau, run_dir=run_dir)
    sf.write(output_path, enhanced.cpu().numpy(), out_sr)
    print(f"Resemble Enhance (lambd={lambd}, tau={tau}) -> {output_path} @ {out_sr} Hz")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4, 5):
        sys.exit(__doc__)
    lambd_arg = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
    tau_arg = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    main(sys.argv[1], sys.argv[2], lambd_arg, tau_arg)
