# Prompt: launch film for a new brand (for Codex)

Paste everything below the line into Codex. Fill in the `{{…}}` fields first.
If Codex has this repository, keep the "Start from" line: it reuses the engine in `launch/uemf/`. If not, delete that line, and Codex will build the engine from the spec.

---

You are building a square brand launch film as code, then rendering it to MP4.

## Brand

- Name: {{BRAND NAME}}. Website: {{https://…}}.
- Logo: download the official logo from the website and keep its original colours and proportions. If it is small, rebuild it at 4×: upsample the alpha, blur away the stair-steps, then re-sharpen with a smoothstep around 50 % coverage.
- Brand colours: read them from the site's CSS and logo pixels. Report the hex codes you used.
- Photos: {{use the images I attached | download photos from the website}}. You need 9 to 12 good ones.
- Story: {{e.g. "a university: choose a filière, apply, graduate" or "a shop: pick a product, order, delivery"}}. Use only real names, products, programmes or schools taken from the website. Do not invent prices, dates or claims; if a placeholder is unavoidable, list it.
- Language of on-screen text: {{French | English | …}}.
- Music: {{path to a royalty-free track | "pick a Mixkit track around 120 BPM with a drop and a quiet breakdown"}}.
- Wall footage: {{path to a clip of a plain wall with moving plant shadows | "generate one procedurally"}}.

Start from: `launch/uemf/index.html` and `launch/uemf/tools/` in this repo (the same engine, a different brand).

## Step 1 — storyboard first, then stop

Before writing the film, deliver:

1. A beat map: 54 beats at the track's measured tempo, with one event per beat, its time, the cursor or camera action and the sound effect.
2. A storyboard image: 12 panels in the brand colours, using the real logo and photos, each panel with its beat range and a short description.

Then wait for my approval.

## Motion rules

- An Apple-keynote style launch film. 2D only, one continuous take, square 1440×1440, 60 fps.
- Every scene is made out of the previous one. Nothing fades, blurs or cuts.
- Objects change shape instead:
  - text rises out of a mask line;
  - icons pop from zero on a spring;
  - bars draw across;
  - pages push;
  - a brand-colour shape floods the whole frame and contracts into the next scene.
- A cursor drives every change with real clicks, drags and long-presses.
- The camera zooms screen-studio style so each moment fills the square, and the cursor scales with it.
- Banned: crossfades, blur-ins, brightness "developing", 3D flips, particles, glows, holds longer than 1 s, anything that looks like a template.

## Sequence (adapt the content to the brand, keep the mechanics)

1. **Open.**
   - The logo squeezes like an accordion into a dot or into its own mark. Every part moves toward it by the same factor, so the letters stay touching.
   - The dot grows into a pill, and a label rises inside it.
   - Click: six iris blades close over the label and snap open onto a photo.
   - The circle becomes a square, shrinks, and a 3×3 grid unfolds from behind it like a paper map: centre, then plus, then corners.
   - The grid reflows into a bento, and a click zooms into one tile, landing exactly on the music drop.
2. **Glass.**
   - A word made of liquid glass pops in letter by letter, melts into a droplet, and the droplet stretches into a glass toolbar.
   - The adjust icon turns the toolbar into a slider. Dragging relights the photo from day to golden hour, using two aligned shots or a regrade of one. The knob becomes a glass lens while held.
   - The lens lifts into a glass orb. The next photo opens inside it as a circle, and the orb expands into a lock screen: glass clock digits, a date, and a home bar that stretches into a glass widget.
3. **Stage.**
   - The lock screen pulls back into a phone, with the bezel growing out of the screen edge.
   - The Dynamic Island stretches like liquid, pinches off, flies over and grows into a Mac window that rolls up like a blind.
   - Long-press the wallpaper, drag it onto a Safari tab showing the brand's real domain. The page pushes in, and dropping the photo makes it the hero.
   - Scroll: the hero morphs into the brand's main choice (products, programmes, services…). A click selects one, and its real options unfold as chips; a second click picks one option.
   - The nav button flies down into the call to action.
4. **One shape.** A single brand-colour shape keeps morphing through the journey ({{e.g. Applied ✓ → Admitted → path → Graduated}}).
5. **Wall.**
   - The last shape floods the frame edge to edge, holds for one beat, and contracts into a framed photo hanging on the wall footage.
   - The same iris opens onto the photo and closes again. The frame floods the screen and contracts back through pill → dot → logo, landing on the beat return.
   - The last frame equals the first.

## Technical rules (these are hard requirements)

1. **One HTML file.** Every style is computed from time inside `async seek(t)`. No CSS transitions, no timers, no state between frames.
2. **Springs** are closed-form damped step responses. A value with many targets is the sum of one response per change, so it stays a pure function of time.
3. **Liquid glass.**
   - Each glass element holds its own replica of the scene behind it. Do not use `backdrop-filter: url()`: Chromium misreads displacement maps.
   - Filter the replica through an SVG `feImage` displacement map built from a rounded-rect distance field.
   - Use three `feDisplacementMap` passes at 1.00 / 1.06 / 1.12 scale, one per colour channel and recombined, for chromatic edges, plus a rim light.
   - Set `color-interpolation-filters="sRGB"` on every filter.
   - Glass letters: a canvas distance field per glyph (Felzenszwalb EDT) gives the map, the mask and the highlights.
4. **Goo:** blur plus an alpha threshold, then composite the source atop so the glass stays sharp inside.
5. **Iris:** 6 blades around a hexagonal aperture. Each blade is the chord through its aperture edge (both edge extensions), closed by the short arc on its side. Fade the seam lines with the aperture so a closed iris is one flat shape, and make the blades exactly the colour of the shape they close into.
6. **Footage:**
   - Re-encode it all-intra (`-g 1`) as **VP9/WebM**: the Chromium bundled with Playwright has no H.264 decoder.
   - Load it with `fetch` → blob URL (python `http.server` cannot range-seek).
   - Await `seeked` before drawing each frame.
7. **Sound:**
   - A downloaded SFX for every event (Mixkit), never synthesized, each placed by its measured peak.
   - Measure the song's real tempo and grid first. Cut it on bar lines so the zoom lands on the drop, the wall sits in the breakdown and the logo returns with the beat.
   - Two-pass loudnorm to −14 LUFS / −1 dBTP.
8. **Render:**
   - Playwright, 4 subframes per frame blended with ffmpeg `tmix` → 60 fps.
   - Split the frame range across parallel browser workers and concatenate.
9. **Checks before delivering:**
   - one frame per beat as a contact sheet;
   - a scan for single-frame pops (frame differences that spike to 3× their neighbours);
   - first frame vs last frame;
   - loudness.
   Fix every pop and re-render the affected segment.

## Pitfalls already learned

- A flood or contraction must start just past the frame edge, overscale past the corners, and take about 0.3–0.4 s. Otherwise half the screen changes in one frame.
- A child with `visibility: visible` shows through a hidden parent. Toggle with `inherit` / `hidden` only.
- Text that swaps inside a morphing shape needs its own mask box placed where the text sits.
- Never swap one element for another unless both render identical pixels at that instant: same colour, same radius, same shadow.
- Images inside the world layer need `position: absolute`, or they fall into the normal flow and vanish off-frame.
- Keep labels inside their pills: measure the longest label and size the shape to it.

## Deliverables

- `index.html` (the film).
- `tools/` with the render, audio, check and mux scripts.
- The storyboard PNG.
- The final `…-launch.mp4`.
- The contact sheet and the check report.
- A README listing every source, every stand-in and every placeholder.
- Commit and push everything.
