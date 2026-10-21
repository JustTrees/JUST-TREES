"""2.03: the animals the farm pack has nothing close to (birds, the turkey / roadrunner / heron, the seal, monkeys, Bigfoot and the Yeti),
built from scratch in the same faceted low-poly style. They keep the game's own moves (wing flaps, the monkey's swinging, the two-legged
walk): each model is skinned to the old animal's own moving parts (body, head, legs and knees, arms, wings), so the game's animation
drives it. Positions are the old animal's, in metres, standing at the root (x = its left, y up, z forward).
Usage: python3 dev/animals/build_rigged.py <out dir> [kind,kind,...]"""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from animal_lib import Model, rgb

OUT = sys.argv[1]; ONLY = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
PAL = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]      # bird colour slots the game fills in (main, patch, head, beak)

class Rig:
    def __init__(self, bones):
        self.B = {k: np.array(v, float) for k, v in bones.items()}; self.names = list(bones); self.T = []
    def w(self, b): return [(self.names.index(b), 1.0)] if isinstance(b, str) else [(self.names.index(n), x) for n, x in b]
    def tri(self, a, b, c, col, wa, wb=None, wc=None, out=None):
        a, b, c = (np.array(v, float) for v in (a, b, c)); wa = self.w(wa); wb = self.w(wb) if wb is not None else wa; wc = self.w(wc) if wc is not None else wa
        if out is not None:
            ce = (a + b + c) / 3; o = out(ce) if callable(out) else np.array(out, float)
            if np.cross(b - a, c - a).dot(ce - o) < 0: b, c, wb, wc = c, b, wc, wb
        self.T.append([(a, col, wa), (b, col, wb), (c, col, wc)])
    def loft(self, rings, cols, wts, centers, cap0=True, cap1=True):
        n = len(rings[0]); cols = cols if isinstance(cols, list) else [cols] * len(rings)
        for i in range(len(rings) - 1):
            A, B = rings[i], rings[i + 1]; o = (centers[i] + centers[i + 1]) / 2
            for k in range(n):
                k2 = (k + 1) % n; self.tri(A[k], B[k], B[k2], cols[i], wts[i], wts[i + 1], wts[i + 1], out=o); self.tri(A[k], B[k2], A[k2], cols[i], wts[i], wts[i + 1], wts[i], out=o)
        if cap0:
            c = sum(rings[0]) / n; o = centers[0] + (centers[0] - centers[1]) * -.3
            for k in range(n): self.tri(c, rings[0][(k + 1) % n], rings[0][k], cols[0], wts[0], out=o)
        if cap1:
            c = sum(rings[-1]) / n; o = centers[-1] + (centers[-1] - centers[-2]) * -.3
            for k in range(n): self.tri(c, rings[-1][k], rings[-1][(k + 1) % n], cols[-1], wts[-1], out=o)
    def tube(self, pts, radii, col, wts, sides=6, up=(0, 1, 0), sq=1.0, cap0=True, cap1=True, rot=0.0):
        pts = [np.array(p, float) for p in pts]; rings = []; wts = wts if isinstance(wts, list) else [wts] * len(pts)
        for i, p in enumerate(pts):
            ax = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]; r = radii[i]
            rings.append(ring(p, ax, up, r, r * sq, sides, rot))
        self.loft(rings, col, wts, pts, cap0, cap1)
    def ball(self, c, r, col, w, n=8, rows=4, sq=(1, 1, 1)):
        c = np.array(c, float); sq = np.array(sq, float); R = []
        for i in range(1, rows):
            a = math.pi * i / rows; R.append([c + np.array([math.cos(2 * math.pi * k / n) * math.sin(a), math.cos(a), math.sin(2 * math.pi * k / n) * math.sin(a)]) * r * sq for k in range(n)])
        top = c + np.array([0, r * sq[1], 0]); bot = c - np.array([0, r * sq[1], 0])
        for k in range(n): self.tri(top, R[0][(k + 1) % n], R[0][k], col, w, out=c)
        for i in range(len(R) - 1):
            for k in range(n): k2 = (k + 1) % n; self.tri(R[i][k], R[i][k2], R[i + 1][k2], col, w, out=c); self.tri(R[i][k], R[i + 1][k2], R[i + 1][k], col, w, out=c)
        for k in range(n): self.tri(bot, R[-1][k], R[-1][(k + 1) % n], col, w, out=c)
    def slab(self, poly, th, top, bot, w, edge=None, up=(0, 1, 0)):
        """a flat plate (a wing, a fin, a fan): poly is its outline, th its thickness along 'up'"""
        P = [np.array(p, float) for p in poly]; u = np.array(up, float) * th / 2; c = sum(P) / len(P); n = len(P)
        for k in range(1, n - 1):
            self.tri(P[0] + u, P[k] + u, P[k + 1] + u, top, w, out=c); self.tri(P[0] - u, P[k + 1] - u, P[k] - u, bot, w, out=c)
        for k in range(n):
            a, b = P[k], P[(k + 1) % n]; self.tri(a + u, a - u, b - u, edge or top, w, out=c); self.tri(a + u, b - u, b + u, edge or top, w, out=c)
    def save(self, path):
        pos, col, si, sw = [], [], [], []
        for t in self.T:
            for p, c, w in t:
                pos.append(p); col.append(rgb(c)); ws = sorted(w, key=lambda x: -x[1])[:4] + [(0, 0)] * 4
                si.append([x[0] for x in ws[:4]]); sw.append([x[1] for x in ws[:4]])
        nodes = [{"n": n, "p": -1, "t": [*self.B[n].tolist(), 0, 0, 0, 1, 1, 1, 1]} for n in self.names]
        m = Model(nodes, pos, col, si, sw); info = m.save(path); return info

def ring(c, ax, up, rx, ry, n, rot=0.0):
    ax = np.array(ax, float); ax /= max(np.linalg.norm(ax), 1e-9); up = np.array(up, float); up = up - ax * up.dot(ax)
    if np.linalg.norm(up) < 1e-6: up = np.array([0, 0, 1.0]) - ax * ax[2]
    up /= np.linalg.norm(up); rt = np.cross(up, ax)
    return [np.array(c, float) + rt * math.cos(2 * math.pi * k / n + rot) * rx + up * math.sin(2 * math.pi * k / n + rot) * ry for k in range(n)]

def zloft(R, secs, col, w, n=8, cap0=True, cap1=True):
    """a body along z: secs = (z, y, half width, half height)"""
    rings = [ring((0, y, z), (0, 0, 1), (0, 1, 0), rx, ry, n, math.pi / n) for z, y, rx, ry in secs]
    R.loft(rings, col, [w] * len(secs), [np.array((0, y, z)) for z, y, _, _ in secs], cap0, cap1)

def leg2(R, i, hip, knee, foot, r, col, colLow, toes=None, toeCol=None, x=0):
    """a two-bone leg: thigh on leg{i}, shin (and toes) on leg{i}k"""
    R.tube([hip, knee], [r[0], r[1]], col, f"leg{i}", sides=6); R.ball(knee, r[1] * 1.05, colLow, f"leg{i}k", n=6, rows=3)
    R.tube([knee, foot], [r[1], r[2]], colLow, f"leg{i}k", sides=6)
    if toes:
        f = np.array(foot, float)
        for d in toes: R.tube([f, f + np.array(d)], [r[2] * .8, r[2] * .3], toeCol or colLow, f"leg{i}k", sides=4)

KINDS = {}
def kind(name): return lambda f: KINDS.__setitem__(name, f) or f

# ---------------------------------------------------------------- birds (one shape, the game paints it per kind)
@kind("bird")
def bird():
    R = Rig({"body": (0, 0, 0), "wing0": (-.14, .04, 0), "wing1": (.14, .04, 0)})
    M, PT, HD, BK = PAL
    zloft(R, [(-.42, .0, .05, .04), (-.3, .0, .12, .1), (-.08, .0, .17, .14), (.18, .02, .15, .13), (.36, .05, .1, .1), (.44, .06, .07, .07)], M, "body", n=7)
    R.ball((0, .08, .5), .1, HD, "body", n=7, rows=4, sq=(.9, .95, 1.1))
    R.tube([(0, .06, .58), (0, .04, .67), (0, .01, .74)], [.035, .02, .004], BK, "body", sides=5)
    R.slab([(0, 0, -.3), (.14, 0, -.42), (.22, -.01, -.72), (0, -.01, -.66), (-.22, -.01, -.72), (-.14, 0, -.42)], .02, M, M, "body")   # the tail fan
    for i, s in ((0, -1), (1, 1)):
        x = lambda v: s * v
        poly = [(x(.1), .04, .14), (x(.6), .06, .16), (x(1.1), .05, .1), (x(1.42), .03, -.02), (x(1.42), .03, -.2), (x(1.05), .03, -.3), (x(.6), .03, -.32), (x(.1), .03, -.2)]
        if s < 0: poly = poly[::-1]
        R.slab(poly, .035, M, M, f"wing{i}")
        R.slab([(x(.5), .012, -.06), (x(.95), .012, -.04), (x(.95), .012, -.26), (x(.5), .012, -.28)][::(-1 if s < 0 else 1)], .012, PT, PT, f"wing{i}")   # the pale patch under the wing
        for f in range(4):                                       # finger feathers at the tip
            z = .02 - f * .07; a = (x(1.38), .03, z); R.slab([a, (x(1.72 - f * .03), .025, z - .03 - f * .02), (x(1.4), .03, z - .06)][::(-1 if s < 0 else 1)], .015, M, M, f"wing{i}")
    return R

# ---------------------------------------------------------------- ground birds
@kind("turkey")
def turkey():
    R = Rig({"body": (0, 0, 0), "head": (0, .86, .32), "leg0": (-.08, .44, 0), "leg0k": (-.08, .24, 0), "leg1": (.08, .44, 0), "leg1k": (.08, .24, 0)})
    br, br2 = 0x3a3028, 0x2a2420
    zloft(R, [(-.3, .58, .05, .05), (-.24, .56, .16, .17), (-.04, .55, .22, .24), (.14, .59, .18, .2), (.26, .68, .08, .08)], br, "body", n=8)
    c = np.array((0, .62, -.3))
    for k in range(9):                                           # the fan tail, banded, a pale rim
        a0, a1 = math.pi * k / 9, math.pi * (k + 1) / 9; p0 = c + np.array([math.cos(a0) * .42, math.sin(a0) * .42, -.02]); p1 = c + np.array([math.cos(a1) * .42, math.sin(a1) * .42, -.02])
        q0 = c + (p0 - c) * .85; q1 = c + (p1 - c) * .85
        R.slab([c, q0, q1], .025, 0x5a4430 if k % 2 else 0x4a3a2a, 0x4a3a2a, "body", up=(0, 0, 1)); R.slab([q0, p0, p1, q1], .025, 0xc8b090, 0xc8b090, "body", up=(0, 0, 1))
    R.tube([(0, .7, .24), (0, .79, .3), (0, .86, .32)], [.06, .04, .035], 0x8ab0d0, [[("body", 1)], [("body", .5), ("head", .5)], [("head", 1)]], sides=6)
    R.ball((0, .88, .34), .045, 0x7aa0c8, "head", n=6, rows=3)
    R.tube([(0, .88, .38), (0, .87, .43)], [.015, .003], 0xc8b088, "head", sides=4)
    R.tube([(0, .86, .37), (0, .8, .36)], [.016, .008], 0xc02828, "head", sides=4)                         # the wattle
    for i, s in ((0, -1), (1, 1)):
        R.ball((s * .1, .5, .02), .1, br2, f"leg{i}", n=6, rows=3, sq=(.8, 1.1, 1))
        leg2(R, i, (s * .08, .44, 0), (s * .08, .24, 0), (s * .08, .03, .02), (.035, .025, .015), br2, 0x9a7a6a, toes=[(0, -.02, .08), (.04, -.02, .06), (-.04, -.02, .06), (0, 0, -.04)])
    return R

@kind("roadrunner")
def roadrunner():
    R = Rig({"body": (0, 0, 0), "head": (0, .82, .33), "leg0": (-.06, .44, 0), "leg0k": (-.06, .24, 0), "leg1": (.06, .44, 0), "leg1k": (.06, .24, 0)})
    br, pale = 0x5a4632, 0xd8ccb4
    zloft(R, [(-.3, .56, .04, .04), (-.2, .56, .1, .11), (.02, .55, .14, .15), (.2, .6, .11, .11), (.3, .68, .05, .05)], [br, br, 0x6e5a42, br, br], "body", n=7)
    R.ball((0, .5, .05), .1, pale, "body", n=6, rows=3, sq=(1, .6, 1.4))
    R.slab([(0, .56, -.22), (.06, .62, -.35), (.05, .8, -.66), (-.05, .8, -.66), (-.06, .62, -.35)], .03, 0x3a2e22, 0x3a2e22, "body", up=(1, 0, 0))   # the long tail, held up
    R.tube([(0, .68, .28), (0, .82, .33)], [.045, .04], br, [[("body", 1)], [("head", 1)]], sides=6)
    R.ball((0, .83, .34), .055, br, "head", n=7, rows=3, sq=(1, 1, 1.25))
    R.tube([(0, .82, .39), (0, .8, .52)], [.016, .002], 0x2a2620, "head", sides=4)
    R.tube([(0, .86, .32), (0, .92, .26)], [.03, .005], 0x3a2e22, "head", sides=4)                          # crest
    for s in (-1, 1): R.ball((s * .042, .835, .33), .014, 0x3a8ad0, "head", n=5, rows=2)
    for i, s in ((0, -1), (1, 1)):
        leg2(R, i, (s * .06, .44, 0), (s * .06, .24, 0), (s * .06, .03, .02), (.03, .02, .012), br, 0x7a7a7a, toes=[(0, -.02, .07), (.03, -.02, .05), (0, -.02, -.05)])
    return R

@kind("heron")
def heron():
    R = Rig({"body": (0, 0, 0), "head": (0, 1.5, .26), "leg0": (-.06, .9, 0), "leg0k": (-.06, .45, 0), "leg1": (.06, .9, 0), "leg1k": (.06, .45, 0)})
    g = 0x8a929a
    zloft(R, [(-.3, .96, .03, .03), (-.2, .95, .11, .11), (.02, .98, .15, .14), (.18, 1.05, .1, .1), (.26, 1.1, .05, .05)], g, "body", n=7)
    R.slab([(0, .97, -.2), (.1, .95, -.32), (0, .93, -.4), (-.1, .95, -.32)], .02, 0x7a828a, 0x7a828a, "body")
    R.tube([(0, 1.08, .22), (0, 1.22, .3), (0, 1.34, .3), (0, 1.44, .24), (0, 1.5, .26)], [.05, .042, .038, .035, .03], 0xd8dcde,
           [[("body", 1)], [("body", .8), ("head", .2)], [("body", .4), ("head", .6)], [("head", 1)], [("head", 1)]], sides=6)
    R.ball((0, 1.51, .27), .048, 0xd8dcde, "head", n=7, rows=3, sq=(.9, 1, 1.3))
    R.tube([(0, 1.5, .32), (0, 1.48, .5)], [.022, .002], 0xd8b040, "head", sides=4)
    R.tube([(0, 1.54, .24), (0, 1.53, .1)], [.012, .003], 0x2a2e32, "head", sides=4)
    for s in (-1, 1): R.ball((s * .035, 1.52, .3), .009, 0xe8c030, "head", n=4, rows=2)
    for i, s in ((0, -1), (1, 1)):
        leg2(R, i, (s * .06, .9, 0), (s * .06, .45, 0), (s * .06, .03, .02), (.035, .018, .012), 0x5a5a52, 0x4a4a40, toes=[(0, -.02, .1), (.05, -.02, .07), (-.05, -.02, .07), (0, -.02, -.06)])
    return R

# ---------------------------------------------------------------- Bigfoot and the Yeti
def ape(yeti):
    sh = lambda s: np.array((s * .54, 1.92, .08)); a = .05; b = .05 - .25
    el = lambda s: sh(s) + .55 * np.array((0, -math.cos(a), -math.sin(a))); wr = lambda s: el(s) + .55 * np.array((0, -math.cos(b), -math.sin(b)))
    R = Rig({"body": (0, 0, 0), "head": (0, 2.18, .16), "leg0": (-.19, 1.02, 0), "leg0k": (-.19, .52, 0), "leg1": (.19, 1.02, 0), "leg1k": (.19, .52, 0),
             "arm0": sh(-1), "arm0k": el(-1), "arm1": sh(1), "arm1k": el(1)})
    fur, fur2, face = (0xe8e6e2, 0xd6d4ce, 0x6a7280) if yeti else (0x4a3020, 0x3a2618, 0x2a1e18)
    secs = [(.9, 0, .27, .2), (1.2, .02, .36, .27), (1.55, .05, .45, .32), (1.85, .08, .5, .33), (2.0, .1, .4, .27), (2.12, .12, .18, .16)]
    rings = [ring((0, y, z), (0, 1, 0), (0, 0, 1), rx, rz, 9, math.pi / 9) for y, z, rx, rz in secs]
    R.loft(rings, [fur, fur, fur2, fur, fur, fur], ["body"] * 6, [np.array((0, y, z)) for y, z, _, _ in secs])
    R.ball((0, 2.2, .14), .17, fur, "head", n=9, rows=5, sq=(.9, 1.05, .95)); R.ball((0, 2.17, .27), .1, face, "head", n=7, rows=4, sq=(1, .95, .55))
    R.ball((0, 2.27, .25), .1, fur2, "head", n=7, rows=3, sq=(1.5, .45, .7)); R.tube([(0, 2.3, .1), (0, 2.44, .05)], [.12, .02], fur, "head", sides=7)   # brow, crown
    for s in (-1, 1): R.ball((s * .045, 2.2, .31), .014, 0x0a0806, "head", n=4, rows=2)
    for i, s in ((0, -1), (1, 1)):
        R.tube([(s * .19, 1.02, 0), (s * .19, .52, 0)], [.18, .13], fur, f"leg{i}", sides=7); R.ball((s * .19, .52, 0), .13, fur2, f"leg{i}k", n=6, rows=3)
        R.tube([(s * .19, .52, 0), (s * .19, .08, -.02)], [.13, .1], fur2, f"leg{i}k", sides=7)
        R.ball((s * .19, .05, .1), .1, face, f"leg{i}k", n=7, rows=3, sq=(.9, .5, 2.0))                             # the big foot
        R.tube([sh(s), el(s)], [.15, .11], fur, f"arm{i}", sides=7); R.ball(el(s), .11, fur2, f"arm{i}k", n=6, rows=3)
        R.tube([el(s), wr(s)], [.11, .09], fur2, f"arm{i}k", sides=7); R.ball(wr(s) + np.array((0, -.06, .02)), .1, face, f"arm{i}k", n=6, rows=3, sq=(.8, 1.2, 1))
    return R
@kind("bigfoot")
def bigfoot(): return ape(False)
@kind("yeti")
def yeti(): return ape(True)

# ---------------------------------------------------------------- the seal and the monkey
@kind("seal")
def seal():
    R = Rig({"body": (0, 0, 0), "head": (0, .36, .78)})
    g, g2, belly = 0x5e5e66, 0x4a4a52, 0x9a968c
    secs = [(-1.0, .12, .06, .03), (-.9, .15, .13, .08), (-.65, .22, .26, .18), (-.3, .28, .34, .26), (.05, .3, .36, .28), (.35, .3, .3, .25), (.6, .32, .2, .18), (.72, .34, .14, .14)]
    zloft(R, [(z, y, rx, ry) for z, y, rx, ry in secs], [g, 0x5a5a62, g, 0x585860, g, 0x5a5a62, g], "body", n=9)
    R.ball((0, .1, .0), .3, belly, "body", n=8, rows=3, sq=(1, .35, 2.2))
    for s in (-1, 1):
        R.slab([(s * .3, .1, .45), (s * .5, .02, .38), (s * .5, .02, .22), (s * .3, .08, .28)][::(1 if s > 0 else -1)], .03, g2, g2, "body")    # front flippers
        R.slab([(s * .03, .12, -.98), (s * .22, .1, -1.2), (s * .12, .1, -1.24), (0, .12, -1.02)][::(1 if s > 0 else -1)], .03, g2, g2, "body")   # tail flippers
    R.ball((0, .38, .82), .14, g, "head", n=8, rows=4, sq=(1, .95, 1.1)); R.ball((0, .35, .96), .07, 0x6e6e76, "head", n=6, rows=3)
    for s in (-1, 1): R.ball((s * .07, .43, .92), .025, 0x050505, "head", n=5, rows=2)
    return R

@kind("monkey")
def monkey():
    R = Rig({"body": (0, 0, 0), "head": (0, .8, .02), "arm0": (-.15, .68, 0), "arm1": (.15, .68, 0), "leg0": (-.08, .3, 0), "leg1": (.08, .3, 0)})
    fur, face = 0x4a3424, 0xb08a6a
    R.ball((0, .5, 0), .2, fur, "body", n=8, rows=4, sq=(.8, 1.2, .7))
    R.ball((0, .82, .02), .1, fur, "head", n=8, rows=4); R.ball((0, .8, .08), .065, face, "head", n=7, rows=3, sq=(1, .9, .6))
    for s in (-1, 1): R.ball((s * .1, .84, 0), .035, face, "head", n=5, rows=2, sq=(.5, 1, 1)); R.ball((s * .03, .83, .13), .01, 0x080604, "head", n=4, rows=2)
    for i, s in ((0, -1), (1, 1)):
        R.tube([(s * .15, .68, 0), (s * .15, .4, 0), (s * .15, .13, 0)], [.035, .03, .025], fur, f"arm{i}", sides=6); R.ball((s * .15, .12, 0), .035, face, f"arm{i}", n=5, rows=2)
        R.tube([(s * .08, .3, 0), (s * .08, -.02, 0)], [.04, .03], fur, f"leg{i}", sides=6); R.ball((s * .08, -.03, .02), .035, face, f"leg{i}", n=5, rows=2, sq=(1, .6, 1.4))
    t = [(0, .35, -.1), (0, .2, -.28), (0, .1, -.45), (0, .15, -.6), (0, .3, -.62), (0, .35, -.52)]
    R.tube(t, [.025, .023, .021, .019, .016, .012], fur, "body", sides=5)
    return R

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for k, f in KINDS.items():
        if ONLY and k not in ONLY: continue
        info = f().save(os.path.join(OUT, k + ".bin")); print(k, info["tris"], "tris", info["bytes"] // 1024, "KB")
