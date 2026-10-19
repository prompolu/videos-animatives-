#!/usr/bin/env python3
"""Synthesize an original, calm 40-second ambient music loop.

Run from the repository root: python tools/compose_ambient_loop.py
Requires NumPy. No third-party recordings, samples, drums or voices are used.
Every sustained note wraps across the loop boundary with a smooth envelope.
"""

from pathlib import Path
import math
import wave

import numpy as np


RATE = 48_000
DURATION = 40.0
FRAMES = round(RATE * DURATION)
DEST = Path(__file__).resolve().parents[1] / "assets" / "saraproc-ambient-loop.wav"
RNG = np.random.default_rng(20261019)


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def envelope(time, duration, attack, release):
    """Cosine ramps have zero amplitude and slope at both note boundaries."""
    rise = 0.5 - 0.5 * np.cos(np.pi * np.minimum(time / attack, 1))
    fall = 0.5 - 0.5 * np.cos(np.pi * np.minimum((duration - time) / release, 1))
    return rise * fall


def add(mix, start, voice, level, pan=0.0):
    """Place a note circularly, including its full tail at the next start."""
    begin = round(start * RATE) % FRAMES
    angle = (pan + 1) * math.pi / 4
    stereo = voice[:, None] * np.array(
        [level * math.cos(angle), level * math.sin(angle)]
    )
    first = min(len(voice), FRAMES - begin)
    mix[begin:begin + first] += stereo[:first]
    if first < len(voice):
        mix[:len(voice) - first] += stereo[first:]


def pad(mix, start, chord):
    """Soft, slow chord swells with a little stereo detuning and movement."""
    duration = 15.0
    time = np.arange(round(duration * RATE), dtype=np.float64) / RATE
    shape = envelope(time, duration, 4.0, 5.5)
    positions = [-0.66, 0.35, -0.20, 0.67, 0.12]
    for index, note in enumerate(chord):
        phase = RNG.uniform(0, 2 * math.pi)
        frequency = hz(note)
        slow_motion = 0.91 + 0.09 * np.sin(2 * np.pi * time / 11.7 + phase)
        voice = (
            np.sin(2 * np.pi * frequency * 0.9992 * time + phase)
            + np.sin(2 * np.pi * frequency * 1.0008 * time + phase + 0.3)
            + 0.07 * np.sin(2 * np.pi * frequency * 2 * time + phase)
        ) / 2.07
        add(mix, start, voice * shape * slow_motion, 0.074, positions[index])


def air_note(mix, start, note, pan):
    """A sparse, rounded upper note: gentle attack, no percussive transient."""
    duration = 8.0
    time = np.arange(round(duration * RATE), dtype=np.float64) / RATE
    shape = envelope(time, duration, 0.9, 4.5)
    frequency = hz(note)
    voice = (
        np.sin(2 * np.pi * frequency * time)
        + 0.04 * np.sin(2 * np.pi * frequency * 2 * time)
    ) / 1.04
    add(mix, start, voice * shape, 0.024, pan)
    add(mix, start + 0.47, voice * shape, 0.004, -pan)


def main():
    mix = np.zeros((FRAMES, 2), dtype=np.float64)
    # Dmaj9 -> Bm11 -> Gmaj9 -> Asus4/add9. Ten seconds per harmony;
    # long overlaps remove pauses and soften each harmonic transition.
    progression = [
        [50, 57, 61, 64, 66],
        [47, 54, 57, 62, 64],
        [43, 54, 57, 62, 66],
        [45, 52, 57, 59, 62],
    ]
    for index, chord in enumerate(progression):
        pad(mix, index * 10.0, chord)

    # A slow, unhurried melodic thread, deliberately without a beat or bass hit.
    for start, note, pan in [
        (3.0, 78, -0.25), (8.7, 76, 0.20), (14.1, 74, -0.15),
        (20.2, 78, 0.28), (25.8, 81, -0.20), (32.0, 76, 0.22),
        (37.0, 73, -0.12),
    ]:
        air_note(mix, start, note, pan)

    # Ambient background level; preserve headroom and avoid a periodic file fade.
    mix -= np.mean(mix, axis=0)
    rms = float(np.sqrt(np.mean(mix ** 2)))
    peak = float(np.max(np.abs(mix)))
    mix *= min(10 ** (-23 / 20) / rms, 10 ** (-11 / 20) / peak)
    pcm = np.round(mix * 32767).astype("<i2")
    decoded = pcm.astype(np.float64) / 32768
    peak = float(np.max(np.abs(decoded)))
    rms = float(np.sqrt(np.mean(decoded ** 2)))
    steps = np.diff(pcm.astype(np.int32), axis=0)
    seam = pcm[0].astype(np.int32) - pcm[-1].astype(np.int32)
    seam_max = int(np.max(np.abs(seam)))
    typical_step = float(np.percentile(np.abs(steps), 99.9))
    assert pcm.shape == (FRAMES, 2)
    assert peak < 0.29, "Planned peak headroom was exceeded"
    assert np.max(np.abs(decoded.mean(axis=0))) < 1e-6, "Unexpected DC offset"
    assert seam_max < typical_step, (
        f"Loop boundary step {seam_max} exceeds the typical maximum {typical_step:.0f}"
    )
    assert np.count_nonzero(np.abs(pcm.astype(np.int32)) >= 32767) == 0

    DEST.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(DEST), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    print(f"Wrote {DEST}")
    print(f"Duration: {DURATION:.3f} s; stereo; {RATE} Hz; 16-bit PCM")
    print(f"Peak: {20 * math.log10(peak):.2f} dBFS; RMS: {20 * math.log10(rms):.2f} dBFS")
    print(f"Loop seam step: {seam_max} PCM units; 99.9th-percentile step: {typical_step:.0f}")
    print("Original ambient synthesis; no drums, samples or recurring fade; seed 20261019")


if __name__ == "__main__":
    main()
