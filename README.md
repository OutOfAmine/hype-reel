# hype-reel

**A Claude Code skill that turns any product into an insane promo reel — from its real screens, in one prompt.**

```
/hype-reel https://your-product.com
```

Claude screenshots your product with headless Chrome, finds the story (the promise, the three moments worth seeing, one honest number), writes a storyboard, and stages it with Framer Motion: the device flies in from deep 3D and the camera dives onto each feature, the UI explodes into floating layers, the camera flies through a corridor of your screens, a giant word filled with your product swallows the viewer… Then it renders a frame-exact **1080x1920 MP4** and a shareable page.

No After Effects. No templates you fill by hand. No API key.

## Demos

Four unofficial demos made with the skill from the products' public websites (not affiliated with these companies):

| Supabase | Cal.com | Resend | Linear |
|---|---|---|---|
| [![Supabase demo](docs/supabase.gif)](videos/supabase.mp4) | [![Cal.com demo](docs/calcom.gif)](videos/calcom.mp4) | [![Resend demo](docs/resend.gif)](videos/resend.mp4) | [![Linear demo](docs/linear.gif)](videos/linear.mp4) |
| [▶ MP4](videos/supabase.mp4) · [storyboard](examples/supabase/reel.json) | [▶ MP4](videos/calcom.mp4) · [storyboard](examples/calcom/reel.json) | [▶ MP4](videos/resend.mp4) · [storyboard](examples/resend/reel.json) | [▶ MP4](videos/linear.mp4) · [storyboard](examples/linear/reel.json) |

The full 1080x1920 MP4s are in [`videos/`](videos).

## Install

```bash
git clone https://github.com/OutOfAmine/hype-reel ~/.claude/skills/hype-reel
cd ~/.claude/skills/hype-reel && npm install
```

Needs Node 18+, Python 3, and Chrome / Edge / Chromium installed (or `CHROME_PATH`). ffmpeg comes with `npm install`.

Then in Claude Code: `/hype-reel <url>` or just *"make a reel for my app"*.

## Scenes

| scene | what happens |
|---|---|
| `slam` | words slam in with blur, RGB split, screen shake |
| `mask` | a giant word filled with your product — the camera dives through it into the real screen |
| `prompt` | a prompt types itself, the product flips out of the box in a burst |
| `screen` | browser/phone flies in, camera dolly-zooms onto each feature, cursor clicks, labels pop |
| `exploded` | the UI splits into floating 3D layers and snaps back |
| `tunnel` | the camera flies down a corridor of your screens |
| `wall` | an infinite tilted wall of screens |
| `orbit` | feature chips orbit your logo in 3D |
| `wipe` | before/after diagonal glitch wipe that swings back |
| `counter` | a real number counts up, rings + particle burst |
| `fan` | phone screens rise and fan out |
| `end` | logo spin, light sweep, CTA pill (`Comment *KEYWORD*`) |

Field-by-field reference: [references/scenes.md](references/scenes.md).

## By hand

```bash
node scripts/capture.mjs https://example.com shots --name home --rects "h1,#cta"
node scripts/capture.mjs https://example.com shots --mobile --name home-m
python scripts/build.py reel.json                       # -> reel.html (plays in any browser)
node scripts/render.mjs reel.html --stills 1,5,9        # quick PNG checks
node scripts/render.mjs reel.html reel.mp4              # frame-exact MP4, with your voice if reel.json has "audio"
```

Every animation is a pure function of time driven by a Framer Motion value, so the page you watch live and the MP4 are the same film.

## License

MIT
