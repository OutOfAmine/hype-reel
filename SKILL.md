---
name: hype-reel
description: Turns any product (a URL, a local app, or a repo you can run) into an insane vertical promo reel built from its REAL screens — 3D device fly-ins with a camera that dives onto each feature, exploded UI layers, a corridor of screens the camera flies through, a giant word filled with the product that you dive into, orbiting feature chips, before/after glitch wipes, counters that burst into particles, AI-prompt typing that spits out the product — all Framer Motion, word-by-word captions, rendered frame-exact to a 1080x1920 MP4 and published as a shareable page. Use it whenever the user says /hype-reel, "make a reel/promo/trailer/ad for my product/site/app/SaaS", "launch video", "TikTok/Reel/Short for my startup", "make my landing page into a video", "product demo video", "hype video", or wants something viral to post about a product — even if they don't say "reel".
---

# hype-reel

Make a 20-40 second vertical reel that sells one product. It is built from the product's **real screens** (captured with headless Chrome), staged with aggressive motion, and plays as a storyboard (`reel.json`) in a bundled React + Framer Motion player. Every frame is a pure function of time, so the same page plays live in a browser and renders to an exact MP4.

`SKILL_DIR` below is this skill's folder. First run in a new copy: `cd SKILL_DIR && npm install` (puppeteer-core + ffmpeg-static; uses the Chrome/Edge already on the machine, or `CHROME_PATH`).

## 1. Find the product

Use what the user gave you: a URL, a local folder (serve it: `python -m http.server 8790` in that folder, in the background), or a repo with a dev server. Ask only if there is nothing to go on. Read its landing page / README so you know what it actually does.

## 2. Capture real screens

```bash
node SKILL_DIR/scripts/capture.mjs <url> <dir>/shots --name home --rects "h1,.hero a,#pricing"
node SKILL_DIR/scripts/capture.mjs <url> <dir>/shots --mobile --name home-m
node SKILL_DIR/scripts/capture.mjs <url> <dir>/shots --mobile --name m1 --scroll 1000
node SKILL_DIR/scripts/capture.mjs <url> <dir>/shots --full --name page      # tall page; slice it into sections for wall/tunnel
node SKILL_DIR/scripts/capture.mjs <url> <dir>/shots --name app --click "#start,.next" --js "await new Promise(r=>setTimeout(r,800))"
```

`--rects` prints each selector's box as fractions of the screenshot: paste them into a `screen` scene's `focus`. Otherwise read the screenshot and estimate fractions yourself (x, y, w, h, all 0-1). Use `--dark` for dark-mode sites, `--click`/`--js` to walk an app into the state worth showing. Capture 6-10 images: one desktop hero, 2-3 mobile, and page sections for the wall/tunnel scenes. Look at every shot before using it; an empty canvas or a cookie wall sells nothing.

## 2b. Record real footage (what makes it feel real)

Screenshots alone look like a slideshow. Record the product actually working and cut to it with `clip` scenes:

```bash
node SKILL_DIR/scripts/record_site.mjs <url> <dir>/site.mp4 --scroll 2400          # the real page loading, then a smooth scroll (mobile 1080x1920)
KEYS='[[1.5,"npm run dev"]]' node SKILL_DIR/scripts/record_term.mjs <dir>/run.cast 30 <project> -- <shell or cli> [args]
node SKILL_DIR/scripts/render_term.mjs <dir>/run.cast <dir>/run.mp4 --title "Terminal"   # real terminal emulator replay -> MP4
```

`record_term.mjs` types `KEYS` into a real PTY ([seconds, text] pairs) and logs every byte; `render_term.mjs` replays it in xterm.js frame by frame and prints the aspect to give the clip. Long runs: use the clip's `rate` (e.g. 8) to fast-forward. Recording Claude Code itself works too (`-- claude --allowedTools ...`).

## 3. Find the story

- **Promise** (≤ 6 words): the hook and the end title. Steal the product's own headline if it is good.
- **3 moments**: the features a viewer should *see* — these become the `focus` rects of the screen scene.
- **Proof**: one honest number that is on the site (stars, users, speed). Never invent numbers, features or logos.
- **Colours**: the brand accent from the site → `theme.accent` / `accent2` (accent2 is drawn behind dark text, so keep it light).

## 4. Storyboard

Read `references/scenes.md` for every scene and field. A shape that hits:

1. **Hook** (≤ 3 s): `slam` with the promise, or `mask` (a giant word filled with the product, dive through it), or `prompt` (type what the user wants → the product appears).
2. **The product working**: `screen` — device flies in, camera dives onto each focus rect, cursor clicks, labels pop.
3. **Depth**: `exploded` (UI splits into 3D layers) or `tunnel` (fly through a corridor of screens).
4. **Breadth**: `orbit` (feature chips around the logo) or `wall` (infinite 3D wall of screens).
5. **Proof**: `counter`, or `wipe` (before → after).
6. **Everywhere**: `fan` of phone screens.
7. **End**: `end` — title, CTA pill (`Comment *KEYWORD*` or the URL), handle.

6-9 scenes, never two of the same type in a row, alternate loud (slam/mask/counter) with screen-heavy scenes. Captions (`say`) are what the voice says, short and concrete; write them in the user's language.

**With the user's own voice** (the strongest version): write the script one line per idea, have them record one take, clean it (any voice enhancer; keep natural speed), then:

```bash
python SKILL_DIR/scripts/align_words.py voice.wav lines.txt words.json   # word times; lines.txt = what was said
```

Put `audio` and `words` in the storyboard and cut scenes on the words: each scene starts ~0.06 s before the word that introduces it, slams get `times` per word. If the script says "look at this video", leave a pause in the voice there (insert room tone) so the footage plays long enough to be seen.

**Look**: `theme.mode: "light"` + `display: "Inter Tight"` + `accentFont: "Instrument Serif"` gives a clean editorial look (paper, ink, one accent colour, serif italic accent words); dark mode with `Anton` + `Montserrat` captions is the loud one. Pick one per reel and keep one accent colour. Transitions default to a zoom/whip/glitch/flash/drop cycle; set `in` to override.

Keep the reel's files outside the user's repo (scratchpad or a reels folder).

## 5. Build, check, render

```bash
python SKILL_DIR/scripts/build.py <dir>/reel.json                     # -> reel.html (fix every ERROR)
node SKILL_DIR/scripts/render.mjs <dir>/reel.html --stills 1,4.5,9    # PNGs to eyeball
node SKILL_DIR/scripts/render.mjs <dir>/reel.html <dir>/reel.mp4      # 1080x1920, 30 fps, with audio if set
```

Always look at stills of every scene before the final render: text clipped at the edges, a focus rect on the wrong element, an empty screenshot. Rendering is ~3x real time.

## 6. Deliver

- Artifact tool available: rebuild with `--artifact` and publish the HTML (icon `play`). Give the link.
- Always hand over the MP4 path, plus a one-line caption + 3-5 hashtags for posting.

## Iterating

Edit the JSON and rebuild; never hand-edit the built HTML. "More hype" = shorter `dur`s, more `slam`/`mask`, `beats` (times of camera punches). "Calmer" = fewer scenes, `in: "cut"`.
