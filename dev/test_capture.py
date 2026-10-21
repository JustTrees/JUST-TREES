"""VR capture point (1.45): a smart hidden spot (higher than around it, or wooded), same for everyone, inside the last zone circle when the zone is on;
+1 point per 20 s held alone, nothing while contested, reset when you leave; flag and ring; points on the board. Usage: python3 dev/test_capture.py /tmp/dbg.html [/tmp/capt.png]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/capt.png'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 800, "height": 500})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {}, T = D.THREE, V = D.vr;
          D.setVR(true); V.on = true; D.setMode('pvp'); Object.assign(D.set, { size: 'small', weather: 'clear', hour: 14, capture: 'on', zone: 'off' }); D.setSeed(4242); D.generate(); D.state = 'play';
          const C = D.CAPT; out.made = !!C; const p1 = [C.x, C.z];
          // how "smart" is the spot: height above its surroundings and trees nearby, against the average random dry spot
          const score = (x, z) => { let ring = 0; for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283; ring += D.H(x + Math.cos(a) * 45, z + Math.sin(a) * 45); } ring /= 8; let t = 0; for (const l of D.obstacles.values()) for (const o of l) if (o.t && Math.hypot(o.x - x, o.z - z) < 18) t++; return [D.H(x, z) - ring, t]; };
          out.spot = score(C.x, C.z).map(v => +v.toFixed(1)); let n = 0, sh = 0, st = 0; for (let k = 0; k < 300 && n < 60; k++) { const x = (Math.random() * 2 - 1) * 150, z = (Math.random() * 2 - 1) * 150; if (!D.okSpot(x, z)) continue; const s = score(x, z); sh += s[0]; st += s[1]; n++; }
          out.averageSpot = [+(sh / n).toFixed(1), +(st / n).toFixed(1)];
          D.generate(); out.sameSpotAgain = Math.abs(D.CAPT.x - p1[0]) < .01 && Math.abs(D.CAPT.z - p1[1]) < .01;
          // with the zone on, it sits inside the last circle
          D.set.zone = 'on'; D.generate(); const Z = D.zone.circles[D.zone.circles.length - 1]; out.insideFinalZone = Math.hypot(D.CAPT.x - Z[0], D.CAPT.z - Z[1]) < Z[2];
          D.set.zone = 'off'; D.generate(); D.state = 'play'; const Cp = D.CAPT;
          const tick = s => { for (let i = 0; i < s * 10; i++) D.mpTick(.1); };
          D.MP.pts = 0; D.MP.dead = 0; D.P.x = Cp.x + 2; D.P.z = Cp.z; D.P.y = D.groundAt(D.P.x, D.P.z);
          tick(19); out.ptsAfter19s = D.MP.pts; tick(2); out.ptsAfter21s = D.MP.pts; out.stateMine = Cp.state;
          // someone else steps in: contested, no points
          D.MP.links.set('fake', { id: 'fake', open: true, bad: false, idx: 2, rx: [], R: { alive: true, head: new T.Vector3(Cp.x - 2, Cp.y + 1.6, Cp.z), feet: Cp.y, cur: {} } });
          tick(25); out.contested = [Cp.state, D.MP.pts];
          D.MP.links.delete('fake'); D.P.x = Cp.x + 40; tick(1); out.leftResets = Cp.prog === 0;
          // the flag, seen from 40 m away
          const I = { head: new T.Vector3(D.P.x, D.groundAt(D.P.x, D.P.z) + 1.7, D.P.z), headQ: new T.Quaternion(), hands: {} }; D.captTick(I);
          out.flagShown = Cp.flag.visible; out.flagDistM = +Cp.flag.position.distanceTo(I.head).toFixed(1);
          D.camera.position.copy(I.head); D.camera.lookAt(Cp.x, Cp.y + 2, Cp.z); D.camera.updateMatrixWorld(); D.renderer.render(D.scene, D.camera);
          window._shot = D.renderer.domElement.toDataURL('image/png'); out.flagDbg = { pos: Cp.flag.position.toArray().map(v => +v.toFixed(1)), head: I.head.toArray().map(v => +v.toFixed(1)), scale: +Cp.flag.scale.x.toFixed(2), vis: Cp.flag.visible, parent: !!Cp.flag.parent, key: Cp.key, capt: [Cp.x, Cp.y, Cp.z].map(v => +v.toFixed(1)), cam: D.camera.position.toArray().map(v => +v.toFixed(1)) };
          return out; }""")
        d = await pg.evaluate("() => window._shot"); open(SHOT, 'wb').write(base64.b64decode(d.split(',')[1]))
        print(json.dumps(r)); print("errors:", errs[:8] or "none")
        await b.close()
asyncio.run(main())
