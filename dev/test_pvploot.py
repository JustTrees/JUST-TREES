"""VR PvP loot (1.40): 1-star pistol start, locked guns on the wheel, gun drops unlock/upgrade (stars), green/blue crosses,
shield soaks damage, dying spills your loot and freezes your view, HUD bar. Usage: python3 dev/test_pvploot.py /tmp/dbg.html [/tmp/wheel.png]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/wheel.png'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 800, "height": 500})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {};
          D.setVR(true); D.setMode('pvp'); D.set.size = 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.set.hour = 13; D.generate(); D.state = 'play';
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.2, 1.35, -.35), Lh: new T.Vector3(-.25, 1.2, -.3) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() };
          V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); D.mpTick(1 / 60); D.updateGun(1 / 60); } };
          const go = (x, z) => { D.P.x = x; D.P.z = z; D.P.y = D.groundAt(x, z); V.ox = x; V.oz = z; V.oy = D.P.y; V.placeAt = true; frames(4); };
          frames(20);
          out.start = { own: JSON.stringify(V.own), weapon: V.weapon, arMag: D.arms.ar.mag, pistolMag: D.arms.pistol.mag, nades: V.nades };
          const drops = [...D.DROPS.values()]; out.guns = drops.filter(d => d.type === 'gun').length; out.crosses = drops.filter(d => d.type === 'hp' || d.type === 'sh').length; out.ammoCans = D.ammoCans.length;
          out.tiers = drops.filter(d => d.type === 'gun').map(d => d.tier).join('');
          D.pickGun('ar'); out.lockedPickRefused = V.weapon === 'pistol';
          // walk onto a gun
          const gd = drops.find(d => d.type === 'gun' && d.kind !== 'pistol'); go(gd.x, gd.z);
          out.gotGun = [gd.kind, gd.tier, V.own[gd.kind] || 0, D.DROPS.has(gd.id) ? 'still there' : 'taken'];
          out.magForTier = [D.WEAP[gd.kind].mag, D.magOf(gd.kind)];
          D.pickGun(gd.kind); out.nowHolding = V.weapon;
          // wheel picture with stars
          V.own.smg = 5; D.arms.smg.mag = D.magOf('smg'); D.drawWheel(-1); window._wheel = V.wheelM.userData.cv.toDataURL('image/png');
          // crosses
          const hc = drops.find(d => d.type === 'hp'), sc = drops.find(d => d.type === 'sh');
          D.MP.hp = 50; go(hc.x, hc.z); out.healthAfterGreen = D.MP.hp; out.greenHidden = hc.got;
          go(sc.x, sc.z); out.shieldAfterBlue = D.MP.sh;
          D.mpTakeHit(50, false); out.afterHit50 = [D.MP.hp, D.MP.sh];
          out.hudShown = !!(D.VHUD.m && D.VHUD.m.visible);
          // die with loot: it spills, you're back to a pistol, your view holds still
          V.own.ar = 3; V.nades = 4; D.arms.ar.res = 60; const n0 = D.DROPS.size, here = [D.P.x, D.P.z];
          D.mpTakeHit(999, false); out.dead = D.MP.dead; out.spilled = D.DROPS.size - n0; out.ownAfterDeath = JSON.stringify(V.own);
          out.spilledGunTier = [...D.DROPS.values()].filter(d => String(d.id).includes(':') && d.type === 'gun').map(d => d.kind + d.tier).join(',');
          pad.L.sy = -1; frames(60); pad.L.sy = 0; out.viewHeldM = +Math.hypot(D.P.x - here[0], D.P.z - here[1]).toFixed(2);
          frames(200); out.backAlive = D.MP.dead <= 0 && D.MP.hp === 100;
          return out; }""")
        d = await pg.evaluate("() => window._wheel"); open(SHOT, 'wb').write(base64.b64decode(d.split(',')[1]))
        print(json.dumps(r)); print("errors:", errs[:8] or "none")
        await b.close()
asyncio.run(main())
