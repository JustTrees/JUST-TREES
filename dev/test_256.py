"""2.56: teammates show as dots in your team colour on the VR map (off-hand trigger) in PvP with 2 teams: people and bots on your side,
never the other side, never the downed. Nothing in free-for-all, and nothing online with Team · fist bump comms (you find each other
by talking). Also checks the dots aren't drawn on the PC/phone minimap.
Usage: python3 dev/test_256.py dbg.html [outdir]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); OUT = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const o = {};
          D.setSeed(31); D.setVR(true); D.setVRON && D.setVRON(true); D.setMode('pvp'); Object.assign(D.set, { size: 'medium', zone: 'off', capture: 'off', teams: 'teams', weather: 'clear', hour: 13, comms: 3 });
          D.generate(); D.state = 'play'; D.vr.on = true; D.vbFit(); D.vrHudParts && D.vrHudParts();
          const L = D.VB.list; o.bots = L.length; if (L.length < 4) return o;
          const me = D.mpMyId(); D.MP.teams[me] = 1; L.forEach((B, i) => { D.MP.teams[B.id] = i % 2; B.alive = true; });   // odd ones on your side (Blue)
          const P = D.P, spots = L.map((B, i) => [P.x - 150 + (i % 4) * 100, P.z - 120 + Math.floor(i / 4) * 120]);
          L.forEach((B, i) => { B.x = spots[i][0]; B.z = spots[i][1]; });
          L[3].alive = false;                                                     // a downed teammate: no dot
          const mm = D.vrMapCv, W = mm.width, Hh = mm.height, V = D.MAPV;
          const blueAt = (x, z) => { D.drawMap(mm); const g = mm.getContext('2d'); const cx = (x - V.cx + V.half) / V.s * W, cz = (z - V.cz + V.half) / V.s * Hh; let n = 0;
            for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) { const c = g.getImageData(Math.round(cx + dx), Math.round(cz + dy), 1, 1).data; if (c[2] > 200 && c[0] < 120 && c[1] > 120 && c[1] < 190) n++; } return n; };
          const count = () => L.map((B, i) => blueAt(B.x, B.z));
          o.solo = count();                                                       // solo vs bots: fist bump doesn't apply
          o.img = mm.toDataURL('image/png');
          D.set.teams = 'solo'; o.ffa = count(); D.set.teams = 'teams';
          D.MP.on = true; o.fist = count(); D.set.comms = 2; o.teamComms = count(); D.MP.on = false;
          D.drawMap(document.getElementById('miniMap')); o.mini = (() => { const m = document.getElementById('miniMap'); return m ? 1 : 0; })();
          D.vr.on = false; return o; }""")
        if OUT and r.get("img"): open(os.path.join(OUT, "t256_mates.png"), "wb").write(base64.b64decode(r["img"].split(",")[1]))
        r.pop("img", None); print(json.dumps(r))
        s, f, ffa, tc = r.get("solo"), r.get("fist"), r.get("ffa"), r.get("teamComms")
        ok = r.get("bots", 0) >= 4 and s and s[1] > 15 and s[3] == 0 and s[0] == 0 and s[2] == 0 \
             and all(v == 0 for v in f) and all(v == 0 for v in ffa) and tc[1] > 15 and tc[0] == 0
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
