"""3.39 (Dev): Competitive Treeocashing without its host (found in review). The host leaves a flat-map game: one of those left keeps the
score (the zone still starts, there is still a winner); in the end game the water or a dinosaur puts you out too; someone who is out
cannot be heard by those still in. (Based on test_331:) Competitive Treeocashing. The main menu's Competitive button opens a public room with an empty lobby (size M: 10 levels).
Friends join; Start: everyone caches up from nothing, no guns lying about. A cache found gives the next reward; the top level makes a
Bigg Wigg (the others see it). Killed by a Bigg Wigg: out. Killed by anyone else: back in, level kept. Everyone left a Bigg Wigg: the
zone comes in for all; a death then is out; the last one standing wins (the board shows it). Needs the PeerJS server.
Usage: python3 dev/test_331.py dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__)); T = 'file://' + os.path.abspath(sys.argv[1])
SETUP = re.search(r'SETUP = """(.*?)"""', open(os.path.join(here, "test_280.py")).read(), re.S).group(1)
SETUP = SETUP.replace("return true; }", "window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => w.label === l); D.geoTick = () => {}; return true; }")
async def run(pages, n, chunk=4):
    for _ in range(n // chunk):
        for pg in pages: await pg.evaluate(f"() => frames({chunk})")
        await pages[0].wait_for_timeout(chunk * 25)
async def until(pgs, js, tries=300):
    for _ in range(tries):
        if all([await pg.evaluate(js) for pg in pgs]): return True
        await run(pgs, 4)
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        pgs = [await (await b.new_context(viewport={"width": 320, "height": 240})).new_page() for _ in range(3)]; A, B, C = pgs; errs = []
        for nm, pg in zip("ABC", pgs): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)[:200]))
        for i, pg in enumerate(pgs): await pg.goto(T); await pg.wait_for_timeout(500); await pg.evaluate(SETUP, [1, 2, 3][i])
        out = {}
        await A.evaluate("() => { D.vruiOpen('mode'); W('mode', 'Competitive').on(); return 1; }")
        for _ in range(60):
            await A.wait_for_timeout(200)
            if "Waiting" in (await A.evaluate("() => D.MP.status")): break
        out["room"] = await A.evaluate("() => [D.set.comp, D.compMode(), D.roomMapName(), D.MP.pub, D.VRUI.stage]")
        code = await A.evaluate("() => D.MP.code")
        for G in (B, C): await G.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        for _ in range(80):
            await A.wait_for_timeout(250)
            if await A.evaluate("() => D.mpOpen().length >= 2") and await B.evaluate("() => D.MP.on") and await C.evaluate("() => D.MP.on"): break
        await run(pgs, 8); out["guestSet"] = await B.evaluate("() => [D.set.comp, D.set.size, D.gameMode]")
        await A.evaluate("() => { D.vruiOpen('setup'); W('setup', 'Start').on(); return 1; }")
        out["preview"] = await until(pgs, "() => D.VRUI.stage === 'preview' && !D.MP.genBusy", 300)
        await A.evaluate("() => { D.vruiDropIn(); return 1; }"); await A.wait_for_timeout(500)
        out["play"] = await until(pgs, "() => D.state === 'play' && D.COMP.on && !!D.COMP.c", 400)
        out["start"] = await B.evaluate("() => [D.COMP.N, D.COMP.lv, [...D.DROPS.values()].filter(d => d.type === 'gun').length, D.MP.roundLeft]")
        aid = await A.evaluate("() => D.MP.peer.id"); bid = await B.evaluate("() => D.MP.peer.id"); cid = await C.evaluate("() => D.MP.peer.id")
        # someone who's out can't be heard by those still in
        out["mute"] = await A.evaluate(f"() => {{ const L = D.MP.links.get('{bid}'); L.co = true; const m = D.mpHear(L)[0]; L.co = false; return [m, D.mpHear(L)[0] > 0]; }}")
        # the host leaves: one of the two left keeps the score
        await A.evaluate("() => { D.mpLeave(); return 1; }"); await run([B, C], 24)
        out["refs"] = sorted([await B.evaluate("() => D.compRef()"), await C.evaluate("() => D.compRef()")])
        out["still"] = [await pg.evaluate("() => D.state === 'play' && D.COMP.on") for pg in (B, C)]
        # both reach the top: the zone starts for both, with no host
        for pg in (B, C): await pg.evaluate("() => { D.COMP.lv = D.COMP.N; D.COMP.c = null; return 1; }")
        out["zone"] = await until([B, C], "() => D.COMP.zone && !!D.zone", 120)
        # end game: the water (or a dinosaur) puts you out too; then C leaves instead: B wins
        out["drownOut"] = await C.evaluate("() => { D.uwRespawn(); return D.COMP.out; }")
        out["won"] = await until([B, C], "() => D.COMP.ended", 120)
        out["winner"] = await B.evaluate("() => D.COMP.winner === D.mpMyId()")
        print(json.dumps(out)); print("errors:", errs[:5] or "none")
        ok = out["play"] and out["mute"] == [0, True] and out["refs"] == [False, True] and all(out["still"]) and out["zone"] and out["drownOut"] and out["won"] and out["winner"] and not errs
        print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
