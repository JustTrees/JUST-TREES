"""2.26 checks: the watch shows on the left wrist on endless land and its minute hand moves each game minute; the player list beside the map
mutes a friend when you point at their button and pull the trigger; the map's bottom carries what the wrist used to show.
Usage: python3 dev/test_226.py dbg.html [picture.png]"""
import sys, asyncio, json, base64
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4242); D.setVR(true); D.setMode('hike'); D.vr.on = true; D.hikeForce = 'endless';
          Object.assign(D.set, { lat: 45, hemi: 1, month: 6, hour: 9.5, weather: 'clear', density: .5, rough: .5 }); D.generate(); D.state = 'play';
          const T = D.THREE, q = new T.Quaternion(), I = { head: new T.Vector3(D.P.x, D.P.y + 1.6, D.P.z), headQ: q, hands: { left: { pos: new T.Vector3(D.P.x - .1, D.P.y + 1.3, D.P.z - .3), q: q.clone() } } };
          D.hourNow = 9.5; D.watchTick(I); const W = D.watchM, m0 = W.userData.m, vis = W.visible; D.hourNow = 9.5 + 1 / 60; D.watchTick(I);
          const out = { watch: [vis, m0, W.userData.m], pic: W.userData.cv.toDataURL('image/png') };
          // the player list: a pretend friend, point at their Mute button, pull the trigger
          D.vrHudParts2(); D.set.teams = true; D.MP.code = '1234'; D.MP.tag = 'RON'; const L = { id: 'justtrees-v1-x', open: true, bad: false, tag: 'BOB', idx: 2 }; D.MP.links.set(L.id, L);
          const M = D.vrMap; M.visible = true; M.position.set(D.P.x, D.P.y + 1.4, D.P.z - .4); M.lookAt(I.head); M.updateMatrixWorld(true);
          const Pn = D.plPanel(); const aim = (u, v, trig) => { Pn.quaternion.copy(M.quaternion); Pn.position.copy(M.position).add(new T.Vector3(.235, 0, 0).applyQuaternion(M.quaternion)); Pn.updateMatrixWorld(true);
              const tgt = Pn.localToWorld(new T.Vector3((u / 384 - .5) * .195, (.5 - v / 512) * .26, 0)), o = I.head.clone(), d = tgt.clone().sub(o).normalize(), rq = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 0, -1), d);
              D.plTick({ rayPos: o, rayQ: rq, trig }); };
          aim(316, 146, 0); aim(316, 146, 1); out.muted = !!L.muted; out.hover = D.vr.plHover; aim(316, 146, 0); aim(316, 146, 1); out.unmuted = !L.muted;
          out.panel = Pn.userData.cv.toDataURL('image/png');
          D.MP.links.delete(L.id); D.MP.code = ''; D.set.teams = false;
          // the map's bottom in PvP
          D.setMode('pvp'); D.drawMap(document.getElementById('vrMap') || D.vrMap.material.map.image); out.map = D.vrMap.material.map.image.toDataURL('image/png');
          return out; }""")
        for k in ("pic", "panel", "map"):
            if len(sys.argv) > 2: open(sys.argv[2].replace(".png", "_" + k + ".png"), "wb").write(base64.b64decode(r[k].split(",")[1]))
            del r[k]
        print(json.dumps(r))
        ok = r["watch"][0] and r["watch"][1] == 570 and r["watch"][2] == 571 and r["muted"] and r["hover"] and r["unmuted"] and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
