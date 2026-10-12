"""VR Hunting (1.65): no wrist score (too small to read); the score sits on the map (off-hand trigger), and your mark (tap B) shows there as a gold pin.
Pickup messages float in front of you but never cover the Bigfoot message.
Bigfoot notices you: binoculars at the strongest zoom, aimed right at him with a clear line, he stops, turns and looks up at you,
then moves off a bit faster (a walk, not a run; he isn't spooked away). Weaker zoom, or a hill in the way: nothing."""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOTS = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const T = D.THREE, o = {};
          D.setSeed(12); D.setVR(true); D.setMode('hunt'); D.set.size = 'large'; D.set.lat = 42; D.set.weather = 'clear'; D.generate(); D.state = 'play'; D.vr.on = true;
          // the map: score box and a mark pin
          D.hunt.score = 123.4; D.hunt.kills = 3; D.hunt.longest = 412;
          D.vrHudParts && D.vrHudParts(); const mm = D.vrMapCv, W = mm.width, Hh = mm.height;
          const from = new T.Vector3(D.P.x, D.H(D.P.x, D.P.z) + 30, D.P.z), dir = new T.Vector3(1, -.25, .3).normalize(); D.placeMark(from, dir);
          D.drawMap(mm); const g = mm.getContext('2d');
          const px = (x, y) => Array.from(g.getImageData(Math.round(x), Math.round(y), 1, 1).data);
          let gold = 0; for (let y = Hh * .7; y < Hh; y += 2) for (let x = 0; x < W * .6; x += 2) { const c = px(x, y); if (c[0] > 200 && c[1] > 170 && c[2] < 140) gold++; } o.scoreText = gold;
          const mk = D.vr.mark.position, mx = (mk.x + 400) / 800 * W, mz = (mk.z + 400) / 800 * Hh; let pin = 0; for (let dy = -W / 12; dy < 0; dy++) for (let dx = -W / 40; dx < W / 40; dx++) { const c = px(mx + dx, mz + dy); if (c[0] > 220 && c[1] > 190 && c[2] < 140) pin++; } o.pin = pin;
          o.mapImg = mm.toDataURL('image/png');
          // banners: a pickup message doesn't cover the Bigfoot one
          D.vrBanner("There's a Bigfoot in these woods", 6, 2); D.vrBanner("Sniper ★★★★★", 2.5, 1); o.bannerKept = D.VBAN.prio === 2;
          // Bigfoot
          D.setLoot({ pistol: 1, hunt: 5 }); const B = D.beasts.find(A => A.kind === 'bigfoot'); o.found = !!B; if (!B) return o;
          const step = n => { for (let i = 0; i < n; i++) D.updateAnimals(1 / 30); };
          step(2);
          // a clear spot ~350 m off
          const tgt = new T.Vector3(B.x, B.y + 1.6, B.z); let eye = null;
          for (let k = 0; k < 64 && !eye; k++) { const a = k * .39, e = new T.Vector3(B.x - 350 * Math.sin(a), B.y + 50 + (k >> 4) * 30, B.z - 350 * Math.cos(a)); const d = tgt.clone().sub(e).normalize(), h = D.castShotDbg(e, d, 3200); if (!h || !h.p || h.p.distanceTo(e) > e.distanceTo(tgt) - 4) eye = e; }
          o.clear = !!eye; if (!eye) return o;
          const look = () => { D.vr.head.copy(eye); const m = new T.Matrix4().lookAt(eye, new T.Vector3(B.x, B.y + 1.6, B.z), new T.Vector3(0, 1, 0)); D.vr.headQ.setFromRotationMatrix(m); D.P.x = eye.x; D.P.z = eye.z; };
          D.vr.binos = true; D.vr.zoom = 2; look(); step(10); o.weakZoomNothing = !(B.noticeT > 0);
          D.vr.zoom = 3; look(); B.mode = 'walk'; B.want = B.walk; B.speed = B.walk; step(2);
          o.noticed = B.noticeT > 0; o.stopped = B.speed === 0;
          const y0 = B.yaw; step(20); const face = Math.atan2(eye.x - B.x, eye.z - B.z); o.facesYou = Math.abs(((face - B.yaw + Math.PI * 3) % (Math.PI * 2)) - Math.PI) < .3; o.headUp = +B.head.rotation.x.toFixed(2);
          o.pose = null; if (SHOTS_ON) { const c = D.camera; const ux = (eye.x - B.x), uz = (eye.z - B.z), ul = Math.hypot(ux, uz); c.position.set(B.x + ux / ul * 3.2 - uz / ul * 3.2, B.y + 1.4, B.z + uz / ul * 3.2 + ux / ul * 3.2); c.fov = 45; c.updateProjectionMatrix(); c.lookAt(B.x, B.y + 1.5, B.z); c.updateMatrixWorld(); D.renderer.render(D.scene, c); o.pose = D.renderer.domElement.toDataURL('image/jpeg', .9); }
          D.vr.binos = false; step(40); o.movesOff = B.mode === 'walk' && B.want > B.walk * 1.5 && B.want < B.run * .5; o.notGone = !B.gone && !B.bolting;
          const d0 = Math.hypot(B.x - eye.x, B.z - eye.z); step(90); o.awayM = +(Math.hypot(B.x - eye.x, B.z - eye.z) - d0).toFixed(1);
          // looking again right away: he's used to you for a bit
          D.vr.binos = true; look(); step(5); o.cooldown = !(B.noticeT > 0);
          D.vr.on = false; return o; }""".replace("SHOTS_ON", "true" if SHOTS else "false"))
        if SHOTS:
            open(os.path.join(SHOTS, "vr_map_score.png"), "wb").write(base64.b64decode(r.pop("mapImg").split(",")[1]))
            if r.get("pose"): open(os.path.join(SHOTS, "bigfoot_looks_up.jpg"), "wb").write(base64.b64decode(r.pop("pose").split(",")[1]))
        r.pop("mapImg", None); r.pop("pose", None)
        print(json.dumps(r))
        ok = r["scoreText"] > 40 and r["pin"] > 10 and r["bannerKept"] and r.get("found") and r.get("clear") and r["weakZoomNothing"] and r["noticed"] and r["stopped"] \
             and r["facesYou"] and r["headUp"] < -.05 and r["movesOff"] and r["notGone"] and r["awayM"] > 5 and r["cooldown"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
