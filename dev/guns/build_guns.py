"""Turn the Quaternius Ultimate Gun Pack picks into small .glb files for Just Trees (1.89).
Each file: three meshes (body, mag, charge) in the game's gun space (forward -z, up +y, right +x, metres),
non-indexed triangles (flat shading), int16 positions (node scale), RGBA8 vertex colours; the gun's hold
points (grip, fore, muzzle, eye, handle, counter, mag drop...) go in the scene's extras as GUNSPOT values."""
import sys, os, json, struct, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from islands import islands

PICKS = {   # Ron's picks, tier 1 (white) .. 5 (red)
    "hunt":   ["SniperRifle_6", "SniperRifle_2", "SniperRifle_4", "SniperRifle_1", "SniperRifle_3"],
    "ar":     ["AssaultRifle_1", "AssaultRifle_3", "AssaultRifle_2", "AssaultRifle_4", "AssaultRifle_5"],
    "smg":    ["SubmachineGun_1", "SubmachineGun_4", "SubmachineGun_3", "SubmachineGun_2", "SubmachineGun_5"],
    "pistol": ["Pistol_2", "Pistol_1", "Pistol_5", "Pistol_4", "Pistol_6"],
}
GUN_SIZE = 1.15                                                       # 1.95 (Ron): all the guns 15% bigger
SCALE = {"hunt": .158, "ar": .162, "smg": .15, "pistol": .115}       # pack units -> metres (sniper ~1.15 m, AK ~0.9 m, pistol ~0.21 m)
GRIP0 = {"hunt": (-.2, -.18), "ar": (.07, .05), "smg": (-.03, -.05), "pistol": (-.03, -.03)}   # where the trigger hand holds (pack x, y), refined below
COLS = {"Black": (50, 52, 56), "Black2": (40, 40, 43), "DarkMetal": (72, 76, 82), "Metal": (118, 122, 128), "LightMetal": (176, 180, 186),
        "Grey": (148, 150, 144), "Glass": (70, 105, 135), "Green": (112, 132, 86), "Wood": (176, 124, 80), "DarkWood": (112, 74, 46)}

def to_game(p, s):            # pack (x fwd, y up, z right) -> game (x right, y up, z back), metres
    return (p[2] * s, p[1] * s, -p[0] * s)

def build(kind, name):
    isl, V, tris, kd = islands(name)
    s = SCALE[kind] * GUN_SIZE
    allv = [V[i] for t in tris for i in t[:3]]
    gx0, gy0 = GRIP0[kind]
    def cen(o): b = o['bb']; return ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
    # magazine: the lowest piece forward of the grip
    mag = None
    if kind in ("ar", "smg"):
        cand = [o for o in isl if cen(o)[0] > .45 and o['n'] >= 20]
        mag = min(cand, key=lambda o: o['bb'][2])
    elif kind == "hunt" and False:                          # (the snipers' only low piece is the trigger guard: they get a flush box magazine made below)
        cand = [o for o in isl if .3 < cen(o)[0] < 1.6 and o['bb'][2] < -.22 and o['n'] >= 12 and (o['bb'][1] - o['bb'][0]) < .7 and 'Glass' not in o['mats']]
        cand = [o for o in cand if not any(m in o['mats'] for m in ('Wood', 'DarkWood', 'Green')) ]
        mag = min(cand, key=lambda o: o['bb'][2]) if cand else None
        if mag and mag['bb'][3] - mag['bb'][2] > .6: mag = None          # that's the trigger guard or the stock, not a box magazine
    # charge: the sniper's bolt handle (sticks out to the right), the pistol's slide (everything on top); rifles/SMGs get a small handle made here
    charge = []
    if kind == "hunt":
        c = [o for o in isl if o['bb'][5] > .18 and o['bb'][4] > -.12 and o['n'] < 160 and 'Glass' not in o['mats']]
        if c: charge = [min(c, key=lambda o: abs(cen(o)[0] - .3))]
    elif kind == "pistol":
        top = max((o for o in isl if o['n'] > 100), key=lambda o: cen(o)[1])
        yy = top['bb'][2] - .01
        charge = [o for o in isl if o['bb'][2] >= yy]
    used = set()
    def tri_list(objs):
        out = []
        for o in objs: out += o['tris']; used.update(o['tris'])
        return out
    magT = tri_list([mag]) if mag else []
    chT = tri_list(charge)
    bodyT = [i for i in range(len(tris)) if i not in used]
    def bbox(tl):
        vs = [V[i] for t in tl for i in tris[t][:3]]
        return [min(v[k] for v in vs) for k in range(3)], [max(v[k] for v in vs) for k in range(3)]
    bmin, bmax = bbox(bodyT)
    # muzzle: the front end of the barrel
    mx = max(v[0] for v in allv); front = [v for v in allv if v[0] > mx - .04]
    muzzle = (mx, sum(v[1] for v in front) / len(front), 0)
    # scope eyepiece (snipers): the rearmost glass
    glass = [V[i] for t in tris if t[3] == 'Glass' for i in t[:3]]
    eye = None; lensR = None
    if glass and kind == "hunt":
        gmin = min(v[0] for v in glass); rear = [v for v in glass if v[0] < gmin + .05]
        eye = (gmin - .02, (max(v[1] for v in rear) + min(v[1] for v in rear)) / 2, 0)
        lensR = (max(v[1] for v in rear) - min(v[1] for v in rear)) / 2
    # the barrel line height near the front, for the fore grip and iron sights
    def slab(x, w=.06, ymax=None):
        vs = [V[i] for t in bodyT for i in tris[t][:3] if abs(V[i][0] - x) < w and (ymax is None or V[i][1] < ymax)]
        return vs
    gx, gy = gx0, gy0
    if kind == "ar":                                                     # the AK's pistol grip is its own piece: hold its middle
        gi = [o for o in isl if -.3 < cen(o)[0] < .4 and o['bb'][2] < 0 and o['n'] >= 40 and o is not mag]
        if gi: gx, gy = cen(gi[0])[0], cen(gi[0])[1]
    L = mx - gx
    if kind == "pistol":
        fore = (gx + .05, gy - .32, 0)                                   # the other hand cups under the grip
    else:
        fx = gx + L * .48
        if mag:                                                          # 1.90 (Ron): the front hand holds just in front of the magazine
            mv = [V[i] for t in mag['tris'] for i in tris[t][:3]]; ymx = max(v[1] for v in mv); h = ymx - min(v[1] for v in mv)
            fx = max(v[0] for v in mv if v[1] > ymx - .2 * h) + (.14 if kind == "ar" else .1)
        top_scope = eye[1] - lensR - .05 if eye else None
        vs = slab(fx, ymax=top_scope)
        fore = (fx, (min(v[1] for v in vs) + max(v[1] for v in vs)) / 2 if vs else muzzle[1], 0)
    if not eye:
        rear = [v for v in allv if v[0] < gx + .3 and v[0] > gx - .4]
        eye = (gx - .6 if kind != "pistol" else gx - 1.2, max(v[1] for v in rear) + .05, 0)
    # the magazine: its own group at the mouth of the magazine well, sliding along the magazine's top
    magInfo = None
    if mag:
        mv = [V[i] for t in magT for i in tris[t][:3]]
        ymx = max(v[1] for v in mv); ymn = min(v[1] for v in mv); h = ymx - ymn
        b1 = [v for v in mv if v[1] > ymx - .25 * h]; b2 = [v for v in mv if ymx - .55 * h < v[1] <= ymx - .25 * h]
        c1 = [sum(v[k] for v in b1) / len(b1) for k in range(3)]; c2 = [sum(v[k] for v in b2) / len(b2) for k in range(3)] if b2 else [c1[0], c1[1] - 1, c1[2]]
        d = [c2[0] - c1[0], c2[1] - c1[1], 0]; dl = math.hypot(d[0], d[1]); d = [d[0] / dl, d[1] / dl, 0]
        top = (c1[0], ymx, 0)
        magInfo = {"top": top, "dir": d, "h": h}
    return dict(kind=kind, name=name, V=V, tris=tris, bodyT=bodyT, magT=magT, chT=chT, s=s, grip=(gx, gy), muzzle=muzzle, eye=eye, lensR=lensR, fore=fore,
                bmin=bmin, bmax=bmax, magInfo=magInfo, chargeIs=[c['bb'] for c in charge])

def write_glb(path, meshes, extras):
    """meshes: list of (name, positions[list of game-space xyz per vertex], colors[rgb per vertex], translation)"""
    bin_ = bytearray(); bviews = []; accs = []; nodes = []; mjs = []
    for mi, (name, pos, col, tr) in enumerate(meshes):
        if not pos: continue
        mx = max(max(abs(c) for c in p) for p in pos) or 1; q = mx / 32767
        pb = b''.join(struct.pack('<hhh', *[int(round(c / q)) for c in p]) + b'\0\0' for p in pos)   # 8-byte stride (aligned)
        cb = b''.join(struct.pack('<BBBB', *c, 255) for c in col)
        for data, stride in ((pb, 8), (cb, 4)):
            while len(bin_) % 4: bin_ += b'\0'
            bviews.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data), "byteStride": stride}); bin_ += data
        mins = [min(int(round(p[k] / q)) for p in pos) for k in range(3)]; maxs = [max(int(round(p[k] / q)) for p in pos) for k in range(3)]
        accs.append({"bufferView": len(bviews) - 2, "componentType": 5122, "count": len(pos), "type": "VEC3", "min": mins, "max": maxs})
        accs.append({"bufferView": len(bviews) - 1, "componentType": 5121, "normalized": True, "count": len(col), "type": "VEC4"})
        mjs.append({"name": name, "primitives": [{"attributes": {"POSITION": len(accs) - 2, "COLOR_0": len(accs) - 1}}]})
        nodes.append({"name": name, "mesh": len(mjs) - 1, "translation": list(tr), "scale": [q, q, q]})
    js = {"asset": {"version": "2.0", "generator": "Just Trees build_guns.py"}, "extensionsUsed": ["KHR_mesh_quantization"], "extensionsRequired": ["KHR_mesh_quantization"],
          "scene": 0, "scenes": [{"nodes": list(range(len(nodes))), "extras": extras}], "nodes": nodes, "meshes": mjs, "accessors": accs, "bufferViews": bviews,
          "buffers": [{"byteLength": len(bin_)}]}
    jb = json.dumps(js, separators=(',', ':')).encode()
    while len(jb) % 4: jb += b' '
    while len(bin_) % 4: bin_ += b'\0'
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(bin_)) + struct.pack('<II', len(jb), 0x4E4F534A) + jb + struct.pack('<II', len(bin_), 0x004E4942) + bin_
    open(path, 'wb').write(out)

def mesh_of(G, tl, origin, qinv=None):
    s = G['s']; pos = []; col = []
    for t in tl:
        a, b, c, m = G['tris'][t]
        for i in (a, b, c):
            v = G['V'][i]; p = [v[0] - origin[0], v[1] - origin[1], v[2] - origin[2]]
            if qinv: p = qinv(p)
            pos.append(to_game(p, s)); col.append(COLS.get(m, (110, 110, 110)))
    return pos, col

def box_tris(cx, cy, cz, sx, sy, sz):                      # an axis-aligned box in pack units, as 12 triangles of 3 points
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4), (3, 7, 6), (3, 6, 2), (0, 4, 7), (0, 7, 3), (1, 2, 6), (1, 6, 5)]
    return [[P[a], P[b], P[c]] for a, b, c in F]

def game_spot(G, p): return [round(c, 4) for c in to_game(p, G['s'])]

def export(G, path):
    kind, s = G['kind'], G['s']
    meshes = []; extras = {}
    body = mesh_of(G, G['bodyT'], (0, 0, 0)); meshes.append(("body", body[0], body[1], (0, 0, 0)))
    gx, gy = G['grip']
    # magazine
    if G['magInfo']:
        mi = G['magInfo']; top = mi['top']; d = mi['dir']
        ang = math.atan2(d[0], -d[1])                                  # tilt from straight down (forward = positive)
        ca, sa = math.cos(-ang), math.sin(-ang)
        rot = lambda p: [p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca, p[2]]
        mp, mc = mesh_of(G, G['magT'], top, rot)
        meshes.append(("mag", mp, mc, to_game(top, s)))
        extras["magTilt"] = round(ang, 4); drop = mi['h'] * s * .55; magC = mi['h'] * s * .5
    else:                                                               # a magazine made here (pistols: in the grip; snipers: a flush box)
        if kind == "pistol":
            top = (gx - .04, gy + .05, 0); h = .48; w = .14; dz = .2; ang = .22   # grip rakes back a little
            tris = box_tris(0, -h / 2, 0, w, h, dz) + box_tris(0, -h - .02, 0, w + .05, .04, dz + .04)
        else:
            mxp = gx + .75; vs = [G['V'][i] for t in G['bodyT'] for i in G['tris'][t][:3] if abs(G['V'][i][0] - mxp) < .1]
            low = min(v[1] for v in vs); h = .24; ang = 0
            top = (mxp, low + h - .05, 0)                                # tucked into the stock, its floor plate just showing
            tris = box_tris(0, -h / 2, 0, .4, h, .13)
        mp = []; mc = []
        for t in tris:
            for p in t: mp.append(to_game(p, s)); mc.append(COLS['Black'])   # built upright; the game tilts the group by magTilt (about +x)
        meshes.append(("mag", mp, mc, to_game(top, s)))
        extras["magTilt"] = round(-ang, 4); drop = h * s * .55; magC = h * s * .5
    # charge: the sniper's bolt / the pistol's slide (cut from the model), or a small handle made here
    if G['chT']:
        cv = [G['V'][i] for t in G['chT'] for i in G['tris'][t][:3]]
        if kind == "hunt":                                              # pivot on the bolt's axis (its innermost end)
            piv = (sum(v[0] for v in cv) / len(cv), max(v[1] for v in cv) - .03, 0)
        else: piv = (min(v[0] for v in cv), min(v[1] for v in cv), 0)
        cp, cc = mesh_of(G, G['chT'], piv)
        meshes.append(("charge", cp, cc, to_game(piv, s)))
        if kind == "hunt": hp = (sum(v[0] for v in cv) / len(cv), min(v[1] for v in cv) + .03, max(v[2] for v in cv) - .03)
        else: hp = (min(v[0] for v in cv) + .12, max(v[1] for v in cv) - .03, 0)
    else:                                                               # rifles/SMGs: a charging handle on the right of the receiver
        mt = G['magInfo']['top'] if G['magInfo'] else (gx + .7, 0, 0)
        piv = (mt[0] - .05, G['bmax'][1] - (.22 if kind == "ar" else .18), G['bmax'][2] * .7)
        tris = box_tris(0, 0, .07, .16, .07, .14) + box_tris(.02, 0, .15, .06, .1, .05)
        cp = []; cc = []
        for t in tris:
            for p in t: cp.append(to_game(p, s)); cc.append(COLS['DarkMetal'])
        meshes.append(("charge", cp, cc, to_game(piv, s)))
        hp = (piv[0], piv[1], piv[2] + .16)
    extras.update({
        "grip": game_spot(G, (gx, gy, 0)),
        "fore": game_spot(G, G['fore']), "muzzle": game_spot(G, G['muzzle']), "eye": game_spot(G, G['eye']),
        "handle": game_spot(G, hp), "counter": [round(G['bmax'][2] * s + .003, 4), round((gy + .35) * s, 4), round(-(gx + (.35 if kind != "pistol" else .45)) * s, 4)],
        "drop": round(drop, 4), "magC": round(magC, 4), "lensR": round(G['lensR'] * s, 4) if G['lensR'] else None,
        "pull": {"hunt": .12, "ar": .1, "smg": .08, "pistol": .06}[kind], "name": G['name'], "len": round((G['muzzle'][0] - min(v[0] for v in G['V'])) * s, 3)})
    write_glb(path, meshes, extras)
    return extras

def rotz(p, a):
    c, s_ = math.cos(a), math.sin(a)
    return [p[0] * c - p[1] * s_, p[0] * s_ + p[1] * c, p[2]]

if __name__ == '__main__':
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True); info = {}
    for kind, names in PICKS.items():
        for t, n in enumerate(names, 1):
            G = build(kind, n); e = export(G, os.path.join(outdir, f"{kind}_{t}.glb"))
            info[f"{kind}_{t}"] = e
            print(kind, t, n, "body", len(G['bodyT']), "mag", len(G['magT']) or "made", "charge", len(G['chT']) or "made", "len", e['len'], "kB", os.path.getsize(os.path.join(outdir, f"{kind}_{t}.glb")) // 1024)
    json.dump(info, open(os.path.join(outdir, "_spots.json"), "w"), indent=1)
