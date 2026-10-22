"""Bigfoot's "eb-le-bla-blbl" as he runs past: a made-up gibbering voice (formant synthesis), written out as an mp3."""
import numpy as np, subprocess, sys, wave
SR = 22050
rng = np.random.default_rng(3)
# (kind, ms, F1, F2, F3): v = vowel, b = lips shut, l = tongue up
seq = [("v", 130, 560, 1750, 2500), ("b", 38, 250, 800, 2200), ("l", 45, 360, 1150, 2600), ("v", 95, 540, 1850, 2550),
       ("b", 34, 250, 800, 2200), ("l", 40, 360, 1100, 2600), ("v", 120, 780, 1220, 2450), ("b", 34, 250, 800, 2200),
       ("l", 40, 360, 1100, 2600), ("v", 70, 620, 1150, 2400), ("l", 38, 360, 1050, 2600), ("v", 65, 600, 1120, 2400),
       ("l", 36, 360, 1050, 2600), ("v", 60, 580, 1100, 2400), ("b", 30, 250, 800, 2200), ("v", 190, 640, 1080, 2350)]
N = int(sum(s[1] for s in seq) / 1000 * SR) + SR // 3
F = np.zeros((N, 3)); A = np.zeros(N); i = 0
for k, ms, f1, f2, f3 in seq:
    n = int(ms / 1000 * SR); F[i:i + n] = (f1, f2, f3); A[i:i + n] = {"v": 1, "b": .0, "l": .28}[k]; i += n
F[i:] = F[i - 1]; A[i:] = 0
sm = lambda x, w: np.convolve(x, np.ones(w) / w, "same")
for j in range(3): F[:, j] = sm(F[:, j], int(.018 * SR))       # the mouth moves smoothly between shapes
A = sm(A, int(.008 * SR))
t = np.arange(N) / SR; T = i / SR
f0 = 150 + 70 * np.sin(np.pi * np.clip(t / T, 0, 1)) ** 1.5 - 45 * np.clip((t - T * .7) / (T * .3), 0, 1) + 6 * np.sin(2 * np.pi * 5.5 * t) + rng.normal(0, 3, N).cumsum() * .02
ph = np.cumsum(f0 / SR); saw = 2 * (ph % 1) - 1
src = saw + .35 * (2 * ((ph / 2) % 1) - 1)                    # a growly undertone an octave down
src *= 1 + .4 * np.sin(2 * np.pi * 34 * t)                    # rough, creature-like
src += rng.normal(0, .25, N)                                   # breath
out = np.zeros(N)
for j, (bw, g) in enumerate(((90, 1.0), (120, .55), (180, .3))):
    y1 = y2 = 0.0; y = np.zeros(N)
    for n in range(N):
        r = np.exp(-np.pi * bw / SR); c = 2 * r * np.cos(2 * np.pi * F[n, j] / SR)
        v = (1 - r) * src[n] + c * y1 - r * r * y2; y[n] = v; y2, y1 = y1, v
    out += g * y
out *= A
env = np.clip(t / .02, 0, 1) * np.clip((T + .12 - t) / .2, 0, 1)
out *= env
# a little room
d = int(.045 * SR); out[d:] += .25 * out[:-d]; d2 = int(.11 * SR); out[d2:] += .15 * out[:-d2]
out /= np.abs(out).max() * 1.15
w = wave.open(sys.argv[1] + ".wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", sys.argv[1] + ".wav", "-b:a", "64k", sys.argv[1] + ".mp3"], check=True)
print("ok", round(N / SR, 2), "s")
