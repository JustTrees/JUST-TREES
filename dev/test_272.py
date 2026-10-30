"""2.72: Geocaching gear. You start with nothing and the first cache is close by; the Nth find always gives the same thing (odd: a weapon,
every gun at 1 star first, all red at #49; even: the next of 24 items). The backpack opens when you reach over your shoulder and squeeze;
items you take out work in your hand (canteen, first aid, campfire, tent, fishing rod, bear spray) or are worn (headlamp, night vision);
the rest just work (boots, snowshoes, machete, wings, pouches, thermos, binoculars, satellite phone, compass, filter, fire starter, flares).
Food and water are two bars: hands in a lake drink, the canteen fills there, meat at a lit campfire counts double, fruit hangs on the trees.
Usage: python3 dev/test_272.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """(sv) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.removeItem('jt-geo'); if (sv) localStorage.setItem('jt-geochar', JSON.stringify(sv)); else localStorage.removeItem('jt-geochar'); } catch (_) {}
  D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true;   // (2.72: Geocaching is in Dev Mode while it's tested)
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
  D.generate(); D.state = 'play'; window.tick = n => { for (let i = 0; i < n; i++) { D.endlessTick(1 / 72); D.updateAnimals(1 / 72); D.geoTick(1 / 72); } };
  const T = D.THREE; window.hand = (pos, o) => Object.assign({ pos: pos.clone(), rayPos: pos.clone(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, sx: 0, sy: 0, a: 0, b: 0, stickBtn: 0 }, o || {});
  window.I = () => ({ head: new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z), headQ: new T.Quaternion(), hands: {} });
  return true; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, None)
        r = await pg.evaluate("""() => { const o = {}, G = D.GLOBE, V = D.vr, T = D.THREE;
          o.startOwn = Object.keys(V.own).filter(k => V.own[k] > 0); o.startItems = D.GEO.items.size; o.wheel = D.wheelKeys();
          o.first = Math.round(Math.min(...D.GEO.caches.map(c => D.glArc(G.p, c.p))) * G.R);
          o.order = [1, 2, 3, 4, 5, 9, 11, 47, 48, 49, 50].map(n => { const r = D.geoRewardOf(n); return r.gun ? r.gun + r.star : r.item || 'refill'; });
          const g49 = D.geoGearFromCount(49); o.at49 = [Object.values(g49.own).every(v => v === 5) && Object.keys(g49.own).length === 5, g49.items.size];
          // the first cache: a 1-star pistol
          tick(72); const c = D.GEO.target; c.p = G.p.slice(); c.ok = true; D.GEO.tT = 0; tick(3); o.got1 = [D.GEO.found.size, V.own.pistol, V.weapon];
          // every item has a model
          o.models = D.GI_LIST.filter(([k]) => { let n = 0; D.giModel(k).traverse(m => { if (m.isMesh) n++; }); return n > 0; }).length;
          // with 48 found: everything but the last red sniper; 49: all red, then the red tools need 10 grenades and full health
          D.geoGearApply(48, true); o.g48 = [D.GEO.items.size, D.geoNadeCap(), D.geoSlots(), V.nades, +D.geoSinkMul().toFixed(2), D.binoFovs().length, D.geoMapCaches().length, D.flareOk(), V.flares];
          D.geoGearApply(49, true); D.MP.hp = 100; o.tools = D.thermalLoaded(); D.MP.hp = 90; o.toolsHurt = D.thermalLoaded(); D.MP.hp = 100;
          // speed: boots; deep snow without snowshoes
          o.speed = +D.geoSpeedMul().toFixed(2); D.GEO.items.delete('snowshoes'); const keep = D.ENDLESS.here; D.ENDLESS.here = { b: 'polar' }; o.snowSlow = +D.geoSpeedMul().toFixed(2); D.ENDLESS.here = keep; D.GEO.items.add('snowshoes');
          // food and water
          D.GEO.food = 50; D.GEO.water = 50; for (let i = 0; i < 60; i++) D.geoBarsTick(1); o.drain = [+(50 - D.GEO.food).toFixed(1), +(50 - D.GEO.water).toFixed(1)];
          D.GEO.food = 0; const hp0 = D.MP.hp; D.geoBarsTick(5); o.starve = +(hp0 - D.MP.hp).toFixed(1); D.GEO.food = 80; D.GEO.water = 80; D.MP.hp = 100;
          // the backpack: reach over the gun-hand shoulder and squeeze; point at a slot and pull the trigger
          const head = new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z); D.P.yaw = 0; const ib = { head, headQ: new T.Quaternion(), hands: {} };
          const behind = hand(head.clone().add(new T.Vector3(.12, -.05, .18))), front = hand(head.clone().add(new T.Vector3(.2, -.3, -.3)));
          D.geoGearTick(ib, front, behind, 1 / 72); behind.a = 1; D.geoGearTick(ib, front, behind, 1 / 72); o.xEarly = D.GEO.packOpen; D.GEO.xT0 -= 500; D.geoGearTick(ib, front, behind, 1 / 72); o.packOpen = D.GEO.packOpen; o.packItems = D.geoPackItems();
          const m = D.GEO.packM; m.updateMatrixWorld(true); const slot = m.localToWorld(new T.Vector3((24 + 73) / 640 * .4 - .2, .15 - (70 + 55) / 480 * .3, 0));   // the first slot
          const aim = hand(head.clone().add(new T.Vector3(0, -.2, -.1))); aim.rayQ.setFromUnitVectors(new T.Vector3(0, 0, -1), slot.clone().sub(aim.rayPos).normalize());
          D.geoGearTick(ib, aim, behind, 1 / 72); aim.trig = 1; D.geoGearTick(ib, aim, behind, 1 / 72); o.held = D.GEO.held; aim.trig = 0; D.geoGearTick(ib, aim, behind, 1 / 72);
          // first aid
          D.geoHeld('aid'); D.MP.hp = 40; const ah = hand(head.clone().add(new T.Vector3(.2, -.4, -.3))); D.geoHeldTick(ib, ah, 1 / 72); ah.trig = 1; D.geoHeldTick(ib, ah, 1 / 72); ah.trig = 0; o.aid = [Math.round(D.MP.hp), D.GEO.aid];
          // a campfire: lit at once with the fire starter; meat eaten by it counts double
          D.geoFirePlace(D.P.x + 2, D.P.z); D.geoFireTick(2.1); o.fireLit = D.GEO.fire.lit; D.GEO.food = 20; D.geoEat(10); o.cooked = Math.round(D.GEO.food);
          // the tent: sleeping at night brings the morning
          D.geoTentPlace(D.P.x + 3, D.P.z + 1); G.utc = ((22 - G.lon / 15) % 24 + 24) % 24; D.globeTick(0); D.geoSleep(); D.globeTick(0); o.slept = Math.round(D.hourNow * 10) / 10;
          // bear spray: an animal right in front of you runs
          return o; }""")
        print("gear", json.dumps(r))
        w = await pg.evaluate("""() => { const o = {}, T = D.THREE, E = D.ENDLESS;
          // water: find a lake near you; a hand in it drinks, the canteen fills there and drinks at your mouth
          let spot = null; for (let r = 20; r < 1200 && !spot; r += 20) for (let a = 0; a < 6.28 && !spot; a += .25) { const x = D.P.x + Math.cos(a) * r, z = D.P.z + Math.sin(a) * r; if (D.H(x, z) < D.water - 1 && D.ENDLESS.chunks.get((Math.floor(x / 200) + 60000) * 120000 + Math.floor(z / 200) + 60000)) spot = [x, z]; }
          o.lake = !!spot; if (spot) {
            const head = new T.Vector3(spot[0], D.water + 1.6, spot[1]), ib = { head, headQ: new T.Quaternion(), hands: {} }, inW = hand(new T.Vector3(spot[0], D.water - .2, spot[1]));
            D.GEO.water = 40; ib.hands.left = inW; for (let i = 0; i < 40; i++) D.geoGearTick(ib, null, null, 1 / 20); o.drank = Math.round(D.GEO.water);
            // the canteen: tipped over in the lake it doesn't fill; held upright under the surface it does; tipped up at your mouth you drink
            D.geoHeld('canteen'); D.GEO.cant = 0; ib.hands = {}; const cw = hand(new T.Vector3(spot[0], D.water - .25, spot[1])); ib.hands[D.set.hand] = cw;
            cw.rayQ.setFromAxisAngle(new T.Vector3(1, 0, 0), Math.PI * .8); for (let i = 0; i < 30; i++) D.geoGearTick(ib, cw, null, 1 / 20); o.tipped = D.GEO.cant;
            cw.rayQ.identity(); for (let i = 0; i < 60; i++) D.geoGearTick(ib, cw, null, 1 / 20); o.filled = D.GEO.cant;
            D.GEO.water = 30; const mouth = hand(head.clone().add(new T.Vector3(0, -.06, -.12))); mouth.rayQ.setFromAxisAngle(new T.Vector3(1, 0, 0), .9); ib.hands = {};
            for (let i = 0; i < 80; i++) D.geoGearTick(ib, mouth, null, 1 / 20); o.sipped = [Math.round(D.GEO.water), D.GEO.cant]; D.geoHeld(null); }
          // the sea is salt: hands in it don't drink
          { const G = D.GLOBE, R = G.R; let sea = null; for (let r = 20; r < 3000 && !sea; r += 40) for (let a = 0; a < 6.28 && !sea; a += .3) { const x = D.P.x + Math.cos(a) * r, z = D.P.z + Math.sin(a) * r, q = D.glToSphere(x, z, [0, 0, 0]); if (D.H(x, z) < D.water - 1 && G.contS(q, q[0] * R, q[1] * R, q[2] * R) < 0) sea = [x, z]; }
            o.sea = !!sea; if (sea) { D.GEO.water = 40; const ib = { head: new T.Vector3(sea[0], D.water + 1.6, sea[1]), headQ: new T.Quaternion(), hands: { left: hand(new T.Vector3(sea[0], D.water - .2, sea[1])) } }; for (let i = 0; i < 40; i++) D.geoGearTick(ib, null, null, 1 / 20); o.seaDrink = Math.round(D.GEO.water); } }
          { const xz = D.glFromSphere(D.GLOBE.basins[1].c, [0, 0]);   /* (2.99: the big one has the island in its middle) */ o.saltSea = D.geoSalty(new T.Vector3(xz[0], -5, xz[1])); o.saltLake = spot ? D.geoSalty(new T.Vector3(spot[0], -1, spot[1])) : false; }
          // Pack on the wheel
          o.packWheel = D.wheelKeys().includes('pack'); D.vr.I = { head: new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z), headQ: new T.Quaternion(), hands: {} }; D.GEO.packOpen = false; D.pickGun('pack'); o.packFromWheel = D.GEO.packOpen; D.GEO.packOpen = false; if (D.GEO.packM) D.GEO.packM.visible = false;
          // fruit on the trees near you: a hand on one, squeezing, eats it
          D.GEO.frT = 0; D.geoGearTick({ head: new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z), headQ: new T.Quaternion(), hands: {} }, null, null, 1 / 72);
          let fr = null; for (const ch of E.chunks.values()) if (ch.fruit) for (const f of ch.fruit) if (f.obj && !fr) fr = f;
          o.fruit = !!fr; if (fr) { D.GEO.food = 30; const h = hand(fr.obj.position.clone(), { grip: 1 }); D.geoGearTick({ head: new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z), headQ: new T.Quaternion(), hands: { left: h } }, null, null, 1 / 72); o.ateFruit = [Math.round(D.GEO.food), !fr.obj]; }
          // bear spray
          const A = D.beasts.find(B => !B.dead && !B.ptero && B.ecellB === undefined); o.animal = !!A;
          if (A) { A.x = D.P.x; A.z = D.P.z - 8; A.flee = 0; const sp = D.GEO.spray, h = hand(new T.Vector3(D.P.x, D.P.y + 1.3, D.P.z)); D.geoSpray(h); o.spray = [sp - D.GEO.spray, !!(A.fleeT > 0 || A.bolting || A.flee || A.mode === 'flee' || A.fleeX !== undefined)]; }
          // worn: the headlamp's light and the goggles; the rod casts only into water
          D.GEO.worn.add('nvg'); D.setLighting && 0; window.__nk = 0; const hd = { head: new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z), headQ: new T.Quaternion(), hands: {} }; for (let i = 0; i < 20; i++) D.geoGearTick(hd, null, null, 1 / 72);
          o.worn = [+D.GEO.nvK.toFixed(2)]; D.GEO.worn.clear();
          D.geoHeld('rod'); const rh = hand(new T.Vector3(D.P.x, D.P.y + 1.3, D.P.z)); D.geoHeldTick(hd, rh, 1 / 72); rh.trig = 1; D.geoHeldTick(hd, rh, 1 / 72); o.rod = D.GEO.rod && D.GEO.rod.st; D.geoHeld(null);
          // the watch's compass draws; a save and a new game keep the count, the gear follows it
          D.drawWatch(600); D.GEO.found = new Set([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]); D.GEO.food = 66; D.GEO.water = 55; D.geoSave(); D.generate(); D.state = 'play';
          { const ok0 = D.DEV.ok; D.DEV.ok = false; D.set.huntMap = 'globe'; D.generate(); D.state = 'play'; o.noDev = [!!D.GLOBE, D.GEO.on]; D.DEV.ok = ok0; D.generate(); D.state = 'play'; }   // (not public yet: only with Dev Mode)
          o.resume = [D.GEO.found.size, D.GEO.items.size, Object.keys(D.vr.own).filter(k => D.vr.own[k] > 0).sort().join(','), Math.round(D.GEO.food), Math.round(D.GEO.water)];
          return o; }""")
        print("world", json.dumps(w))
        ok = r["startOwn"] == [] and r["startItems"] == 0 and r["first"] < 160 and r["order"] == ["pistol1", "canteen", "smg1", "campfire", "bow1", "hunt1", "pistol2", "ar5", "tscope", "hunt5", "refill"] \
             and r["at49"] == [True, 24] and r["got1"][:2] == [1, 1] and r["got1"][2] == "pistol" and r["models"] == 30 \
             and r["g48"][:6] == [24, 10, 16, 10, .42, 7] and r["g48"][6] == 3 and r["g48"][7] and r["g48"][8] > 0 and r["tools"] and not r["toolsHurt"] \
             and r["speed"] == 1.15 and r["snowSlow"] < 1 and 2 < r["drain"][0] < 4.5 and 3.5 < r["drain"][1] < 6.5 and r["starve"] > 2 \
             and r["packOpen"] and not r["xEarly"] and len(r["packItems"]) >= 6 and r["held"] == r["packItems"][0] and r["aid"] == [100, 0] and r["fireLit"] and r["cooked"] == 40 and 6.5 <= r["slept"] <= 7.5 \
             and (not w["lake"] or (w["drank"] > 60 and w["tipped"] == 0 and w["filled"] == 4 and w["sipped"][0] > 60 and w["sipped"][1] < 3)) \
             and (not w["fruit"] or (w["ateFruit"][0] > 30 and w["ateFruit"][1])) and (not w["animal"] or w["spray"][0] == 1)
        ok = ok and w["resume"][:2] == [10, 5] and w["resume"][2] == "ar,bow,hunt,pistol,smg" and w["resume"][3] == 100 and w["resume"][4] == 100 and w["worn"][0] > .9 and (not w["sea"] or w["seaDrink"] == 40) and w["packWheel"] and w["packFromWheel"] and w["saltSea"] and not w["saltLake"] and w["noDev"] == [True, True] and w["rod"] in ("ready", "cast", "out")
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
