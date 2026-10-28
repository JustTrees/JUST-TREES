"""2.52: Big heads (PvP setup button, the host's choice online): every person's head is 4x, and the head you can hit is the one you
see: a shot passing well above a normal head hits a big one (a headshot), and misses with it off. Dead animals lie a minute, then fade
away over a few seconds and are gone (their see-through copies don't touch the living animals' look).
Served over http (the people load). Usage: python3 dev/test_252.py dbg.html"""
import os, sys, asyncio, json, threading, shutil, tempfile
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=srvdir, **k)
    def log_message(self, *a): pass
srv = ThreadingHTTPServer(("127.0.0.1", 0), H); PORT = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:200]))
        await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(1000)
        await pg.evaluate("""() => { window.FREEZE = true; D.setVR(true); D.setVRON(true); D.vr.on = true; try { localStorage.setItem('jt-age', 'ok'); } catch (_) {} D.VRUI.rulesOk = true;
          window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => !(w.hide && w.hide()) && !w.ghost && (w.label === l || (w.labelFn && w.labelFn() === l)));
          D.vruiOpen('mode'); W('mode', 'Solo').on(); W('setup', 'Bot battle').on(); return 1; }""")
        out = {}
        out["button"] = await pg.evaluate("() => { const w = W('setup', 'Big heads'); if (!w) return null; const a = !!D.set.bigHead; w.on(); const b = !!D.set.bigHead; w.on(); return [a, b, !!D.set.bigHead]; }")
        await pg.evaluate("() => { D.setSeed(4242); Object.assign(D.set, { size: 'medium', zone: 'off', capture: 'off', teams: 'solo', hour: 13, weather: 'clear', botFill: 3 }); D.generate(); D.state = 'play'; D.vbFit(); D.vbRoundStart(); return 1; }")
        for _ in range(240):
            if await pg.evaluate("() => { for (let i = 0; i < 3; i++) D.vbTick(1 / 30); return D.VB.list.some(B => B.C && B.alive) || D.CHAR.failed > 0; }"): break
            await pg.wait_for_timeout(250)
        out["shots"] = await pg.evaluate("""() => { const B = D.VB.list.find(B => B.C && B.alive); if (!B) return null; const T = D.THREE, res = {};
          for (const on of [false, true]) { D.set.bigHead = on; D.camera.position.set(B.x + 4, B.y + 1.6, B.z); D.camera.updateMatrixWorld(); for (let i = 0; i < 6; i++) D.vbTick(1 / 30); B.C.top.updateMatrixWorld(true);
            const hp = B.C.by.Head.getWorldPosition(new T.Vector3()), sc = B.C.by.Head.scale.x; let hits = 0, heads = 0;
            for (let k = 0; k < 8; k++) { const a = k * .785, from = new T.Vector3(hp.x + Math.sin(a) * 6, hp.y + .45, hp.z + Math.cos(a) * 6), dir = new T.Vector3(hp.x, hp.y + .45, hp.z).sub(from).normalize();
              const h = D.vbRayOne(B, from, dir, 20); if (h) { hits++; if (h.head) heads++; } }
            const nh = new T.Vector3(hp.x + 6, hp.y + .1, hp.z), body = D.vbRayOne(B, nh, new T.Vector3(-1, 0, 0), 20);
            res[on ? 'on' : 'off'] = { scale: sc, hits, heads, normalHead: !!(body && body.head) }; }
          D.set.bigHead = false; return res; }""")
        # dead animals: a minute, then they fade and are gone
        out["fade"] = await pg.evaluate("""() => { D.setMode('hunt'); D.set.dino = false; D.set.size = 'medium'; D.generate(); D.state = 'play';
          const A = D.beasts.find(A => !A.wings && !A.ptero && A.kind !== 'monkey' && A.root), O = D.beasts.find(B => B !== A && B.kind === A.kind && !B.wings);
          let mat0 = null; A.root.traverse(o => { if (o.material && !mat0) mat0 = Array.isArray(o.material) ? o.material[0] : o.material; });
          D.killAnimal(A, 50); const r = { kind: A.kind, n0: D.beasts.length };
          for (let i = 0; i < 59 * 10; i++) D.updateAnimals(.1); r.at59 = { in: D.beasts.includes(A), op: A.fadeMats ? 1 : 0 };
          for (let i = 0; i < 15; i++) D.updateAnimals(.1); r.mid = A.fadeMats ? +A.fadeMats[0][0].opacity.toFixed(2) : null; r.otherOk = !mat0 || mat0.opacity === 1 && !mat0.transparent || mat0.transparent;
          let othersMat = null; if (O) O.root.traverse(o => { if (o.material && !othersMat) othersMat = Array.isArray(o.material) ? o.material[0] : o.material; }); r.otherOpacity = othersMat ? othersMat.opacity : 1;
          for (let i = 0; i < 30; i++) D.updateAnimals(.1); r.gone = !D.beasts.includes(A) && !A.root.parent; r.n1 = D.beasts.length; return r; }""")
        print(json.dumps(out))
        s = out["shots"]; f = out["fade"]
        ok = out["button"] == [False, True, False] and s and s["off"]["scale"] == 1 and s["on"]["scale"] == 4 and s["off"]["hits"] == 0 and s["on"]["heads"] >= 6 and s["off"]["normalHead"] \
             and f["at59"]["in"] and 0 < f["mid"] < 1 and f["otherOpacity"] == 1 and f["gone"]
        print("errors:", errs[:3] or ("none" if ok else "CHECKS FAILED")); await b.close(); srv.shutdown()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
