# Findings

What happened when real interview recordings went through every open-source cleanup model we could get running on a MacBook. Everything here was judged on 2-minute clips from real episodes. The recordings themselves stay private.

## The source material

Zoom local recordings of remote interviews: one mixed track of host and guest, AAC at about 84 kbps, 48 kHz. Measured on a typical episode:

- **Noise is not the problem.** Silences are already near-silent, because Zoom's own suppression gates them. Most "AI noise removal" tools have almost nothing to do here.
- **Dull, boxy tone is the problem.** 250–500 Hz is the loudest band. 2–4 kHz sits about 11 dB lower, and 4–7 kHz about 17 dB lower. Voices lack presence and "air".
- **Nothing above about 12 kHz.** Zoom's codec cuts it off hard.
- **The two voices need different fixes.** One speaker's voice died off above about 4.4 kHz, while the other reached 12 kHz. Both share one mixed track, so no single EQ suits both.
- **The stereo is fake.** Left and right are identical, so everything is treated as mono.
- **It's quiet.** About -20 to -23 LUFS, against a usual podcast target of -16.
- On a messier recording, the real issues were **room echo and uneven volume**, not noise.

## Round 1: tone and bandwidth

Every output was loudness-matched to -16 LUFS before listening, because louder always sounds "better".

| Option | What it is | Verdict |
|---|---|---|
| A | FFmpeg EQ chain (`chain_a_ffmpeg.sh`): +4 dB at 3.2 kHz, treble shelf, compressor | Clearer, but it lifts the 2.5–5 kHz "fatigue zone" by about 6 dB and doesn't reduce mud at all. Tiring over an hour. |
| B | [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance): generative restoration | Fills the full frequency range and keeps silences clean. The strongest option. |
| C | [ClearerVoice](https://github.com/modelscope/ClearerVoice-Studio) `MossFormer2_SR_48K`: super-resolution | **Made it duller.** It keeps the original only up to its 99%-energy point (about 7 kHz on this audio), and the highs it generates are weak. |
| D | [LavaSR](https://github.com/ysharma3501/LavaSR): bandwidth extension | Adds a hiss layer above 12 kHz, even in the silences. Fed at 16 kHz instead of 24, it's the same hiss plus an audible seam at 8 kHz. |

That led to a second DSP chain, the **warm chain** (`warm_filters.txt`), built for long listening rather than clarity: cut mud at 250 Hz, a gentle broad lift at 2.5 kHz, a slight dip at 4.5 kHz, a soft top shelf, and slow compression. Compared with chain A, it took mud from 3.5 to 2.5 dB and lifted harshness by about 4 dB instead of 6.

### Which layers of the warm chain matter

`render_layers.sh` renders the chain one step at a time, all loudness-matched, so each step can be heard on its own.

- **The mud cut is the biggest change** (-1.4 dB in the mud band). On a voice that isn't boomy, it can thin the sound out. One messy clip went from 1.4 dB of mud to 0.0.
- **The compressor matters next.** It evens out volume (loudness range 3.0 to 2.2), but adds about 0.5 dB of mud back. On rough recordings it needs to be firmer: one went only from 4.2 to 3.6.
- **The rumble cut and the de-esser do almost nothing** on Zoom audio.

## Round 2: echo

On a recording with audible room echo:

| Tool | Type | Verdict |
|---|---|---|
| [WPE](https://github.com/fgnt/nara_wpe) (taps 20, 1024/256 STFT) | Classic signal processing, invents nothing | Mediocre |
| [VoiceFixer](https://github.com/haoheliu/voicefixer) (mode 0) | AI general restoration | Mediocre |
| ClearerVoice `MossFormer2_SE_48K` | AI speech enhancement | Mediocre |
| **Resemble Enhance, lambd 0.9** | Strong denoise before generative restoration | **Clear winner by ear. It still sounds like the real person.** |

The winner was about 0.5 dB *quieter* than the WPE and ClearVoice outputs (-24.0 vs -23.4 LUFS), so the preference isn't a loudness bias.

## The machine couldn't pick a winner

`score_quality.py` reports UTMOS (a model trained to predict human naturalness ratings) alongside a tone balance per band. On real recordings, **UTMOS scored everything between 2.1 and 2.3**. Changing nothing but volume moved it by 0.05, so those gaps are noise. When the source is a compressed Zoom call, the source sets the ceiling, and the metric can't see past it.

So the final calls were made **by ear, on headphones and a phone speaker**, with the tone-balance numbers used to explain what the ears heard rather than to decide.

DNSMOS was dropped as a second metric: the PyPI `speechmos` package clashes with the SpeechMOS repo that provides UTMOS.

## Current best chain

```
Resemble Enhance (lambd 0.9, tau 0.5)  →  warm chain  →  two-pass loudnorm to -16 LUFS
```

This is what `pipeline.sh` runs. The fallback with no AI is the warm chain alone (`pipeline.sh … dsp`).

**Not yet done:** this exact chain has only been rendered on short clips. It hasn't been listened to on a full episode, and nobody has checked whether the Resemble sound holds up over a long listen.

## Speed (Apple M5, 16 GB, CPU)

| Step | 2-minute clip |
|---|---|
| FFmpeg chains | a couple of seconds |
| LavaSR (MPS) | about 15 s |
| ClearerVoice | under a minute |
| Resemble Enhance (CPU) | about 2.5–4 minutes |

A full 26-minute episode through Resemble is roughly an hour. Apple's MPS backend is untested with Resemble and might cut that down.

## The biggest wins aren't software

1. **Record each participant on a separate track.** Zoom has a setting for it. Two voices that need different EQs could then be cleaned separately.
2. **A less echoey room.** Every echo tool was a compromise. The one that worked is the slowest step in the chain.

## Setup lessons

- **Each model gets its own virtual environment.** Their dependency pins clash, for example Resemble pins an old torch.
- **Resemble Enhance imports DeepSpeed, which won't build on macOS.** Inference never calls it, so `run_resemble.py` installs an empty stub module first. The package is installed with `--no-deps` for the same reason.
- **Newer PyTorch refuses Resemble's 2023 checkpoint** (`torch.load` now defaults to `weights_only=True`). The script loosens that for this one official checkpoint.
- **VoiceFixer hard-codes its weights to `~/.cache`.** `run_voicefixer.py` refuses to run unless `HOME` points inside the repo.
- **ClearerVoice downloads into whatever the current directory is.** The script changes into `.cache/clearvoice` first.
- **`$BASH_SOURCE` is empty under zsh.** The first version of `env.sh` used it to find the repo, resolved to the wrong folder, and quietly wrote 1.3 GB of caches outside the project. It now uses the working directory and refuses to run from anywhere else.
