"""2.03: the animals for normal hunting, in the Quaternius style (Ron: "use the animal polys he made and make adjacent ones").
A small toolkit: load a farm animal dumped from its FBX (dev/animals/dump.html: the rest pose with the mesh baked into it, colours,
skin, every clip sampled as each bone's world rotation/position), reshape it (bone lengths, regions, colours), add parts (horns,
antlers, tusks, manes, humps), copy the horse's walk / run / death onto it (world-space retargeting, so it works across the rigs),
and write the game's "QDN1" file (the same format as the dinosaurs)."""
import json, math, struct
import numpy as np

# ---------------- quaternions [x, y, z, w]
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])
def qinv(q): return np.array([-q[0], -q[1], -q[2], q[3]]) / max(1e-12, float(np.dot(q, q)))
def qrot(q, v):
    u = np.array(q[:3]); w = q[3]; v = np.array(v, float)
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)
def qaxis(axis, ang):
    a = np.array(axis, float); a /= np.linalg.norm(a); s = math.sin(ang / 2); return np.array([a[0] * s, a[1] * s, a[2] * s, math.cos(ang / 2)])
def qnorm(q): return q / np.linalg.norm(q)
def mat(p, q, s):
    x, y, z, w = q; R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R * np.array(s); M[:3, 3] = p; return M
def decompose(M):
    p = M[:3, 3].copy(); sx = np.linalg.norm(M[:3, 0]); sy = np.linalg.norm(M[:3, 1]); sz = np.linalg.norm(M[:3, 2])
    R = M[:3, :3] / np.array([sx, sy, sz]); t = np.trace(R)
    if t > 0: s = math.sqrt(t + 1) * 2; q = [(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, .25 * s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]: s = math.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2; q = [.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s, (R[2, 1] - R[1, 2]) / s]
    elif R[1, 1] > R[2, 2]: s = math.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2; q = [(R[0, 1] + R[1, 0]) / s, .25 * s, (R[1, 2] + R[2, 1]) / s, (R[0, 2] - R[2, 0]) / s]
    else: s = math.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2; q = [(R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, .25 * s, (R[1, 0] - R[0, 1]) / s]
    return p, qnorm(np.array(q)), np.array([sx, sy, sz])

class Model:
    """nodes: [{n, p, t:[px,py,pz,qx,qy,qz,qw,sx,sy,sz]}]; verts in rest (world) space; tris = consecutive triples; skin as node indices"""
    def __init__(self, nodes, pos, col, si, sw, tags=None):
        self.nodes = nodes; self.pos = np.array(pos, float).reshape(-1, 3); self.col = np.array(col, float).reshape(-1, 3)
        self.si = np.array(si, int).reshape(-1, 4); self.sw = np.array(sw, float).reshape(-1, 4); self.tag = list(tags) if tags is not None else [""] * len(self.pos)
        self.clips = {}
    @staticmethod
    def load(path):
        d = json.load(open(path)); m = Model(d["nodes"], d["pos"], d["col"], d["si"], d["sw"], d["mat"]); m.src = d; return m
    # ---- the skeleton
    def idx(self, name):
        for i, n in enumerate(self.nodes):
            if n["n"] == name: return i
        return -1
    def world(self):
        W = []
        for i, n in enumerate(self.nodes):
            t = n["t"]; L = mat(t[0:3], t[3:7], t[7:10]); W.append(L if n["p"] < 0 else W[n["p"]] @ L)
        return W
    def bpos(self, name): return self.world()[self.idx(name)][:3, 3].copy()
    def dom(self):
        """each vertex's main bone name"""
        return [self.nodes[self.si[i][int(np.argmax(self.sw[i]))]]["n"] for i in range(len(self.pos))]
    def repose(self, edits):
        """edits: {bone: {"pos": scale of its offset from the parent (number or 3-vector), "scale": uniform scale of the bone}}.
        The mesh follows its bones (each vertex moves with the bones it's skinned to)."""
        W0 = self.world()
        for name, e in edits.items():
            i = self.idx(name)
            if i < 0: continue
            t = self.nodes[i]["t"]
            if "pos" in e: k = np.array(e["pos"], float) * np.ones(3); t[0:3] = list(np.array(t[0:3]) * k)
            if "scale" in e: t[7:10] = list(np.array(t[7:10]) * e["scale"])
        W1 = self.world(); D = [W1[j] @ np.linalg.inv(W0[j]) for j in range(len(W0))]
        P = np.c_[self.pos, np.ones(len(self.pos))]; out = np.zeros_like(self.pos)
        for k in range(4):
            Mj = np.stack([D[j] for j in self.si[:, k]]); out += (np.einsum("nij,nj->ni", Mj, P)[:, :3]) * self.sw[:, k:k + 1]
        tot = self.sw.sum(1, keepdims=True); tot[tot == 0] = 1; self.pos = out / tot
    # ---- reshaping in place: move points (vertices and joints) with a function of position and bone name; rotations stay
    def warp(self, fn):
        """fn(P (n,3) world points, names [n] bone names) -> new points. Joints use their own bone's name (X_end uses X's).
        The skeleton's joint positions follow, so the moves still bend at the right places. The root never moves."""
        W0 = self.world(); jn = [(n["n"][:-4] if n["n"].endswith("_end") else n["n"]) for n in self.nodes]
        JP = np.array([M[:3, 3] for M in W0]); JP2 = np.array(fn(JP.copy(), jn), float)
        self.pos = np.array(fn(self.pos.copy(), self.dom()), float)
        keep = {"Armature", "root"}; Wn = []
        for j, n in enumerate(self.nodes):
            t = n["t"]
            if n["p"] >= 0 and n["n"] not in keep:
                lp = (np.linalg.inv(Wn[n["p"]]) @ np.r_[JP2[j], 1])[:3]; t[0:3] = [float(v) for v in lp]
            L = mat(t[0:3], t[3:7], t[7:10]); Wn.append(L if n["p"] < 0 else Wn[n["p"]] @ L)
        self.snap_feet()
    def snap_feet(self):
        W = self.world()
        for j, n in enumerate(self.nodes):
            if "Foot" in n["n"] and n["n"].endswith(("L", "R")):
                e = self.idx(n["n"].replace("Foot", "LowLeg") + "_end")
                if e < 0: continue
                lp = (np.linalg.inv(W[n["p"]]) @ np.r_[W[e][:3, 3], 1])[:3]; n["t"][0:3] = [float(v) for v in lp]
    def ground(self):
        """feet on y = 0"""
        dy = float(self.pos[:, 1].min()); self.warp(lambda P, N: P - np.array([0, dy, 0]))
    def names(self): return [n["n"] for n in self.nodes]
    # ---- regions
    def region(self, bones):
        d = self.dom(); return np.array([x in bones or any(x.startswith(b) for b in bones if b.endswith("*")) or any(x.startswith(b[:-1]) for b in bones if b.endswith("*")) for x in d])
    def scale_about(self, mask, c, s):
        s = np.array(s, float) * np.ones(3); self.pos[mask] = c + (self.pos[mask] - c) * s
    def recolor(self, fn):
        for i in range(len(self.pos)): self.col[i] = fn(i, self.pos[i], self.col[i], self.tag[i])
    def drop(self, tri_mask):
        keep = ~np.repeat(tri_mask, 3)
        self.pos, self.col, self.si, self.sw = self.pos[keep], self.col[keep], self.si[keep], self.sw[keep]; self.tag = [t for t, k in zip(self.tag, keep) if k]
    def tri_bones(self):
        d = self.dom(); return [d[i:i + 3] for i in range(0, len(d), 3)]
    # ---- new parts (rigid on one bone, or a blend)
    def add_tris(self, P, col, bone, tag="part", out=None):
        """out: a point, or a function centroid -> point, that every face should face away from"""
        P = np.array(P, float).reshape(-1, 3); n = len(P); b = self.idx(bone) if isinstance(bone, str) else bone
        if out is not None:
            T = P.reshape(-1, 3, 3)
            for t in range(len(T)):
                c = T[t].mean(0); o = out(c) if callable(out) else np.array(out, float); nn = np.cross(T[t, 1] - T[t, 0], T[t, 2] - T[t, 0])
                if nn.dot(c - o) < 0: T[t] = T[t][[0, 2, 1]]
            P = T.reshape(-1, 3)
        self.pos = np.r_[self.pos, P]; self.col = np.r_[self.col, np.tile(rgb(col), (n, 1))]
        self.si = np.r_[self.si, np.tile([b, 0, 0, 0], (n, 1))]; self.sw = np.r_[self.sw, np.tile([1, 0, 0, 0], (n, 1))]; self.tag += [tag] * n
    def add_loft(self, rings, col, bone, cap0=True, cap1=True, tag="part", out=None):
        T = []; n = len(rings[0])
        for i in range(len(rings) - 1):
            A, B = rings[i], rings[i + 1]
            for k in range(n):
                k2 = (k + 1) % n; T += [A[k], B[k], B[k2], A[k], B[k2], A[k2]]
        if cap0: c = sum(rings[0]) / n; [T.extend([c, rings[0][(k + 1) % n], rings[0][k]]) for k in range(n)]
        if cap1: c = sum(rings[-1]) / n; [T.extend([c, rings[-1][k], rings[-1][(k + 1) % n]]) for k in range(n)]
        self.add_tris(T, col, bone, tag, out=out)
    def tube(self, pts, radii, col, bone, sides=6, up=(0, 1, 0), tag="part", cap0=True):
        pts = [np.array(p, float) for p in pts]; rings = []
        for i, p in enumerate(pts):
            q = pts[min(i + 1, len(pts) - 1)]; o = pts[max(i - 1, 0)]; ax = q - o
            rings.append(ring(p, ax, up, radii[i], radii[i], sides))
        def near(c):                                  # the closest point on the tube's own line
            best, bd = pts[0], 1e18
            for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
                ab = b - a; t = (c - a).dot(ab) / max(ab.dot(ab), 1e-12)
                if k == len(pts) - 2 and t > .98: q = b - ab * .3          # the end caps face outward along the line
                elif k == 0 and t < .02: q = a + ab * .3
                else: q = a + ab * max(0.0, min(1.0, t))
                d = np.sum((c - q) ** 2)
                if d < bd: best, bd = q, d
            return best
        self.add_loft(rings, col, bone, cap0=cap0, cap1=True, tag=tag, out=near)
    # ---- moves: copy clips from a source dump (world-space retargeting)
    def retarget(self, src, names, rename=None, body="Body", posScale=None):
        """src: a loaded source Model (with .src clips). Copies each clip's motion: every bone keeps its own rest orientation
        and turns the way the source's bone of the same name turns in the world; the body bobs/falls scaled to this animal."""
        Wt = self.world(); restQ = [decompose(M)[1] for M in Wt]; restP = [M[:3, 3] for M in Wt]
        sidx = {n["n"]: i for i, n in enumerate(src.src["nodes"])}
        sRestQ = {n["n"]: np.array(n["wq"]) for n in src.src["nodes"]}; sRestP = {n["n"]: np.array(n["wp"]) for n in src.src["nodes"]}
        hipT = max(1e-6, restP[self.idx(body)][1] - min(self.pos[:, 1])); hipS = max(1e-6, sRestP[body][1] - min(np.array(src.src["pos"]).reshape(-1, 3)[:, 1]))
        k = posScale if posScale is not None else hipT / hipS
        for cname in names:
            c = src.src["clips"].get(cname)
            if not c: continue
            frames = []
            feet = {j: self.idx(n["n"].replace("Foot", "LowLeg") + "_end") for j, n in enumerate(self.nodes) if n["n"].endswith(("FootL", "FootR")) and "Foot" in n["n"]}
            for row in c["frames"]:
                Wq = [None] * len(self.nodes); loc = []
                for j, n in enumerate(self.nodes):
                    if n["n"] in sidx and not n["n"].endswith("_end"):
                        sq = np.array(row[sidx[n["n"]]][3:7]); D = qmul(sq, qinv(sRestQ[n["n"]])); Wq[j] = qnorm(qmul(D, restQ[j]))
                    else:
                        Wq[j] = qnorm(qmul(Wq[n["p"]], np.array(n["t"][3:7]))) if n["p"] >= 0 else restQ[j]
                    if n["p"] >= 0: Lq = qnorm(qmul(qinv(Wq[n["p"]]), Wq[j]))
                    else: Lq = Wq[j]
                    lp = None
                    if n["n"] == body and body in sidx:
                        dp = (np.array(row[sidx[body]][0:3]) - sRestP[body]) * k; wp = restP[j] + dp
                        par = Wt[n["p"]] if n["p"] >= 0 else np.eye(4); lp = (np.linalg.inv(par) @ np.r_[wp, 1])[:3]   # (parent assumed still)
                    loc.append([Lq, lp])
                if feet:                                    # the feet are IK targets under the root: put each at the end of its own leg
                    Wm = []
                    for j, n in enumerate(self.nodes):
                        t = n["t"]; lp = loc[j][1] if loc[j][1] is not None else t[0:3]; L = mat(lp, loc[j][0], t[7:10]); Wm.append(L if n["p"] < 0 else Wm[n["p"]] @ L)
                    for j, e in feet.items():
                        if e < 0: continue
                        par = Wm[self.nodes[j]["p"]]; loc[j][1] = (np.linalg.inv(par) @ np.r_[Wm[e][:3, 3], 1])[:3]
                frames.append([tuple(x) for x in loc])
            self.clips[rename.get(cname, cname) if rename else cname] = {"d": c["d"], "frames": frames}
    def pose_clip(self, name, dur, keys, fps=30):
        """a made-up move: keys(t) -> {bone: quaternion}, world-space turns of each bone about its own joint (passed down to its children)"""
        Wt = self.world(); restQ = [decompose(M)[1] for M in Wt]; nf = max(2, int(round(dur * fps)) + 1); frames = []
        feet = {j: self.idx(n["n"].replace("Foot", "LowLeg") + "_end") for j, n in enumerate(self.nodes) if "Foot" in n["n"] and n["n"].endswith(("L", "R"))}
        for f in range(nf):
            K = keys(dur * f / (nf - 1)); Dt = [None] * len(self.nodes); Wq = [None] * len(self.nodes); loc = []
            for j, n in enumerate(self.nodes):
                d = np.array(K.get(n["n"], (0, 0, 0, 1)), float); Dt[j] = qnorm(qmul(Dt[n["p"]], d)) if n["p"] >= 0 else d
                if n["n"] in feet or (n["p"] >= 0 and self.nodes[n["p"]]["n"] in ("root",)): Dt[j] = d if n["n"] in feet else Dt[j]
                Wq[j] = qnorm(qmul(Dt[j], restQ[j])); Lq = qnorm(qmul(qinv(Wq[n["p"]]), Wq[j])) if n["p"] >= 0 else Wq[j]; loc.append([Lq, None])
            self._snap(loc, feet); frames.append([tuple(x) for x in loc])
        self.clips[name] = {"d": dur, "frames": frames}
    def _snap(self, loc, feet):
        Wm = []
        for j, n in enumerate(self.nodes):
            t = n["t"]; lp = loc[j][1] if loc[j][1] is not None else t[0:3]; L = mat(lp, loc[j][0], t[7:10]); Wm.append(L if n["p"] < 0 else Wm[n["p"]] @ L)
        for j, e in feet.items():
            if e >= 0: loc[j][1] = (np.linalg.inv(Wm[self.nodes[j]["p"]]) @ np.r_[Wm[e][:3, 3], 1])[:3]
    def copy_clip(self, a, b, speed=1.0):
        c = self.clips[a]; self.clips[b] = {"d": c["d"] / speed, "frames": c["frames"]}
    def own_clips(self, names, rename=None):
        """this model's own sampled clips (its rest is unchanged), turned into local keys the same way"""
        self.retarget(self, names, rename)
    # ---- write the game's file
    def save(self, path, soft=.35, step=2):
        n = len(self.pos); assert n % 3 == 0
        P = self.pos.reshape(-1, 3, 3); fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); fnu = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        acc = {}
        for ti in range(len(P)):
            for k in range(3): key = tuple(np.round(P[ti, k] * 50).astype(int)); acc[key] = acc.get(key, 0) + fn[ti]
        nrm = np.zeros((n, 3))
        for ti in range(len(P)):
            for k in range(3):
                sm = acc[tuple(np.round(P[ti, k] * 50).astype(int))]; sm = sm / max(np.linalg.norm(sm), 1e-12); v = fnu[ti] * (1 - soft) + sm * soft; nrm[ti * 3 + k] = v / max(np.linalg.norm(v), 1e-12)
        mn = self.pos.min(0); mx = self.pos.max(0)
        pq = np.round((self.pos - mn) / np.maximum(mx - mn, 1e-9) * 65535 - 32768).astype(np.int16)
        nq = np.zeros((n, 4), np.int8); nq[:, :3] = np.round(nrm * 127).astype(np.int8)
        col = np.zeros((n, 4), np.uint8); col[:, :3] = np.clip(np.round(self.col * 255), 0, 255); col[:, 3] = 255
        # skin: the bones the mesh uses become the skeleton
        used = sorted(set(int(b) for b, w in zip(self.si.reshape(-1), self.sw.reshape(-1)) if w > 0))
        remap = {b: i for i, b in enumerate(used)}; si = np.zeros((n, 4), np.uint8); sw = np.zeros((n, 4), np.uint8)
        for i in range(n):
            ws = sorted([(self.si[i, k], self.sw[i, k]) for k in range(4) if self.sw[i, k] > 0], key=lambda x: -x[1])[:4]; tot = sum(w for _, w in ws) or 1
            q = [int(round(w / tot * 255)) for _, w in ws]; q[0] += 255 - sum(q)
            for k, (b, _) in enumerate(ws): si[i, k] = remap[int(b)]; sw[i, k] = q[k]
        W = self.world(); inv = [np.linalg.inv(W[b]).T.reshape(-1).round(7).tolist() for b in used]
        parts, off = [], 0
        def put(arr):
            nonlocal off
            b = arr.tobytes(); o = off; parts.append(b); off += len(b); pad = (4 - off % 4) % 4
            if pad: parts.append(b"\0" * pad); off += pad
            return o
        nodes = [{"n": nd["n"], "p": nd["p"], "b": 1, "t": [round(float(v), 7) for v in nd["t"]]} for nd in self.nodes]
        M = {"n": n, "bb": [mn.tolist(), mx.tolist()], "p": -1, "t": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1], "bind": np.eye(4).reshape(-1).tolist(), "inv": inv, "bones": used,
             "pos": put(pq), "nrm": put(nq), "col": put(col), "si": put(si), "sw": put(sw)}
        clips = []
        for cn, c in self.clips.items():
            fr0 = c["frames"]; keep = list(range(0, len(fr0), step)); keep += [len(fr0) - 1] if keep[-1] != len(fr0) - 1 else []
            fr = [fr0[i] for i in keep]; nf = len(fr); ts = (np.array(keep, float) / max(1, len(fr0) - 1) * c["d"]).astype(np.float32); tr = []; to = put(ts)
            for j, nd in enumerate(self.nodes):
                qs = np.array([fr[f][j][0] for f in range(nf)])
                for f in range(1, nf):
                    if np.dot(qs[f], qs[f - 1]) < 0: qs[f] = -qs[f]
                rest = np.array(nd["t"][3:7])
                if np.abs(qs - rest).max() > 2e-4 and np.abs(qs + rest).max() > 2e-4:
                    tr.append({"nd": j, "pr": "q", "nk": nf, "t": to, "v": put(np.round(np.clip(qs, -1, 1) * 32767).astype(np.int16))})
                if fr[0][j][1] is not None:
                    ps = np.array([fr[f][j][1] for f in range(nf)], np.float32)
                    if np.abs(ps - np.array(nd["t"][0:3])).max() > 1e-4: tr.append({"nd": j, "pr": "p", "nk": nf, "t": to, "v": put(ps)})
            clips.append({"n": cn, "d": round(float(c["d"]), 4), "tr": tr})
        if getattr(self, "variants", None):              # other coats: colour swaps the game can pick from
            M["vars"] = [[[[int(round(x * 255)) for x in np.clip(rgb(a), 0, 1)], [int(round(x * 255)) for x in np.clip(rgb(b), 0, 1)]] for a, b in v.items()] for v in self.variants]
        js = json.dumps({"v": 1, "nodes": nodes, "mesh": M, "clips": clips}).encode(); js += b" " * ((4 - len(js) % 4) % 4)
        open(path, "wb").write(b"QDN1" + struct.pack("<I", len(js)) + js + b"".join(parts))
        return {"tris": n // 3, "bytes": 8 + len(js) + off, "clips": [(c["n"], len(c["tr"])) for c in clips]}

def ring(c, ax, up, rx, ry, n, rot=0.0):
    ax = np.array(ax, float); ax /= max(np.linalg.norm(ax), 1e-9); up = np.array(up, float); up = up - ax * up.dot(ax)
    if np.linalg.norm(up) < 1e-6: up = np.array([1.0, 0, 0]) - ax * ax[0]
    up /= np.linalg.norm(up); rt = np.cross(up, ax)
    return [np.array(c, float) + rt * math.cos(2 * math.pi * k / n + rot) * rx + up * math.sin(2 * math.pi * k / n + rot) * ry for k in range(n)]

# ---------------- reshaping helpers (all in the model's world units: cm, y up, z forward, +x = the animal's left)
def is_leg(n): return "UpLeg" in n or "LowLeg" in n or ("Foot" in n)
def is_front(n): return n.startswith("Front")
def is_neck(n): return n == "Neck"
def is_head(n): return n == "Head"
def is_tail(n): return n.startswith("Tail")
def is_body(n): return not (is_leg(n) or is_neck(n) or is_head(n) or is_tail(n))

def legs(m, fF, fB=None, thick=1.0, thickB=None):
    """legs fF (front) / fB (back) times as long (feet stay on the ground, the body rises), and thick times as thick"""
    fB = fF if fB is None else fB; thickB = thick if thickB is None else thickB
    m.ground(); W = m.world(); J = lambda n: W[m.idx(n)][:3, 3]
    top = {s: J(s + "UpLegL") for s in ("Front", "Back")}; foot = {s: J(s + "LowLegL_end") for s in ("Front", "Back")}
    yF, yB, zF, zB = top["Front"][1], top["Back"][1], top["Front"][2], top["Back"][2]
    def fn(P, N):
        for i, n in enumerate(N):
            x, y, z = P[i]
            if is_leg(n):
                s = "Front" if is_front(n) else "Back"; f = fF if s == "Front" else fB; th = thick if s == "Front" else thickB
                yt = top[s][1]; u = max(0.0, min(1.0, y / yt)); cx = abs(top[s][0]) * (1 if x >= 0 else -1); cz = foot[s][2] + (top[s][2] - foot[s][2]) * u
                P[i] = [cx + (x - cx) * th, y * f if y <= yt else y + yt * (f - 1), cz + (z - cz) * th]   # (the haunch above the hip joint rides with the body, or it pokes up over the back)
            else:
                t = max(0.0, min(1.0, (z - zB) / (zF - zB))); P[i, 1] = y + yB * (fB - 1) * (1 - t) + yF * (fF - 1) * t
        return P
    m.warp(fn)

def body(m, L=1.0, G=1.0, H=1.0, Hb=None):
    """the trunk L times as long, G times as wide, H times as deep (about the Body joint); legs, neck, head and tail ride along"""
    W = m.world(); J = lambda n: W[m.idx(n)][:3, 3]
    c = J("Body"); tops = {s: J(s + "UpLegL") for s in ("Front", "Back")}; nb = J("Neck"); tb = J("Tail1") if m.idx("Tail1") >= 0 else J("Back")
    yc = c[1]
    def at(p): return np.array([0.0, (p[1] - yc) * (H - 1), (p[2] - c[2]) * (L - 1)])
    def fn(P, N):
        for i, n in enumerate(N):
            x, y, z = P[i]
            if is_body(n): P[i] = [x * G, yc + (y - yc) * (H if (Hb is None or y > yc) else Hb), c[2] + (z - c[2]) * L]
            elif is_leg(n):
                s = "Front" if is_front(n) else "Back"; tp = tops[s]; d = at(tp); P[i] = [x + np.sign(x) * abs(tp[0]) * (G - 1), y, z + d[2]]
            elif is_tail(n): P[i] = P[i] + at(tb) * np.array([0, 1, 1])
            else: P[i] = P[i] + at(nb)
        return P
    m.warp(fn)

def neck(m, f=1.0, thick=1.0, tilt=0.0, thickH=None):
    """neck f times as long and thick times as thick; tilt (radians, + = forward/down) swings the neck and head about the neck's root"""
    W = m.world(); base = W[m.idx("Neck")][:3, 3].copy(); hj = W[m.idx("Head")][:3, 3].copy(); ax = (hj - base) / np.linalg.norm(hj - base); L0 = np.linalg.norm(hj - base)
    R = mat([0, 0, 0], qaxis([1, 0, 0], tilt), [1, 1, 1])[:3, :3]
    def fn(P, N):
        for i, n in enumerate(N):
            if is_neck(n):
                r = P[i] - base; a = r.dot(ax); pr = r - a * ax; P[i] = base + R @ (ax * a * f + pr * thick)
            elif is_head(n): P[i] = base + R @ (P[i] - base + ax * L0 * (f - 1))
        return P
    m.warp(fn)

def head(m, s=1.0, snout=1.0, sx=None, sy=None):
    """head s times as big (about its joint); snout stretches the part in front of the joint forward; sx/sy widen/deepen it"""
    W = m.world(); hj = W[m.idx("Head")][:3, 3].copy(); k = np.array([sx or 1, sy or 1, 1]) * s
    def fn(P, N):
        for i, n in enumerate(N):
            if is_head(n):
                r = (P[i] - hj) * k
                if r[2] > 0: r[2] *= snout
                P[i] = hj + r
        return P
    m.warp(fn)

def tail(m, f=1.0, thick=1.0, droop=0.0):
    W = m.world(); t1 = W[m.idx("Tail1")][:3, 3].copy(); te = W[m.idx("Tail4_end")][:3, 3].copy(); ax = (te - t1) / np.linalg.norm(te - t1)
    R = mat([0, 0, 0], qaxis([1, 0, 0], droop), [1, 1, 1])[:3, :3]
    def fn(P, N):
        for i, n in enumerate(N):
            if is_tail(n):
                r = P[i] - t1; a = r.dot(ax); pr = r - a * ax; P[i] = t1 + R @ (ax * a * f + pr * thick)
        return P
    m.warp(fn)

def tri_info(m):
    """per triangle: centroid, main bone, colour (of its first vertex)"""
    P = m.pos.reshape(-1, 3, 3); d = m.dom()
    return P.mean(1), [d[i * 3] for i in range(len(P))], m.col[0::3].copy()

def paint(m, fn):
    """fn(centroid, bone, colour) -> new colour (0..1 or 0..255 rgb / hex int) or None to keep; whole triangles, flat"""
    C, B, K = tri_info(m)
    for t in range(len(C)):
        v = fn(C[t], B[t], K[t])
        if v is None: continue
        m.col[t * 3:t * 3 + 3] = rgb(v)

LIFT = 2.3                                  # our colours a touch brighter, like the pack's (its darkest browns read as black otherwise)
def lin(c): c = np.array(c, float); return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def rgb(v):
    """a colour as the file stores it (linear, like the pack's own): hex ints and 0-255 triples are screen (sRGB) colours, 0-1 triples are already linear"""
    if isinstance(v, (int, np.integer)): return np.minimum(1, lin(np.array([(v >> 16) & 255, (v >> 8) & 255, v & 255]) / 255.0) * LIFT)
    v = np.array(v, float); return lin(v / 255.0) if v.max() > 1 else v

def drop_where(m, fn):
    C, B, K = tri_info(m); m.drop(np.array([bool(fn(C[t], B[t], K[t])) for t in range(len(C))]))

def is_col(k, ref, tol=.02): return np.abs(np.array(k) - rgb(ref)).max() < tol

def headbox(m):
    d = np.array(m.dom()); own = np.array([t != "part" for t in m.tag]); v = m.pos[(d == "Head") & own]; return v.min(0), v.max(0)   # (the head itself, not horns added to it)

def horn(m, pts, r0, r1, col, bone="Head", sides=6, mirror=True):
    """a horn / antler beam through pts (left side, +x), tapering r0 -> r1; mirrored to the right"""
    pts = [np.array(p, float) for p in pts]; n = len(pts); rad = [r0 + (r1 - r0) * i / (n - 1) for i in range(n)]
    m.tube(pts, rad, col, bone, sides=sides)
    if mirror: m.tube([p * np.array([-1, 1, 1]) for p in pts], rad, col, bone, sides=sides)

def ear(m, base, tip, w, col, inner=None, bone="Head", mirror=True, flat=.35):
    """a pointed ear: a flattened cone from base to tip"""
    for s in ((1, -1) if mirror else (1,)):
        b = np.array(base, float) * np.array([s, 1, 1]); t = np.array(tip, float) * np.array([s, 1, 1]); ax = t - b
        rg = ring(b, ax, (0, 0, 1), w, w * flat, 5); T = []
        for k in range(5): T += [rg[k], rg[(k + 1) % 5], t]
        c0 = sum(rg) / 5
        for k in range(5): T += [c0, rg[(k + 1) % 5], rg[k]]
        m.add_tris(T, col, bone, out=b + ax * .3)

def blob(m, c, r, col, bone, n=8, rows=4, sq=(1, 1, 1)):
    """a faceted ball (a hump, a mane, a nose)"""
    c = np.array(c, float); sq = np.array(sq, float); rings = []
    for i in range(1, rows):
        a = math.pi * i / rows; rings.append([c + np.array([math.cos(2 * math.pi * k / n) * math.sin(a), math.cos(a), math.sin(2 * math.pi * k / n) * math.sin(a)]) * r * sq for k in range(n)])
    top = c + np.array([0, r, 0]) * sq; bot = c - np.array([0, r, 0]) * sq; T = []
    for k in range(n): T += [top, rings[0][(k + 1) % n], rings[0][k]]
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(n): k2 = (k + 1) % n; T += [A[k], A[k2], B[k2], A[k], B[k2], B[k]]
    for k in range(n): T += [bot, rings[-1][k], rings[-1][(k + 1) % n]]
    m.add_tris(T, col, bone, out=c)

def pieces(m):
    """the separate mesh pieces (triangles that share corners), each as an array of triangle numbers"""
    P = m.pos.reshape(-1, 3, 3); key = {}; par = list(range(len(P)))
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for t in range(len(P)):
        for k in range(3):
            q = tuple(np.round(P[t, k] * 20).astype(int))
            if q in key: ra, rb = find(t), find(key[q]); par[ra] = rb
            else: key[q] = t
    g = {}
    for t in range(len(P)): g.setdefault(find(t), []).append(t)
    return [np.array(v) for v in g.values()]

def drop_pieces(m, fn):
    """drop whole pieces: fn(centre, size (bbox), triangle count, main bone) -> True to drop"""
    P = m.pos.reshape(-1, 3, 3); d = m.dom(); mask = np.zeros(len(P), bool)
    for pc in pieces(m):
        v = P[pc].reshape(-1, 3); bones = [d[t * 3] for t in pc]; mb = max(set(bones), key=bones.count)
        if fn(v.mean(0), v.max(0) - v.min(0), len(pc), mb): mask[pc] = True
    m.drop(mask)

def squash(m, sel, to):
    """move the vertices sel(p, bone) picks to to(p) (flatten a curly tail or floppy ears back into the body) - no holes"""
    d = m.dom(); W = m.world(); jn = [n["n"] for n in m.nodes]
    for i in range(len(m.pos)):
        if sel(m.pos[i], d[i]): m.pos[i] = to(m.pos[i])

def cells(m, n, seed, sel):
    """for spotted / patched coats: per triangle (centroid) -> (distance to nearest cell centre, gap to the second) over random centres on the selected triangles"""
    C, B, K = tri_info(m); idx = [t for t in range(len(C)) if sel(C[t], B[t])]; rs = np.random.RandomState(seed)
    cen = C[rs.choice(idx, size=min(n, len(idx)), replace=False)]
    out = {}
    for t in idx:
        dd = np.sort(np.linalg.norm(cen - C[t], axis=1)); out[t] = (dd[0], dd[1] - dd[0])
    return out
