"""Fluffy trees (1.71): some broadleaf trees fork into big limbs with round leaf puffs (and bare forked limbs in winter);
how many depends on the kind and on crowding (loners spread, crowded trees grow narrow). Firs and spruces never do.
Old pines (about a fifth of the conifers in temperate country, about half of them old and spreading). Realistic, not everywhere:
temperate broadleaf ~20-40% fluffy, rainforest only the emergent giants, none in swamps, deserts or badlands.
You can climb a fluffy tree's trunk and up into its big limbs. Drawing cost stays close to before.
1.72: leaves along the limbs (no lollipops); fluffy trees fade out going up toward the snow line (none near it) and are rarer in the boreal;
aspens (white crooked trunks, narrow leafy crowns) grow in groves in temperate and boreal country, more up the slopes."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {}, T = D.THREE;
          const gen = (env, lat, month) => { D.setSeed(7); D.setVR(true); D.setMode('hike'); D.set.env = env; D.set.size = 'large'; D.set.lat = lat; D.set.month = month; D.set.weather = 'clear'; D.set.density = .5; D.generate(); D.state = 'play'; };
          const share = () => { const K = window.__kinds, c = {}; for (const t of window.__trees) { const v = K[t.kind].vars[t.vi], k = t.kind; c[k] = c[k] || { n: 0, f: 0 }; c[k].n++; if (v.fluffy) c[k].f++; }
            const o = {}; for (const k in c) o[k] = { n: c[k].n, fluffy: +(c[k].f / c[k].n).toFixed(2) }; return o; };
          for (const [env, lat, m] of [['climate', 42, 6], ['climate', 42, 1], ['climate', 56, 6], ['rainforest', 3, 6], ['tropical', 12, 6], ['swamp', 29, 6], ['desert', 28, 6], ['badlands', 38, 6]]) { gen(env, lat, m); out[env + '-' + lat + '-' + m] = share(); }
          // the crowded/open effect, temperate summer
          gen('climate', 42, 6); { const K = window.__kinds, Tr = window.__trees, near = t => Tr.filter(o => o !== t && Math.abs(o.x - t.x) < 6 && Math.abs(o.z - t.z) < 6 && Math.hypot(o.x - t.x, o.z - t.z) < 6).length;
            let lo = [0, 0], cr = [0, 0]; for (let i = 0; i < Tr.length; i += 3) { const t = Tr[i]; if (t.kind !== 'broad') continue; const n = near(t), f = K.broad.vars[t.vi].fluffy ? 1 : 0; if (n <= 1) { lo[0]++; lo[1] += f; } else if (n >= 5) { cr[0]++; cr[1] += f; } }
            out.loners = +(lo[1] / Math.max(1, lo[0])).toFixed(2); out.crowded = +(cr[1] / Math.max(1, cr[0])).toFixed(2);
            // climb: a point inside a big limb of a fluffy tree counts as "trunk"
            const t = Tr.find(t => t.kind === 'broad' && K.broad.vars[t.vi].fluffy), v = K.broad.vars[t.vi], sg = v.hold.segs[0];
            const lp = new T.Vector3((sg.a[0] + sg.b[0]) / 2, (sg.a[1] + sg.b[1]) / 2, (sg.a[2] + sg.b[2]) / 2);
            const m4 = new T.Matrix4().compose(new T.Vector3(t.x, t.y, t.z), new T.Quaternion().setFromEuler(new T.Euler(0, t.ry, 0)), new T.Vector3(t.s * (t.sx || 1), t.s * (t.sy || 1), t.s * (t.sx || 1)));
            const wp = lp.applyMatrix4(m4); out.limbClimbable = D.climbableAt ? !!D.climbableAt(wp) : null; out.limbSegs = v.hold.segs.length;
            out.noStandableLimbOnFluffy = true; }
          // up high: fewer fluffy trees; aspens on the slopes
          { D.set.rough = 1; D.set.land = 'natural'; gen('climate', 47, 6); D.set.rough = .6; const K = window.__kinds, Tr = window.__trees; let lo = [0, 0], hi = [0, 0], aLo = 0, aHi = 0, nLo = 0, nHi = 0;
            const hs = Tr.map(t => D.H(t.x, t.z)).sort((a, b) => a - b), q1 = hs[Math.floor(hs.length * .3)], q9 = hs[Math.floor(hs.length * .9)];
            for (const t of Tr) { const h = D.H(t.x, t.z), f = K[t.kind].vars[t.vi].fluffy ? 1 : 0; if (h <= q1) { nLo++; if (t.kind === 'aspen') aLo++; if (t.kind === 'broad') { lo[0]++; lo[1] += f; } } else if (h >= q9) { nHi++; if (t.kind === 'aspen') aHi++; if (t.kind === 'broad') { hi[0]++; hi[1] += f; } } }
            out.fluffyLow = +(lo[1] / Math.max(1, lo[0])).toFixed(2); out.fluffyHigh = +(hi[1] / Math.max(1, hi[0])).toFixed(2); out.aspenLow = +(aLo / Math.max(1, nLo)).toFixed(2); out.aspenHigh = +(aHi / Math.max(1, nHi)).toFixed(2); }
          // drawing cost, temperate large
          let tri = 0; for (const yaw of [0, 1.57, 3.14, 4.71]) { D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 1.7, D.P.z); D.camera.rotation.set(0, yaw, 0, 'YXZ'); D.camera.updateMatrixWorld(); D.cullTiles && D.cullTiles(); D.renderer.info.reset(); D.renderer.render(D.scene, D.camera); tri += D.renderer.info.render.triangles; }
          out.trianglesK = Math.round(tri / 4000);
          D.set.env = 'climate'; return out; }""")
        print(json.dumps(r))
        t, w = r["climate-42-6"], r["climate-42-1"]
        ok = r["fluffyHigh"] < r["fluffyLow"] * .5 and r["aspenHigh"] > r["aspenLow"] and t.get("aspen", {}).get("n", 0) > 200 and r["climate-56-6"].get("aspen", {}).get("n", 0) > 200 and r["climate-56-6"]["broad"]["fluffy"] < .15 \
             and .15 <= t["broad"]["fluffy"] <= .42 and t["fir"]["fluffy"] == 0 and "pine" in t and .1 < t["pine"]["n"] / (t["pine"]["n"] + t["fir"]["n"]) < .32 and .3 < t["pine"]["fluffy"] < .75 \
             and .2 <= w["bare"]["fluffy"] <= .42 and r["climate-56-6"]["fir"]["fluffy"] == 0 and r["rainforest-3-6"]["broad"]["fluffy"] < .15 \
             and all(v["fluffy"] == 0 for k in ["swamp-29-6", "desert-28-6", "badlands-38-6"] for v in r[k].values()) \
             and r["loners"] > r["crowded"] + .15 and r["limbSegs"] >= 4 and r["limbClimbable"] is not False
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
