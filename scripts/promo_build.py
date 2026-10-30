#!/usr/bin/env python3
"""promo.json + build/ (assets, voice) -> build/reel.html with the voice, word timing, music and sound effects.

Usage: python promo_build.py promo.json [--artifact]
Then:  node scripts/render.mjs <promo dir>/build/reel.html <promo dir>/promo.mp4

Optional own-voice lines: `intro.audio` / `outro.audio` in promo.json (any format ffmpeg reads, e.g. a phone voice memo).
They are kept as recorded (only gain-matched), so clean them first if you want (scripts like resemble-enhance).
Word timing uses align_words.py (torch + torchaudio); without them the words are spread evenly over each line.
"""
import argparse, base64, importlib.util, io, json, pathlib, subprocess, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument("promo"); ap.add_argument("--artifact", action="store_true")
ap.add_argument("--python", default=sys.executable, help="python with torch/torchaudio for word alignment")
a = ap.parse_args()
cfg_path = pathlib.Path(a.promo).resolve(); cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
root = cfg_path.parent; B = root / "build"
spec = importlib.util.spec_from_file_location("sfx", HERE / "sfx.py"); sfx = importlib.util.module_from_spec(spec); spec.loader.exec_module(sfx)
F = sfx.ffmpeg(); SR = 48000
LOUD = cfg.get("voice", {}).get("loudness", -11)   # LUFS; loud and clear on a phone

def load(p): return np.frombuffer(subprocess.run([F, "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).astype(float)
def save(x, p, extra=()): subprocess.run([F, "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", *extra, str(p)], input=x.astype("<f8").tobytes(), check=True)
def edges(x, lo=.03, head=.03, tail=.08):
    e = np.convolve(np.abs(x), np.ones(480) / 480, "same"); idx = np.where(e > max(e.max() * lo, 1e-5))[0]
    y = x[max(0, idx[0] - int(head * SR)):idx[-1] + int(tail * SR)].copy(); f = int(.008 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y
def lufs(x):
    p = B / "_m.wav"; save(x, p)
    r = subprocess.run([F, "-hide_banner", "-i", str(p), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in r.splitlines() if l.strip().startswith("I:")][-1].split()[1])

# ---- voice track: [intro] promo lines [outro]; your lines on their own track, untouched except gain ----
shots = cfg["shots"]; takes = cfg.get("voice", {}).get("takes", [0] * len(shots))
ai, me, t, spans = [np.zeros(int(.1 * SR))], [np.zeros(int(.1 * SR))], .1, []   # spans: (line text, start, end, own voice)
def put(x, mine): (me if mine else ai).append(x); (ai if mine else me).append(np.zeros(len(x)))
def own(part, fallback):
    if part and part.get("audio"):
        x = edges(load(root / part["audio"]), lo=.02, head=.02, tail=.12); return x * 10 ** ((LOUD - lufs(x)) / 20)
    return np.zeros(int(fallback * SR))   # no take yet: a silent slot, so the edit can be timed before you record
if cfg.get("intro"):
    x = own(cfg["intro"], 2.4); spans.append((cfg["intro"]["text"], t, t + len(x) / SR, True)); put(x, True); t += len(x) / SR
    put(np.zeros(int(.2 * SR)), False); t += .2
for i, s in enumerate(shots):
    c = sorted((B / "voice").glob(f"{i:02d}_*.wav")); x = edges(load(c[min(takes[i], len(c) - 1)])); x *= .5 / np.abs(x).max()
    spans.append((s["line"], t, t + len(x) / SR, False)); put(x, False); t += len(x) / SR
    gap = s.get("gap", .45); put(np.zeros(int(gap * SR)), False); t += gap
if cfg.get("outro"):
    x = own(cfg["outro"], 3.6); spans.append((cfg["outro"]["text"], t, t + len(x) / SR, True)); put(x, True); t += len(x) / SR
put(np.zeros(int(1.0 * SR)), False)
save(np.concatenate(ai), B / "_ai.wav")
subprocess.run([F, "-v", "error", "-y", "-i", str(B / "_ai.wav"), "-af", f"highpass=f=70,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3500:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I={LOUD}:TP=-1:LRA=7", "-ar", str(SR), str(B / "_ai_l.wav")], check=True)
va = load(B / "_ai_l.wav"); vm = np.concatenate(me); n0 = min(len(va), len(vm)); voice = va[:n0] + vm[:n0]
save(voice, B / "voice.wav")

# ---- word timing per line ----
words = []
for li, (text, s0, s1, mine) in enumerate(spans):
    ok = False
    if not (mine and not (cfg.get("intro" if li == 0 else "outro") or {}).get("audio")):
        seg = B / "_seg.wav"; subprocess.run([F, "-v", "error", "-y", "-ss", str(max(0, s0 - .05)), "-to", str(s1 + .1), "-i", str(B / "voice.wav"), str(seg)], check=True)
        (B / "_l.txt").write_text(text, encoding="utf-8")
        r = subprocess.run([a.python, str(HERE / "align_words.py"), str(seg), str(B / "_l.txt"), str(B / "_al.json"), "--shift", "-0.05"], capture_output=True)
        if r.returncode == 0:
            for w in json.loads((B / "_al.json").read_text(encoding="utf-8"))["words"]:
                words.append({"w": w["w"], "s": round(w["s"] + max(0, s0 - .05), 3), "e": round(w["e"] + max(0, s0 - .05), 3), "line": li})
            ok = True
    if not ok:
        ws = text.split(); step = (s1 - s0) / len(ws)
        words += [{"w": w, "s": round(s0 + j * step, 3), "e": round(s0 + (j + .8) * step, 3), "line": li} for j, w in enumerate(ws)]
(B / "words.json").write_text(json.dumps(words), encoding="utf-8")

# ---- music + sound effects keyed to the lines ----
n = len(voice) + SR; fx = np.zeros(n); mus = np.zeros(n)
def add(bus, x, at, g=1.):
    x = np.asarray(x, float); x = x if x.ndim == 1 else x.mean(1); i = int(max(0, at) * SR); j = min(n, i + len(x)); bus[i:j] += x[:j - i] * g
def G(kind): x, _ = sfx.GEN[kind](); return np.asarray(x, float) * sfx.GAIN.get(kind, .5)
LW = [[w for w in words if w["line"] == i] for i in range(len(spans))]
P0 = 1 if cfg.get("intro") else 0; PN = len(shots)
if P0:
    for w in LW[0]: add(fx, G("pop"), w["s"], .3)
    add(fx, G("riser"), LW[P0][0]["s"] - 1.0, .6); add(fx, G("click"), LW[P0][0]["s"] - .35, .9)
for k in range(PN):
    L = LW[P0 + k]; st = L[0]["s"] - .1
    if k: add(fx, G("whoosh"), st - .28, .8)
    kind = shots[k]["type"]
    if kind == "hook": add(fx, G("impact"), L[0]["s"], 1.1); add(fx, G("impact"), L[min(1, len(L) - 1)]["s"], .8); add(fx, G("whoosh"), L[min(2, len(L) - 1)]["s"] - .25, .7)
    if kind in ("detail", "end"): add(fx, G("impact"), L[0]["s"], 1.0)
    if kind == "colors":
        for j in range(1, len(cfg.get("colors", []))): add(fx, G("whoosh"), st + j * (L[-1]["s"] - st) / max(1, len(cfg["colors"])) - .1, .35)
        add(fx, G("impact"), L[-1]["s"], 1.0)
if cfg.get("outro"):
    L = LW[-1]; add(fx, G("whoosh"), L[0]["s"] - .3, .8)
    kw = [w for w in L if w["w"].strip(".,!?").lower() == cfg["outro"]["keyword"].lower()]
    if kw: add(fx, G("impact"), kw[0]["s"], 1.0); add(fx, G("pop"), kw[0]["s"] + .1, .6)
fx *= 10 ** (-14 / 20) / max(1e-9, np.abs(fx).max())
# a slow cinematic pulse under the promo only
tt = lambda d: np.arange(int(d * SR)) / SR; rng = np.random.default_rng(5); Bt = 60 / cfg.get("bpm", 100)
def kick(): x = tt(.6); f = 42 + 120 * np.exp(-x * 28); return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 5))
def hat(): x = tt(.06); y = np.diff(np.concatenate([[0], rng.standard_normal(len(x))])); return y * np.exp(-x * 80) * .3
def pad(f, d): x = tt(d); return sum(np.sin(2 * np.pi * f * m * x + m) / m for m in (1, 1.5, 2, 3)) * np.minimum(1, x / .4) * np.minimum(1, (d - x) / .6) * .25
m0, m1 = spans[P0][1] - .1, spans[P0 + PN - 1][2] + .5
add(mus, pad(55, m1 - m0), m0, .8); add(mus, pad(82.4, m1 - m0), m0, .5)
x, b = m0, 0
while x < m1: add(mus, kick(), x, .9 if b % 2 == 0 else .5); add(mus, hat(), x + Bt / 2, .5); x += Bt; b += 1
mus *= 10 ** (-19 / 20) / max(1e-9, np.abs(mus).max())
env = np.convolve(np.abs(np.concatenate([voice, np.zeros(n - len(voice))])), np.ones(2400) / 2400, "same"); duck = 1 - .55 * np.clip(env / (env.max() * .2 + 1e-9), 0, 1)
mix = np.zeros(n); mix[:len(voice)] += voice; mix += fx + mus * duck; mix = mix[:len(voice)]
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix *= .97 / np.abs(mix).max()
# loud on a phone speaker: gentle bus compression, then measured gain into a limiter (twice, the limiter takes some back)
save(mix, B / "_mix.wav", ["-af", "acompressor=threshold=-20dB:ratio=3:attack=4:release=150:makeup=2"])
mix = load(B / "_mix.wav")
for _ in range(2):
    save(mix * 10 ** ((LOUD + 1 - lufs(mix)) / 20), B / "_mix.wav", ["-af", "alimiter=limit=0.89:attack=1:release=50:level=disabled"])
    mix = load(B / "_mix.wav")
save(mix, B / "mix.mp3", ["-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k"])
for f in B.glob("_*"): f.unlink()

# ---- page ----
from PIL import Image
def d64(p):
    if p.suffix.lower() == ".png": return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
    im = Image.open(p).convert("RGB"); im.thumbnail((1200, 2200)); b = io.BytesIO(); im.save(b, "JPEG", quality=84)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
imgs = {p.stem: d64(p) for p in B.glob("*") if p.suffix.lower() in (".png", ".jpg") and p.stem in ("cutout", "hero", "detail1", "detail2") or p.stem.startswith("cw")}
page = (HERE.parent / "assets" / "promo_player.html").read_text(encoding="utf-8")
page = (page.replace("/*__WORDS__*/[]", json.dumps(words)).replace("/*__LOGOS__*/{}", json.dumps(imgs)).replace("/*__CFG__*/{}", json.dumps(cfg))
            .replace("/*__AUDIO__*/null", json.dumps("data:audio/mpeg;base64," + base64.b64encode((B / "mix.mp3").read_bytes()).decode()))
            .replace("/*__AUDIO_PATH__*/null", "null" if a.artifact else json.dumps(str((B / "mix.mp3").resolve())))
            .replace("<title>Product Promo</title>", f"<title>{cfg.get('brand', 'Product')} Promo</title>"))
(B / "reel.html").write_text(page, encoding="utf-8")
print(f"OK {B / 'reel.html'}  {len(page) / 1e6:.1f} MB, {words[-1]['e'] + 1.1:.1f} s, {len(words)} words")
