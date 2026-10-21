"""2.21: an Endless hike with two headsets (through a local PeerJS server, see dev/peer_server.js). Checks:
- a friend joining mid-hike lands a few steps from the host (not back at the start), on the same land
- both share one clock (a day in 24 minutes): the guest takes the host's hour when joining and stays with it
- split up 3 km apart, each builds its own land and still sees the other where they really are
- 2.22: the host's animals: the friend sees the same ones near them; split up, the host puts animals out round the friend too
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_en_online.py /tmp/dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_mp.py")).read()
SETUP = re.search(r'SETUP = """(.*?)"""', src, re.S).group(1)          # the same pretend headset as the PvP test
SETUP = SETUP.replace("D.setMode('pvp');", "D.setMode('hike'); D.hikeForce = 'endless';").replace("D.mpTick(1 / 60); D.updateGun(1 / 60);", "D.mpTick(1 / 60); D.endlessTick(1 / 60); D.updateAnimals(1 / 60);")
assert "hikeForce" in SETUP and "endlessTick" in SETUP
async def run_frames(pg, n, chunk=6):
    for _ in range(n // chunk): await pg.evaluate(f"() => frames({chunk})"); await pg.wait_for_timeout(chunk * 16)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        A = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); B = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page()
        errs = []
        for nm, pg in (("host", A), ("guest", B)): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)))
        await A.goto(T); await B.goto(T); await A.wait_for_timeout(800)
        await A.evaluate(SETUP, "host"); await B.evaluate(SETUP, "guest")
        out = {}
        await A.evaluate("() => D.mpHost()")
        for _ in range(50):
            await A.wait_for_timeout(200)
            if "Waiting" in (await A.evaluate("() => D.MP.status")): break
        code = await A.evaluate("() => D.MP.code"); await B.evaluate(f"() => D.mpJoin('{code}')")
        for _ in range(80):
            await A.wait_for_timeout(250)
            if await A.evaluate("() => D.MP.on") and await B.evaluate("() => D.MP.on"): break
        out["connected"] = [await A.evaluate("() => D.MP.on"), await B.evaluate("() => D.MP.on")]
        # the host is already 2 km into the hike, at 3 pm, when the friend joins
        await A.evaluate("""() => { D.setSeed(5151); Object.assign(D.set, { hour: 9 }); D.generate(); D.state = 'play'; D.hourNow = 15;
          const x = 2000, z = 300; D.enEnsure(x, z, 300); placeAt(x, z); frames(5); D.mpSendStart(); return 1; }""")
        for _ in range(80):
            await B.wait_for_timeout(250)
            if await B.evaluate("() => D.state === 'play' && D.seed === 5151"): break
        await B.evaluate("() => { placeAt(D.P.x, D.P.z); frames(3); return 1; }")
        hp = await A.evaluate("() => [D.P.x, D.P.z, D.hourNow, D.H(2100, 350), D.H(-400, 900), D.HIKEMAP]")
        gp = await B.evaluate("() => [D.P.x, D.P.z, D.hourNow, D.H(2100, 350), D.H(-400, 900), D.HIKEMAP]")
        out["guestFromHostM"] = round(((hp[0] - gp[0]) ** 2 + (hp[1] - gp[1]) ** 2) ** .5, 1)
        out["sameLand"] = abs(hp[3] - gp[3]) < 1e-6 and abs(hp[4] - gp[4]) < 1e-6 and gp[5] == "endless"
        out["hourAtJoin"] = [round(hp[2], 3), round(gp[2], 3)]
        # both walk on together for a while: the clocks stay together
        await asyncio.gather(run_frames(A, 300), run_frames(B, 300))
        ha = await A.evaluate("() => D.hourNow"); hb = await B.evaluate("() => D.hourNow")
        out["hourGap"] = round(abs(ha - hb), 4); out["hourRan"] = round(ha - 15, 3)
        # the animals: the guest has the host's (same kind, same place)
        ha = await A.evaluate("() => { const m = {}; for (const A of D.beasts) if (A.nid && A.ecellB === undefined) m[A.nid] = [A.kind, A.x, A.z]; return m; }")
        ga = await B.evaluate("() => { const out = []; for (const A of D.beasts) if (A.net) out.push([A.nid, A.kind, A.x, A.z]); return out; }")
        match = [g for g in ga if str(g[0]) in ha and ha[str(g[0])][0] == g[1] and abs(ha[str(g[0])][1] - g[2]) < 8 and abs(ha[str(g[0])][2] - g[3]) < 8]
        out["guestAnimals"] = len(ga); out["guestAnimalsMatch"] = len(match); out["hostAnimals"] = len(ha)
        # split up: the guest goes 3 km north and builds its own land there; the host still sees it where it is
        await B.evaluate("() => { const x = D.P.x, z = D.P.z - 3000; D.enEnsure(x, z, 300); placeAt(x, z); frames(3); return 1; }")
        await asyncio.gather(run_frames(A, 90), run_frames(B, 90))
        rem = await A.evaluate("() => { for (const L of D.MP.links.values()) if (L.R && L.R.cur !== undefined) return [L.R.head.x, L.R.head.y, L.R.head.z]; return null; }")
        real = await B.evaluate("() => { const h = D.vr.readInputs().head; return [h.x, h.y, h.z]; }")
        out["hostSeesGuestWithinM"] = round(sum((a - c) ** 2 for a, c in zip(rem, real)) ** .5, 2) if rem else None
        await asyncio.gather(run_frames(A, 120), run_frames(B, 120))
        gpos = await B.evaluate("() => [D.P.x, D.P.z]")
        out["hostAnimalsNearGuest"] = await A.evaluate(f"() => D.beasts.filter(A => A.ecellB === undefined && Math.hypot(A.x - {gpos[0]}, A.z - {gpos[1]}) < 1000).length")
        out["guestBuiltThere"] = await B.evaluate("() => { const E = D.ENDLESS, ch = E.chunks.get((Math.floor(D.P.x / 200) + 60000) * 120000 + (Math.floor(D.P.z / 200) + 60000)); return !!(ch && ch.tile); }")
        # 2.23: Prehistoric hunting on endless land together: the friend gets the host's dinosaurs, the same guns lying about, and a gun one takes is gone for the other
        await A.evaluate("""() => { D.setMode('hunt'); Object.assign(D.set, { huntMap: 'endless', dino: true }); D.setSeed(6262); D.generate(); D.state = 'play'; placeAt(D.P.x, D.P.z); frames(5); D.mpSendStart(); return 1; }""")
        for _ in range(80):
            await B.wait_for_timeout(250)
            if await B.evaluate("() => D.state === 'play' && D.seed === 6262 && D.gameMode === 'hunt' && D.DINO.on"): break   # (DINO.on: the friend's map is really made — the start message sets the seed before the build)
        await B.evaluate("() => { placeAt(D.P.x, D.P.z); frames(3); window.__an = [0, 0, 0, '']; for (const L of D.MP.links.values()) if (L.conn) L.conn.on('data', o => { if (o && o.t === 'an') { window.__an[0]++; window.__an[1] += o.a.length / 11; window.__an[2] = D.MP.nb.size; window.__an[3] = o.a.slice(0, 11).join(','); } }); return 1; }")
        await asyncio.gather(run_frames(A, 180), run_frames(B, 180))
        out["guestAn"] = await B.evaluate("() => window.__an")
        hd = await A.evaluate("() => [...D.DROPS.keys()]"); gd = await B.evaluate("() => [...D.DROPS.keys()]")
        out["huntGuest"] = await B.evaluate("() => ({ map: D.HIKEMAP, dino: D.DINO.on, net: [...new Set(D.beasts.filter(A => A.net).map(A => A.kind))], n: D.beasts.filter(A => A.net).length })")
        gp2 = await B.evaluate("() => [D.P.x, D.P.z, !!D.animalGroup, D.MP.nb.size, D.MP.code, D.MP.host, [...D.MP.links.values()].map(L => [L.open, !!L.bad, L.id === 'justtrees-v1-' + D.MP.code])]")
        out["hostKinds"] = await A.evaluate("() => { const m = {}; for (const A of D.beasts) m[A.kind] = (m[A.kind] || 0) + 1; return [m, D.ENDLESS.acG.size, D.ENDLESS.aMade, D.seed, D.set.dino, D.HIKEMAP]; }")
        out["guestKinds"] = await B.evaluate("() => { const m = {}; for (const A of D.beasts) m[A.kind] = (m[A.kind] || 0) + 1; return [m, D.seed, D.set.dino, D.HIKEMAP, D.state]; }")
        out["hostSend"] = await A.evaluate("() => [D.MP.anN || 0, D.MP.on, D.state, D.gameMode, D.DINO.on, [...D.MP.links.values()].map(L => [L.open, !!(L.R && L.R.cur)])]")
        out["hostDinosNearGuest"] = await A.evaluate(f"() => [D.beasts.filter(A => !A.ptero && Math.hypot(A.x - {gp2[0]}, A.z - {gp2[1]}) < 480).length, D.beasts.length, Math.round(Math.hypot(D.P.x - {gp2[0]}, D.P.z - {gp2[1]}))]"); out["guestGroup"] = gp2[2:]
        out["sameGuns"] = len(set(hd) & set(gd)); out["guns"] = [len(hd), len(gd)]
        took = await B.evaluate("() => { let best = null, bd = 1e9; for (const d of D.DROPS.values()) { const k = Math.hypot(d.x - D.P.x, d.z - D.P.z); if (k < bd) { bd = k; best = d; } } D.dropTake(best.id); D.mpSend({ t: 'take', id: best.id }); return best.id; }")
        await asyncio.gather(run_frames(A, 30), run_frames(B, 30))
        out["hostLostTaken"] = not await A.evaluate(f"() => D.DROPS.has('{took}')")
        print(json.dumps(out)); print("errors:", errs or "none")
        if os.environ.get("JT_OUT"): open(os.environ["JT_OUT"], "w").write(json.dumps(out))
        ok = all(out["connected"]) and out["guestFromHostM"] < 80 and out["sameLand"] and abs(out["hourAtJoin"][0] - out["hourAtJoin"][1]) < .02 \
             and out["hourGap"] < .03 and out["hourRan"] > .05 and out["hostSeesGuestWithinM"] is not None and out["hostSeesGuestWithinM"] < 3 and out["guestBuiltThere"] and not errs \
             and out["guestAnimals"] >= 3 and out["guestAnimalsMatch"] >= out["guestAnimals"] * .8 and out["hostAnimalsNearGuest"] >= 3 \
             and out["huntGuest"]["map"] == "endless" and out["huntGuest"]["dino"] and out["huntGuest"]["n"] >= 2 and set(out["huntGuest"]["net"]) <= {"triceratops", "parasaur", "stego", "bronto", "trex", "ptero", "raptor"} \
             and out["sameGuns"] > 50 and out["hostLostTaken"]
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
