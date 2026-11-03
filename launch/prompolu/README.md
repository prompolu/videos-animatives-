# Prompolu — launch film

Square 1440×1440, 60 fps, 24.3 s (54 beats at the supplied track's 133.33 BPM), one continuous take.
The film is [`index.html`](index.html): every style is computed from time inside `async seek(t)`.
It uses no CSS transitions, no timers and no state between frames.
The beat map is in [`creative/prompolu-launch/beat-map.md`](../../creative/prompolu-launch/beat-map.md).

Final export: [`output/prompolu-launch/prompolu-launch.mp4`](../../output/prompolu-launch/prompolu-launch.mp4).

## How it is built

- **Springs** are closed-form step responses. A value with several targets is the sum of one response per change (`A(t, v0, keys)`), so every value stays a pure function of time.
- **Liquid glass**: each glass element paints its own replica of the scene behind it.
  - Displacement: an SVG `feImage` map built from a rounded-rect distance field.
  - Chromatic edges: three `feDisplacementMap` passes at 1.00 / 1.06 / 1.12 scale, one per colour channel, recombined.
  - Rim light on top.
  - Glass letters (`light`, the clock digits) use a canvas distance field per glyph (Felzenszwalb EDT). It provides the map, the mask and the highlights.
- **Goo**: blur + alpha threshold, then the source composited atop, so the glass stays sharp inside.
- **Iris**: six blades around a hexagonal aperture. Each blade is the chord through its aperture edge (both edge extensions), closed by the short arc on its side.
- **Logo squeeze**: the official logo (prompolu.com, rebuilt at 4× by `tools/prepare_logo.py`) is an image, so it has no `wdth` axis to narrow. Every part moves toward the centre by the same factor, so the letters stay touching. In the last quarter the ink also gathers vertically into the dot, and at the end it reverses on the beat return.
- **Footage**: an all-intra VP9 clip (`-g 1`), fetched as a blob URL. Each frame awaits `seeked` before it is drawn.
- **Render**: Playwright renders 4 subframes per frame. ffmpeg `tmix` averages them, giving 60 fps.

## Inputs and stand-ins

| Input | Source |
| --- | --- |
| Photos | the 5 supplied images, upscaled 4× with EDSR (OpenCV dnn_superres), then cropped into 9 tiles, the hero and the album art |
| Golden-hour shot | a regrade of the day shot (`tools/prepare_photos.py`), so the two frames align exactly |
| Wall footage | generated procedurally (`tools/make_wall.py`): a plaster wall with swaying leaf shadows. Pexels was not reachable from the build machine. Drop a real clip in as `assets/video/wall-src.mp4` and re-run the VP9 step. |
| Song | `lnplusmusic — Product Launch` (Pixabay 611921, supplied). Not committed; cut on bar lines by `tools/build_audio.py`. |
| SFX | 41 Mixkit sound effects (`assets/sfx/<id>.mp3`), one per event, aligned by measured peak |
| Logo | `assets/brand/logo-prompolu-original.png`, downloaded from https://prompolu.com/assets/logo-prompolu.png, upscaled 4× to `prompolu-logo@4x.png` |
| Fonts | Archivo (OFL), Geist (OFL) |

## Rebuild

```bash
python3 tools/prepare_logo.py
python3 tools/prepare_photos.py                        # needs assets/photos/src/p1..p5.png (EDSR x4)
python3 tools/make_wall.py assets/video/wall-src.mp4
ffmpeg -i assets/video/wall-src.mp4 -t 4 -c:v libvpx-vp9 -g 1 -keyint_min 1 -crf 28 -b:v 0 -row-mt 1 -an assets/video/wall.webm
python3 -m http.server 8765 --bind 127.0.0.1            # from the repository root
NODE_PATH=$(npm root -g) node tools/render.cjs 0 486 r/s0.mp4    # and 486 972, 972 1458 in parallel
python3 tools/build_audio.py <song.mp3> r/mix.wav
sh tools/mux.sh r r/mix.wav ../../output/prompolu-launch/prompolu-launch.mp4
python3 tools/check_video.py ../../output/prompolu-launch/prompolu-launch.mp4 beats.jpg check.json
```

The Chromium bundled with Playwright has no H.264 decoder, so the footage is VP9/WebM.
