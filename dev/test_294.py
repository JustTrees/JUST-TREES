"""2.94 (3.21: Hike can be the 3 km island too; endless is the planet): the VR menus' map rules: solo Hike on the planet starts in the land of the latitude you chose; solo Hunt and Bot battle are
the 3 km island or endless; a Bot battle on endless land has no closing zone and the bots come round you.
Usage: python3 dev/test_294.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setVR(true); D.vr.on = true; D.set.hand = 'right'; const o = {}, P = D.P;
          Object.assign(D.set, { env: 'climate', land: 'natural', hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .5, dino: false });
          // Hike: endless; the start is your latitude's land
          o.hike = []; for (const [lat, sd] of [[4, 11], [70, 12], [58, 13], [27, 14]]) { D.setSeed(sd); D.set.lat = lat; D.setMode('hike'); D.set.hikeMap = 'endless'; D.mapRules(); D.generate(); D.state = 'play';
            const b = D.enDom(P.x, P.z).b, ok = D.envOptions(lat).map(e => e[0]); o.hike.push([lat, D.set.hikeMap, !!D.ENDLESS, b, ok.includes(b)]); }
          D.set.hikeMap = 'island'; D.mapRules(); o.hikeIsland = D.set.hikeMap;
          // Hunt: the 3 km island or endless
          D.setMode('hunt'); D.set.huntMap = 'island'; D.set.size = 'small'; D.mapRules(); o.hunt = [D.set.size, D.set.edges, D.set.huntMap];
          // Bot battle on endless land
          D.setSeed(15); D.setMode('pvp'); D.set.pvpMap = 'endless'; D.set.zone = 'on'; D.mapRules(); D.generate(); D.state = 'play'; D.vbFit(); for (let i = 0; i < 90; i++) { D.endlessTick(1 / 30); D.vbTick(1 / 30); }
          const bots = D.VB.ents.filter(e => e.alive); o.bot = [D.pvpEndless(), !!D.ENDLESS, D.zone === null, D.set.zone, bots.length, Math.round(Math.max(0, ...bots.map(e => Math.hypot(e.x - P.x, e.z - P.z))))];
          D.set.pvpMap = 'island'; D.mapRules(); o.botIsland = [D.set.size, D.set.edges];
          return o; }""")
        print(json.dumps(r))
        ok = all(h[1] == "endless" and h[2] and h[4] for h in r["hike"]) and r["hikeIsland"] == "island" and r["hunt"] == ["xxxl", "island", "island"] \
             and r["bot"][0] and r["bot"][1] and r["bot"][2] and r["bot"][3] == "off" and r["bot"][4] > 0 and r["bot"][5] < 800 and r["botIsland"] == ["xxxl", "island"]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
