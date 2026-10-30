#!/usr/bin/env python3
"""Word-by-word caption timing for a recorded voice-over (forced alignment, MMS_FA / wav2vec2).

Usage: python align_words.py voice.wav lines.txt words.json [--shift -0.08]

lines.txt: one spoken line per row, written as it was SAID (any Latin-script language, Darija with 3/7/9 works).
A word can carry a phonetic hint for the aligner after '|', e.g. "Effects,|afekt" or "3D,|trwadi".
Out: {"duration", "words": [{w, s, e, line}]} -> put "words" in reel.json and set each scene's dur to its line.
Needs: pip install torch torchaudio (a GPU is used when there is one).
"""
import argparse, json, re
import torch, torchaudio
from torchaudio.pipelines import MMS_FA as bundle

ap = argparse.ArgumentParser()
ap.add_argument("wav"); ap.add_argument("lines"); ap.add_argument("out")
ap.add_argument("--shift", type=float, default=-0.08, help="MMS marks onsets a little late; captions read better slightly early")
a = ap.parse_args()

words = []
for li, ln in enumerate(l for l in open(a.lines, encoding="utf-8").read().splitlines() if l.strip()):
    for tok in ln.split():
        shown, _, say = tok.partition("|")
        words.append({"w": shown, "say": say or shown, "line": li})

def norm(s):
    s = s.lower()
    for k, v in {"é": "e", "è": "e", "ê": "e", "à": "a", "â": "a", "ç": "s", "ô": "o", "î": "i", "û": "u", "3": "a", "7": "h", "9": "q"}.items():
        s = s.replace(k, v)
    return re.sub(r"[^a-z]", "", s) or "a"

dev = "cuda" if torch.cuda.is_available() else "cpu"
wave, sr = torchaudio.load(a.wav)
wave = torchaudio.functional.resample(wave.mean(0, keepdim=True), sr, bundle.sample_rate).to(dev)
model = bundle.get_model(with_star=False).to(dev)
with torch.inference_mode():
    em, _ = model(wave)
    spans = bundle.get_aligner()(em[0], bundle.get_tokenizer()([norm(w["say"]) for w in words]))
ratio = wave.size(1) / em.size(1) / bundle.sample_rate
out = [{"w": w["w"], "s": round(max(0, sp[0].start * ratio + a.shift), 3), "e": round(max(0, sp[-1].end * ratio + a.shift), 3), "line": w["line"]} for w, sp in zip(words, spans)]
json.dump({"duration": round(wave.size(1) / bundle.sample_rate, 3), "words": out}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
for li in sorted({w["line"] for w in out}):
    ws = [w for w in out if w["line"] == li]
    print(f"{ws[0]['s']:6.2f}-{ws[-1]['e']:6.2f}  " + " ".join(w["w"] for w in ws))
