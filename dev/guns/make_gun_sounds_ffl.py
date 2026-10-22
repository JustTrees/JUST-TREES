"""2.64: gunshots from The Free Firearm Sound Library (CC0; models/source/Free Firearm Sound Library): two near-distance shots per gun
(the game picks one at random), each cut from its onset with the outdoor echo kept, faded, mono, peak-matched to the old ones.
Sniper = Mosin Nagant, assault rifle = AK-47, SMG = Carl Gustav M45 (9 mm), pistol = Walther PPQ (9 mm).
Usage: python3 dev/guns/make_gun_sounds_ffl.py   (writes sounds/guns/ffl_<gun>.mp3 and ffl_<gun>_b.mp3)"""
import os, subprocess, numpy as np
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "models", "source", "Free Firearm Sound Library")
OUT = os.path.join(REPO, "sounds", "guns")
SR = 44100
def load(rel):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(SRC, rel), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
def shots(x, thr=.35, gap=.3):
    e = np.abs(x).max(1); m = e.max(); out = []; last = -1e9
    for i in np.where(e > m * thr)[0]:
        if i - last > gap * SR: out.append(i)
        last = i
    return out
def first_rise(x, o):                                       # back up from the loud point to where the shot really starts
    e = np.abs(x).max(1); m = e[o]; i = o
    while i > 0 and o - i < int(.02 * SR) and e[i] > m * .03: i -= 1
    return max(0, i - int(.002 * SR))
def save(x, name, peak, mean_db):
    x = x.mean(1)
    n = int(.5 * SR); x[-n:] *= np.linspace(1, 0, n) ** 2        # fade out the tail
    x = x / max(np.abs(x).max(), 1e-6)
    lo, hi = 1.0, 60.0                                           # these recordings are a sharp crack and quiet body: soft-saturate until as loud as the old ones (mean level)
    for _ in range(30):
        g = (lo * hi) ** .5; y = np.tanh(g * x) / np.tanh(g); db = 20 * np.log10(np.sqrt(np.mean(y * y)) + 1e-9)
        lo, hi = (g, hi) if db < mean_db else (lo, g)
    x = y * peak
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "96k", os.path.join(OUT, name + ".mp3")],
                   input=np.clip(x, -1, 1).astype(np.float32).tobytes(), check=True)
GUNS = {  # name: (recording, keep seconds, peak, mean loudness dB like the old sounds)
    "sniper": ("Mosin Nagant/M_21P.wav", 2.0, .95, -20.5),
    "ar": ("AK-47/C_28P.wav", 1.6, .9, -21.5),
    "smg": ("Carl Gustav M45/G_31P.wav", 1.5, .85, -23),
    "pistol": ("Walther PPQ/X_39P.wav", 1.5, .85, -23),
}
for g, (rel, keep, peak, mdb) in GUNS.items():
    x = load(rel); on = shots(x)
    for k, suf in enumerate(["", "_b"]):
        o = first_rise(x, on[k]); end = min(o + int(keep * SR), on[k + 1] - int(.05 * SR) if k + 1 < len(on) else len(x))
        save(x[o:end], "ffl_" + g + suf, peak, mdb); print(g + suf, rel, round(o / SR, 2), "s,", round((end - o) / SR, 2), "s long")
