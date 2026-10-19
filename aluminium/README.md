# PROMPOLU ALUMINIUM — B2B presentation film

60-second motion-design film for **PROMPOLU ALUMINIUM**, supplier of premium aluminium profiles and systems to joiners (menuisiers). Prompolu does not install: it supplies the joiners who fabricate and install. French and English versions, 1080p at 60 fps, with an original energetic soundtrack cut to the picture.

Branding comes from `assets/brand/PROMPOLU-logo-et-icone.pdf` (supplied by the client): wordmark, "P" site icon, ink `#15171A`, paper `#F1F0EC`, bronze `#8C6A45`, and prompolu.com. The transparent PNGs in `assets/brand/` were extracted from that PDF at 600 dpi. The PDF notes that its logo is a vector reconstruction of a 602 × 83 px web file; ask for the original `.ai`/`.eps`/`.svg` for print work.

## Deliverables (`output/`)

| File | Content |
| --- | --- |
| `aluminium-60s-fr-musique.mp4` / `aluminium-60s-en-musique.mp4` | 1920 × 1080, 60 fps, H.264, original music (AAC 256 kb/s). No voice-over. |
| `aluminium-60s-fr-sans-son.mp4` / `aluminium-60s-en-sans-son.mp4` | Same film without sound (showroom / trade-fair screens). |
| `storyboard-fr.jpg` / `storyboard-en.jpg` | The 16 shots at a glance. |
| `affiche-fr.jpg` / `affiche-en.jpg` | Poster still. |
| `timeline-*.json`, `validation.json` | Shot timings, transitions and the export check report. |

## Edit (120 BPM, every cut on the beat)

| Time | Shot | Motion |
| --- | --- | --- |
| 0–4 s | Hook: « Profilés. Systèmes. Haut de gamme. » | Words punch in on the beat, then the "P" icon slams in with a ring and the wordmark rises. |
| 4–10 s | L’aluminium haut de gamme | Zoom-through cut; a window profile cross-section snaps together (frame, sash, glazing) on three beats. |
| 10–16 s | Nous fournissons, vous fabriquez | Bronze wipe; Prompolu → menuisier → client final, cards pop in, arrows draw and supply dots flow. |
| 16–46 s | 10 product shots, 3 s each | Coulissant, battant, portes · mur rideau, bardage aluminium, Stacbond · cuisines, dressings, volets roulants, pergolas. Each drawing moves (sash slides, leaves open, shutter closes, louvres rotate…), with Ken Burns drift and word-by-word titles. Motion-blurred push between shots, vertical push between groups. |
| 46–52 s | 10 gammes. Un seul partenaire. | Camera pulls back from the pergola tile to reveal all ten ranges; a highlight runs across the grid. |
| 52–56 s | Menuisiers, parlons de vos projets. | Bronze wipe to a bronze screen with moving stripes and the prompolu.com button. |
| 56–60 s | Logo, tagline, prompolu.com | Zoom-through, logo slam, fade to black (loops cleanly). |

Every frame is colour graded: gentle S-curve, warm highlights and cool shadows, +10 % saturation, vignette and fine film grain. A thin bronze progress bar runs along the bottom.

All illustrations are drawn in code (`tools/art.py`); no photos or stock footage are used, so there are no image rights to clear.

## Customise

`brand.json` holds the website, optional `phone` (shown on the closing card when set), logo files, colours and every on-screen line per language (hook words, product names and subtitles, groups, calls to action). The product order is fixed by `PRODUCT_KEYS` in `tools/art.py`.

## Render

Requires Python 3, NumPy, Pillow (see `../requirements.txt`), FFmpeg with libx264/AAC and the Inter fonts (`/usr/share/fonts/opentype/inter`).

```bash
python3 aluminium/tools/compose_music.py                    # assets/aluminium-original-60s.wav
python3 aluminium/tools/render_video.py --lang fr --stills  # storyboard and review frames (~20 s)
python3 aluminium/tools/render_video.py --lang fr           # full 60 fps export (4 processes)
python3 aluminium/tools/render_video.py --lang en
python3 aluminium/tools/validate_outputs.py                 # full decode + format checks
```

If you change cut times in `render_video.py`, update `PRODUCT_CUTS`, `GROUP_CUTS` and `IMPACTS` in `compose_music.py` so the music stays in sync.
