# Saraproc Maroc — original instrumental cue

- File: `saraproc-original-60s.wav` — exactly 60.000 seconds, stereo, 48 kHz, 16-bit PCM.
- Created for this project by `tools/compose_music.py`, using NumPy and the Python standard library.
- All pads, plucks, bass pulses, and soft noise percussion are synthesized mathematically. No third-party recordings, music, loops, samples, or network assets are used.
- Mood: calm, clean, positive corporate instrumental, with an understated 96 BPM pulse. No voice or speech. Fade-in: 0.9 seconds; fade-out: 2.5 seconds.
- Reproduce with `python tools/compose_music.py` (requires NumPy). Random seed is fixed at `20261018`.
- The file is prepared for the 60-second Saraproc exhibition/presentation video. Reduce gain beneath any future voice-over.
- Validation: FFprobe confirms 60.000 seconds, 48 kHz stereo PCM; peak is approximately -7.73 dBFS and RMS is -20.45 dBFS, with no clipping.
