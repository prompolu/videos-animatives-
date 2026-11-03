# Euromed University of Fes — launch film

Square 1440×1440, 60 fps, 24.3 s (54 beats at 133.33 BPM), one continuous take, in UEMF colours.
It is built on the Prompolu engine ([`../prompolu/README.md`](../prompolu/README.md)): `index.html` computes every style from time inside `async seek(t)`.
The approved storyboard is [`creative/uemf-launch/storyboard.png`](../../creative/uemf-launch/storyboard.png).

Final export: [`output/uemf-launch/uemf-launch.mp4`](../../output/uemf-launch/uemf-launch.mp4).

## Brand

| | |
| --- | --- |
| Navy (site UI) | `#003882` |
| Logo blue | `#005696` |
| Leaf green | `#53BC46` |
| Background | `#F4F7FB` |
| Logo | the trilingual UEMF lockup from ueuromed.org, split into the two-leaf mark (`uemf-leaves.png`) and the rest (`uemf-rest.png`) |

The opening squeezes the lockup into its leaves. The leaves become the navy dot, the dot becomes the "Rentrée 2027/2028" pill, and at the end it all runs back on the beat return.

## Story

1. Logo → pill → iris → campus.
2. Campus grid → bento → zoom onto the campus on the drop.
3. Glass word "Fès" → toolbar → day/golden-hour slider.
4. Orb → lock screen with the graduation photo and the "Candidatures 2027/2028" widget.
5. Phone → Mac → ueuromed.org: "Construis ta carrière professionnelle à l'Euromed".
6. **Choisis ta filière**: the three poles. Ingénierie & Architecture unfolds its three schools, and École d'Ingénierie Digitale et d'IA is picked. Santé and SHS & management list theirs.
7. "Candidater" flies into "Candidater en ligne". One navy shape then runs: Candidature envoyée ✓ → Admis·e · année n/5 → Licence → Master → Ingénieur → Diplômé·e.
8. Navy flood → the graduates, framed on the wall → iris → flood → pill → leaves → logo.

The photos come from ueuromed.org. The schools are listed as on its "Nos établissements" page. The music, sound effects and the wall clip are the same as in the Prompolu film. The "30 juin" deadline is a placeholder.

## Rebuild

```bash
python3 -m http.server 8765 --bind 127.0.0.1            # from the repository root
NODE_PATH=$(npm root -g) node tools/render.cjs 0 486 r/s0.mp4    # and 486 972, 972 1458 in parallel
python3 tools/build_audio.py <song.mp3> r/mix.wav       # same cue sheet as the Prompolu film
sh tools/mux.sh r r/mix.wav ../../output/uemf-launch/uemf-launch.mp4
python3 tools/check_video.py ../../output/uemf-launch/uemf-launch.mp4 beats.jpg check.json
```
