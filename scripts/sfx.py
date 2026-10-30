#!/usr/bin/env python3
"""Sound design for a reel: whooshes on cuts, impacts on slams, pops on labels, keyboard clicks, shutters, risers,
all synthesised (no sample packs), placed from the storyboard and mixed under the voice.

Usage: python sfx.py reel.json [-o mix.wav] [--level -16] [--no-voice]

Writes the mix next to the storyboard and prints the path; point the storyboard's "audio" at it and rebuild.
Automatic: a sound for each scene's `in` transition, an impact per slam word, a pop per clip label, a burst on the end.
Per scene, add {"sfx": [{"t": 0.3, "type": "typing", "dur": 2.2}, {"t": 3.8, "type": "enter"}]} (t = seconds into the scene).
Types: whoosh, impact, glitch, pop, click, typing, enter, shutter, riser.
"""
import argparse, json, pathlib, shutil, subprocess, sys
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def ffmpeg():
    here = pathlib.Path(__file__).resolve().parent.parent / "node_modules" / "ffmpeg-static"
    for c in [here / "ffmpeg.exe", here / "ffmpeg", shutil.which("ffmpeg")]:
        if c and pathlib.Path(c).exists():
            return str(c)
    sys.exit("ffmpeg not found (npm install in the skill folder, or put ffmpeg on PATH)")


def t_(d): return np.arange(int(d * SR)) / SR


def lowpass(x, cut):  # one-pole, cut may be an array (Hz per sample)
    cut = np.broadcast_to(np.asarray(cut, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc); y[i] = acc
    return y


def whoosh(d=.5, up=True):
    t = t_(d); n = rng.standard_normal(len(t))
    sweep = np.where(up, 0, 0) + (400 + 5200 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2)
    x = lowpass(n, sweep) - lowpass(n, sweep * .25)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * (t / d) ** .3
    return x * env * 2.2, np.linspace(-.7, .7, len(t)) if up else np.linspace(.7, -.7, len(t))


def impact(d=.7):
    t = t_(d); f = 45 + 95 * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 180) * .6
    air = lowpass(rng.standard_normal(len(t)), 2500) * np.exp(-t * 14) * .5
    return (body * 1.1 + click + air), 0


def glitch(d=.32):
    out = np.zeros(int(d * SR))
    for k in range(7):
        a = int(rng.uniform(0, d - .03) * SR); n = int(rng.uniform(.012, .03) * SR)
        f = rng.uniform(180, 2400); tt = np.arange(n) / SR
        out[a:a + n] += np.sign(np.sin(2 * np.pi * f * tt)) * .35 + rng.standard_normal(n) * .25
    return np.round(out * 6) / 6, rng.uniform(-.4, .4)


def pop(d=.09):
    t = t_(d); f = 1300 * np.exp(-t * 22) + 380
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38) * .9, 0


def click(d=.03, g=1.0):
    t = t_(d); n = rng.standard_normal(len(t))
    hp = n - lowpass(n, 1800)
    tone = np.sin(2 * np.pi * rng.uniform(1900, 2600) * t) * .3
    return (hp + tone) * np.exp(-t * 260) * .55 * g, rng.uniform(-.25, .25)


def enter(d=.12):
    a, _ = click(.04, 1.6); t = t_(d)
    thock = lowpass(rng.standard_normal(len(t)), 600) * np.exp(-t * 45) * 2.4
    x = thock.copy(); x[:len(a)] += a
    return x, 0


def shutter(d=.16):
    x = np.zeros(int(d * SR))
    for at in (0, .07):
        c, _ = click(.05, 2.2); i = int(at * SR); x[i:i + len(c)] += c
    return x, 0


def riser(d=1.0):
    t = t_(d); n = rng.standard_normal(len(t))
    x = lowpass(n, 300 + 6000 * (t / d) ** 2) * (t / d) ** 2 * 1.4
    x += np.sin(2 * np.pi * np.cumsum(200 + 700 * (t / d) ** 2) / SR) * (t / d) ** 3 * .25
    return x, 0


def typing(dur, at=0.0):
    hits, t = [], 0.0
    while t < dur:
        hits.append((at + t, "click")); t += rng.uniform(.05, .11)
    return hits


GEN = {"whoosh": whoosh, "impact": impact, "glitch": glitch, "pop": pop, "click": click, "enter": enter, "shutter": shutter, "riser": riser,
       "whoosh_down": lambda: whoosh(.5, up=False)}
GAIN = {"whoosh": .55, "whoosh_down": .5, "impact": .8, "glitch": .45, "pop": .5, "click": .35, "enter": .6, "shutter": .6, "riser": .45}


def plan(story):
    out, start = [], 0.0
    for i, sc in enumerate(story["scenes"]):
        d, kind = sc.get("dur", 4), sc.get("type")
        tr = sc.get("in")
        if i > 0:
            if tr in ("whip", "zoom"): out.append((start - .3, "whoosh"))
            elif tr == "drop": out.append((start - .3, "whoosh_down"))
            elif tr == "glitch": out.append((start - .02, "glitch"))
            elif tr == "flash": out.append((start - .01, "impact"))
        if kind == "slam":
            for k, tt in enumerate(sc.get("times") or [.12 + .3 * k for k in range(8)][:len(" ".join(sc.get("lines", [])).split())]):
                out.append((start + tt, "impact" if k % 2 == 0 else "pop"))
        if kind == "clip" and sc.get("label"): out.append((start + .12, "pop"))
        if kind in ("wall", "tunnel"): out.append((start, "riser" if kind == "tunnel" else "shutter"))
        if kind == "counter": out += [(start + .7, "riser"), (start + 1.7, "impact")]
        if kind == "end": out += [(start + .3, "impact"), (start + 1.0, "pop")]
        for s in sc.get("sfx", []):
            if s["type"] == "typing": out += typing(s.get("dur", 1.5), start + s["t"])
            else: out.append((start + s["t"], s["type"]))
        start += d
    return out, start


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story"); ap.add_argument("-o", "--out")
    ap.add_argument("--level", type=float, default=-16, help="SFX peak level in dBFS (voice sits around -14 LUFS)")
    ap.add_argument("--no-voice", action="store_true")
    a = ap.parse_args()
    src = pathlib.Path(a.story).resolve(); story = json.loads(src.read_text(encoding="utf-8"))
    F = ffmpeg()
    events, total = plan(story)
    voice = None
    if story.get("audio") and not a.no_voice:
        vp = (src.parent / story["audio"]).resolve()
        voice = np.frombuffer(subprocess.run([F, "-v", "error", "-i", str(vp), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
    n = max(int((total + 1) * SR), len(voice) if voice is not None else 0)
    bus = np.zeros((n, 2))
    for at, kind in events:
        x, pan = GEN[kind]()
        x = np.asarray(x, float) * GAIN.get(kind, .5)
        pan = np.broadcast_to(pan, x.shape)
        st = np.stack([x * np.sqrt((1 - pan) / 2), x * np.sqrt((1 + pan) / 2)], 1)
        i = int(max(0, at) * SR); j = min(n, i + len(st)); bus[i:j] += st[:j - i]
    peak = np.abs(bus).max() or 1
    bus *= 10 ** (a.level / 20) / peak
    mix = bus.copy()
    if voice is not None: mix[:len(voice)] += voice
    pk = np.abs(mix).max()
    if pk > .97: mix *= .97 / pk
    if voice is not None: mix = mix[:max(len(voice), int(total * SR))]
    out = pathlib.Path(a.out) if a.out else src.parent / ((pathlib.Path(story.get("audio", "voice.wav")).stem) + "_sfx.wav")
    subprocess.run([F, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", str(out)], input=mix.astype("<f4").tobytes(), check=True)
    kinds = {}
    for _, k in events: kinds[k] = kinds.get(k, 0) + 1
    print(f"OK {out}  {len(events)} sounds " + ", ".join(f"{k}x{v}" for k, v in sorted(kinds.items())))


if __name__ == "__main__":
    main()
