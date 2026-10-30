#!/usr/bin/env python3
"""Turn a hype-reel storyboard (JSON) into one self-contained, auto-playing HTML page.

Usage: build.py reel.json [-o reel.html] [--artifact]

Image and audio paths in the storyboard are read relative to the JSON file and
inlined as data URIs, so the page works anywhere (and as a claude.ai Artifact).
The storyboard is checked first: errors stop the build, warnings are things that
make a reel drag or break.
"""
import argparse
import base64
import json
import mimetypes
import pathlib
import re
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "player.html"
NEEDS = {
    "clip": ["video"], "tunnel": ["images"], "mask": ["image", "word"],
    "slam": ["lines"], "screen": ["image"], "exploded": ["image"], "wall": ["images"], "orbit": ["items"],
    "wipe": ["before", "after"], "counter": ["value"], "fan": ["images"], "prompt": ["prompt"], "end": ["title"],
}
IMAGE_KEYS = ["image", "before", "after", "logo"]
FORMATS = {"9:16", "16:9", "1:1", "4:5"}


def image_size(data):
    """(width, height) for PNG, JPEG, GIF and WebP bytes, or None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kind = data[12:16]
        if kind == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if kind == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if kind == b"VP8L":
            b = int.from_bytes(data[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            seg = struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + seg
    return None


class Inliner:
    def __init__(self, base):
        self.base, self.bytes, self.errors = base, 0, []

    def image(self, ref, where):
        if isinstance(ref, dict) and ref.get("src", "").startswith("data:"):
            return ref
        path = (self.base / str(ref)).resolve()
        if not path.is_file():
            self.errors.append(f"{where}: image not found: {path}")
            return {"src": "", "w": 16, "h": 9}
        data = path.read_bytes()
        size = image_size(data)
        if not size:
            self.errors.append(f"{where}: can't read the size of {path.name} (use PNG, JPEG, WebP or GIF)")
            size = (16, 9)
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        self.bytes += len(data)
        return {"src": f"data:{mime};base64,{base64.b64encode(data).decode()}", "w": size[0], "h": size[1]}

    def audio(self, ref):
        path = (self.base / str(ref)).resolve()
        if not path.is_file():
            self.errors.append(f"audio not found: {path}")
            return None, None
        data = path.read_bytes()
        self.bytes += len(data)
        mime = mimetypes.guess_type(path.name)[0] or "audio/mpeg"
        return f"data:{mime};base64,{base64.b64encode(data).decode()}", str(path)


def check(story):
    errors, warns = [], []
    scenes = story.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return ["'scenes' must be a non-empty list"], warns
    if story.get("format", "9:16") not in FORMATS:
        errors.append(f"format must be one of {sorted(FORMATS)}")
    if not story.get("title"):
        warns.append("no top-level 'title'")
    total = sum(s.get("dur", 4) for s in scenes)
    if not 5 <= len(scenes) <= 11:
        warns.append(f"{len(scenes)} scenes; 6-10 keeps a reel punchy")
    if total > 60:
        warns.append(f"about {total:.0f} s long; product reels hit hardest at 20-40 s")
    types = [s.get("type") for s in scenes]
    if not {"screen", "exploded", "wipe", "fan", "wall", "tunnel", "mask"} & set(types):
        warns.append("no scene shows the product's real screen (screen / exploded / wipe / fan / wall)")
    if types[0] not in ("slam", "prompt", "screen", "wall", "mask", "tunnel", "clip"):
        warns.append("open on a hook: slam, mask, prompt, screen, tunnel or wall")
    if types[-1] != "end":
        warns.append("finish on an 'end' scene with the call to action")
    for i, s in enumerate(scenes, 1):
        t = s.get("type")
        where = f"scene {i} ({t})"
        if t not in NEEDS:
            errors.append(f"{where}: unknown type, use one of {sorted(NEEDS)}")
            continue
        for k in NEEDS[t]:
            if not s.get(k) and s.get(k) != 0:
                errors.append(f"{where}: needs '{k}'")
        say = s.get("say", "")
        if not story.get("words") and say and len(say.split()) > 3.2 * s.get("dur", 4):
            warns.append(f"{where}: {len(say.split())} caption words for {s.get('dur', 4)} s; it will flash by")
        if t == "slam":
            for ln in s.get("lines") or []:
                if len(re.sub(r"[*~]", "", ln).split()) > 5:
                    warns.append(f"{where}: '{ln}' is long; slams hit at <= 4 words a line")
        for f in s.get("focus") or []:
            for k in ("x", "y", "w", "h"):
                v = f.get(k)
                if not isinstance(v, (int, float)) or not 0 <= v <= 1:
                    errors.append(f"{where}: focus '{f.get('label', '?')}' needs {k} as a fraction 0-1 of the screenshot")
        if t in ("wall", "fan") and len(s.get("images") or []) < (3 if t == "wall" else 2):
            warns.append(f"{where}: give it {'3+' if t == 'wall' else '2-4'} images")
        if t == "orbit" and len(s.get("items") or []) > 8:
            warns.append(f"{where}: more than 8 orbit items gets crowded")
    return errors, warns


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story")
    ap.add_argument("-o", "--out")
    ap.add_argument("--artifact", action="store_true", help="emit a page body for claude.ai Artifacts (no doctype/html/head/body)")
    a = ap.parse_args()
    src = pathlib.Path(a.story).resolve()
    story = json.loads(src.read_text(encoding="utf-8"))
    errors, warns = check(story)
    inl = Inliner(src.parent)
    for i, s in enumerate(story.get("scenes") or [], 1):
        where = f"scene {i} ({s.get('type')})"
        for k in IMAGE_KEYS:
            if s.get(k):
                s[k] = inl.image(s[k], where)
        if s.get("images"):
            s["images"] = [inl.image(x, where) for x in s["images"]]
        if s.get("video") and not (src.parent / s["video"]).is_file():
            errors.append(f"{where}: video not found: {s['video']} (kept as a relative path, not inlined: render the MP4 next to the JSON)")
    if story.get("audio"):
        story["audio"], story["_audioPath"] = inl.audio(story["audio"])
    errors += inl.errors
    if inl.bytes > 14_000_000:
        errors.append(f"inlined media is {inl.bytes / 1e6:.1f} MB; artifacts cap at 16 MB, use JPEG screenshots (capture.mjs default)")
    elif inl.bytes > 8_000_000:
        warns.append(f"inlined media is {inl.bytes / 1e6:.1f} MB; the page will load slowly")
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    if errors:
        sys.exit(1)
    page = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(story, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace("/*__STORY__*/null", data).replace("__TITLE__", re.sub(r"[<>&*~]", "", story.get("title", "Hype reel")))
    if a.artifact:
        page = re.sub(r"<!--DOC-->.*?<!--/DOC-->", "", page, flags=re.S)
    else:
        page = page.replace("<!--DOC-->", "").replace("<!--/DOC-->", "")
    out = pathlib.Path(a.out) if a.out else src.with_suffix(".html")
    out.write_text(page, encoding="utf-8")
    total = sum(s.get("dur", 0) for s in story["scenes"])
    print(f"OK    {out}  ({len(story['scenes'])} scenes, ~{total:.1f} s, {out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
