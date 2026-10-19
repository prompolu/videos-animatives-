#!/usr/bin/env python3
"""Create an original 20-second, seamless instrumental catalogue music loop.

Run: python tools/compose_catalogue_loop.py
Requires Python 3 and NumPy. No network access or third-party audio is used.
All event tails wrap into the beginning, so the resulting WAV can be repeated
without imposing a fade or a pause every 20 seconds.
"""

from pathlib import Path
import math
import wave

import numpy as np


RATE = 48_000
DURATION = 20.0
BPM = 96
BEAT = 60 / BPM
FRAMES = round(RATE * DURATION)
DEST = Path(__file__).resolve().parents[1] / "assets" / "saraproc-catalogue-loop-20s.wav"
RNG = np.random.default_rng(20261018)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def envelope(time, duration, attack, release):
    """A cosine envelope whose value and slope vanish at each endpoint."""
    rise = 0.5 - 0.5 * np.cos(np.pi * np.minimum(time / attack, 1))
    fall = 0.5 - 0.5 * np.cos(np.pi * np.minimum((duration - time) / release, 1))
    return rise * fall


def add(mix, start, voice, level=1.0, pan=0.0):
    """Place a compact voice circularly, preserving all tails across the seam."""
    begin = round(start * RATE) % FRAMES
    angle = (pan + 1) * math.pi / 4
    stereo = voice[:, None] * np.array(
        [level * math.cos(angle), level * math.sin(angle)], dtype=np.float32
    )
    first = min(len(voice), FRAMES - begin)
    mix[begin:begin + first] += stereo[:first]
    if first < len(voice):
        mix[:len(voice) - first] += stereo[first:]


def pad(mix, start, notes):
    duration = 6.25
    time = np.arange(round(duration * RATE), dtype=np.float32) / RATE
    shape = envelope(time, duration, 1.25, 1.75)
    for index, note in enumerate(notes):
        phase = RNG.uniform(0, 2 * math.pi)
        frequency = hz(note)
        voice = (
            np.sin(2 * np.pi * frequency * 0.9985 * time + phase)
            + np.sin(2 * np.pi * frequency * 1.0015 * time + phase + 0.5)
            + 0.12 * np.sin(2 * np.pi * frequency * 2 * time + phase)
        ) / 2.12
        add(mix, start, voice * shape, 0.075, [-0.6, 0.35, -0.2, 0.6][index])


def pluck(mix, start, note, level=0.061, pan=0.0):
    duration = 2.5
    time = np.arange(round(duration * RATE), dtype=np.float32) / RATE
    frequency = hz(note)
    shape = (1 - np.exp(-time * 250)) * np.exp(-time / 0.55)
    shape *= envelope(time, duration, 0.008, 0.2)
    voice = np.sin(
        2 * np.pi * frequency * time
        + 0.6 * np.exp(-time * 6) * np.sin(2 * np.pi * frequency * 2 * time)
    )
    voice += 0.09 * np.sin(2 * np.pi * frequency * 3 * time) * np.exp(-time * 5)
    voice *= shape
    add(mix, start, voice, level, pan)
    add(mix, start + BEAT / 2, voice, level * 0.15, -pan)
    add(mix, start + BEAT, voice, level * 0.08, pan * 0.7)


def bass(mix, start, note, level):
    duration = 0.9
    time = np.arange(round(duration * RATE), dtype=np.float32) / RATE
    shape = (1 - np.exp(-time * 150)) * np.exp(-time / 0.24)
    shape *= envelope(time, duration, 0.012, 0.1)
    voice = np.sin(2 * np.pi * hz(note) * time)
    voice += 0.09 * np.sin(4 * np.pi * hz(note) * time)
    add(mix, start, voice * shape, level)


def main():
    mix = np.zeros((FRAMES, 2), dtype=np.float32)
    # Eight bars at 96 BPM. Each chord spans two bars (five seconds).
    # The final Asus chord leads naturally back into the opening Dmaj7.
    progression = [
        ([50, 57, 61, 66], 38, [74, 78, 81, 78, 76]),
        ([47, 54, 57, 62], 35, [74, 78, 81, 78, 73]),
        ([43, 54, 57, 62], 31, [74, 78, 81, 83, 78]),
        ([45, 52, 59, 62], 33, [76, 81, 83, 81, 73]),
    ]
    for index, (chord, root, melody) in enumerate(progression):
        start = index * 5.0
        pad(mix, start, chord)
        for item, (offset, note) in enumerate(zip([0.5, 2, 3.5, 5.5, 7], melody)):
            pluck(mix, start + offset * BEAT, note, pan=-0.18 if item % 2 == 0 else 0.2)
        for beat in [0, 2, 4, 6]:
            bass(mix, start + beat * BEAT, root, 0.043 if beat == 0 else 0.032)

    # Leave background-music headroom. No file-level fade: the video render
    # applies a fade just once at the beginning and once at its final end.
    rms = float(np.sqrt(np.mean(mix ** 2)))
    peak = float(np.max(np.abs(mix)))
    mix *= min(0.089 / max(rms, 1e-9), 0.65 / max(peak, 1e-9))
    pcm = np.round(mix * 32767).astype("<i2")
    peak = float(np.max(np.abs(pcm.astype(np.int32)))) / 32768
    rms = float(np.sqrt(np.mean((pcm.astype(np.float32) / 32768) ** 2)))
    step = pcm[0].astype(np.int32) - pcm[-1].astype(np.int32)
    seam = float(np.max(np.abs(step))) / 32768
    assert len(pcm) == FRAMES
    assert peak < 0.66, "Audio exceeds the planned peak headroom"
    assert seam < 0.005, "Unexpected waveform discontinuity at the loop seam"

    DEST.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(DEST), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    print(f"Wrote {DEST}")
    print(f"Duration: {FRAMES / RATE:.3f} s; stereo; {RATE} Hz; 16-bit PCM")
    print(f"Peak: {20 * math.log10(peak):.2f} dBFS; RMS: {20 * math.log10(rms):.2f} dBFS")
    print(f"Loop seam step: {seam:.7f} full-scale ({int(np.max(np.abs(step)))} PCM units)")
    print("Original synthesis; 96 BPM; no recurring fade; seed: 20261018")


if __name__ == "__main__":
    main()
