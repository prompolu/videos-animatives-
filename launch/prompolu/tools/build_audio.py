"""Song edit on bar lines + one downloaded Mixkit SFX per event, each placed
by its measured peak, then two-pass loudnorm to -14 LUFS / -1 dBTP.
usage: python3 tools/build_audio.py <song.mp3> <out.wav>"""
import json, subprocess, sys
import numpy as np

SR, DUR = 48000, 54 * 0.45
SONG_BEAT0, BEAT = 0.465, 0.45          # measured grid of the supplied track
def sb(k): return SONG_BEAT0 + BEAT * k

def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

song = decode(sys.argv[1])
# (film beat, song beat, beats) — cut on bar lines
EDIT = [(0, 154, 44), (44, 70, 4), (48, 78, 6)]
n = int(round(DUR * SR))
mix = np.zeros((n + SR, 2), np.float32)
XF = int(0.01 * SR)
for fb, sbk, nb in EDIT:
    a = int(round(sb(sbk) * SR)); L = int(round(nb * BEAT * SR)) + XF
    chunk = song[a:a + L].copy()
    o = int(round(fb * BEAT * SR))
    ramp = np.linspace(0, 1, XF, dtype=np.float32)[:, None]
    if fb: chunk[:XF] *= ramp
    chunk[-XF:] *= ramp[::-1]
    mix[o:o + len(chunk)] += chunk

CUES = [  # (time s, mixkit id, gain dB, max length s)
    (0.45, 1490, -9, 1), (0.95, 2608, -7, 1), (1.35, 2358, -5, 1), (1.80, 2570, -12, 1),
    (2.25, 1109, -5, 1), (2.70, 1439, -5, 1), (3.15, 1430, -4, 1), (3.60, 2577, -12, 1), (4.05, 166, -11, 1),
    (4.50, 1530, -7, 1), (4.95, 2380, -7, 1), (5.40, 3120, -7, 1), (6.30, 2997, -5, 1), (7.20, 790, -8, 3),
    (7.20, 1143, -4, 3),
    *[(7.65 + i * 0.1125, (2925, 3192)[i % 2], -10, .6) for i in range(5)],
    (8.10, 3000, -5, 1), (8.55, 1531, -10, 1.2), *[(8.72 + i * .05, 2533, -17, .3) for i in range(5)],
    (9.00, 1109, -5, 1), (9.45, 3115, -9, 1), (9.90, 2585, -7, 1),
    *[(10.35 + i * .05, 2533, -18, .25) for i in range(10)],
    (11.25, 2621, -8, 1.2), (11.70, 2357, -7, 1), (12.15, 2619, -7, 1), *[(12.22 + i * .06, 2570, -16, .5) for i in range(4)],
    (12.60, 3097, -10, 1.5), (13.05, 1489, -8, 2), (13.50, 1531, -10, 1.2), (13.95, 1491, -7, 1), (14.40, 2364, -7, 1),
    (14.85, 1092, -8, 1), (15.30, 2585, -7, 1), (15.75, 1530, -7, 1), (15.95, 1104, -8, 1), (16.20, 2364, -7, 1),
    (16.65, 2383, -8, 1), (17.10, 2182, -9, 1), (17.55, 1109, -5, 1), (17.62, 2998, -10, .8), (18.00, 1109, -5, 1),
    (18.45, 1109, -5, 1), (18.50, 1490, -10, 1), (18.90, 2997, -5, 1), (19.00, 2867, -8, 1.5),
    (19.40, 2535, -12, .45), (19.95, 1538, -11, 1.2), (20.30, 2870, -7, 1.5), (20.70, 1486, -7, 2.5),
    (21.60, 1461, -7, 1), (22.05, 1433, -5, 1), (22.48, 1439, -5, 1), (22.70, 1490, -7, 1), (22.98, 2608, -7, 1),
    (23.40, 2902, -4, 3),
]
placed = []
for t, sid, g, mx in CUES:
    x = decode(f'assets/sfx/{sid}.mp3')
    x = x[:int(mx * SR)]
    f = int(0.02 * SR); x[-f:] *= np.linspace(1, 0, f, dtype=np.float32)[:, None]
    env = np.convolve(np.abs(x).max(1), np.ones(int(.005 * SR)) / (.005 * SR), 'same')
    pk = int(np.argmax(env))
    o = int(round(t * SR)) - pk
    s0 = max(0, -o); o = max(0, o)
    seg = x[s0:] * (10 ** (g / 20))
    e = min(len(mix), o + len(seg))
    mix[o:e] += seg[:e - o]
    placed.append(dict(t=t, id=sid, peak_s=round(pk / SR, 4), gain_db=g))
mix = mix[:n]
f = int(0.03 * SR); mix[-f:] *= np.linspace(1, 0, f, dtype=np.float32)[:, None]
tmp = sys.argv[2] + '.raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', tmp], input=mix.astype(np.float32).tobytes(), check=True)
# two-pass loudnorm
m = subprocess.run(['ffmpeg', '-hide_banner', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
J = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
af = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={J['input_i']}:measured_TP={J['input_tp']}:measured_LRA={J['input_lra']}"
      f":measured_thresh={J['input_thresh']}:offset={J['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', af, '-ar', str(SR), sys.argv[2]], check=True)
json.dump(dict(edit=EDIT, cues=placed), open(sys.argv[2] + '.cues.json', 'w'), indent=1)
