import sys, asyncio, subprocess, time, os
from playwright.async_api import async_playwright
D, OUT, names = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8772", "--bind", "127.0.0.1"], cwd=D, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://127.0.0.1:8772/dump.html"); await pg.wait_for_function("window.ready === true", timeout=30000)
        for n in names:
            s = await pg.evaluate("n => dump(n)", n); open(os.path.join(OUT, n + ".json"), "w").write(s); print(n, len(s) // 1024, "kB", flush=True)
        print(errs[:3]); await b.close()
try: asyncio.run(main())
finally: srv.terminate()
