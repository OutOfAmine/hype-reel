# Product promo mode — one photo to a cinematic promo reel

The user has a physical product and maybe zero editing experience. Your job is to get them from "I have a photo" to a finished
MP4 without them touching a config file. **Guide them one step at a time**: ask one short question, wait, confirm what you got,
move on. Say in one line what the next step will produce. Never dump all the questions at once.

What they get (about 20 s, 1080x1920): an optional line in their own voice ("Want a video like this for your product?"),
then the promo plays as a video card that expands to full screen — the product rises into a spotlight with its name, floats with
a close-up lens, a huge close-up with one bold word, a colourway carousel, a hero lockup with a tagline — with an emotional
AI voice-over, music and sound effects, then their call to action with a keyword pill ("Comment PROMO").
Example: `examples/espadrille/promo.json`.

## Step 0 — setup (once)
Check, and install what is missing, telling the user what each thing is for:
- `cd SKILL_DIR && npm install` (Chrome renderer + ffmpeg).
- Python packages: `pip install pillow numpy "kokoro>=0.9.4" soundfile` (voice). Background removal if their photo is not a
  transparent PNG: `pip install rembg onnxruntime`. Word timing: `pip install torch torchaudio` (optional; without it words are spread evenly).
- Emotional voice (recommended, needs an NVIDIA GPU to be quick): `pip install chatterbox-tts "setuptools<81"`. No GPU: keep Kokoro,
  or run promo_voice.py in a free Kaggle/Colab GPU notebook and download `build/voice/`.
Make a folder for the reel outside this skill (e.g. `~/reels/<brand>/`).

## Step 1 — the product
Ask: **"What's the product called, and can you send me one clear photo of it?"**
- One product, whole product in frame, plain background, sharp. A transparent PNG is perfect. Phone photos are fine (rembg cuts them out).
- No photo yet: offer to generate a clean studio product image with any image generator they have, and say plainly that the reel
  will then show an illustration, not their real product.
Copy the photo into the reel folder.

## Step 2 — the brand colour
Ask: **"What's your brand colour?"** (offer: red #ff2b2b, or pick the strongest colour from their photo/logo). It becomes `accent`:
the rim light, the big words, the CTA pill.

## Step 3 — what makes it great
Ask: **"Give me 2-3 things that make it special"** (light, comfortable, grip, smell, ingredients, price, handmade…) and
**"Does it come in several colours? Which ones?"**
Then WRITE the five promo lines yourself and show them for approval. Rules that make it hit:
- Line 1, `hook`: two short sentences, the second names the brand — "Stop scrolling... This is <Brand>."
- Line 2, `float`: one feeling, with a pause — "So light... you'll forget you're wearing them." (`big` = the word to blow up)
- Line 3, `detail`: first word is the hero detail — "Grip... that never lets go." / "Leather... made by hand."
- Line 4, `colors`: "<N> colors. Zero chill." (or a second detail line if there are no colourways: use `detail` again)
- Line 5, `end`: "<Brand>... <tagline>." — the tagline is what stays on screen.
- 4-8 words per line, "..." where the voice should breathe, no claims they can't back up (no fake prices, ratings, "#1").
Write the lines in the language of their audience (the AI voice speaks English best).

## Step 4 — the voice
Ask: **"Female or male voice? Calm and classy, or intense and hyped?"** Map it:
- female warm `af_heart`, soft/whispery `af_nicole`, bright `af_bella`; male deep `am_onyx`, `am_fenrir`, `am_michael`.
- emotion: `voice.engine: "chatterbox"` with `exaggeration` 0.9 (intense) … 0.5 (calm). Kokoro only = steady narrator.
- `voice.loudness` -11 (loud, default) .. -14 (softer).
Run `python SKILL_DIR/scripts/promo_voice.py promo.json`. With chatterbox it makes 3 takes per line; listen-check with the user
or pick with any speech-to-text that every word is right, and set `voice.takes` (e.g. `[0, 2, 1, 0, 1]`).

## Step 5 — their own voice (optional, strongest for social)
Ask: **"Do you want to say a line before and after the promo, in your own voice?"** Suggest, in their language:
- intro: "Want a video like this for your product?" → `intro.text`, `intro.highlight` (the word to colour)
- outro: "Comment PROMO and I'll send you the link in DM." → `outro.text`, `outro.keyword` (PROMO), `outro.handle` (@them)
They record each line once on their phone (voice memo is fine), one clean take, energetic, and send the files:
`intro.audio`, `outro.audio`. The text must match what they actually said, word for word (it drives the on-screen words).
No recording yet? Leave `audio` out: those parts are silent slots so the edit can be checked first, and they record later.

## Step 6 — build, check, render
```bash
python SKILL_DIR/scripts/promo_assets.py promo.json     # cutout, hero plate, close-ups, colourways  -> build/
python SKILL_DIR/scripts/promo_voice.py  promo.json     # AI voice-over                            -> build/voice/
python SKILL_DIR/scripts/promo_build.py  promo.json     # voice + timing + music + SFX              -> build/reel.html
node   SKILL_DIR/scripts/render.mjs build/reel.html --stills 1,4,7,10,13,16 --outdir build/stills
node   SKILL_DIR/scripts/render.mjs build/reel.html promo.mp4
```
Look at the stills before rendering: the close-ups (`crops` in promo.json, fractions of the product box, change them if a close-up
shows nothing interesting), the colourways (products with no coloured parts: set `"recolor": false` per colour, the glow still changes),
text inside the frame. Then give the user the MP4 path, and offer a caption + 3-5 hashtags. Publishing as a page: `promo_build.py --artifact`.

## promo.json
```json
{
  "brand": "Espadrille", "photo": "espadrille.png", "accent": "#ff2b2b",
  "voice": { "engine": "chatterbox", "voice": "af_heart", "exaggeration": 0.9, "loudness": -11, "takes": [0, 0, 0, 0, 0] },
  "intro": { "text": "Want a video like this for your product?", "highlight": "product", "audio": "intro.m4a" },
  "shots": [
    { "type": "hook",   "line": "Stop scrolling... This is Espadrille." },
    { "type": "float",  "line": "So light... you'll forget you're wearing them.", "big": "light" },
    { "type": "detail", "line": "Grip... that never lets go." },
    { "type": "colors", "line": "Five colors. Zero chill." },
    { "type": "end",    "line": "Espadrille... Move different.", "badge": "NEW DROP" }
  ],
  "colors": [ { "name": "RED", "color": "#ff2b2b" }, { "name": "BLUE", "color": "#3d8bff" } ],
  "crops": { "detail1": [0.5, 0.05, 0.9, 0.55], "detail2": [0.0, 0.45, 0.55, 1.0] },
  "outro": { "text": "Comment PROMO and I'll send you the link in DM.", "keyword": "PROMO", "audio": "outro.m4a", "handle": "@you" }
}
```
Shot types: `hook`, `float`, `detail`, `colors`, `end` (any order, any count; a line's `gap` sets the pause after it).
