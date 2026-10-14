"""2.04: the bows for stars 2-5 from Quaternius' Medieval Weapons Pack (CC0, models/source/Medieval_Weapons_Pack_by_Quaternius.zip):
2 = Bow_Wooden2, 3 = Bow_Wooden, 4 = Bow_Golden, 5 = Bow_Evil (1 star is the game's own bow). The pack's string is left out (the game draws
its own, which bends when you draw). Each bow is laid into the game's bow frame: y up, the tips at +-0.8 m, the string line at the game's
brace (z = tip), the back of the grip at z = -0.02, so the draw feels exactly the same. Flat colours (the pack's), per triangle.
Writes models/bows/bow_<star>.json = {"p": [x,y,z,...] (mm, whole triangles), "c": [r,g,b,...] (0-255 linear, per triangle)}.
Usage: python3 dev/bows/make_bows.py <pack zip> <out dir>"""
import sys, os, io, json, zipfile, math
import numpy as np
LEN, HALF = 1.6, .8
def tipz(t=1.0): return .012 + .25 * t ** 1.55 - .05 * max(0, (t - .7) / .3) ** 2     # the game's bowTipZ()
TZ = tipz()
z = zipfile.ZipFile(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
for star, name in ((2, "Bow_Wooden2"), (3, "Bow_Wooden"), (4, "Bow_Golden"), (5, "Bow_Evil")):
    mtl, cur = {}, None
    for l in z.read(f"OBJ/{name}.mtl").decode().splitlines():
        p = l.split()
        if p and p[0] == "newmtl": cur = p[1]
        elif p and p[0] == "Kd": mtl[cur] = [float(x) for x in p[1:4]]
    V, F, cm = [], [], None
    for l in z.read(f"OBJ/{name}.obj").decode().splitlines():
        p = l.split()
        if not p: continue
        if p[0] == "v": V.append([float(x) for x in p[1:4]])
        elif p[0] == "usemtl": cm = p[1]
        elif p[0] == "f":
            idx = [int(x.split("/")[0]) - 1 for x in p[1:]]
            for k in range(1, len(idx) - 1): F.append(([idx[0], idx[k], idx[k + 1]], cm))
    V = np.array(V)
    sv = sorted({i for f, m in F if m == "White" for i in f}); xs = V[sv, 0].mean() if sv else V[:, 0].max()   # where the pack's string runs
    F = [(f, m) for f, m in F if m != "White"]
    used = sorted({i for f, _ in F for i in f}); y0, y1 = V[used, 1].min(), V[used, 1].max(); grip = V[used][np.abs(V[used, 1]) < (y1 - y0) * .08]
    xb = grip[:, 0].min()                                               # the back of the grip
    sy = LEN / (y1 - y0) * .985; sx = (TZ + .02) / (xs - xb)            # (flattened front-to-back so the brace is the game's)
    P, C = [], []
    for f, m in F:
        for i in f: x, y, zz = V[i]; P += [round(zz * sy * 1000), round(y * sy * 1000), round(((x - xb) * sx - .02) * 1000)]   # pack x (toward the string) -> game z
        C += [int(round(min(1, c) * 255)) for c in mtl.get(m, [.5, .5, .5])]
    # (the pack's x -> z swap mirrors it: put the winding back)
    P = np.array(P).reshape(-1, 3, 3)[:, [0, 2, 1]].reshape(-1).tolist()
    json.dump({"p": P, "c": C, "src": name}, open(os.path.join(out, f"bow_{star}.json"), "w"), separators=(",", ":"))
    print(star, name, len(F), "triangles", "depth scale", round(sx / sy, 2))
