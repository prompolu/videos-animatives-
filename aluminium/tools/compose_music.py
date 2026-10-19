#!/usr/bin/env python3
"""Original 60-second energetic electronic cue for the Prompolu film, synced to its cuts.

120 BPM (one beat = 0.5 s, one bar = 2 s). Kick, clap, hats, pumping bass, arpeggio,
lead hook, pads, risers, whooshes and impacts are all synthesized with NumPy:
no samples, loops or recordings. Run: python3 aluminium/tools/compose_music.py
"""
from pathlib import Path
import math
import wave

import numpy as np

RATE = 48_000
DURATION = 60.0
BEAT = 0.5
DEST = Path(__file__).resolve().parents[1] / "assets" / "aluminium-original-60s.wav"
RNG = np.random.default_rng(20261019)
N = round(DURATION * RATE)
BUS = {name: np.zeros((N, 2), np.float32) for name in ("drums", "bass", "music", "fx", "send")}

# Scene cuts in the film (seconds); keep in sync with render_video.py.
PRODUCT_CUTS = [16 + 3*i for i in range(1, 10)]
GROUP_CUTS = [25, 34]
IMPACTS = [4, 16, 46, 52, 56]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def tline(duration):
    return np.arange(round(duration * RATE), dtype=np.float32) / RATE


def add(bus, start, samples, level=1.0, pan=0.0, send=0.0):
    begin = round(start * RATE)
    if begin < 0:
        samples, begin = samples[-begin:], 0
    end = min(N, begin + len(samples))
    if begin >= end:
        return
    s = samples[:end - begin] * level
    if np.ndim(pan) == 0:
        angle = (pan + 1) * math.pi / 4
        left, right = s * math.cos(angle), s * math.sin(angle)
    else:
        angle = (np.asarray(pan[:end - begin]) + 1) * math.pi / 4
        left, right = s * np.cos(angle), s * np.sin(angle)
    BUS[bus][begin:end, 0] += left
    BUS[bus][begin:end, 1] += right
    if send:
        BUS["send"][begin:end, 0] += left * send
        BUS["send"][begin:end, 1] += right * send


def band_noise(duration, lo, hi):
    """White noise shaped in the frequency domain (no filter library needed)."""
    n = round(duration * RATE)
    spec = np.fft.rfft(RNG.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / RATE) + 1e-3
    spec *= 1 / np.sqrt(1 + (lo / f) ** 4) / np.sqrt(1 + (f / hi) ** 4)
    out = np.fft.irfft(spec, n).astype(np.float32)
    return out / (np.max(np.abs(out)) + 1e-9)


def saw(freq, t, harmonics=10, bright=1.0):
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        out += np.sin(2 * math.pi * freq * k * t) / k * np.exp(-k * (1.2 - bright) * 0.25)
    return out


# ----------------------------------------------------------------- drums

def kick(start, level=0.95):
    t = tline(0.45)
    f = 44 + 120 * np.exp(-t * 30)
    body = np.sin(2 * math.pi * np.cumsum(f) / RATE) * np.exp(-t * 7.5)
    click = band_noise(0.45, 1500, 8000) * np.exp(-t * 400)
    add("drums", start, body + 0.25 * click, level)


def clap(start, level=0.42):
    t = tline(0.35)
    noise = band_noise(0.35, 900, 7000)
    env = np.zeros_like(t)
    for offset in (0, 0.011, 0.023):
        shifted = np.clip(t - offset, 0, None)
        env += (t >= offset) * np.exp(-shifted * 55)
    env += (t >= 0.023) * 0.6 * np.exp(-np.clip(t - 0.023, 0, None) * 13)
    add("drums", start, noise * env, level, 0.05, send=0.35)


def hat(start, level=0.11, open_=False, pan=0.25):
    duration = 0.28 if open_ else 0.06
    t = tline(duration)
    add("drums", start, band_noise(duration, 7000, 17000) * np.exp(-t * (14 if open_ else 85)), level, pan)


def crash(start, level=0.22):
    t = tline(2.4)
    add("drums", start, band_noise(2.4, 3500, 16000) * np.exp(-t * 1.8), level, 0, send=0.3)


# --------------------------------------------------------- tonal parts

def bass(start, note, duration, level=0.30):
    t = tline(duration)
    env = np.minimum(1, t / 0.005) * np.minimum(1, (duration - t) / 0.03)
    tone = saw(hz(note), t, 8, 0.6) + 0.6 * np.sin(2 * math.pi * hz(note) * t)
    add("bass", start, tone * env, level)


def pluck(start, note, level=0.10, pan=0.0, decay=6.0, send=0.25, bus="music"):
    duration = 0.6
    t = tline(duration)
    f = hz(note)
    tone = np.zeros_like(t)
    for k in range(1, 11):
        tone += np.sin(2 * math.pi * f * k * t) / k * np.exp(-t * (decay + k * 2.5))
    tone *= np.minimum(1, t / 0.003) * np.minimum(1, (duration - t) / 0.05)
    add(bus, start, tone, level, pan, send)


def pad(start, notes, duration, level=0.045, bright=0.5):
    t = tline(duration)
    env = np.minimum(1, t / 0.25) * np.minimum(1, (duration - t) / 0.4)
    for i, note in enumerate(notes):
        for detune in (-0.12, 0.0, 0.12):
            voice = saw(hz(note + detune), t, 6, bright)
            add("music", start, voice * env, level / 3, [-0.5, 0.5, -0.2, 0.3][i % 4], send=0.3)


# ------------------------------------------------------------------- fx

def riser(start, duration, level=0.20):
    t = tline(duration)
    x = t / duration
    noise = band_noise(duration, 1500, 12000) * x ** 2.2
    f = 220 * (1 + 4 * x ** 2)
    tone = np.sin(2 * math.pi * np.cumsum(f) / RATE) * 0.35 * x ** 2
    add("fx", start, noise + tone, level, 0, send=0.4)


def whoosh(start, duration=0.45, level=0.30, direction=1):
    t = tline(duration)
    x = t / duration
    env = np.sin(math.pi * x) ** 2
    pan = direction * (x * 1.6 - 0.8)
    add("fx", start, band_noise(duration, 500, 6000) * env, level, pan, send=0.25)


def impact(start, level=0.75):
    t = tline(2.6)
    f = 38 + 50 * np.exp(-t * 6)
    boom = np.sin(2 * math.pi * np.cumsum(f) / RATE) * np.exp(-t * 2.0)
    hit = band_noise(2.6, 80, 5000) * np.exp(-t * 9)
    add("fx", start, boom + 0.35 * hit, level, 0, send=0.45)
    crash(start, 0.16)


def reverse_swell(end, duration=1.0, level=0.18):
    t = tline(duration)
    add("fx", end - duration, band_noise(duration, 2500, 15000) * (t / duration) ** 3, level, 0)


# --------------------------------------------------------- arrangement

# Am – F – C – G, one chord per bar.
CHORDS = [
    (45, [57, 60, 64, 67], [76, None, 72, 74, 76, None, 79, 76]),
    (41, [53, 57, 60, 64], [77, None, 76, 72, 74, None, 72, 69]),
    (48, [55, 60, 64, 67], [76, None, 72, 74, 79, None, 76, 74]),
    (43, [55, 59, 62, 67], [74, None, 71, 74, 79, 78, 79, None]),
]


def bar_parts(bar, kick_on=True, hats16=False, lead=False, arp=True, bass_on=True, clap_on=True):
    start = bar * 2.0
    root, chord, melody = CHORDS[bar % 4]
    pad(start, chord, 2.0)
    for b in range(4):
        beat = start + b * BEAT
        if kick_on:
            kick(beat)
        if clap_on and b in (1, 3):
            clap(beat)
        hat(beat + BEAT / 2, 0.12, open_=(b == 3 and bar % 2 == 1), pan=0.3)
        if hats16:
            hat(beat + BEAT / 4, 0.06, pan=-0.3)
            hat(beat + 3 * BEAT / 4, 0.06, pan=-0.3)
    if bass_on:
        for e in range(8):
            bass(start + e * BEAT / 2, root + (12 if e % 2 else 0), BEAT / 2 - 0.02, 0.30 if e % 2 else 0.36)
    if arp:
        order = [0, 1, 2, 3, 2, 1, 2, 3]
        for s in range(16):
            pluck(start + s * BEAT / 4, chord[order[s % 8]] + 12, 0.055, -0.4 if s % 2 else 0.4, 11, 0.2)
    if lead:
        for e, note in enumerate(melody):
            if note is not None:
                pluck(start + e * BEAT, note, 0.15, 0.0, 4.5, 0.3)


def main():
    # Hook (0–4 s): hits on each title word, logo slam at 3 s, riser into the drop.
    for bar in (0, 1):
        root, chord, _ = CHORDS[bar % 4]
        pad(bar * 2.0, chord, 2.0, 0.05, 0.3)
        for s in range(16 if bar else 8):
            step = BEAT / 4 if bar else BEAT / 2
            pluck(bar * 2.0 + s * step, chord[s % 4] + 12, 0.04, -0.3 if s % 2 else 0.3, 12, 0.3)
    for hit in (0.05, 1.0, 2.0):
        kick(hit, 0.8)
        clap(hit, 0.30)
    impact(3.0, 0.55)
    riser(3.0, 1.0, 0.16)
    reverse_swell(4.0, 0.9)
    for s in range(8):
        clap(3.0 + s * BEAT / 8 * 2, 0.08 + s * 0.02)

    # Profile + "we supply, you build" (4–16 s): groove A.
    for bar in range(2, 8):
        bar_parts(bar, hats16=bar >= 5)
    whoosh(9.75, 0.5, 0.32)

    # Ten product shots (16–46 s): groove B with the lead hook, a whoosh on every cut.
    for bar in range(8, 23):
        bar_parts(bar, hats16=True, lead=True)
    for cut in [16] + PRODUCT_CUTS:
        whoosh(cut - 0.25, 0.45, 0.34 if cut not in GROUP_CUTS else 0.42, -1 if cut in GROUP_CUTS else 1)
    for cut in GROUP_CUTS:
        crash(cut, 0.14)
    riser(44.0, 2.0, 0.20)
    reverse_swell(46.0, 1.0)

    # Recap (46–52 s): one airy bar, then the beat returns and builds.
    pad(46.0, CHORDS[3][1], 2.0, 0.06, 0.4)
    for s in range(16):
        pluck(46.0 + s * BEAT / 4, CHORDS[3][1][s % 4] + 12, 0.05, -0.3 if s % 2 else 0.3, 9, 0.35)
    for bar in (24, 25):
        bar_parts(bar, hats16=bar == 25, lead=False)
    riser(50.5, 1.5, 0.18)
    for s in range(8):
        clap(51.0 + s * BEAT / 4, 0.06 + s * 0.025)

    # Call to action (52–56 s): full drop.
    for bar in (26, 27):
        bar_parts(bar, hats16=True, lead=True)
    whoosh(55.75, 0.5, 0.30)

    # End card (56–60 s): logo hit, then the final chord rings out.
    root, chord, _ = CHORDS[0]
    pad(56.0, chord + [72], 4.0, 0.06, 0.5)
    bass(56.0, root, 1.5, 0.32)
    for i, note in enumerate([76, 72, 69, 64]):
        pluck(56.0 + i * BEAT, note + 12, 0.07, -0.3 + 0.2 * i, 5, 0.5)
    for cut in IMPACTS:
        impact(cut, 0.7 if cut in (4, 46, 56) else 0.5)

    # Sidechain pump: bass and music duck under every kick.
    duck = np.ones(N, np.float32)
    kicks = [0.05, 1.0, 2.0] + [bar * 2.0 + b * BEAT for bar in list(range(2, 23)) + [24, 25, 26, 27] for b in range(4)]
    t = np.arange(N, dtype=np.float32) / RATE
    for k in kicks:
        i0 = round(k * RATE)
        i1 = min(N, i0 + round(0.4 * RATE))
        duck[i0:i1] = np.minimum(duck[i0:i1], 1 - 0.6 * np.exp(-(t[i0:i1] - k) / 0.11))

    # Reverb: convolution with a decaying stereo noise tail (FFT).
    ir_len = round(1.6 * RATE)
    tail = np.exp(-np.arange(ir_len) / (0.35 * RATE)).astype(np.float32)
    size = 1 << int(math.ceil(math.log2(N + ir_len)))
    wet = np.zeros_like(BUS["send"])
    for ch in range(2):
        ir = RNG.standard_normal(ir_len).astype(np.float32) * tail
        ir = np.convolve(ir, np.ones(6) / 6, mode="same")
        wet[:, ch] = np.fft.irfft(np.fft.rfft(BUS["send"][:, ch], size) * np.fft.rfft(ir, size), size)[:N]
    wet *= 0.10 / (np.sqrt(np.mean(wet ** 2)) + 1e-9) * np.sqrt(np.mean(BUS["send"] ** 2))

    mix = BUS["drums"] + (BUS["bass"] + BUS["music"]) * duck[:, None] + BUS["fx"] + wet
    fade_in, fade_out = round(0.02 * RATE), round(1.8 * RATE)
    mix[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)[:, None]
    mix[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)[:, None] ** 1.5

    # Gentle bus compression via soft clipping, then peak normalisation to -1 dBFS.
    mix /= np.percentile(np.abs(mix), 99.99) + 1e-9
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
    pcm = np.round(np.clip(mix, -1, 1) * 32767).astype("<i2")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(DEST), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())
    rms = float(np.sqrt(np.mean(mix ** 2)))
    print(f"Wrote {DEST}")
    print(f"Duration: {N / RATE:.3f} s; stereo; {RATE} Hz; 16-bit PCM; 120 BPM")
    print(f"Peak: -1.00 dBFS; RMS: {20 * math.log10(rms):.2f} dBFS")


if __name__ == "__main__":
    main()
