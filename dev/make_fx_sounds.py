"""2.64: hit and kill sounds from Kenney's CC0 packs (models/source/Kenney Interface Sounds, Kenney Impact Sounds) into sounds/fx/*.mp3,
peak-normalized (how loud each plays is set in the game). Usage: python3 dev/make_fx_sounds.py"""
import os, subprocess, numpy as np
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(REPO, "models", "source", "Kenney Interface Sounds", "Audio")
IM = os.path.join(REPO, "models", "source", "Kenney Impact Sounds")
OUT = os.path.join(REPO, "sounds", "fx"); os.makedirs(OUT, exist_ok=True)
SR = 44100
PICK = {                                  # game name: source file
    "hit_metal_0": (IM, "impactMetal_light_000"), "hit_metal_1": (IM, "impactMetal_light_001"), "hit_metal_2": (IM, "impactMetal_light_002"),   # a sniper hit 150+: a metal ping
    "hit_clang": (IM, "impactPlate_heavy_001"),                          # 250+: a heavy clang under it
    "hit_bell": (IM, "impactBell_heavy_001"),                            # 350+: a big bell
    "sparkle": (UI, "glass_004"),                                        # 350+: a bright glassy shimmer
    "kill_1": (UI, "confirmation_002"),                                  # a sniper kill 150+
    "kill_2a": (UI, "maximize_005"), "kill_2b": (UI, "confirmation_004"), "kill_bell": (IM, "impactBell_heavy_002"),   # 250+
    "kill_3": (UI, "select_006"), "kill_3b": (UI, "maximize_004"), "big_bell": (IM, "impactBell_heavy_000"),           # 350+
}
for name, (d, f) in PICK.items():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(d, f + ".ogg"), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy(); x *= .9 / max(np.abs(x).max(), 1e-6)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "96k", os.path.join(OUT, name + ".mp3")], input=x.tobytes(), check=True)
    print(name, "<-", f, round(len(x) / SR, 2), "s")
