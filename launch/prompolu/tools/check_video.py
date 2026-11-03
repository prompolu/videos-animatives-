"""One frame per beat as a contact sheet + scan for single-frame pops
(frame differences that spike to 3x their neighbours).
usage: python3 tools/check_video.py <film.mp4> <beats.jpg> <report.json>"""
import json, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
src, sheet, rep = sys.argv[1:4]
B, FPS, N = 0.45, 60, 64
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', f'scale={N*3}:{N*3},format=gray', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, N * 3, N * 3).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean((1, 2))          # d[i] = |f[i+1] - f[i]|
pops = []
for i in range(1, len(d) - 1):
    nb = (d[i - 1] + d[i + 1]) / 2
    if d[i] > 3 * nb and d[i] > 1.0:
        pops.append(dict(frame=i + 1, t=round((i + 1) / FPS, 3), diff=round(float(d[i]), 2), neighbours=round(float(nb), 2)))
# one frame per beat
S = 240; cols = 9; beats = list(range(55))
im = Image.new('RGB', (cols * S, ((len(beats) + cols - 1) // cols) * S), 'white'); dr = ImageDraw.Draw(im)
for j, b in enumerate(beats):
    t = min(b * B, len(fr) / FPS - 1 / FPS)
    png = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', src, '-frames:v', '1', '-vf', f'scale={S-4}:{S-4}', '-f', 'image2pipe', '-c:v', 'png', '-'], capture_output=True, check=True).stdout
    from io import BytesIO
    x, y = (j % cols) * S, (j // cols) * S
    im.paste(Image.open(BytesIO(png)), (x, y)); dr.text((x + 5, y + 4), f'beat {b}  {t:.2f}s', fill=(230, 0, 0))
im.save(sheet, quality=85)
first, last = fr[0], fr[-1]
json.dump(dict(frames=len(fr), pops=pops, first_last_mean_abs_diff=round(float(np.abs(first - last).mean()), 3),
               max_diff=round(float(d.max()), 2), max_diff_t=round(float((np.argmax(d) + 1) / FPS), 3)), open(rep, 'w'), indent=1)
print(open(rep).read())
