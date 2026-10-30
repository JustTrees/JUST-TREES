"""3.33 (Dev): Competitive Treeocashing on the planet. Planet in the lobby: a public online Treeocashing planet with a fresh level 0 for
everyone (your saved level isn't used or touched), friends starting far apart. Level 50 = Bigg Wigg (a big head for the others to see).
Everyone left a Bigg Wigg: the beam comes down far off; the zone round it closes over an hour (the whole planet → 5 km by 30 min);
outside it hurts, a death then is out, the last one standing wins. Needs the PeerJS server.
Usage: python3 dev/test_332.py dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__)); T = 'file://' + os.path.abspath(sys.argv[1])
SETUP = re.search(r'SETUP = """(.*?)"""', open(os.path.join(here, "test_280.py")).read(), re.S).group(1)
SETUP = SETUP.replace("return true; }", "window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => w.label === l); return true; }")
async def run(pages, n, chunk=4):
    for _ in range(n // chunk):
        for pg in pages: await pg.evaluate(f"() => frames({chunk})")
        await pages[0].wait_for_timeout(chunk * 25)
async def until(pgs, js, tries=300):
    for _ in range(tries):
        if all([await pg.evaluate(js) for pg in pgs]): return True
        for pg in pgs: await pg.evaluate("() => { if (D.VRUI.stage === 'preview' && D.MP.host && !D.MP.genBusy && D.state !== 'play') D.vruiDropIn(); return 1; }")
        await run(pgs, 4)
    return False
SPH = "() => D.glToSphere(D.P.x, D.P.z, [0, 0, 0])"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        pgs = [await (await b.new_context(viewport={"width": 320, "height": 240})).new_page() for _ in range(2)]; A, B = pgs; errs = []
        for nm, pg in zip("AB", pgs): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)[:200]))
        for i, pg in enumerate(pgs): await pg.goto(T); await pg.wait_for_timeout(500); await pg.evaluate(SETUP, [7, 2][i])
        out = {}
        await A.evaluate("() => { D.vruiOpen('mode'); W('mode', 'Competitive').on(); return 1; }")
        for _ in range(60):
            await A.wait_for_timeout(200)
            if "Waiting" in (await A.evaluate("() => D.MP.status")): break
        out["room"] = await A.evaluate("() => { D.vruiOpen('setup'); W('setup', 'Planet').on(); return [D.compPlanet(), D.geoMode(), D.roomMapName(), D.MP.pub, D.compTop()]; }")
        code = await A.evaluate("() => D.MP.code"); await B.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        for _ in range(80):
            await A.wait_for_timeout(250)
            if await A.evaluate("() => D.mpOpen().length >= 1") and await B.evaluate("() => D.MP.on"): break
        await run(pgs, 8)
        await A.evaluate("() => { W('setup', 'Start').on(); return 1; }")
        out["play"] = await until(pgs, "() => D.state === 'play' && D.GEO.on && D.COMP.on && D.COMP.planet", 500)
        out["fresh"] = [await pg.evaluate("() => [D.GEO.found.size, D.COMP.N, D.geoNet()]") for pg in pgs]
        await run(pgs, 20)
        pa = await A.evaluate(SPH); pb = await B.evaluate(SPH)
        out["apart"] = round(await A.evaluate(f"() => D.glArc({json.dumps(pa)}, {json.dumps(pb)}) * D.GLOBE.R"))
        # B gets to 50: Bigg Wigg (a big head for A to see); nothing saved over B's own character
        out["bw"] = await B.evaluate("() => { for (let i = 1; i <= 50; i++) D.GEO.found.add(i); frames(2); return [D.COMP.lv, D.COMP.bwSaid, JSON.parse(localStorage.getItem('jt-geochar')).n]; }")
        await run(pgs, 16); bid = await B.evaluate("() => D.MP.peer.id")
        out["seen"] = await A.evaluate(f"() => {{ const L = D.MP.links.get('{bid}'); return [!!L.cbw, D.bigHeadK(L)]; }}")
        # A too: the beam
        await A.evaluate("() => { for (let i = 1; i <= 50; i++) D.GEO.found.add(i); frames(2); return 1; }")
        out["beam"] = await until(pgs, "() => D.COMP.zone && !!D.COMP.beam", 100)
        out["same"] = await A.evaluate("() => D.COMP.beam.p.map(v => +v.toFixed(4))") == await B.evaluate("() => D.COMP.beam.p.map(v => +v.toFixed(4))")
        out["radii"] = await A.evaluate("() => [Math.round(D.compBeamR(0)), Math.round(D.compBeamR(1800)), Math.round(D.compBeamR(3000)), Math.round(D.compBeamR(9999))]")
        out["gps"] = await B.evaluate("() => { D.geoGpsModel(); D.compGpsDraw(); const m = document.createElement('canvas'); m.width = m.height = 256; D.geoMapDraw(m); return Math.round(D.compBeamDir()[2]); }")
        # late in the hour B is far outside: it hurts, B dies, out; A wins
        out["outside"] = await B.evaluate("""() => { D.COMP.beam.t0 -= 3500e3; D.MP.hp = 100; const hp0 = D.MP.hp; for (let i = 0; i < 150; i++) frames(1); const hp1 = D.MP.hp;
          D.MP.hp = 3; for (let i = 0; i < 90; i++) frames(1); return [hp1 < hp0, D.COMP.out, !!D.COMP.pillar && D.COMP.pillar.visible]; }""")
        out["won"] = await until(pgs, "() => D.COMP.ended", 120)
        out["winner"] = await A.evaluate("() => D.COMP.winner === D.mpMyId()")
        print(json.dumps(out)); print("errors:", errs[:5] or "none")
        ok = out["room"] == [True, True, "Competitive · Planet", True, 50] and out["play"] and all(f == [0, 50, True] for f in out["fresh"]) and out["apart"] > 1000 \
             and out["bw"] == [50, True, 2] and out["seen"] == [True, 4] and out["beam"] and out["same"] and out["radii"][1:] == [5000, 300, 40] and out["radii"][0] > 20000 \
             and out["gps"] > 0 and out["outside"] == [True, True, True] and out["won"] and out["winner"] and not errs
        print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
