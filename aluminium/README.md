# PROMPOLU ALUMINIUM — animated presentation film

60-second motion-design film for an aluminium joinery business (windows, doors, façades), built in the same style and with the same pipeline as the Saraproc Maroc film at the root of this repository. Two languages: French and English.

Branding comes from `assets/brand/PROMPOLU-logo-et-icone.pdf` (supplied by the client): the PROMPOLU ALUMINIUM wordmark, the "P" site icon, the colours ink `#15171A`, paper `#F1F0EC` and bronze `#8C6A45`, and the website prompolu.com. The transparent PNGs in `assets/brand/` were extracted from that PDF at 600 dpi (ink and paper versions of the wordmark, paper version of the "P"). The PDF itself notes that its logo is a vector reconstruction of a 602 × 83 px web file; ask for the original `.ai`/`.eps`/`.svg` for print work.

No phone number is shown yet: add it as `phone` in `brand.json` and re-render.

## Deliverables (`output/`)

| File | Content |
| --- | --- |
| `aluminium-60s-fr-musique.mp4` / `aluminium-60s-en-musique.mp4` | 1920 × 1080, 30 fps, H.264, original instrumental (AAC stereo). No voice-over. |
| `aluminium-60s-fr-sans-son.mp4` / `aluminium-60s-en-sans-son.mp4` | Same film, silent, loopable (for a showroom or trade-fair screen). |
| `storyboard-fr.jpg` / `storyboard-en.jpg` | Overview of the seven scenes. |
| `affiche-fr.jpg` / `affiche-en.jpg` | Poster still. |
| `timeline-*.json`, `validation.json` | Scene timings and the export check report. |

## Storyboard

| Time | Scene | Visual |
| --- | --- | --- |
| 00–07 s | **Aluminium, made to measure.** | Modern house illustration; the sliding bay window opens, clouds drift, light sweeps on the glass. |
| 07–15 s | **From measuring to installation.** | Four steps: measuring, design, fabrication, installation, with an animated progress line. |
| 15–24 s | **Windows & doors.** | Sliding window gliding open, casement window opening inward, entrance door with light reflection. |
| 24–33 s | **Façades, verandas, railings.** | Curtain wall, veranda and glass railing, each with moving reflections. |
| 33–43 s | **Why aluminium?** | Six benefits: durable, light & strong, insulating, recyclable, low upkeep, made to measure. |
| 43–51 s | **Let’s talk about your project.** | Call for a personalised quote, house illustration. |
| 51–60 s | Contact card | Logo, company name, tagline, website (and phone if set). |

All illustrations are drawn in code (`tools/render_video.py`); no photos or stock footage are used, so there are no image rights to clear. Frames use RAL 7016 anthracite-style profiles; the interface uses the Prompolu ink, paper and bronze colours.

## Customise

Everything a client would change lives in `brand.json`:

- `company`, `website` — per language; `phone` — shown on the closing card when not empty.
- `logo` — `on_light` / `on_dark` wordmark PNGs and the square `icon` (paths relative to this folder). Set it to `""` to fall back to a drawn window mark plus the company name in text.
- `colors` — accent and background colours.
- `text` — every on-screen line, per language. Statements such as fabrication, installation or quotes are generic: remove any that don’t match the business.

## Render

Requires Python 3, NumPy, Pillow (see `../requirements.txt`), FFmpeg with libx264/AAC and the Inter fonts (`/usr/share/fonts/opentype/inter`).

```bash
python3 aluminium/tools/compose_music.py            # writes assets/aluminium-original-60s.wav
python3 aluminium/tools/render_video.py --lang fr --stills   # review frames only (seconds)
python3 aluminium/tools/render_video.py --lang fr   # full export (~ a few minutes, 4 processes)
python3 aluminium/tools/render_video.py --lang en
python3 aluminium/tools/validate_outputs.py         # full decode + format checks
```
