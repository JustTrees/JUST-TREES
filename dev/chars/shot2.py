import sys, asyncio, subprocess, time, base64, os
from playwright.async_api import async_playwright
D = os.path.dirname(os.path.abspath(__file__)); OUT, LIST = sys.argv[1], sys.argv[2]; YAW = float(sys.argv[3]) if len(sys.argv) > 3 else 0; CZ = float(sys.argv[4]) if len(sys.argv) > 4 else 0
W = int(sys.argv[5]) if len(sys.argv) > 5 else 1600; H = int(sys.argv[6]) if len(sys.argv) > 6 else 700
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8793", "--bind", "127.0.0.1"], cwd=D, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]); pg = await b.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text[:600]) if m.type in ("error", "warning") else None)
        await pg.goto("http://127.0.0.1:8793/view.html"); await pg.wait_for_function("window.ready === true", timeout=30000)
        await pg.evaluate(os.environ.get("PRE", "0"))
        src = open(os.path.join(D, os.environ.get("COMPOSE", "compose.js"))).read()
        if os.environ.get("BAKED"): src = src.rstrip().rstrip("0;") + "\n" + open(os.path.join(D, "bview.js")).read()
        await pg.evaluate(src)
        if os.environ.get("BAKED"): await pg.evaluate("useBaked()")
        u = await pg.evaluate("([l, y, cz, W, H, cy, ly, fv]) => shot2(eval(l), W, H, y, cz, cy, ly, fv)", [LIST, YAW, CZ, W, H, float(os.environ.get("CAMY", "1.0")), float(os.environ.get("LOOKY", ".9")), float(os.environ.get("FOV", "30"))])
        open(OUT, "wb").write(base64.b64decode(u.split(",")[1])); print("errors", [e for e in errs if "ERROR" in e or "rror" in e][:3]); await b.close()
try: asyncio.run(main())
finally: srv.terminate()
