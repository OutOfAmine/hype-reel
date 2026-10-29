# Scene reference

Top level of `reel.json`:

| field | |
|---|---|
| `title` | page title |
| `format` | `9:16` (default, 1080x1920), `16:9`, `1:1`, `4:5` |
| `theme` | `{bg, fg, accent, accent2, hot, muted}` — accent2 sits behind dark text (chips, active words), keep it light |
| `scenes` | list, played in order |
| `audio` | voice/music file (path relative to the JSON); inlined, and muxed into the MP4 |
| `words` | `[{w, s, e}]` absolute word times from a voice take; otherwise captions are spread over each scene's `say` |
| `beats` | times (s) for a camera punch |
| `captions` | `false` to hide captions |
| `progress` | `false` to hide the top progress bar |
| `fps` | render fps (30) |
| `rtl` | `true` for Arabic captions |

Every scene: `type`, `dur` (seconds), `say` (caption), `in` (`zoom`, `whip`, `glitch`, `flash`, `drop`, `cut`). Text fields accept `*accent*` and `~struck~`. Images are paths relative to the JSON.

## slam — kinetic hook
`lines`: 1-3 short lines; each word slams in with blur, RGB split, screen shake and a white hit. `gap`: seconds between words (0.3).

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
