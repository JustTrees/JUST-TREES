"""2.74: Geocaching gear, part 3 (3.24: the fishing is tested in test_324 now). The machete chops bushes (and bushes slow you down); fishing: fling-cast, a bite, jerk to hook, reel
with the other hand at the speed the bar asks, tip the rod the way the fish pulls, "Pull up!" and it flies into your hand; reel too hard
and the line snaps, too slow and it shakes free. Thermal binoculars and a thermal scope are items now (X switches them); bear spray is
item 4 (cache #8), the compass later; the campfire lights in 2 s.
Usage: python3 dev/test_274.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.removeItem('jt-geo'); localStorage.removeItem('jt-geochar'); } catch (_) {}
  D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true;
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
  D.generate(); D.state = 'play'; window.tick = n => { for (let i = 0; i < n; i++) { D.endlessTick(1 / 72); D.updateAnimals(1 / 72); D.geoTick(1 / 72); } };
  const T = D.THREE; window.hand = (pos, o) => Object.assign({ pos: pos.clone(), rayPos: pos.clone(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, sx: 0, sy: 0, a: 0, b: 0, stickBtn: 0 }, o || {});
  return true; }"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN)
        r = await pg.evaluate("""() => { const o = {}, T = D.THREE, P = D.P, V = D.vr; tick(72);
          o.order = [8, 16, 18, 26, 44, 48].map(n => D.geoRewardOf(n).item); o.models = D.GI_LIST.filter(([k]) => { let n = 0; D.giModel(k).traverse(m => { if (m.isMesh) n++; }); return n > 0; }).length;
          // thermal: binoculars from item 8 (cache #16), the scope from the last item; without them, nothing (short of the full red set)
          D.geoGearApply(14, true); V.binos = true; V.scoped = false; D.TOOL.on.binos = true; o.thB0 = D.thermalOk();
          D.geoGearApply(16, true); o.thB1 = D.thermalOk(); V.binos = false; V.scoped = true; V.gunKind = 'hunt'; D.TOOL.on.hunt = true; o.thS0 = D.thermalOk(); D.geoGearApply(48, true); o.thS1 = D.thermalOk(); V.scoped = false;
          // the campfire lights in 2 s
          D.geoFirePlace(P.x + 2, P.z); D.geoFireTick(1); const l1 = D.GEO.fire.lit; D.geoFireTick(1.1); o.fire = [l1, D.GEO.fire.lit];
          // a bush: it slows you; the machete swung through it cuts it down
          let bush = null; for (const ch of D.ENDLESS.chunks.values()) if (ch.bgrid) { for (const L of ch.bgrid.values()) { bush = L.find(t => t.s > .8 && t._b); if (bush) break; } if (bush) break; }
          o.bush = !!bush;
          if (bush) { D.geoGearApply(26, true); P.x = bush.x; P.z = bush.z; o.slow = +D.geoSpeedMul().toFixed(2); o.touch = D.geoBushTouch();
            D.geoHeld('machete'); const head = new T.Vector3(P.x, bush.y + 1.7, P.z), I = { head, headQ: new T.Quaternion(), hands: {} }, y = bush.y + bush.s * .5;
            const m = hand(new T.Vector3(bush.x - .8, y, bush.z + .39)); D.geoHeldTick(I, m, 1 / 72); for (let i = 0; i < 8; i++) { m.pos.x += .2; D.geoHeldTick(I, m, 1 / 72); }
            const B = bush._b, blk = B[0].blocks.get(B[1]); o.cut = [!!bush.cut, blk.m.slice(B[2] * 16, B[2] * 16 + 16).every(v => v === 0), D.GEO.leaves.length > 0, D.geoBushTouch() < o.touch];
            D.geoHeld(null); }
          return o; }""")
        print("gear", json.dumps(r))
        await pg.evaluate("""() => { D.set.huntMap = 'endless'; D.generate(); D.state = 'play'; }""")
        n = await pg.evaluate("""() => { D.vr.binos = true; D.vr.scoped = false; D.TOOL.on.binos = true; return [D.GEO.on, D.thermalOk(), D.geoSpeedMul()]; }""")
        print("normal", json.dumps(n))
        ok = r["order"] == ["spray", "tbinos", "rod", "machete", "compass", "tscope"] and r["models"] == 30 and r["thB0"] is False and r["thB1"] is True \
             and r["thS0"] is False and r["thS1"] is True and r["fire"] == [False, True] and r["bush"] and r["slow"] < .95 and r["touch"] >= 1 and r["cut"] == [True, True, True, True] \
             and n == [False, False, 1]   # (fishing has its own test now: test_324)
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
