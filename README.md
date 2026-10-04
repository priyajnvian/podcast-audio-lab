# Podcast Audio Lab

**Can you get studio-quality podcast audio out of a Zoom call, for free, with open-source models on a laptop?**

Adobe's Podcast Enhance does it in one click, on Adobe's servers, behind a subscription. This is an attempt to beat it with tools anyone can run: Resemble Enhance, ClearerVoice, LavaSR, VoiceFixer, WPE and plain FFmpeg, all tested on real interview recordings and judged by ear.

We're not there yet. What's here is the **framework**: a pipeline that already makes a Zoom recording noticeably warmer and more even, a harness for testing any new model against it fairly, and a write-up of everything that worked and everything that didn't.

> **This is for developers, not a finished product.** No app, no UI, no installer. You'll be creating Python virtual environments, downloading model weights, and reading shell scripts. If you want one-click cleanup today, use Adobe Podcast. If you want to help build the free version, read on.

## What it does today

```bash
scripts/pipeline.sh interview.mp4 cleaned.wav        # AI chain (slow, best result)
scripts/pipeline.sh interview.mp4 cleaned.wav dsp    # FFmpeg only (seconds, no AI)
```

```
any audio/video ──► mono 48 kHz ──► Resemble Enhance ──► warm chain ──► -16 LUFS
                                    (denoise, dereverb,   (mud cut, gentle presence,
                                     restore bandwidth)    slow compression)
```

On a synthetic test recording, made boomy, echoey and band-limited to imitate a Zoom call, the AI chain cut mud by about 3 dB, lifted the "air" band by about 14 dB, and brought the loudness from -25 to exactly -16 LUFS. Your recordings will differ, and the scoring tools will tell you how.

## Why it's a framework, not a tool

The interesting part isn't the pipeline. It's how the pipeline was found, and that process is reusable:

- **Diagnose before you fix.** We measured first. The obvious move for "bad podcast audio" is noise removal, but Zoom recordings have almost no noise. The real problems were dull tone, a codec cutoff at 12 kHz, and room echo. That changed which models were worth trying.
- **Loudness-match everything.** Every output goes through two-pass loudnorm to the same level before anyone listens (`loudnorm.sh`), because louder always sounds better and will fool you.
- **Hear each layer separately.** `render_layers.sh` renders the DSP chain one step at a time, so you can hear which filters earn their place. Two of the seven barely do anything.
- **Score it, but trust your ears.** `score_quality.py` gives a UTMOS naturalness score and a tone balance per band. On real Zoom audio, UTMOS couldn't separate any of the options. That's a finding in itself.
- **Keep it contained.** Every model downloads gigabytes into hidden cache folders. `env.sh` forces all of it into the repo's `.cache/`, and the scripts refuse to run if that's bypassed.

Read **[FINDINGS.md](FINDINGS.md)** for the full results: which models won, which made things worse, and why.

## Setup

You need macOS or Linux, FFmpeg, and Python 3.12. It was built and tested on an Apple Silicon Mac, on the CPU.

The `dsp` mode needs nothing but FFmpeg. Each AI model gets its own virtual environment, because their dependencies clash. Run everything from the repo root.

```bash
source scripts/env.sh   # keeps every cache and download inside .cache/

# Resemble Enhance (the one pipeline.sh uses)
python3.12 -m venv .venv-resemble
.venv-resemble/bin/pip install -r requirements/resemble.txt
.venv-resemble/bin/pip install --no-deps resemble-enhance==0.0.1   # its deps include DeepSpeed, which won't build on macOS

# Optional: the models that lost, for comparison
python3.12 -m venv .venv-clearvoice && .venv-clearvoice/bin/pip install -r requirements/clearvoice.txt
python3.12 -m venv .venv-lavasr && .venv-lavasr/bin/pip install -r requirements/lavasr.txt \
  && .venv-lavasr/bin/pip install --no-deps git+https://github.com/ysharma3501/LavaSR@33ac040892519c1bb4aed7eb32e79af51cc29e2a
python3.12 -m venv .venv-dereverb && .venv-dereverb/bin/pip install -r requirements/dereverb.txt \
  && .venv-dereverb/bin/pip install --no-deps voicefixer==0.1.3
```

The requirements files are exact snapshots of the environments the experiments ran in. Model weights download on first use: about 800 MB for Resemble Enhance.

## Running the individual models

Each script takes `<in.wav> <out.wav>` and does one thing. Loudness and EQ are applied afterwards by the shell scripts.

| Script | What it does |
|---|---|
| `pipeline.sh` | The full chain, in one command |
| `run_resemble.py` | Resemble Enhance. Optional `lambd` (denoise strength) and `tau` (how creative the restoration is) |
| `run_clearvoice.py` | ClearerVoice super-resolution or speech enhancement |
| `run_lavasr.py` | LavaSR bandwidth extension |
| `run_voicefixer.py` | VoiceFixer restoration. Needs `HOME="$PWD/.cache/home"` |
| `run_wpe.py` | WPE dereverberation, no AI |
| `chain_warm.sh` | The warm DSP chain + loudnorm |
| `chain_a_ffmpeg.sh` | The first, brighter DSP chain it replaced |
| `render_layers.sh` | The warm chain one step at a time, each loudness-matched |
| `loudnorm.sh` | Two-pass loudnorm to -16 LUFS / -1.5 dBTP |
| `score_quality.py` | UTMOS + tone balance (mud, harsh, sss, air) for any number of files |

## What's not done

Honestly, a lot. That's what makes it a lab.

- **The Adobe comparison hasn't been run.** Adobe Podcast Enhance is the benchmark this is chasing, but no side-by-side has been done yet. Until then, "beat Adobe" is the goal, not a result.
- **No full episode has been processed end to end.** The best chain has only been heard on 2-minute clips. Whether it still sounds good after 45 minutes is unknown.
- **It's slow.** Resemble Enhance on a CPU takes roughly an hour per episode. Apple's MPS backend is untested with it.
- **Two voices, one track.** Zoom mixes host and guest together, and they need different EQ. The real fix is recording separate tracks, which this can't do for you.
- **Video isn't handled.** The pipeline outputs audio only. Putting it back onto the video is one FFmpeg command, but it's not scripted yet.
- **Only tested on Zoom recordings.** Other sources will need different settings.
- **No automated tests.** `pipeline.sh` was verified in both modes on a synthetic clip. Everything else was verified by running it on real recordings.

## Ideas worth trying next

Separate-track recording. Running Resemble on MPS. DeepFilterNet for recordings that do have background noise. Voice-specific EQ, by splitting the speakers first. A proper blind A/B against Adobe Podcast.

## License

MIT for the code in this repo. Each model has its own license and weights: Resemble Enhance (MIT), ClearerVoice-Studio (Apache 2.0), LavaSR (Apache 2.0), VoiceFixer (MIT), NARA-WPE (MIT). Check them before shipping anything built on top.
