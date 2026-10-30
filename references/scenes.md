# Scene reference

Top level of `reel.json`:

| field | |
|---|---|
| `title` | page title |
| `format` | `9:16` (default, 1080x1920), `16:9`, `1:1`, `4:5` |
| `theme` | `{bg, fg, accent, accent2, hot, muted}` — accent2 sits behind dark text (chips, active words), keep it light |
| `theme.mode` | `"light"`: warm paper background, ink text, dot grid, film-editor frame marks + timecode (default is dark) |
| `theme.display` | headline font: `Unbounded` (default), `Inter Tight` (clean, lower case), `Anton`, `Bebas Neue`, `Montserrat` |
| `theme.accentFont` | font for `*accent*` words, e.g. `Instrument Serif` (set in italic) |
| `theme.caption` | caption font: `Inter` (default), `Montserrat`, `Inter Tight` |
| `scenes` | list, played in order |
| `audio` | voice/music file (path relative to the JSON); inlined, and muxed into the MP4 |
| `words` | `[{w, s, e, line}]` absolute word times from a voice take (`scripts/align_words.py`); a new `line` starts a new caption page; wrap a word in `*…*` to colour it. Without it, captions are spread over each scene's `say` |
| `beats` | times (s) for a camera punch |
| `captions` | `false` to hide captions |
| `progress` | `false` to hide the top progress bar |
| `fps` | render fps (30) |
| `rtl` | `true` for Arabic captions |

Every scene: `sfx` (extra sounds for `scripts/sfx.py`: `[{t, type, dur}]`, types whoosh, impact, glitch, pop, click, typing, enter, shutter, riser), `type`, `dur` (seconds), `say` (caption), `in` (`zoom`, `whip`, `glitch`, `flash`, `drop`, `cut`), `captions: "top"` (move captions to the top while footage has its own text at the bottom). Text fields accept `*accent*` and `~struck~`. Images are paths relative to the JSON.

## slam — kinetic hook
`lines`: 1-3 short lines; each word slams in with blur, RGB split, screen shake and a white hit. `gap`: seconds between words (0.3), or `times`: one start per word (seconds into the scene) to hit exactly when the voice says it.

## clip — real footage
`video` (MP4 path relative to the JSON, not inlined), `from` (start second in the source), `rate` (playback speed; above 1.5 shows a ▶▶ badge), `aspect` (width/height of the source: 0.5625 for 9:16, ~1.0 for a terminal from `render_term.mjs`), `full: true` (fills the frame; `mask: false` keeps the bottom of the footage visible), `position` (CSS object-position, `top` by default), `label` (chip), `zoom: [from, to]` + `origin` (CSS transform-origin) + `zoomAt` (start second) to push in on the part that matters, e.g. the line being typed in a terminal (`origin: "18% 88%"`). Use it for screen recordings: `record_site.mjs` (a real site loading and scrolling), `record_term.mjs` + `render_term.mjs` (a real terminal session, e.g. Claude Code running a command), or any demo video. Frame-exact in the MP4; the page only plays them when the videos sit next to it.

## mask — dive into a word
`word`, `image`: a giant word filled with the moving screenshot; at `dive` (1.5 s) the camera dives through it into the full screen. `caption`: chip shown after the dive. `origin`: CSS transform-origin of the dive (`"38% 50%"` to aim at a letter).

## prompt — AI makes it
`prompt` (typed), `app` (header label), then either `image` (the product flips out of the box with a burst) or `result` (list of ✓ lines). `cps` typing speed, `think` seconds of shimmer.

## screen — the product working
`image`, `device` (`browser` | `phone` | `none`, auto by aspect), `url` (browser bar), `title`, `scroll` (0-1 idle scroll for tall pages), `focus`: list of `{x, y, w, h, label, at, hold, zoom}` — fractions of the screenshot. The device flies in from deep 3D, the camera dolly-zooms onto each rect at `at`, a cursor travels there and clicks, the rest dims, the label pops under it.

## exploded — UI in layers
`image`, `slices` (4), `labels`: `[{slice, text}]`, `title`. The screen splits into floating 3D layers, then snaps back with a flash.

## tunnel — fly through the product
`images` (5-8), `title`, `speed`. The camera flies down a corridor of screens and lands on the last one.

## wall — infinite screen wall
`images` (3+), `title`. Tilted 3D wall of screens scrolling in opposite directions, title on top.

## orbit — everything it does
`items` (≤ 8, emoji welcome), `center` text or `logo` image, `title`, `speed`. Chips orbit in 3D; each one lights up in turn.

## wipe — before / after
`before`, `after`, `labels` (`["Before","After"]`), `title`. Diagonal glowing wipe that swings back and slams home.

## counter — the number
`value`, `from`, `prefix`, `suffix`, `decimals`, `label`, `title`. Counts up with motion blur, then rings + particle burst. Only real numbers.

## fan — on every screen
`images` (2-4 phone screenshots), `title`. Phones rise and fan out in 3D.

## end — call to action
`title`, `logo`, `cta` (pill; `Comment *PLAY*` highlights the keyword), `handle`. Logo spins in, title gets a light sweep, burst.
