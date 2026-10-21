"""2.02: the pterosaur (a Quetzalcoatlus: huge wings, long stiff neck, giant beak, small crest, no front feet, legs trailing in flight),
built from scratch in the Quaternius style the dinosaurs use: faceted low-poly, flat colours, a little softened so it's less boxy.
Its own skeleton and moves (Flying = flapping, Glide, Attack = the dive with wings swept back and beak open, Death).
Writes the same "QDN1" file the dinosaurs use.   Usage: python3 dev/dinos/make_ptero.py models/dinos/ptero.bin"""
import sys, json, struct, math
import numpy as np

# ---------------- colours (pictures: rusty-brown wings, grey-brown neck, a pale beak with a dark tip, a red crest)
COL = {"body": (0x6a, 0x4a, 0x3e), "neck": (0x7c, 0x5f, 0x50), "head": (0x8c, 0x6c, 0x5a), "beak": (0xc8, 0xb3, 0x8a), "tip": (0x3c, 0x32, 0x2a),
       "crest": (0xb0, 0x46, 0x36), "wingT": (0x6e, 0x3a, 0x2c), "wingB": (0xc8, 0x9c, 0x82), "arm": (0x5e, 0x40, 0x34), "eye": (0x12, 0x10, 0x10), "leg": (0x5a, 0x42, 0x38)}

# ---------------- bones: all with no rest rotation (frames line up with the world), so a key is a plain rotation
BONES = [  # name, parent, world position (x right, y up, z forward; metres, the animal flying level)
    ("Body", -1, (0, 0, 0)), ("Neck1", 0, (0, .12, .55)), ("Neck", 1, (0, .95, 1.75)), ("Head", 2, (0, 1.55, 2.85)), ("Jaw", 3, (0, 1.42, 3.05)),
    ("ShoulderL", 0, (.22, .12, .38)), ("ElbowL", 5, (1.35, .2, .3)), ("WristL", 6, (2.55, .22, .45)), ("FingerL", 7, (3.9, .2, .0)), ("TipL", 8, (5.35, .15, -.55)),
    ("ShoulderR", 0, (-.22, .12, .38)), ("ElbowR", 10, (-1.35, .2, .3)), ("WristR", 11, (-2.55, .22, .45)), ("FingerR", 12, (-3.9, .2, .0)), ("TipR", 13, (-5.35, .15, -.55)),
    ("LegL", 0, (.16, -.1, -.45)), ("LegR", 0, (-.16, -.1, -.45))]
BI = {b[0]: i for i, b in enumerate(BONES)}
BPOS = np.array([b[2] for b in BONES], float)

tris = []   # each: [(p, colour, [(bone, w)...]) x3]
def add(a, b, c, col, wa, wb=None, wc=None):
    tris.append([(np.array(a, float), col, wa), (np.array(b, float), col, wb or wa), (np.array(c, float), col, wc or wa)])

def ring(c, ax, up, rx, ry, n, rot=0.0):
    ax = np.array(ax, float); ax /= np.linalg.norm(ax); up = np.array(up, float); up -= ax * up.dot(ax); up /= np.linalg.norm(up); rt = np.cross(up, ax)
    return [np.array(c) + rt * math.cos(2 * math.pi * k / n + rot) * rx + up * math.sin(2 * math.pi * k / n + rot) * ry for k in range(n)]

def loft(rings, cols, wts, cap0=True, cap1=True):
    """rings: list of point lists (same count), cols: colour per ring band, wts: skin weights per ring"""
    n = len(rings[0])
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(n):
            k2 = (k + 1) % n
            add(A[k], B[k], B[k2], cols[i], wts[i], wts[i + 1], wts[i + 1]); add(A[k], B[k2], A[k2], cols[i], wts[i], wts[i + 1], wts[i])
    if cap0: c = sum(rings[0]) / n; [add(c, rings[0][(k + 1) % n], rings[0][k], cols[0], wts[0]) for k in range(n)]
    if cap1: c = sum(rings[-1]) / n; [add(c, rings[-1][k], rings[-1][(k + 1) % n], cols[-1], wts[-1]) for k in range(n)]

W = lambda *bw: list(bw)
def mix(b1, b2, t): return [(BI[b1], 1 - t), (BI[b2], t)] if 0 < t < 1 else [(BI[b2 if t >= 1 else b1], 1.0)]

# ---------------- body: small, a little keel under the chest
body = [(-.75, .0, .06, .06), (-.55, .02, .16, .15), (-.2, .04, .25, .24), (.15, .06, .27, .27), (.45, .1, .22, .23), (.62, .14, .15, .16)]
loft([ring((0, y, z), (0, 0, 1), (0, 1, 0), rx, ry, 12, math.pi / 12) for z, y, rx, ry in body], ["body"] * 6, [W((BI["Body"], 1))] * 6)
# ---------------- the neck: long and stiff, up and forward
neck_pts = [(0, .12, .55), (0, .3, .8), (0, .45, 1.05), (0, .63, 1.3), (0, .8, 1.55), (0, .97, 1.82), (0, 1.12, 2.1), (0, 1.26, 2.36), (0, 1.38, 2.6), (0, 1.52, 2.85)]
rad = [.15, .135, .12, .11, .1, .095, .09, .087, .085, .1]
rings, wts = [], []
for i, p in enumerate(neck_pts):
    q = neck_pts[min(i + 1, len(neck_pts) - 1)]; o = neck_pts[max(i - 1, 0)]; ax = np.array(q) - np.array(o)
    rings.append(ring(p, ax, (0, 1, 0), rad[i], rad[i] * 1.1, 10)); t = i / (len(neck_pts) - 1)
    wts.append(mix("Neck1", "Neck", t * 2) if t < .5 else mix("Neck", "Head", (t - .5) * 2.2))
loft(rings, ["neck"] * len(rings), wts, cap0=False, cap1=False)
# ---------------- the head: skull, the giant beak (upper and lower), a small crest, eyes
H, J = W((BI["Head"], 1)), W((BI["Jaw"], 1))
skull = [(2.6, 1.56, .12, .16), (2.8, 1.61, .17, .22), (3.0, 1.61, .16, .21), (3.2, 1.55, .12, .16)]
loft([ring((0, y, z), (0, 0, 1), (0, 1, 0), rx, ry, 10) for z, y, rx, ry in skull], ["head"] * 4, [H] * 4, cap1=False)
# upper beak: from the skull, long and straight, pointing a little down; the last part dark
up_b = [(3.2, 1.57, .11, .14), (3.6, 1.49, .085, .1), (4.1, 1.39, .06, .065), (4.55, 1.29, .035, .035), (4.95, 1.21, .012, .012)]
loft([ring((0, y, z), (0, -.2, 1), (0, 1, 0), rx, ry, 8, math.pi / 8) for z, y, rx, ry in up_b], ["head", "beak", "beak", "tip"], [H] * 5, cap0=False)
# lower jaw: a long thin blade under it, on its own bone so the beak opens
lo_b = [(3.05, 1.42, .09, .06), (3.6, 1.35, .068, .048), (4.1, 1.27, .045, .034), (4.5, 1.19, .025, .02), (4.85, 1.12, .01, .008)]
loft([ring((0, y, z), (0, -.2, 1), (0, 1, 0), rx, ry, 6, math.pi / 6) for z, y, rx, ry in lo_b], ["head", "beak", "beak", "tip"], [J] * 5)
# crest: a thin swept-back blade on top of the skull, both sides
c0, c1, c2, c3 = (0, 1.78, 3.05), (0, 1.84, 2.72), (0, 2.3, 2.3), (0, 1.7, 2.6)
for s in (-1, 1):
    o = np.array((s * .025, 0, 0)); P4 = [np.array(c) + o for c in (c0, c1, c2, c3)]
    if s > 0: add(P4[0], P4[1], P4[2], "crest", H); add(P4[0], P4[2], P4[3], "crest", H)
    else: add(P4[0], P4[2], P4[1], "crest", H); add(P4[0], P4[3], P4[2], "crest", H)
for a, b in ((c0, c1), (c1, c2), (c2, c3), (c3, c0)):   # the blade's edges
    a1, b1 = np.array(a) + (.025, 0, 0), np.array(b) + (.025, 0, 0); a2, b2 = np.array(a) - (.025, 0, 0), np.array(b) - (.025, 0, 0)
    add(a1, a2, b2, "crest", H); add(a1, b2, b1, "crest", H)
for s in (-1, 1):   # eyes
    loft([ring((s * .16, 1.67, z), (s, 0, 0), (0, 1, 0), r, r, 6) for z, r in ((3.0, .001), (3.0, .04))], ["eye"], [H, H], cap0=False)
# ---------------- wings: the arm bones along the front edge, a big membrane behind (not too narrow), a claw at the wrist
def wing(s):
    sd = "L" if s > 0 else "R"
    lead = [BPOS[BI[n + sd]] for n in ("Shoulder", "Elbow", "Wrist", "Finger", "Tip")]
    names = ["Shoulder", "Elbow", "Wrist", "Finger", "Tip"]
    # the arm itself: a thin loft along the leading edge
    rr = [.1, .085, .07, .045, .015]
    rings, wts = [], []
    for i, p in enumerate(lead):
        q = lead[min(i + 1, 4)]; o = lead[max(i - 1, 0)]
        rings.append(ring(p, q - o, (0, 1, 0), rr[i], rr[i] * .8, 7)); wts.append(W((BI[names[i] + sd], 1)))
    loft(rings, ["arm"] * 5, wts, cap0=False)
    # membrane: rows from the leading edge back to the trailing edge (which sweeps from the wing tip in to the hips)
    trail = [np.array((s * .3, .05, -.62)), np.array((s * 1.3, .1, -1.25)), np.array((s * 2.45, .12, -1.35)), np.array((s * 3.7, .1, -.95)), lead[4] + np.array((0, 0, -.02))]
    rows = 7
    grid = [[lead[i] * (1 - r / rows) + trail[i] * (r / rows) for i in range(5)] for r in range(rows + 1)]
    def wt(i, r):
        b = [(BI[names[i] + sd], 1.0 - .55 * (r / rows) * (1 if i < 2 else .3))]
        if i < 2: b.append((BI["Body"], .55 * (r / rows)))
        elif r: b.append((BI[names[i - 1] + sd], .3 * .55 * (r / rows)))
        return b
    # a gentle camber: the middle of the membrane sits a touch lower
    for r in range(1, rows): grid[r] = [p + np.array((0, -.05 * math.sin(math.pi * r / rows), 0)) for p in grid[r]]
    for r in range(rows):
        for i in range(4):
            a, b, c, d = grid[r][i], grid[r][i + 1], grid[r + 1][i + 1], grid[r + 1][i]
            wa, wb, wc, wd = wt(i, r), wt(i + 1, r), wt(i + 1, r + 1), wt(i, r + 1)
            top = (s > 0)
            for (p1, p2, p3, w1, w2, w3) in ((a, b, c, wa, wb, wc), (a, c, d, wa, wc, wd)):
                if top: add(p1, p3, p2, "wingB", w1, w3, w2); add(p1, p2, p3, "wingT", w1, w2, w3)
                else: add(p1, p2, p3, "wingB", w1, w2, w3); add(p1, p3, p2, "wingT", w1, w3, w2)
    # a little claw at the wrist (the wing's thumb), pointing forward
    wr = lead[2]; cl = [ring(wr + np.array((0, .02, .04)), (0, -.2, 1), (0, 1, 0), .03, .03, 4), ring(wr + np.array((0, -.03, .2)), (0, -.2, 1), (0, 1, 0), .004, .004, 4)]
    loft(cl, ["tip"], [W((BI["Wrist" + sd], 1))] * 2, cap1=False)
wing(1); wing(-1)
# ---------------- legs: thin, trailing behind
for s, sd in ((1, "L"), (-1, "R")):
    lp = [(s * .16, -.08, -.45), (s * .2, -.18, -.95), (s * .2, -.16, -1.35), (s * .2, -.12, -1.5)]
    loft([ring(p, (0, -.1, -1), (0, 1, 0), r, r, 5) for p, r in zip(lp, (.07, .045, .03, .04))], ["leg"] * 4, [W((BI["Leg" + sd], 1))] * 4)

# ---------------- normals: faces, softened a little toward the shared normal (less boxy, the same triangles)
P = np.array([[v[0] for v in t] for t in tris])          # (n, 3, 3)
fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); area = np.linalg.norm(fn, axis=1, keepdims=True); fnu = fn / np.maximum(area, 1e-9)
acc = {}
for ti in range(len(tris)):
    for k in range(3):
        key = (tuple(np.round(P[ti, k] * 200).astype(int)), tris[ti][k][1] == "wingB")
        acc[key] = acc.get(key, 0) + fn[ti]
SOFT = .35
# ---------------- moves (rotations of the bones; times in seconds)
def qa(axis, ang):
    axis = np.array(axis, float); axis /= np.linalg.norm(axis); s = math.sin(ang / 2); return (axis[0] * s, axis[1] * s, axis[2] * s, math.cos(ang / 2))
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
def wingpose(flap, sweep, fold, twist=0):
    """flap: + = wings up; sweep: + = swept back; fold: + = elbow/wrist folded in. Returns {bone: quat} for both wings."""
    out = {}
    for s, sd in ((1, "L"), (-1, "R")):
        out["Shoulder" + sd] = qmul(qa((0, 1, 0), s * sweep), qmul(qa((0, 0, 1), s * flap), qa((1, 0, 0), twist)))
        out["Elbow" + sd] = qmul(qa((0, 1, 0), s * fold * .6), qa((0, 0, 1), s * flap * .25))
        out["Wrist" + sd] = qmul(qa((0, 1, 0), -s * fold * 1.1), qa((0, 0, 1), s * flap * .3))
        out["Finger" + sd] = qmul(qa((0, 1, 0), s * fold * .5), qa((0, 0, 1), s * flap * .35))
    return out
I = (0, 0, 0, 1)
def clip(name, dur, frames):
    """frames: list of (t, {bone: quat}); missing bones stay at rest"""
    names = sorted({b for _, d in frames for b in d})
    return {"n": name, "d": dur, "tracks": {b: [(t, d.get(b, I)) for t, d in frames] for b in names}}
CLIPS = []
fl = []                                                     # Flying: big slow flaps, the neck steady, the legs swinging a touch
for k in range(13):
    t = k / 12 * 1.4; ph = 2 * math.pi * k / 12; f = .55 * math.sin(ph) + .05
    d = wingpose(f, -.08 * math.cos(ph), .18 * max(0, math.sin(ph)), twist=-.12 * math.cos(ph))
    d["Neck1"] = qa((1, 0, 0), .04 * math.sin(ph + 1)); d["LegL"] = d["LegR"] = qa((1, 0, 0), .08 * math.sin(ph))
    fl.append((t, d))
CLIPS.append(clip("Flying", 1.4, fl))
gl = []                                                     # Glide: wings locked out, a slow sway
for k in range(9):
    t = k / 8 * 3.2; ph = 2 * math.pi * k / 8
    d = wingpose(.08 + .03 * math.sin(ph), .02, 0, twist=.02 * math.sin(ph)); d["Neck1"] = qa((0, 1, 0), .06 * math.sin(ph)); d["Head"] = qa((0, 1, 0), .08 * math.sin(ph + .6))
    gl.append((t, d))
CLIPS.append(clip("Glide", 3.2, gl))
at = []                                                     # Attack: the dive: wings swept back, neck out, the beak snapping
for k in range(9):
    t = k / 8 * .9; ph = 2 * math.pi * k / 8
    d = wingpose(.1 + .05 * math.sin(ph * 2), .55, .65, twist=.15); d["Neck1"] = qa((1, 0, 0), .2); d["Neck"] = qa((1, 0, 0), .15); d["Head"] = qa((1, 0, 0), .25)
    d["Jaw"] = qa((1, 0, 0), .25 + .2 * math.sin(ph * 2)); d["LegL"] = d["LegR"] = qa((1, 0, 0), -.15)
    at.append((t, d))
CLIPS.append(clip("Attack", .9, at))
de = []                                                     # Death: wings crumple, the neck goes limp
for k in range(7):
    t = k / 6 * 1.4; e = min(1, k / 6 * 1.2)
    d = wingpose(-.4 * e + .3 * (1 - e), .7 * e, 1.0 * e, twist=.3 * e); d["Neck1"] = qa((1, 0, 0), .5 * e); d["Neck"] = qa((1, 0, 0), .6 * e); d["Head"] = qa((1, 0, 0), .5 * e)
    d["Jaw"] = qa((1, 0, 0), .3 * e); d["LegL"] = qa((1, 0, 0), .5 * e); d["LegR"] = qa((1, 0, 0), .3 * e)
    de.append((t, d))
CLIPS.append(clip("Death", 1.4, de))

# ---------------- pack it (the same layout the game reads for the dinosaurs)
n = len(tris) * 3
pos = P.reshape(-1, 3); mn = pos.min(0); mx = pos.max(0)
pq = np.round((pos - mn) / np.maximum(mx - mn, 1e-9) * 65535 - 32768).astype(np.int16)
nq = np.zeros((n, 4), np.int8); col = np.zeros((n, 4), np.uint8); si = np.zeros((n, 4), np.uint8); sw = np.zeros((n, 4), np.uint8)
for ti, t in enumerate(tris):
    for k, (p, c, w) in enumerate(t):
        vi = ti * 3 + k; key = (tuple(np.round(p * 200).astype(int)), c == "wingB")
        sm = acc[key] / max(np.linalg.norm(acc[key]), 1e-9); nn = fnu[ti] * (1 - SOFT) + sm * SOFT; nn /= max(np.linalg.norm(nn), 1e-9)
        nq[vi, :3] = np.round(nn * 127).astype(np.int8); col[vi] = (*COL[c], 255)
        ws = sorted(w, key=lambda x: -x[1])[:4]; tot = sum(x[1] for x in ws) or 1; q = [round(x[1] / tot * 255) for x in ws]; q[0] += 255 - sum(q)
        for j, (b, _) in enumerate(ws): si[vi, j] = b; sw[vi, j] = q[j]
parts, off = [], 0
def put(arr):
    global off
    b = arr.tobytes(); o = off; parts.append(b); off += len(b); pad = (4 - off % 4) % 4
    if pad: parts.append(b"\0" * pad); off += pad
    return o
nodes = [{"n": b[0], "p": b[1], "b": 1, "t": [*(np.array(b[2]) - (BPOS[b[1]] if b[1] >= 0 else 0)).round(6).tolist(), 0, 0, 0, 1, 1, 1, 1]} for b in BONES]
inv = []
for b in BONES:
    m = np.eye(4); m[:3, 3] = -np.array(b[2]); inv.append(m.T.reshape(-1).round(6).tolist())   # column-major, like three.js
M = {"n": n, "bb": [mn.tolist(), mx.tolist()], "p": -1, "t": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1], "bind": np.eye(4).reshape(-1).tolist(), "inv": inv, "bones": list(range(len(BONES))),
     "pos": put(pq), "nrm": put(nq), "col": put(col), "si": put(si), "sw": put(sw)}
clips = []
for c in CLIPS:
    tr = []
    for b, keys in c["tracks"].items():
        ts = np.array([k[0] for k in keys], np.float32); qs = np.array([k[1] for k in keys], float)
        for i in range(1, len(qs)):
            if np.dot(qs[i], qs[i - 1]) < 0: qs[i] = -qs[i]
        tr.append({"nd": BI[b], "pr": "q", "nk": len(keys), "t": put(ts), "v": put(np.round(np.clip(qs, -1, 1) * 32767).astype(np.int16))})
    clips.append({"n": c["n"], "d": c["d"], "tr": tr})
js = json.dumps({"v": 1, "nodes": nodes, "mesh": M, "clips": clips}).encode(); js += b" " * ((4 - len(js) % 4) % 4)
open(sys.argv[1], "wb").write(b"QDN1" + struct.pack("<I", len(js)) + js + b"".join(parts))
print("triangles", len(tris), "span m", round(mx[0] - mn[0], 2), "length m", round(mx[2] - mn[2], 2), "bytes", 8 + len(js) + off)
