"""3.36: out at sea. Shoals of fish swim under the water near you (deep sea only); the fish-finder glasses show them, but only while you're
on your jet ski; a lure cast near one gets bites much sooner. The sea is drawn choppier while you ride. The others' jet skis show up where
they are, and their fish leaping. Usage: python3 dev/test_336.py dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__))
GEN = re.search(r'GEN = """(.*?)"""', open(os.path.join(here, "test_275.py")).read(), re.S).group(1)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, 50)
        r = await pg.evaluate("""() => { const o = {}, T = D.THREE, P = D.P;
          // out over deep sea
          let spot = null; for (const j of D.jetPlaceOld()) { D.geoTeleport(j.p); tick(30); for (let k = 0; k < 400 && !spot; k++) { const x = P.x + (Math.random() - .5) * 600, z = P.z + (Math.random() - .5) * 600; if (D.water - D.H(x, z) > 25 && D.geoSalty({ x, z })) spot = [x, z]; } if (spot) break; }
          if (!spot) return { noSea: true };
          P.x = spot[0]; P.z = spot[1]; D.enEnsure(P.x, P.z, 200); D.SEA.scanT = 0; for (let i = 0; i < 12; i++) { D.SEA.scanT = 0; D.seaTick(1 / 30); }
          o.shoals = D.SEA.shoals.length; const S = D.SEA.shoals[0]; o.near = !!(S && D.shoalNear(S.x + 2, S.z, 7));
          // glasses on, but on foot: nothing; on a jet ski: the fish show, and the sea goes choppy
          D.GEO.worn = new Set(['fglass']); D.seaTick(1 / 30); o.onFoot = !!(D.SEA.im && D.SEA.im.visible);
          D.JET.ride = { J: { obj: null }, air: false }; for (let i = 0; i < 90; i++) D.seaTick(1 / 30); o.riding = [!!(D.SEA.im && D.SEA.im.visible), D.SEA.im ? D.SEA.im.count : 0, +D.WATER_U.uChop.value.toFixed(2)];
          D.JET.ride = null; for (let i = 0; i < 120; i++) D.seaTick(1 / 30); o.chopOff = +D.WATER_U.uChop.value.toFixed(2);
          // someone else's jet ski and their fish leaping
          const L = { id: 'zz', open: true, bad: false, R: { alive: true, head: new T.Vector3(P.x, P.y + 1.5, P.z) }, js: [P.x + 5, D.water, P.z, 0, 0, 0, 1] }; D.MP.links.set('zz', L);
          D.seaTick(1 / 30); const J = D.SEA.jets.get('zz'); o.theirJet = !!(J && J.visible) && Math.abs(J.position.x - (P.x + 5)) < .01;
          D.fishJumpSee({ o: [P.x + 8, D.water, P.z], H: 2.5, T: 1, c: 0x2a4a9a, kg: 90, a: 0 }); D.seaTick(.5); o.jump = D.SEA.jumps.length ? +(D.SEA.jumps[0].o.position.y - D.water).toFixed(1) : -1; for (let i = 0; i < 40; i++) D.seaTick(1 / 30); o.jumpDone = D.SEA.jumps.length;
          D.MP.links.delete('zz'); D.seaTick(1 / 30); o.gone = D.SEA.jets.size;
          return o; }""")
        print(json.dumps(r)); print("errors:", errs[:5] or "none")
        ok = r.get("shoals", 0) >= 3 and r["near"] and not r["onFoot"] and r["riding"][0] and r["riding"][1] > 8 and r["riding"][2] > .9 and r["chopOff"] < .05 \
             and r["theirJet"] and r["jump"] > 2 and r["jumpDone"] == 0 and r["gone"] == 0 and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
