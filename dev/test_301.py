"""3.01: pteranodons: a quarter of them are the giant kind (4x the size) that one sniper shot brings down (the usual one takes several);
they come for you from closer (50 m) and less often, with a big warning caw (a 2.6 s beat before the dive); once one gets you, they all
leave you be for a couple of minutes. Long banners wrap onto up to three lines.
Usage: python3 dev/test_301.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(31); D.setVR(true); D.vr.on = true;
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', huntMap: 'island', size: 'medium', dino: true });
          D.generate(); D.state = 'play'; const o = {}, P = D.P;
          const L = []; for (let i = 0; i < 40; i++) L.push(D.pteroAdd(P.x + 300, P.z));
          const G = L.filter(A => A.giant), N = L.filter(A => !A.giant); o.mix = [G.length, N.length, G[0] && G[0].size];
          D.hitAnimal(G[0], 100, 100, false, 'hunt', 3); D.hitAnimal(N[0], 100, 100, false, 'hunt', 3); o.shot = [G[0].dead, N[0].dead];
          D.hitAnimal(G[1], 100, 30, false, 'ar', 3); o.arGiant = G[1].dead;
          // close enough under it: the warning beat, then the dive; once it gets you, everyone backs off
          const A = N[1]; A.cd = 0; A.state = 'circle'; A.x = P.x + 20; A.z = P.z; A.y = P.y + 50; A.aggro = null; D.pteroMind(A, 1 / 30); o.warn = [A.state, +A.stT.toFixed(1)];
          const B = N[2]; B.state = 'dive'; B.aggro = 'me'; D.pteroGot(A, 'me'); o.calm = [B.state, B.aggro, B.cd >= 120];
          D.vrBanner('Tied! Now the glowing tree (squeeze here again to untie) and a few more words to make it long', 3, 3);
          return o; }""")
        print(json.dumps(r))
        ok = r["mix"][0] > 3 and r["mix"][1] > 15 and r["mix"][2] == 4 and r["shot"] == [True, False] and not r["arGiant"] and r["warn"] == ["screech", 2.6] and r["calm"] == ["climb", None, True]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
