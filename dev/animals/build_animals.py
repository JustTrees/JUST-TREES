"""2.03: every animal of the normal hunts, in the Quaternius farm-animal style (Ron gave us the pack: "use those and make adjacent ones").
Each one starts from the nearest farm animal (dumped from its FBX by dump.html), gets reshaped (legs, trunk, neck, head, tail), repainted,
and given its own parts (antlers, horns, humps, manes, tusks, trunks, ears); the horse's walk / run / fall are copied onto it, plus a grazing move.
Usage: python3 dev/animals/build_animals.py <dumps dir> <out dir> [kind,kind,...]"""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from animal_lib import *

DUMPS, OUT = sys.argv[1], sys.argv[2]
ONLY = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
_src = {}
def src(name):
    if name not in _src: _src[name] = Model.load(os.path.join(DUMPS, name + ".json"))
    return _src[name]
def base(name): return Model.load(os.path.join(DUMPS, name + ".json"))

HORSE_DARK = (.02, .02, .02); HORSE_BODY = (.175, .074, .047)
def J(m, n): return m.bpos(n)

def moves(m, own=False, eat=(.95, .35), run=1.0):
    """walk / run / fall from the horse (or its own), its own idle if it has one, and a grazing move"""
    if own: m.own_clips(["Idle", "Walk", "Run", "Death"])
    else:
        if "Idle" in m.src["clips"]: m.own_clips(["Idle"])
        m.retarget(src("Horse"), ["Walk", "Run", "Death"] + ([] if "Idle" in m.src["clips"] else ["Idle"]))
    if run != 1.0: m.copy_clip("Walk", "Run", run)        # (a low one doesn't gallop: a quick walk)
    n, h = eat if eat else (0, 0)
    if n or h:
        def keys(t):                                      # head down, nibbling, a slow look up and down again
            e = min(1, t / .5, (3.0 - t) / .5) if t < 3 else 0; e = e * e * (3 - 2 * e); nib = math.sin(t * 9) * .05 * e
            return {"Neck": qaxis([1, 0, 0], n * e), "Head": qaxis([1, 0, 0], h * e + nib)}
        m.pose_clip("Eat", 3.0, keys)
    return m

def mane_off(m):
    """the horse's mane and forelock go (a deer has none)"""
    drop_where(m, lambda c, b, k: is_col(k, HORSE_DARK) and ((b in ("Neck", "Shoulders", "Torso", "Body") and c[1] > J(m, "Shoulders")[1]) or (b == "Head" and c[2] < J(m, "Head")[2] + 40)))

def belly_y(m, k=.2):
    """the height under which the trunk counts as belly (k of the way up its depth)"""
    d = np.array(m.dom()); v = m.pos[[is_body(n) for n in d]]; return v[:, 1].min() + (v[:, 1].max() - v[:, 1].min()) * k

def ears(m, at, tip, w, col, flat=.35):
    o, Lh = hunits(m); ear(m, o + np.array(at) * Lh, o + np.array(tip) * Lh, w * Lh, col, flat=flat)

def deer_paint(m, coat, belly, dark=0x2a2018, white_rump=False, legs_col=None, face=None):
    by = belly_y(m) - 20; hz = J(m, "Head")[2]; hb0, hb1 = headbox(m)
    def f(c, b, k):
        if is_col(k, HORSE_DARK) and ("Foot" in b): return 0x1a1410                       # hooves
        if b == "Head":
            if c[2] > hb1[2] - (hb1[2] - hb0[2]) * .12: return dark                        # the nose
            if is_col(k, HORSE_DARK): return 0x0c0a08                                      # eyes, ear tips
            return face(c, b, k) if face else coat
        if is_tail(b): return belly if c[1] < J(m, "Tail1")[1] - 6 else coat
        if is_body(b) and c[1] < by + 20: return belly
        if legs_col and is_leg(b) and "Up" not in b: return legs_col
        return coat
    paint(m, f)

def hunits(m):
    """the head's top-middle (between the ears) and its length, to place antlers and horns"""
    hb0, hb1 = headbox(m); hj = J(m, "Head"); Lh = hb1[2] - hb0[2]
    return np.array([0.0, hb1[1] - .06 * Lh, hj[2] + .12 * Lh]), Lh

def antlers(m, beam, tines=(), r0=.045, r1=.015, col=0xd8ccb0, at=(.1, 0, 0)):
    """beam: points (left side) in head lengths from the top of the head; tines: (t along the beam 0..1, direction, length)"""
    o, Lh = hunits(m); o = o + np.array(at) * Lh; P = [o + np.array(p, float) * Lh for p in beam]
    horn(m, P, r0 * Lh, r1 * Lh, col, sides=5)
    seg = np.cumsum([0] + [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)]); tot = seg[-1]
    for t, d, ln in tines:
        L = t * tot; i = min(len(P) - 2, int(np.searchsorted(seg, L) - 1)); i = max(i, 0); u = (L - seg[i]) / max(1e-9, seg[i + 1] - seg[i]); p = P[i] + (P[i + 1] - P[i]) * u
        d = np.array(d, float); d /= np.linalg.norm(d); horn(m, [p, p + d * ln * Lh * .5, p + (d + np.array([0, .25, .1])) / 1.1 * ln * Lh], r0 * Lh * .6, r1 * Lh * .7, col, sides=4)

def plate(m, pts, th, col, bone="Head"):
    """a flat palm (moose antler): a fan of triangles through pts (left side, head units from the top), with a thickness, mirrored"""
    o, Lh = hunits(m); P = [o + np.array(p, float) * Lh for p in pts]; c = sum(P) / len(P); T = []
    for s in (1, -1):
        Q = [p * np.array([s, 1, 1]) for p in P]; cc = c * np.array([s, 1, 1]); up = np.array([0, th * Lh / 2, 0])
        for k in range(len(Q)):
            a, b = Q[k], Q[(k + 1) % len(Q)]; T += [cc + up, a + up, b + up, cc - up, b - up, a - up, a + up, a - up, b - up, a + up, b - up, b + up]
        m.add_tris(T, col, bone, out=lambda q, cc=cc: cc); T = []

# ---------------------------------------------------------------- the recipes
R = {}
def recipe(name): return lambda f: R.__setitem__(name, f) or f

@recipe("horse")
def _horse():
    m = base("Horse"); moves(m, own=True, eat=(.6, .3))
    # coat variants (the game picks one): bay, chestnut, black, grey, palomino; the mane and tail dark or matching
    m.variants = [{HORSE_BODY: c} for c in [(.28, .17, .09), (.42, .2, .1), (.07, .06, .055), (.5, .48, .45), (.66, .55, .36)]]
    return m

@recipe("zebra")
def _zebra():
    m = base("Zebra"); moves(m, own=True, eat=(.6, .3)); return m

@recipe("buck")
def _buck():                                           # white-tailed deer: slim, tan-brown, white belly and tail, antlers
    m = base("Horse"); mane_off(m)
    legs(m, .95, .95, thick=.62); body(m, L=.82, G=.72, H=.8); neck(m, .72, .78, tilt=-.05); head(m, .72, snout=.78, sx=.85)
    tail(m, .28, .7, droop=-1.2)
    deer_paint(m, 0x8a6644, 0xe8dfcf, legs_col=0x7a5a3c); ears(m, (.25, -.02, -.08), (.62, .2, -.2), .11, 0x8a6644)
    antlers(m, [(0, 0, 0), (.22, .22, -.12), (.42, .36, -.02), (.5, .42, .2), (.44, .45, .4)], [(.35, (0, 1, .1), .32), (.6, (0, 1, .1), .3), (.82, (-.1, 1, .1), .22)])
    return moves(m, eat=(.65, .35))

@recipe("elk")
def _elk():                                            # big, tan body, dark brown neck, pale rump, huge antlers
    m = base("Horse"); mane_off(m)
    legs(m, 1.05, 1.05, thick=.72); body(m, L=.95, G=.85, H=.9); neck(m, .95, .9, tilt=.05); head(m, .9, snout=.85, sx=.9); tail(m, .25, .8, droop=-1.2)
    nb = J(m, "Neck")
    def face(c, b, k): return 0x4a3222
    deer_paint(m, 0x9a7a52, 0x5a4030, legs_col=0x3a2a1e, face=face)
    paint(m, lambda c, b, k: 0x4a3222 if (b in ("Neck", "Shoulders") and not is_col(k, (0x1a, 0x14, 0x10))) else (0xd8c8a8 if (is_body(b) and c[2] < J(m, "Hips")[2] - 30 and c[1] > J(m, "Body")[1] + 20) else None))
    antlers(m, [(0, 0, 0), (.25, .45, -.35), (.42, .9, -.55), (.48, 1.3, -.5), (.42, 1.55, -.3)], [(.12, (.1, .2, 1), .4), (.25, (.1, .3, 1), .38), (.5, (0, .5, 1), .35), (.7, (0, .6, 1), .32), (.86, (0, .7, 1), .25)], r0=.05)
    return moves(m, eat=(.6, .35))

def paint_rule(m, fn):
    """like paint, but fn also gets this model's landmarks: fn(c, b, k, L) with L = {belly, back, hips z, shoulders z, head box ...}"""
    hb0, hb1 = headbox(m); d = np.array(m.dom()); v = m.pos[[is_body(n) for n in d]]
    L = {"belly": belly_y(m), "back": v[:, 1].max(), "low": v[:, 1].min(), "z0": v[:, 2].min(), "z1": v[:, 2].max(), "hb0": hb0, "hb1": hb1,
         "hips": J(m, "Hips"), "sh": J(m, "Shoulders"), "neck": J(m, "Neck"), "head": J(m, "Head")}
    paint(m, lambda c, b, k: fn(c, b, k, L))

def hooves(m, col=0x1a1410):
    paint(m, lambda c, b, k: col if ("Foot" in b) else None)

@recipe("moose")
def _moose():                                          # dark, tall, humped, a long drooping nose, the bell, wide palms
    m = base("Horse"); mane_off(m)
    legs(m, 1.18, 1.1, thick=.8); body(m, L=.95, G=.9, H=1.0); neck(m, .62, 1.1, tilt=.3); head(m, .95, snout=1.25, sy=1.05)
    tail(m, .2, .7, droop=-1.2)
    sh = J(m, "Shoulders"); blob(m, sh + np.array([0, 95, -20]), 70, 0x3a2a1e, "Shoulders", sq=(.8, .9, 1.6))
    o, Lh = hunits(m); hj = J(m, "Head")
    m.tube([o + np.array([0, -.75, -.05]) * Lh, o + np.array([0, -1.05, .0]) * Lh], [.09 * Lh, .03 * Lh], 0x2e2218, "Head")      # the bell
    paint_rule(m, lambda c, b, k, L: 0x8a7a64 if (is_leg(b) and "Up" not in b and "Foot" not in b) else 0x1a1410 if "Foot" in b else (0x4a3a2a if b == "Head" and c[2] > L["hb1"][2] - 40 else 0x3a2a1e))
    pc = 0xc8b898
    antlers(m, [(0, 0, 0), (.35, .08, .0)], [], r0=.06, r1=.05, col=pc)
    plate(m, [(.3, .04, -.1), (.65, .3, -.25), (.95, .42, -.05), (1.0, .4, .25), (.7, .25, .3), (.35, .08, .12)], .05, pc)
    for k in range(5):
        p = np.array([.6 + .09 * k, .3 + .03 * k, -.25 + .12 * k]); antlers(m, [p, p + np.array([.1, .22, .02])], [], r0=.03, r1=.008, col=pc, at=(0, 0, 0))
    return moves(m, eat=(.9, .4))

@recipe("caribou")
def _caribou():                                        # grey-brown, a white neck and mane, tall back-curving antlers with a brow shovel
    m = base("Horse"); mane_off(m)
    legs(m, .95, .95, thick=.72); body(m, L=.85, G=.82, H=.85); neck(m, .8, .95, tilt=.05); head(m, .82, snout=.85); tail(m, .2, .8, droop=-1.2)
    paint_rule(m, lambda c, b, k, L: 0x1a1410 if "Foot" in b else 0x2a2018 if (b == "Head" and c[2] > L["hb1"][2] - 25) else
               0xe8e2d6 if (b in ("Neck", "Shoulders") or (is_body(b) and c[1] < L["belly"] - 10) or (is_tail(b))) else 0x6a5a48)
    ears(m, (.22, -.02, -.08), (.5, .12, -.2), .09, 0x6a5a48)
    pc = 0xd8ccb0
    antlers(m, [(0, 0, 0), (.25, .5, -.3), (.35, 1.0, -.4), (.3, 1.35, -.15), (.2, 1.5, .15)], [(.65, (.3, .3, 1), .3), (.85, (.4, .4, 1), .25), (.95, (.2, .6, 1), .2)], r0=.04, col=pc)
    plate(m, [(.08, .05, .1), (.12, .3, .25), (.1, .2, .45), (.06, .02, .3)], .03, pc)
    return moves(m, eat=(.9, .35))

@recipe("pronghorn")
def _pronghorn():                                      # tan and white, small, fast; short black horns with a prong
    m = base("Horse"); mane_off(m)
    legs(m, .88, .88, thick=.55); body(m, L=.72, G=.68, H=.78); neck(m, .72, .7, tilt=0); head(m, .66, snout=.8, sx=.85); tail(m, .15, .7, droop=-1.2)
    def f(c, b, k, L):
        if "Foot" in b: return 0x1a1410
        if b == "Head": return 0x2a201a if c[2] > L["hb1"][2] - 30 else 0xc08a4a
        if b == "Neck": return 0xf2ece0 if int((c[1] - L["neck"][1]) / 25) % 3 == 1 else 0xc08a4a
        if is_tail(b) or (is_body(b) and (c[1] < L["belly"] + 25 or c[2] < L["hips"][2] - 40)): return 0xf2ece0
        if is_leg(b) and "Up" not in b: return 0xc8925a
        return 0xc08a4a
    paint_rule(m, f); ears(m, (.22, -.02, -.06), (.48, .2, -.16), .07, 0xc08a4a)
    antlers(m, [(0, 0, 0), (.02, .35, -.04), (-.04, .55, -.16)], [(.5, (0, .3, 1), .12)], r0=.04, r1=.012, col=0x1a1612)
    return moves(m, eat=(.9, .35))

@recipe("oryx")
def _oryx():                                           # pale, black face mask, a dark side stripe and legs, very long straight horns
    m = base("Horse"); mane_off(m)
    legs(m, .92, .92, thick=.62); body(m, L=.85, G=.78, H=.85); neck(m, .8, .82, tilt=.05); head(m, .74, snout=.86, sx=.85); tail(m, .55, .4, droop=-.2)
    def f(c, b, k, L):
        if "Foot" in b: return 0x1a1410
        if is_tail(b): return 0x1e1814
        if b == "Head": return 0x2a201a if (abs(c[0]) < 10 or c[2] > L["hb1"][2] - 30 or (abs(c[0]) > 22 and c[1] < L["hb1"][1] - 30)) else 0xe2dacc
        if is_body(b) and L["belly"] - 5 < c[1] < L["belly"] + 25: return 0x3a2c24
        if is_leg(b) and "Up" not in b: return 0x5a4a3e
        return 0xd8d0c2
    paint_rule(m, f); ears(m, (.22, -.02, -.06), (.48, .15, -.16), .08, 0xe2dacc)
    antlers(m, [(0, 0, 0), (.04, .5, -.35), (.08, 1.0, -.75), (.1, 1.4, -1.05)], [], r0=.035, r1=.008, col=0x1a1612)
    return moves(m, eat=(.9, .35))

@recipe("giraffe")
def _giraffe():                                        # very long neck and legs, sloping back, patched coat, ossicones
    m = base("Horse"); mane_off(m)
    legs(m, 1.75, 1.45, thick=.8); body(m, L=.72, G=.78, H=.92); neck(m, 2.5, .78, tilt=-.32); head(m, .75, snout=.88, sx=.85); tail(m, .6, .35, droop=-.15)
    sel = lambda c, b: b in ("Neck", "Shoulders", "Torso", "Body", "Hips", "Back", "FrontLegL", "FrontLegR") or ("UpLeg" in b)
    cl = cells(m, 70, 7, sel)
    def f(c, b, k, L):
        if "Foot" in b: return 0x2a1e14
        if is_tail(b): return 0x2a1e14 if c[1] < J(m, "Tail1")[1] - 120 else 0xd8be8e
        if b == "Head": return 0x3a2a1e if c[2] > L["hb1"][2] - 20 else 0xd8be8e
        return None
    paint_rule(m, f); C, B, K = tri_info(m)
    for t, (d0, gap) in cl.items(): m.col[t * 3:t * 3 + 3] = rgb(0xe0c48e if gap < 16 else 0x6e3e1c)
    paint_rule(m, lambda c, b, k, L: 0xe0c898 if (is_leg(b) and "LowLeg" in b) else None)
    ears(m, (.22, -.02, -.1), (.55, .05, -.2), .07, 0xd8be8e)
    for x in (.1,): antlers(m, [(x, 0, 0), (x + .02, .28, -.04)], [], r0=.05, r1=.05, col=0x3a2a1e)
    return moves(m, eat=(.35, .3))

@recipe("goat")
def _goat():                                           # mountain goat: shaggy white, black horns, a beard
    m = base("Sheep")
    legs(m, 1.25, 1.2, thick=.95); head(m, .95, snout=1.15); neck(m, 1.1, .9)
    paint_rule(m, lambda c, b, k, L: 0x16130f if "Foot" in b else 0x2a2622 if (b == "Head" and c[2] > L["hb1"][2] - 12) else 0xeeeae0)
    antlers(m, [(0, 0, 0), (.04, .28, -.08), (.05, .4, -.25)], [], r0=.045, r1=.012, col=0x16130f)
    o, Lh = hunits(m); m.tube([o + np.array([0, -.62, .45]) * Lh, o + np.array([0, -.95, .4]) * Lh], [.07 * Lh, .02 * Lh], 0xf2eee6, "Head")
    return moves(m, eat=(.9, .3))

@recipe("bighorn")
def _bighorn():                                        # brown, white muzzle / rump / belly, the big curled horns
    m = base("Sheep")
    legs(m, 1.25, 1.2, thick=.85); body(m, G=.85, H=.9); head(m, .95, snout=1.1)
    def f(c, b, k, L):
        if "Foot" in b: return 0x2a2018
        if b == "Head": return 0xe8e0d0 if c[2] > L["hb1"][2] - 35 else 0x7a5a3e
        if is_body(b) and (c[1] < L["belly"] or c[2] < L["z0"] + 45): return 0xe8e0d0
        if is_leg(b) and "Up" not in b: return 0x6a4e36
        return 0x7a5a3e
    paint_rule(m, f)
    curl = [(0, 0, 0), (.25, .2, -.2), (.5, .12, -.45), (.62, -.15, -.4), (.58, -.4, -.12), (.45, -.45, .12)]
    antlers(m, curl, [], r0=.14, r1=.04, col=0x9a8a72)
    return moves(m, eat=(.9, .3))

@recipe("muskox")
def _muskox():                                         # a low dark shaggy block, pale saddle and socks, horns hooked down and out
    m = base("Sheep")
    legs(m, .8, .8, thick=1.1); body(m, L=1.1, G=1.1, H=1.15, Hb=1.3); head(m, 1.12, snout=.95)
    def f(c, b, k, L):
        if "Foot" in b: return 0x2a2018
        if is_leg(b) and "Low" in b: return 0xc8bca8
        if is_body(b) and c[1] > L["back"] - 35 and L["hips"][2] < c[2] < L["sh"][2]: return 0x6a5640
        if b == "Head" and c[2] > L["hb1"][2] - 20: return 0x6a5a4a
        return 0x3e3024
    paint_rule(m, f)
    antlers(m, [(-.08, 0, .05), (.25, -.02, .02), (.42, -.3, .05), (.38, -.45, .3)], [], r0=.1, r1=.03, col=0xd8ccb4)
    return moves(m, eat=(.7, .3))

@recipe("camel")
def _camel():                                          # the llama, lower-necked, longer, one big hump, sandy all over
    m = base("Llama")
    legs(m, 1.15, 1.15, thick=1.0); body(m, L=1.2, G=1.1, H=1.0); neck(m, 1.05, 1.0, tilt=.55); head(m, 1.05, snout=1.3, sy=.95)
    hj = J(m, "Body"); d = np.array(m.dom()); v = m.pos[[is_body(n) for n in d]]
    blob(m, [0, v[:, 1].max() - 40, J(m, "Body")[2] - 10], 95, 0xc49a66, "Torso", n=9, rows=6, sq=(.72, 1.05, 1.0))
    paint_rule(m, lambda c, b, k, L: 0x3a2a1e if "Foot" in b else 0x6a4a30 if (b == "Head" and c[2] > L["hb1"][2] - 12) else 0xb88e5c if (is_leg(b) and "Low" in b) else 0xc49a66)
    return moves(m, eat=(.6, .3))

# ---------------- the pig's family
def pig_tail_off(m):
    squash(m, lambda p, b: b in ("Back", "Hips") and abs(p[0]) < 27 and p[2] < -372, lambda p: np.array([p[0] * .7, min(380.0, max(300.0, p[1])), -372.0]))
def pig_ears_off(m):
    hb0, hb1 = headbox(m); cut = hb1[1] - 32
    squash(m, lambda p, b: b == "Head" and p[1] > cut and abs(p[0]) > 12 and p[2] < hb0[2] + (hb1[2] - hb0[2]) * .5, lambda p: np.array([p[0] * .8, cut, p[2]]))
def round_ears(m, r, col, at=(.32, -.02, -.05)):
    o, Lh = hunits(m)
    for s_ in (1, -1): blob(m, o + np.array([at[0] * s_, at[1], at[2]]) * Lh, r * Lh, col, "Head", n=7, rows=3, sq=(1, 1, .45))
def rear(m):
    d = np.array(m.dom()); own = np.array([t != "part" for t in m.tag]); v = m.pos[np.array([is_body(n) for n in d]) & own]
    i = np.argmin(v[:, 2]); return np.array([0.0, v[:, 1].max(), v[:, 2].min()]), v[:, 1].max() - v[:, 1].min(), v[:, 2].max() - v[:, 2].min()

@recipe("boar")
def _boar():                                           # dark bristly, a ridge of a mane, tusks, a thin tail
    m = base("Pig"); pig_tail_off(m)
    legs(m, 1.05, 1.0, thick=.82); body(m, L=.9, G=.78, H=1.0); head(m, 1.0, snout=1.2, sx=.9)
    r, dep, ln = rear(m); bk = J(m, "Shoulders")
    m.tube([r + np.array([0, -dep * .25, 5]), r + np.array([0, -dep * .6, -25])], [10, 4], 0x1a1410, "Back")
    o, Lh = hunits(m); hb0, hb1 = headbox(m)
    paint_rule(m, lambda c, b, k, L: 0x1a1410 if "Foot" in b else 0x4a3a34 if (b == "Head" and c[2] > L["hb1"][2] - 18) else 0x241e1a if (is_leg(b) and "Low" in b) else 0x3e342a)
    d = np.array(m.dom()); v = m.pos[[is_body(n) for n in d]]; top = v[:, 1].max()
    m.tube([np.array([0, top - 8, J(m, "Hips")[2]]), np.array([0, top + 10, J(m, "Torso")[2]]), np.array([0, top + 6, J(m, "Shoulders")[2] + 30])], [12, 18, 12], 0x1e1814, "Torso", sides=4)
    tz = hb1[2] - (hb1[2] - hb0[2]) * .12; ty = hb0[1] + (hb1[1] - hb0[1]) * .25
    horn(m, [(28, ty, tz - 10), (40, ty + 25, tz), (34, ty + 45, tz - 12)], 7, 2, 0xeee6d4)
    return moves(m, eat=(.5, .4))

@recipe("tapir")
def _tapir():                                          # dark, round, a short trunk of a nose
    m = base("Pig"); pig_tail_off(m); pig_ears_off(m)
    legs(m, 1.25, 1.2, thick=.95); body(m, L=1.05, G=.9, H=1.0); head(m, .9, snout=1.55, sy=.85, sx=.85)
    paint_rule(m, lambda c, b, k, L: 0x1a1410 if "Foot" in b else 0x1e1816 if (b == "Head" and c[2] > L["hb1"][2] - 25) else 0x342a24)
    round_ears(m, .1, 0x2a2420, at=(.3, -.05, -.15))
    return moves(m, eat=(.5, .35))

@recipe("capybara")
def _capybara():                                       # a big blunt-headed guinea pig, reddish brown, no tail
    m = base("Pig"); pig_tail_off(m); pig_ears_off(m)
    legs(m, .9, .95, thick=1.0); body(m, L=.95, G=.95, H=1.05); head(m, 1.2, snout=.95, sy=1.25, sx=.95)
    paint_rule(m, lambda c, b, k, L: 0x2a1e16 if ("Foot" in b or (b == "Head" and c[2] > L["hb1"][2] - 12)) else 0x8a6a48)
    round_ears(m, .08, 0x6a4e32, at=(.3, -.02, -.12))
    return moves(m, eat=(.45, .35), run=1.7)

def bear(m, coat, snout_c, nose=0x0c0a08, polar=False):
    pig_tail_off(m); pig_ears_off(m)
    legs(m, 1.55, 1.45, thick=1.35); body(m, L=.85, G=.95, H=1.05); neck(m, 1.35 if polar else 1.15, 1.05, tilt=.1); head(m, .82 if polar else .88, snout=1.05 if polar else .95)
    paint_rule(m, lambda c, b, k, L: nose if (b == "Head" and c[2] > L["hb1"][2] - 12) else snout_c if (b == "Head" and c[2] > L["hb1"][2] - 45 and c[1] < L["hb1"][1] - 30) else
               (0x2a2018 if "Foot" in b and not polar else coat))
    round_ears(m, .11, coat, at=(.32, -.04, -.12))
    return moves(m, eat=(.5, .35))

@recipe("bear")
def _bear():
    m = bear(base("Pig"), 0x3e2818, 0x8a6a4a)
    m.variants = [{}, {0x3e2818: 0x1c1410, 0x8a6a4a: 0x6a5038}]                 # brown, black
    return m

@recipe("polar")
def _polar(): return bear(base("Pig"), 0xe4ddc8, 0xefe9d8, polar=True)

@recipe("rhino")
def _rhino():                                          # grey, heavy, two horns on the nose
    m = base("Pig"); pig_tail_off(m)
    legs(m, 1.15, 1.1, thick=1.35); body(m, L=1.12, G=1.05, H=1.05); head(m, 1.15, snout=1.25, sx=.9)
    paint_rule(m, lambda c, b, k, L: 0x5a5650 if ("Foot" in b) else 0x7a766e)
    r, dep, ln = rear(m); m.tube([r + np.array([0, -dep * .3, 5]), r + np.array([0, -dep * .7, -15])], [7, 3], 0x2a2622, "Back")
    o, Lh = hunits(m); hb0, hb1 = headbox(m); zt = hb1[2] - (hb1[2] - hb0[2]) * .12; yt = hb0[1] + (hb1[1] - hb0[1]) * .62
    m.tube([np.array([0, yt, zt]), np.array([0, yt + .55 * Lh, zt + .15 * Lh])], [.12 * Lh, .01 * Lh], 0xb0a898, "Head", sides=6)
    m.tube([np.array([0, yt + .08 * Lh, zt - .3 * Lh]), np.array([0, yt + .32 * Lh, zt - .26 * Lh])], [.09 * Lh, .01 * Lh], 0xb0a898, "Head", sides=6)
    return moves(m, eat=(.5, .35))

@recipe("elephant")
def _elephant():                                       # grey, pillar legs, the trunk, big ears, tusks
    m = base("Pig"); pig_tail_off(m); pig_ears_off(m)
    legs(m, 2.0, 1.55, thick=1.5); body(m, L=1.0, G=1.0, H=1.12); neck(m, .45, 1.15, tilt=-.15); head(m, 1.45, snout=.55, sy=1.15)
    paint_rule(m, lambda c, b, k, L: 0x625e5a if "Foot" in b else 0x77736e)
    o, Lh = hunits(m); hb0, hb1 = headbox(m); zt = hb1[2] - 10; yt = hb0[1] + (hb1[1] - hb0[1]) * .45
    m.tube([np.array([0, yt, zt - 15]), np.array([0, yt - .4 * Lh, zt + .15 * Lh]), np.array([0, yt - 1.0 * Lh, zt + .2 * Lh]), np.array([0, yt - 1.6 * Lh, zt + .12 * Lh]),
            np.array([0, yt - 1.95 * Lh, zt + .25 * Lh])], [.26 * Lh, .2 * Lh, .15 * Lh, .12 * Lh, .1 * Lh], 0x6e6a66, "Head", sides=7)
    horn(m, [(.22 * Lh, yt - .25 * Lh, zt - .2 * Lh), (.26 * Lh, yt - .55 * Lh, zt + .15 * Lh), (.2 * Lh, yt - .6 * Lh, zt + .5 * Lh)], .07 * Lh, .03 * Lh, 0xe8e0cc)
    for s_ in (1, -1): blob(m, np.array([s_ * (hb1[0] + .05 * Lh), hb1[1] - .4 * Lh, hb0[2] + .05 * Lh]), .75 * Lh, 0x6e6a66, "Head", n=9, rows=5, sq=(.08, 1, .75))
    r, dep, ln = rear(m); m.tube([r + np.array([0, -dep * .25, 5]), r + np.array([0, -dep * .85, -20])], [6, 3], 0x2a2622, "Back")
    return moves(m, eat=(.35, .3))

@recipe("gator")
def _gator():                                          # 2.17 (Ron: "the gator's shape looks kinda dumb", "make his head and snout bigger"): built from scratch on the pig's bones
    m = base("Pig"); pig_tail_off(m); pig_ears_off(m)
    legs(m, .5, .52, thick=1.45); body(m, L=1.5, G=1.25, H=.6); neck(m, .5, 1.1, tilt=.25); head(m, .9, snout=2.6, sy=.5, sx=1.0)   # (just to place the bones)
    C, B, K = tri_info(m); m.drop(np.array([not is_leg(b) or "UpLeg" in b for b in B]))      # keep only the lower legs and feet; short sprawling upper legs below
    TOP, TOP2, BELLY, TOOTH, EYE = 0x2c3220, 0x22261a, 0x9a967a, 0xe8e2c8, 0xb89a30
    # one smooth skin from the tail tip to the nose: (z, centre height, half width, half height); a long flat body, a heavy tail, a big broad head and snout
    S = [(-1510, 24, 4, 8), (-1440, 32, 12, 16), (-1300, 45, 22, 26), (-1150, 58, 32, 33), (-1000, 70, 42, 39), (-850, 82, 56, 44), (-700, 92, 72, 48), (-570, 98, 92, 50),
         (-470, 101, 112, 50), (-380, 102, 126, 49), (-250, 102, 134, 47), (-100, 102, 138, 47), (50, 102, 138, 47), (200, 102, 134, 47), (300, 102, 126, 46),
         (360, 104, 112, 47), (410, 108, 110, 53), (470, 111, 118, 57), (540, 107, 106, 47), (620, 101, 92, 38), (700, 95, 80, 31), (770, 91, 72, 27),
         (830, 89, 66, 25), (858, 88, 56, 20), (872, 87, 33, 12)]
    HZ = lambda z: 360 + (z - 360) * 1.14 if z > 360 else z                                   # the head a bit longer ...
    TZ = lambda z: -470 + (z + 470) * .86 if z < -470 else z                                 # ... and the tail a bit shorter
    S = [(TZ(HZ(z)), cy + (ry * .12 if z > 360 else 0), rx * (1.17 if z > 400 else 1), ry * (1.17 if z > 400 else 1)) for z, cy, rx, ry in S]
    def at(z):                                              # the skin's section at any z
        for (z0, *a), (z1, *b) in zip(S[:-1], S[1:]):
            if z0 <= z <= z1: t = (z - z0) / (z1 - z0); return [a[i] + (b[i] - a[i]) * t for i in range(3)]
        return list(S[0][1:]) if z < S[0][0] else list(S[-1][1:])
    def sect(z, cy, rx, ry, n=14):                           # a rounded section, a little flatter underneath
        return [np.array([rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n) * (.82 if math.sin(2 * math.pi * k / n) < 0 else 1), z]) for k in range(n)]
    STOPS = [(TZ(-1510), "Back"), (-560, "Back"), (-330, "Hips"), (0, "Body"), (170, "Shoulders"), (330, "Shoulders"), (400, "Neck"), (440, "Head")]
    def blend(n0, n1):                                      # each new corner follows the bones near it along the body (no cracks when it bends)
        for i in range(n0, n1):
            z = m.pos[i][2]
            if z <= STOPS[0][0]: m.si[i] = [m.idx(STOPS[0][1]), 0, 0, 0]; m.sw[i] = [1, 0, 0, 0]; continue
            if z >= STOPS[-1][0]: m.si[i] = [m.idx(STOPS[-1][1]), 0, 0, 0]; m.sw[i] = [1, 0, 0, 0]; continue
            for (z0, b0), (z1, b1) in zip(STOPS[:-1], STOPS[1:]):
                if z0 <= z <= z1: t = (z - z0) / (z1 - z0); m.si[i] = [m.idx(b0), m.idx(b1), 0, 0]; m.sw[i] = [1 - t, t, 0, 0]; break
    n0 = len(m.pos); m.add_loft([sect(z, cy, rx, ry) for z, cy, rx, ry in S], TOP, "Body", out=lambda c: np.array([0, at(c[2])[0], c[2]]))
    # bumps on top: two rows of plates down the back, then a double crest and a single fin row along the tail
    def spike(c, h, w, col=TOP2, ln=None):
        ln = ln or w; c = np.array(c, float); tip = c + np.array([0, h, 0]); q = [c + np.array([-w, 0, 0]), c + np.array([0, 0, ln]), c + np.array([w, 0, 0]), c + np.array([0, 0, -ln])]
        m.add_tris([v for k in range(4) for v in (q[k], q[(k + 1) % 4], tip)], col, "Body", out=c - np.array([0, 10, 0]))
    for z in range(-470, 330, 42):
        cy, rx, ry = at(z)
        for xs in (.3, .6):
            for sg in (1, -1): x = sg * rx * xs; spike((x, cy + ry * math.sqrt(max(0, 1 - xs * xs)) - 3, z), 11, 13)
    for z in range(int(TZ(-500)), int(TZ(-1000)), -40):
        cy, rx, ry = at(z)
        for sg in (1, -1): spike((sg * rx * .35, cy + ry * .93 - 3, z), 20, 9, ln=18)
    for z in range(int(TZ(-1000)), int(TZ(-1470)), -36):
        cy, rx, ry = at(z); spike((0, cy + ry - 3, z), 22 * (1 - (TZ(-1000) - z) / (TZ(-1000) - TZ(-1600))) + 6, 4, ln=16)
    nlg = len(m.pos)
    # upper legs: out sideways from the trunk, down to the knee (each rides its own upper-leg bone)
    for sg, sd in ((1, "L"), (-1, "R")):
        for fb, z0, z1, r0, r1 in (("Back", -395, -457, 36, 27), ("Front", 280, 290, 30, 23)):
            a, b_ = np.array([sg * 80, 98, z0]), np.array([sg * 152, 40, z1])
            m.tube([a, a + (b_ - a) * .55, b_], [r0, (r0 + r1) / 2 * 1.05, r1], TOP, fb + "UpLeg" + sd, sides=7)
            blob(m, b_ + np.array([0, -4, 0]), r1 * 1.05, TOP, fb + "UpLeg" + sd, n=7, rows=3)
    nl = len(m.pos)
    # the head: eyes up on top, nostrils at the tip, teeth along the jaw
    hb = len(m.pos)
    for sg in (1, -1):
        cy, rx, ry = at(HZ(452)); blob(m, (sg * 64, cy + ry - 4, HZ(452)), 23, TOP, "Head", n=8, rows=4, sq=(1, .8, 1.15))
        blob(m, (sg * 76, cy + ry + 5, HZ(462)), 9, EYE, "Head", n=6, rows=3, sq=(.6, 1, 1))
        cy, rx, ry = at(HZ(842)); blob(m, (sg * 17, cy + ry - 3, HZ(842)), 11, TOP2, "Head", n=6, rows=3, sq=(1, .6, 1.2))
        for z in range(int(HZ(478)), int(HZ(850)), 28):
            cy, rx, ry = at(z); x = sg * rx * .985; y = cy - ry * .08; L_ = 10 if (z // 28) % 2 else 15
            m.add_tris([(x, y, z - 6), (x, y, z + 6), (x + sg * 2, y - L_, z), (x, y, z - 6), (x + sg * 2, y - L_, z), (x - sg * 6, y, z)], TOOTH, "Head", out=(0, y, z))
    blend(n0, nlg); blend(nl, len(m.pos))
    def f(c, b, k, L):
        if is_leg(b) or k is None: return None
        if np.abs(k - rgb(TOOTH)).max() < .02 or np.abs(k - rgb(EYE)).max() < .02: return None
        z = c[2]; cy, rx, ry = at(z)
        if z > 380 and c[1] < cy - ry * .12: return BELLY                                     # the pale lower jaw
        if c[1] < cy - ry * .45: return BELLY
        if np.abs(k - rgb(TOP2)).max() < .02: return None
        if z > 380: return TOP
        seg = max(i for i in range(len(S)) if S[i][0] <= z) if z >= S[0][0] else 0
        return TOP2 if seg % 2 else TOP                                                         # bands, one per section of the skin
    paint(m, lambda c, b, k: f(c, b, k, None))
    paint(m, lambda c, b, k: (0x1e2216 if "Foot" in b else 0x2a301e) if is_leg(b) else None)
    m = moves(m, eat=None, run=2.2)
    m.variants = [{}, {0x22261a: 0x3a4228, 0x2c3220: 0x4a5232, 0x9a967a: 0xb4ac80, 0x1e2216: 0x30361f, 0x2a301e: 0x3e4630}]   # (the crocodile: lighter, more olive)
    return m

# ---------------- the dog's family (the pug: a longer nose, longer legs, upright ears, a proper tail)
PUG_DARK = (.04, .014, .009)
def pug_tail_off(m):
    squash(m, lambda p, b: b in ("Back", "Hips") and abs(p[0]) < 20 and (p[2] < -127 or p[1] > 222), lambda p: np.array([p[0], min(218.0, p[1]), max(-127.0, p[2])]))
def pug_ears_off(m):
    hb0, hb1 = headbox(m); hj = J(m, "Head")
    squash(m, lambda p, b: b == "Head" and abs(p[0]) > 36 and p[1] > 215, lambda p: np.array([np.sign(p[0]) * 36, min(p[1], 238.0), p[2]]))
def dog(m, legF, legB, L, G, H, nk, hd, snout, thick=.8, tilt=-.1):
    pug_tail_off(m); pug_ears_off(m)
    legs(m, legF, legB, thick=thick); body(m, L=L, G=G, H=H); neck(m, nk, .9, tilt=tilt); head(m, hd, snout=snout, sx=.85, sy=.88)
    return m
def dog_tail(m, ln, r, col, droop=.5, bone="Back", tip=None, up=0.0):
    rr, dep, lb = rear(m); o = rr + np.array([0, -dep * .18, 6]); L = ln * lb
    pts = [o, o + np.array([0, -L * .25 * droop + L * .1 * up, -L * .35]), o + np.array([0, -L * .6 * droop + L * .2 * up, -L * .7]), o + np.array([0, -L * .85 * droop + L * .25 * up, -L * .95])]
    m.tube(pts, [r * .7 * dep, r * dep, r * .9 * dep, r * .25 * dep], col, bone, sides=6)
    if tip: m.tube([pts[2] + (pts[3] - pts[2]) * .5, pts[3]], [r * .8 * dep, r * .25 * dep], tip, bone, sides=6)
def dog_paint(m, coat, belly=None, nose=0x111010, legs_col=None, muzzle=None):
    def f(c, b, k, L):
        if b == "Head" and c[2] > L["hb1"][2] - 10: return nose
        if muzzle and b == "Head" and c[2] > L["hb1"][2] - 45 and c[1] < L["hb1"][1] - 28: return muzzle
        if belly and ((is_body(b) and c[1] < L["belly"]) or (b == "Neck" and c[1] < L["neck"][1])): return belly
        if legs_col and is_leg(b) and "Up" not in b: return legs_col
        return coat
    paint_rule(m, f)
def dog_ears(m, col, size=1.0, inner=None):
    ears(m, (.3, -.06, -.1), (.36, .35 * size, -.18), .12 * size, col, flat=.4)

@recipe("wolf")
def _wolf():
    m = dog(base("Pug"), 1.75, 1.65, 1.35, .72, .82, 1.3, .74, 2.0)
    dog_paint(m, 0x6e6a64, 0xc8c2b8, muzzle=0xb4aea4); dog_ears(m, 0x5e5a54); dog_tail(m, .45, .22, 0x6e6a64, tip=0x2a2826)
    m.variants = [{}, {0x6e6a64: 0xc8c2b4, 0x5e5a54: 0xb4ad9f, 0xc8c2b8: 0xeeeae2, 0xb4aea4: 0xe0dcd4}]          # grey, the pale one of the north
    return moves(m, eat=(.8, .45))

@recipe("coyote")
def _coyote():
    m = dog(base("Pug"), 1.75, 1.65, 1.3, .66, .78, 1.3, .7, 2.1)
    dog_paint(m, 0x9a8466, 0xd8ccb4, muzzle=0xc8b898, legs_col=0xa8906a); dog_ears(m, 0x8a7458, 1.1); dog_tail(m, .42, .2, 0x8a7458, tip=0x2a2420)
    return moves(m, eat=(.8, .45))

@recipe("fox")
def _fox():
    m = dog(base("Pug"), 1.45, 1.4, 1.3, .62, .75, 1.2, .68, 2.2)
    dog_paint(m, 0xc0602a, 0xeee6da, muzzle=0xeee6da, legs_col=0x2a1e16); dog_ears(m, 0xb05420, 1.15); dog_tail(m, .62, .3, 0xc0602a, droop=.35, tip=0xf4f0ea)
    return moves(m, eat=(.8, .45))

@recipe("arcticfox")
def _arcticfox():
    m = dog(base("Pug"), 1.35, 1.3, 1.2, .7, .8, 1.1, .72, 1.8)
    dog_paint(m, 0xe8e6e0, 0xf6f4f0, nose=0x1a1818); dog_ears(m, 0xe0ded6, .8); dog_tail(m, .6, .36, 0xf0eee8, droop=.35)
    m.variants = [{}, {0xe8e6e0: 0x6a625a, 0xf6f4f0: 0x9a928a, 0xe0ded6: 0x5a524a, 0xf0eee8: 0x7a726a}]          # white in winter, grey-brown in summer
    return moves(m, eat=(.8, .45))

@recipe("panther")
def _panther():                                        # long, low, a long tail; tawny (a cougar) or black (a jaguar's dark phase)
    m = dog(base("Pug"), 1.4, 1.45, 1.55, .7, .78, 1.1, .72, 1.25, thick=.85)
    dog_paint(m, 0xa47c50, 0xe2d2b4, muzzle=0xeee2cc, nose=0x2a1a1a); round_ears(m, .1, 0x8a6640, at=(.33, -.04, -.12))
    rr, dep, lb = rear(m); o = rr + np.array([0, -dep * .2, 6])
    m.tube([o, o + np.array([0, -dep * .9, -lb * .25]), o + np.array([0, -dep * 1.6, -lb * .55]), o + np.array([0, -dep * 1.2, -lb * .85]), o + np.array([0, -dep * .6, -lb * .95])],
           [dep * .14, dep * .13, dep * .12, dep * .11, dep * .09], 0x8a6640, "Back", sides=6)
    m.variants = [{}, {0xa47c50: 0x18181e, 0xe2d2b4: 0x202028, 0xeee2cc: 0x202028, 0x8a6640: 0x131317}]
    return moves(m, eat=(.6, .4))

def lion(male):
    m = dog(base("Pug"), 1.5, 1.5, 1.45, .8, .85, 1.0, .82, 1.4, thick=.95)
    dog_paint(m, 0xc49a60, 0xe0caa0, muzzle=0xe8d8b8, nose=0x3a2622); round_ears(m, .1, 0xb08a52, at=(.33, -.04, -.12))
    rr, dep, lb = rear(m); o = rr + np.array([0, -dep * .2, 6])
    m.tube([o, o + np.array([0, -dep * .9, -lb * .2]), o + np.array([0, -dep * 1.5, -lb * .45]), o + np.array([0, -dep * 1.6, -lb * .7])], [dep * .1, dep * .09, dep * .08, dep * .07], 0xc49a60, "Back", sides=6)
    blob(m, o + np.array([0, -dep * 1.62, -lb * .72]), dep * .16, 0x2a1e14, "Back", n=6, rows=3)
    if male:
        o2, Lh = hunits(m); hj = J(m, "Head")
        blob(m, o2 + np.array([0, -.45, -.25]) * Lh, .62 * Lh, 0x7a5028, "Head", n=10, rows=5, sq=(1.05, 1.1, .75))
        blob(m, J(m, "Neck") + np.array([0, 10, 0]), .55 * Lh, 0x7a5028, "Neck", n=8, rows=4, sq=(1, 1.1, 1.1))
    return moves(m, eat=(.6, .4))
@recipe("lion")
def _lion(): return lion(False)
@recipe("lion_m")
def _lion_m(): return lion(True)

@recipe("baboon")
def _baboon():                                         # a dog-faced monkey on all fours: long muzzle, a grey-olive mane, the tail arched over
    m = dog(base("Pug"), 1.7, 1.45, 1.05, .78, .85, .9, .7, 2.0, thick=.9, tilt=.25)
    hb0, hb1 = headbox(m)
    def f(c, b, k, L):
        if b == "Head" and c[2] > L["hb1"][2] - 50: return 0x3a2a24
        if b in ("Neck", "Shoulders") or (is_body(b) and c[2] > L["sh"][2] - 20 and c[1] > L["belly"]): return 0xa89a78
        if is_body(b) and c[2] < L["z0"] + 25: return 0xb87a78
        return 0x7a6a4a
    paint_rule(m, f); round_ears(m, .07, 0x5e5236, at=(.35, -.1, -.15))
    rr, dep, lb = rear(m); o = rr + np.array([0, -dep * .1, 4])
    m.tube([o, o + np.array([0, dep * .35, -lb * .18]), o + np.array([0, dep * .1, -lb * .35]), o + np.array([0, -dep * .5, -lb * .45]), o + np.array([0, -dep * 1.1, -lb * .45])],
           [dep * .08, dep * .075, dep * .07, dep * .06, dep * .05], 0x6e6044, "Back", sides=5)
    return moves(m, eat=(.6, .4))

@recipe("rabbit")
def _rabbit():                                         # round, big hind legs, long ears, a white puff of a tail
    m = base("Pug"); pug_tail_off(m); pug_ears_off(m)
    legs(m, 1.0, 1.25, thick=.85, thickB=1.15); body(m, L=.85, G=.9, H=.95); neck(m, .8, .9, tilt=-.2); head(m, .78, snout=1.15, sx=.85)
    dog_paint(m, 0x8a7a62, 0xeae4d8, nose=0x5a3a34)
    ears(m, (.18, -.05, -.18), (.24, 1.0, -.45), .13, 0x7a6a52, flat=.3)
    rr, dep, lb = rear(m); blob(m, rr + np.array([0, -dep * .3, 0]), dep * .2, 0xf6f6f2, "Back", n=6, rows=3)
    m.variants = [{}, {0x8a7a62: 0xeeeeea, 0x7a6a52: 0xe4e4de, 0xeae4d8: 0xf4f4f0}]                      # brown, the snowshoe's winter white
    return moves(m, eat=(.5, .4))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for k, f in R.items():
        if ONLY and k not in ONLY: continue
        m = f(); m.ground() if False else None
        info = m.save(os.path.join(OUT, k + ".bin")); print(k, info["tris"], "tris", info["bytes"] // 1024, "KB", [c[0] for c in info["clips"]])
