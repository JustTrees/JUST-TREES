"""2.61: snipers. Every sniper model is 25% bigger and 10% wider on top (the hold points, scope eye and muzzle move with it).
A sniper bullet's damage follows the distance it flew: 70% at 50 m and in, normal at 100 m, 150% from 400 m, smooth between (other
guns unchanged); it counts as your damage on the board. The scope shows the distance (to 5 m) and, in PvP, a head and a body shot's
damage there. Served over http (the pack guns load). Usage: python3 dev/test_261.py dbg.html [outdir]"""
import os, sys, asyncio, json, subprocess, shutil, tempfile, time, struct, base64
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8791", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
def raw_box(path):                                            # the file's own size (body + parts), before the game grows it
    b = open(path, "rb").read(); jl = struct.unpack("<I", b[12:16])[0]; js = json.loads(b[20:20 + jl]); bo = 20 + jl + 8; lo = [1e9] * 3; hi = [-1e9] * 3
    for nd in js["nodes"]:
        pa = js["accessors"][js["meshes"][nd["mesh"]]["primitives"][0]["attributes"]["POSITION"]]; pv = js["bufferViews"][pa["bufferView"]]; sc = nd["scale"][0]; tr = nd.get("translation", [0, 0, 0])
        for i in range(pa["count"]):
            o = bo + pv.get("byteOffset", 0) + i * pv["byteStride"]; v = struct.unpack("<hhh", b[o:o + 6])
            for k in range(3): x = v[k] * sc + tr[k]; lo[k] = min(lo[k], x); hi[k] = max(hi[k], x)
    return [hi[k] - lo[k] for k in range(3)], js["scenes"][0]["extras"]
JS = """async (raw) => { const T = D.THREE, o = {};
  window.FREEZE = true; D.setSeed(5); D.setVR(true); D.setMode('pvp'); Object.assign(D.set, { size: 'xl', teams: 'solo', zone: 'off', capture: 'off', weather: 'clear', hour: 12 }); D.generate(); D.state = 'play';
  // the models
  D.qgunFor('hunt', 3); D.qgunFor('ar', 3); for (let i = 0; i < 100 && !(D.QGUN.models.hunt_3 && D.QGUN.models.ar_3); i++) await new Promise(r => setTimeout(r, 100));
  const box = g => { g.visible = true; g.updateMatrixWorld(true); const b = new T.Box3().setFromObject(g); g.visible = false; const s = b.getSize(new T.Vector3()); return [s.x, s.y, s.z]; };
  const Q = D.QGUN.models.hunt_3; o.loaded = !!Q; if (!Q) return o;
  o.ratio = box(Q.group).map((v, i) => +(v / raw.size[i]).toFixed(3)); o.arRatio = box(D.QGUN.models.ar_3.group).map((v, i) => +(v / raw.arSize[i]).toFixed(3));
  o.muzzle = Q.spots.muzzle.map((v, i) => +(v / (raw.ex.muzzle[i] || 1)).toFixed(3)); o.lens = +(Q.lensR / raw.ex.lensR).toFixed(3);
  // the curve
  o.mul = [0, 30, 50, 75, 100, 250, 400, 800].map(d => +D.sniperMul(d).toFixed(3));
  // real bullets into a bot hanging in the open air 60 m up, at different distances
  D.vbFit(); const B = D.VB.list[0]; o.bots = D.VB.list.length; if (!B) return o; D.vbJoin(B, true); B.C = null;
  for (const O of D.VB.list) if (O !== B) { O.alive = false; O.x = 1e5; }
  D.P.x = -560; D.P.z = 0; let top = -1e9; for (let x = -560; x <= 200; x += 5) top = Math.max(top, D.H(x, 0));
  const base = Math.round(D.WEAP.hunt.dmg * D.TIER.dmg[3]), y0 = top + 60, res = [];   // (high over the land all the way)
  const shoot = (dist, gun) => { B.alive = true; B.hp = 5000; B.sh = 0; B.x = D.P.x + dist; B.z = D.P.z; B.y = y0; if (B.S) { B.S.x = B.x; B.S.y = B.y; B.S.z = B.z; }
    const from = new T.Vector3(D.P.x, B.y + 1.0, D.P.z), dmg0 = D.MP.dmg || 0;
    const t = D.makeBullet(from, new T.Vector3(850, 0, 0), { reach: 3200, dmg: gun === 'hunt' ? base : 30, gun }); let n = 0; while (n++ < 400 && !D.bulletStep(t, 1 / 60)) {}
    return [dist, gun, 5000 - B.hp, (D.MP.dmg || 0) - dmg0]; };
  for (const d of [30, 100, 250, 400, 700]) res.push(shoot(d, 'hunt'));
  res.push(shoot(30, 'ar'), shoot(500, 'ar')); o.shots = res; o.base = base;
  // the scope readout
  D.setLoot && D.setLoot({ hunt: 3 }); D.vr.gunKind = 'hunt'; D.vr.weapon = 'hunt';
  const G = D.vrGun(); G.visible = true; const M = D.GUNSPOT.hunt.muzzle;
  G.position.set(D.P.x, y0 + .5, D.P.z); G.quaternion.setFromAxisAngle(new T.Vector3(0, 1, 0), -Math.PI / 2); G.updateMatrixWorld(true);   // pointing along +x at the bot
  B.alive = true; B.x = D.P.x + 312; B.y = y0; if (B.S) { B.S.x = B.x; B.S.y = B.y; B.S.z = B.z; }
  D.SCOPE_RO.t = 0; D.SCOPE_RO.key = ''; D.scopeReadout(); o.readKey = D.SCOPE_RO.key; o.readImg = D.SCOPE_RO.cv.toDataURL();
  G.quaternion.setFromAxisAngle(new T.Vector3(1, 0, 0), Math.PI / 2); G.updateMatrixWorld(true); D.SCOPE_RO.t = 0; D.scopeReadout(); o.skyKey = D.SCOPE_RO.key;   // straight up: the sky
  return o; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context()).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8791/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        size, ex = raw_box(os.path.join(REPO, "models/guns/hunt_3.glb")); ars, _ = raw_box(os.path.join(REPO, "models/guns/ar_3.glb"))
        r = await pg.evaluate(JS, {"size": size, "arSize": ars, "ex": ex})
        img = r.pop("readImg", None)
        if OUT and img: open(os.path.join(OUT, "t261_readout.png"), "wb").write(base64.b64decode(img.split(",")[1]))
        print(json.dumps(r))
        mul = lambda d: .7 if d <= 50 else (.7 + .3 * (lambda x: x * x * (3 - 2 * x))((d - 50) / 50) if d < 100 else (1 + .5 * (lambda x: x * x * (3 - 2 * x))((d - 100) / 300) if d < 400 else 1.5))
        ok = r.get("loaded") and all(abs(a - e) < .03 for a, e in zip(r["ratio"], [1.375, 1.25, 1.25])) and all(abs(a - 1) < .05 for a in r["arRatio"]) \
             and abs(r["muzzle"][2] - 1.25) < .01 and abs(r["lens"] - 1.25) < .01 and r["mul"] == [.7, .7, .7, .85, 1, 1.25, 1.5, 1.5]
        for d, gun, took, mine in r.get("shots", []):
            want = round(r["base"] * mul(d)) if gun == "hunt" else 30
            ok = ok and took in (want, round(r["base"] * 2 * mul(d)) if gun == "hunt" else 60) and mine == took
        ok = ok and r.get("readKey", "").startswith("310|true|") or r.get("readKey", "").startswith("315|true|")
        ok = ok and r.get("skyKey", "").startswith("|true|")
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
try: asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
