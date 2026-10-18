#!/usr/bin/env python3
"""Render an original 60-second instrumental cue using only synthesized tones.

Requires Python 3 and NumPy. No downloaded audio, samples, or external programs.
Run from any directory: python tools/compose_music.py
"""

from pathlib import Path
import math
import wave

import numpy as np


RATE = 48_000
DURATION = 60.0
BPM = 96
BEAT = 60 / BPM
DEST = Path(__file__).resolve().parents[1] / "assets" / "saraproc-original-60s.wav"
RNG = np.random.default_rng(20261018)
MIX = np.zeros((round(DURATION * RATE), 2), dtype=np.float32)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def add(start, samples, level=1.0, pan=0.0):
    """Place a mono instrument with constant-power stereo positioning."""
    begin = round(start * RATE)
    if begin < 0:
        samples = samples[-begin:]
        begin = 0
    end = min(len(MIX), begin + len(samples))
    if begin >= end:
        return
    samples = samples[:end - begin]
    angle = (pan + 1) * math.pi / 4
    MIX[begin:end, 0] += samples * (level * math.cos(angle))
    MIX[begin:end, 1] += samples * (level * math.sin(angle))


def window(t, duration, attack, release):
    return np.minimum(1, t / attack) * np.minimum(1, (duration - t) / release)


def pad(start, notes, duration=5.8):
    t = np.arange(round(duration * RATE), dtype=np.float32) / RATE
    envelope = window(t, duration, 1.0, 1.35)
    # Sine partials with small, symmetric detuning create a soft string-like bed.
    for index, note in enumerate(notes):
        phase = RNG.uniform(0, 2 * math.pi)
        f = hz(note)
        tone = (
            np.sin(2 * math.pi * (f * 0.9985) * t + phase)
            + np.sin(2 * math.pi * (f * 1.0015) * t + phase + 0.5)
            + 0.18 * np.sin(2 * math.pi * f * 2 * t + phase)
        ) / 2.18
        add(start, tone * envelope, 0.075, [-0.6, 0.35, -0.2, 0.6][index])


def pluck(start, note, level=0.083, pan=0.0):
    duration = 2.5
    t = np.arange(round(duration * RATE), dtype=np.float32) / RATE
    f = hz(note)
    envelope = (1 - np.exp(-t * 350)) * np.exp(-t / 0.62)
    # A little phase modulation gives a rounded, glassy attack, without samples.
    voice = np.sin(2 * math.pi * f * t + 0.9 * np.exp(-t * 6) * np.sin(2 * math.pi * f * 2 * t))
    voice += 0.12 * np.sin(2 * math.pi * f * 3 * t) * np.exp(-t * 5)
    voice *= envelope * window(t, duration, 0.004, 0.15)
    add(start, voice, level, pan)
    # Two quiet reflected notes provide depth while leaving the middle clear.
    add(start + 0.3125, voice, level * 0.17, -pan * 0.7)
    add(start + 0.625, voice, level * 0.09, pan * 0.6)


def low_pulse(start, note, level=0.04):
    t = np.arange(round(0.7 * RATE), dtype=np.float32) / RATE
    f = hz(note)
    envelope = (1 - np.exp(-t * 180)) * np.exp(-t / 0.19)
    sound = np.sin(2 * math.pi * f * t) + 0.13 * np.sin(2 * math.pi * f * 2 * t)
    add(start, sound * envelope, level)


def soft_tick(start, level=0.005):
    t = np.arange(round(0.075 * RATE), dtype=np.float32) / RATE
    noise = RNG.standard_normal(len(t)).astype(np.float32)
    # A moving average removes the harshest high frequencies.
    noise = np.convolve(noise, np.ones(9, dtype=np.float32) / 9, mode="same")
    add(start, noise * np.exp(-t * 85), level, 0.35)


def main():
    # 24 bars at 96 BPM: Dmaj7, Bm7, Gmaj9, Asus2/D, repeating every 20 s.
    # Every chord lasts two bars; three complete cycles fill exactly one minute.
    chords = [
        ([50, 57, 61, 66], 38, [74, 78, 81, 78, 76, 74]),
        ([47, 54, 57, 62], 35, [74, 78, 81, 78, 74, 73]),
        ([43, 54, 57, 62], 31, [74, 78, 81, 83, 81, 78]),
        ([45, 52, 59, 62], 33, [76, 81, 83, 81, 76, 73]),
    ]
    offsets = [0, 1.5, 3, 4.5, 6, 7]
    for index in range(12):
        chord, bass, melody = chords[index % 4]
        start = index * 5.0
        pad(start, chord)
        # First five seconds are intentionally spacious for the brand reveal.
        if index > 0:
            for k, (offset, note) in enumerate(zip(offsets, melody)):
                # One breath in every phrase; smaller phrases in closing bars.
                if k == 3 or (index >= 11 and k > 2):
                    continue
                pan = -0.15 if k % 2 == 0 else 0.2
                pluck(start + offset * BEAT, note, 0.072 if k == 0 else 0.058, pan)
        if 1 <= index <= 10:
            for beat in [0, 2, 4, 6]:
                low_pulse(start + beat * BEAT, bass, 0.055 if beat == 0 else 0.038)
            for beat in [1, 3, 5, 7]:
                soft_tick(start + beat * BEAT)

    # A resolved D major closing figure; ample fade allows a smooth loop/cut.
    pluck(56.25, 78, 0.045, -0.2)
    pluck(57.0, 74, 0.055, 0.15)

    fade_in = round(0.9 * RATE)
    fade_out = round(2.5 * RATE)
    MIX[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)[:, None]
    MIX[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)[:, None]

    # Normalize for comfortable background listening and retain headroom.
    rms = float(np.sqrt(np.mean(MIX ** 2)))
    peak = float(np.max(np.abs(MIX)))
    gain = min(0.095 / max(rms, 1e-9), 0.78 / max(peak, 1e-9))
    MIX[:] *= gain
    pcm = np.round(np.clip(MIX, -1, 1) * 32767).astype("<i2")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(DEST), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    peak = float(np.max(np.abs(MIX)))
    rms = float(np.sqrt(np.mean(MIX ** 2)))
    print(f"Wrote {DEST}")
    print(f"Duration: {len(MIX) / RATE:.3f} s; stereo; {RATE} Hz; 16-bit PCM")
    print(f"Peak: {20 * math.log10(peak):.2f} dBFS; RMS: {20 * math.log10(rms):.2f} dBFS")
    print("All audio synthesized locally; seed: 20261018; tempo: 96 BPM")


if __name__ == "__main__":
    main()
