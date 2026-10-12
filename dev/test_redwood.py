"""Redwood forest (1.74): an environment for 35-45° (California). Tall coast redwoods with red furrowed trunks bare a third to half way up,
giant sequoias (shorter, massive trunks, rounded crowns) more of them up the slopes, groves of pale eucalyptus low down, some Douglas fir
and broadleaf understory, ferns, needle duff, morning fog. The level's giant is always a sequoia. Redwoods and sequoias are never fluffy.
Animals: Roosevelt elk, deer, black bear, cougar, fox, turkey, rabbits, eagles (and Bigfoot on big maps)."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          out.opts = D.envOptions(40).map(o => o[0]); out.note = D.envNote(40); out.opts50 = D.envOptions(50).map(o => o[0]);
          const gen = (env, lat, month, size) => { D.setSeed(4); D.setVR(true); D.setMode('hunt'); D.set.env = env; D.set.land = 'natural'; D.set.size = size; D.set.lat = lat; D.set.month = month; D.set.weather = 'clear'; D.generate(); D.state = 'play'; };
          const stats = () => { const K = window.__kinds, st = {}; let g = null;
            for (const t of window.__trees) { if (t.giant) { g = t; continue; } const v = K[t.kind].vars[t.vi], o = st[t.kind] = st[t.kind] || { n: 0, h: 0, r: 0, f: 0, max: 0 };
              const h = v.h * t.s * t.sy; o.n++; o.h += h; o.max = Math.max(o.max, h); o.r += (v.r - .2) * t.s * t.sx; if (v.fluffy) o.f++; }
            let N = 0; for (const k in st) N += st[k].n;
            for (const k in st) { const o = st[k]; o.share = +(o.n / N).toFixed(2); o.h = +(o.h / o.n).toFixed(1); o.r = +(o.r / o.n).toFixed(2); o.f = +(o.f / o.n).toFixed(2); o.max = +o.max.toFixed(1); }
            return { st, g }; };
          for (const [m, key] of [[6, 'summer'], [0, 'winter']]) {
            gen('redwood', 40, m, 'large'); const { st, g } = stats(), o = out[key] = { env: D.MAPENV.b, st };
            o.giant = g ? { kind: g.kind, name: g.name, porch: +g.porchH.toFixed(1) } : null; o.porch = !!D.PORCH;
            const kinds = {}; for (const A of D.beasts) kinds[A.kind] = (kinds[A.kind] || 0) + 1; o.kinds = kinds;
            o.missing = D.NATIVE.redwood.map(k => k[0]).filter(k => !D.LEGEND[k] && !kinds[k]); o.foreign = Object.keys(kinds).filter(k => !D.NATIVE.redwood.some(n => n[0] === k));
            for (let i = 0; i < 200; i++) D.updateAnimals(1 / 30); o.moving = D.beasts.filter(A => !A.wings && A.speed > .1).length;
            if (key === 'summer' && D.climbableAt) { const t = window.__trees.find(t => t.kind === 'sequoia' && !t.giant), T = D.THREE;
              o.climb = !!D.climbableAt(new T.Vector3(t.x, D.H(t.x, t.z) + 3, t.z)); }
          }
          gen('climate', 40, 6, 'medium'); out.plainKinds = Object.keys(stats().st);
          D.set.env = 'climate'; return out; }""")
        print(json.dumps(r))
        S, W = r["summer"], r["winter"]
        def good(o):
            st = o["st"]
            return o["env"] == "redwood" and all(k in st for k in ["redwood", "sequoia", "euc"]) and st["redwood"]["share"] > .35 and .03 < st["euc"]["share"] < .2 \
                and st["redwood"]["h"] > 2 * st["broad" if "broad" in st else "bare"]["h"] and st["redwood"]["h"] > st["sequoia"]["h"] and st["sequoia"]["r"] > 1.5 * st["redwood"]["r"] \
                and st["redwood"]["f"] == 0 and st["sequoia"]["f"] == 0 and st["redwood"]["max"] < 55 \
                and o["giant"] and o["giant"]["kind"] == "sequoia" and "sequoia" in o["giant"]["name"] and o["porch"] and o["giant"]["porch"] < 65 \
                and not o["missing"] and not o["foreign"] and o["moving"] > 5
        ok = "redwood" in r["opts"] and "redwood" not in r["opts50"] and "redwood forest" in r["note"].lower() and good(S) and good(W) and S["climb"] is not False \
             and not ({"redwood", "sequoia", "euc"} & set(r["plainKinds"]))
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
