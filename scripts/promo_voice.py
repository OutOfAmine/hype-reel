#!/usr/bin/env python3
"""The promo's AI voice-over, one wav per shot line, from open-source models that run on your machine.

Usage: python promo_voice.py promo.json [--engine kokoro|chatterbox] [--voice af_heart] [--takes 3]

kokoro (default, CPU is fine; pip install "kokoro>=0.9.4" soundfile): clear, steady voices.
  Female: af_heart (warm), af_nicole (soft, whispery), af_bella. Male: am_onyx (deep), am_fenrir, am_michael.
chatterbox (pip install chatterbox-tts "setuptools<81"; an NVIDIA GPU makes it fast): emotional, punchy delivery.
  It clones the Kokoro voice above and acts it out with `voice.exaggeration` (0.5 calm .. 0.9 intense).
Write pauses into the lines with "..." ("So light... you'll forget you're wearing them.").
Writes <promo dir>/build/voice/<shot>_<take>.wav; promo_build.py picks take 0 unless `voice.takes` says otherwise.
"""
import argparse, json, pathlib
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("promo")
ap.add_argument("--engine"); ap.add_argument("--voice"); ap.add_argument("--takes", type=int)
a = ap.parse_args()
cfg_path = pathlib.Path(a.promo).resolve(); cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
vc = cfg.get("voice", {})
engine, voice = a.engine or vc.get("engine", "kokoro"), a.voice or vc.get("voice", "af_heart")
takes = a.takes or (3 if engine == "chatterbox" else 1)
lines = [s["line"] for s in cfg["shots"]]
out = cfg_path.parent / "build" / "voice"; out.mkdir(parents=True, exist_ok=True)
for f in out.glob("*.wav"): f.unlink()

import soundfile as sf
from kokoro import KPipeline
kp = KPipeline(lang_code="b" if voice[:1] == "b" else "a", repo_id="hexgrad/Kokoro-82M")
ref = []
for i, t in enumerate(lines):
    x = np.concatenate([np.asarray(c.audio) for c in kp(t, voice=voice, speed=vc.get("speed", .92))])
    ref += [x, np.zeros(int(.2 * 24000))]
    if engine == "kokoro": sf.write(out / f"{i:02d}_0.wav", x, 24000)
print("kokoro", voice)

if engine == "chatterbox":
    import torch, torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    refp = out / "_ref.wav"; sf.write(refp, np.concatenate(ref), 24000)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    m = ChatterboxTTS.from_pretrained(device=dev)
    ex = vc.get("exaggeration", .9); cw = vc.get("cfg_weight", .3)
    for i, t in enumerate(lines):
        for k in range(takes):
            torch.manual_seed(100 * i + k)
            ta.save(str(out / f"{i:02d}_{k}.wav"), m.generate(t, audio_prompt_path=str(refp), exaggeration=ex, cfg_weight=cw).cpu(), m.sr)
        print("chatterbox line", i + 1, "/", len(lines), flush=True)
    refp.unlink()
print("OK", out)
