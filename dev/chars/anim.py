import asyncio, os, sys, json, base64
from playwright.async_api import async_playwright
D = os.path.dirname(os.path.abspath(__file__))
OUT, LIST, ANIMS = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS = int(os.environ.get("W", 1280)), int(os.environ.get("H", 600)), int(os.environ.get("FPS", 20))
async def main():
    import subprocess
    srv = subprocess.Popen(["python3", "-m", "http.server", "8794"], cwd=D, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
            pg = await b.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await asyncio.sleep(.8)
            await pg.goto("http://127.0.0.1:8794/view.html"); await pg.wait_for_function("window.ready === true", timeout=60000)
            await pg.evaluate(os.environ.get("PRE", "0"))
            src = open(os.path.join(D, "compose.js")).read()
            if os.environ.get("BAKED"): src = src.rstrip().rstrip("0;") + "\n" + open(os.path.join(D, "bview.js")).read()
            await pg.evaluate(src)
            if os.environ.get("BAKED"): await pg.evaluate("useBaked()")
            fr = await pg.evaluate("([l, a, W, H, fps, y, cz, cy, ly, fv]) => animFrames(eval(l), eval(a), W, H, fps, y, cz, cy, ly, fv)",
                [LIST, ANIMS, W, H, FPS, float(os.environ.get("YAW", ".9")), float(os.environ.get("CZ", "5")), float(os.environ.get("CAMY", "1.1")), float(os.environ.get("LOOKY", ".9")), float(os.environ.get("FOV", "26"))])
            os.makedirs(OUT, exist_ok=True)
            for i, u in enumerate(fr): open(f"{OUT}/f{i:04d}.jpg", "wb").write(base64.b64decode(u.split(",")[1]))
            print("frames", len(fr), "errors", errs); await b.close()
    finally: srv.terminate()
asyncio.run(main())
