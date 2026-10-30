#!/usr/bin/env python3
"""Product photo -> everything the promo reel shows: a clean cutout, a studio hero plate, two close-ups and colourways.

Usage: python promo_assets.py promo.json

Reads `photo` from promo.json (a PNG with transparency is best; any photo works when `rembg` is installed:
pip install rembg onnxruntime). Writes to <promo dir>/build/: cutout.png, hero.jpg, detail1.jpg, detail2.jpg, cw0.jpg..
Colourways recolour the product's saturated parts to each `colors[].color` (its accent parts: soles, logos, panels).
"""
import json, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

cfg_path = pathlib.Path(sys.argv[1]).resolve(); cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
root = cfg_path.parent; out = root / "build"; out.mkdir(exist_ok=True)
accent = cfg.get("accent", "#ff2b2b")
hexrgb = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

# 1. cutout
im = Image.open(root / cfg["photo"]).convert("RGBA")
a = np.array(im)[..., 3]
if a.min() > 250:   # no transparency: remove the background
    try:
        from rembg import remove
    except ImportError:
        sys.exit("The photo has a background. Either give a PNG with transparency, or: pip install rembg onnxruntime")
    im = remove(im).convert("RGBA")
im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
im.thumbnail((1400, 1400), Image.LANCZOS)
im.save(out / "cutout.png", optimize=True)
print("cutout", im.size)


def radial(w, h, cx, cy, r, inner, outer):
    y, x = np.mgrid[0:h, 0:w]
    d = np.clip(np.hypot((x - cx) / r, (y - cy) / r), 0, 1)[..., None]
    return Image.fromarray((np.array(inner) * (1 - d) + np.array(outer) * d).astype("uint8"))


def plate(img, w, h, glow, scale=.92, cy=.5, rot=-8):
    """the product on a dark studio floor with a coloured rim glow"""
    base = radial(w, h, w * .5, h * cy, max(w, h) * .62, (34, 30, 32), (10, 10, 12)).convert("RGBA")
    s = img.rotate(rot, expand=True, resample=Image.BICUBIC)
    k = w * scale / s.width; s = s.resize((int(s.width * k), int(s.height * k)), Image.LANCZOS)
    pad = Image.new("RGBA", (s.width + 300, s.height + 300), (0, 0, 0, 0)); pad.paste(s, (150, 150)); s = pad
    halo = Image.new("RGBA", s.size, glow + (0,)); halo.putalpha(s.getchannel("A").filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * .85)))
    x, y = (w - s.width) // 2, int(h * cy - s.height / 2)
    sh = Image.new("L", (w, h), 0); ImageDraw.Draw(sh).ellipse([x + s.width * .2, y + s.height * .78, x + s.width * .82, y + s.height * .9], fill=150)
    base.paste(Image.new("RGBA", (w, h), (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(40)))
    base.alpha_composite(halo, (x, y)); base.alpha_composite(s, (x, y))
    return base.convert("RGB")


def recolor(img, rgb):
    """move the hue of the saturated parts to the target colour, keep their shading"""
    arr = np.array(img); hsv = np.array(Image.fromarray(arr[..., :3]).convert("HSV")).astype(float)
    th = np.array(Image.fromarray(np.uint8([[rgb]])).convert("HSV"))[0, 0, 0]
    mask = (hsv[..., 1] > 90) & (hsv[..., 2] > 60)
    hsv[..., 0] = np.where(mask, th, hsv[..., 0])
    rgbout = np.array(Image.fromarray(hsv.astype("uint8"), "HSV").convert("RGB"))
    return Image.fromarray(np.dstack([rgbout, arr[..., 3]]), "RGBA")


plate(im, 1080, 1920, hexrgb(accent)).save(out / "hero.jpg", quality=90)
big = plate(im, 2400, 2400, hexrgb(accent), scale=.95, rot=0)
# close-ups relative to the product's box on the big plate: top-right (detail1) and bottom-left (detail2), or `crops` in promo.json
pw = 2400 * .95; ph = pw * im.height / im.width; x0, y0 = (2400 - pw) / 2, (2400 - ph) / 2
crops = cfg.get("crops", {"detail1": [.5, .05, .9, .55], "detail2": [.0, .45, .55, 1.0]})
for name, (fx0, fy0, fx1, fy1) in crops.items():
    box = (int(x0 + fx0 * pw), int(y0 + fy0 * ph), int(x0 + fx1 * pw), int(y0 + fy1 * ph))
    c = big.crop(box); c = c.resize((1200, int(1200 * c.height / c.width)), Image.LANCZOS); c.save(out / f"{name}.jpg", quality=88)
for k, col in enumerate(cfg.get("colors", [])):
    rgb = hexrgb(col["color"])
    plate(recolor(im, rgb) if col.get("recolor", True) else im, 1080, 1920, rgb).save(out / f"cw{k}.jpg", quality=86)
print("OK", out)
