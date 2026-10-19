# Saraproc Maroc — original catalogue music loop

- File: `saraproc-catalogue-loop-20s.wav`, exactly **20.000 seconds**, stereo, **48 kHz**, **16-bit PCM**, 3,840,044 bytes.
- Original instrumental composition and mathematical synthesis by `tools/compose_catalogue_loop.py`. Uses Python, NumPy and the standard library; no downloaded recordings, samples, voices, loops or sound libraries.
- Calm corporate mood: warm sustained pads, soft glassy plucks and understated bass pulses. Tempo: **96 BPM**, eight bars; Dmaj7 → Bm7 → Gmaj9 → Asus2 progression.
- Every note tail wraps into the next loop cycle. The file has **no global fade-in or fade-out**, so a long video can repeat it without fading every 20 seconds. Apply fades only to the start and end of the complete video.
- Deterministic generation, seed `20261018`. The existing 60-second composition and its source are preserved.

Reproduce from the repository root:

```sh
python tools/compose_catalogue_loop.py
```

Validation of the saved PCM file:

- 960,000 stereo frames / 48,000 Hz = **20.000 seconds**.
- Peak: **−9.03 dBFS**; RMS: **−21.01 dBFS**; zero clipped samples.
- Maximum first-to-last sample difference across the loop seam: **2 PCM units**, or 0.000061 full-scale. The nearby waveform has no seam spike, and the circular event tails preserve continuity.
- FFprobe identifies PCM signed 16-bit little-endian audio, 48 kHz, two channels.

Check file format with:

```sh
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,bits_per_sample,duration -of json assets/saraproc-catalogue-loop-20s.wav
```

For example, mux this loop beneath a **300-second** silent video, with one opening fade and one ending fade:

```sh
ffmpeg -i output/catalogue-sans-son.mp4 \
  -stream_loop -1 -i assets/saraproc-catalogue-loop-20s.wav \
  -map 0:v:0 -map 1:a:0 -t 300 \
  -c:v copy -c:a aac -b:a 192k \
  -af 'afade=t=in:st=0:d=0.9,afade=t=out:st=297.5:d=2.5' \
  -movflags +faststart output/catalogue-musique.mp4
```

Use the actual video duration for `-t`, and set the final fade start to that duration minus 2.5 seconds. No full-duration WAV is necessary. Lower music volume further if a voice-over is added later.
