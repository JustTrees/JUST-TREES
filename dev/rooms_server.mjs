// A local stand-in for the Cloudflare Worker's /rooms (tests): runs cf/worker.js's own code on http://127.0.0.1:<port>
import http from "node:http"; import fs from "node:fs"; import path from "node:path"; import url from "node:url";
const here = path.dirname(url.fileURLToPath(import.meta.url)), tmp = path.join(process.argv[3] || "/tmp", "jt-worker.mjs");
fs.copyFileSync(path.join(here, "..", "cf", "worker.js"), tmp);
const { default: W, Rooms } = await import(url.pathToFileURL(tmp).href);
const R = new Rooms({}, {}), env = { ROOMS: { idFromName: () => "all", get: () => R }, ASSETS: { fetch: () => new Response("", { status: 404 }) } };
http.createServer(async (q, s) => { let body = ""; for await (const c of q) body += c;
  const r = await W.fetch(new Request("http://127.0.0.1" + q.url, { method: q.method, headers: q.headers, body: q.method === "POST" ? body : undefined }), env);
  const h = {}; r.headers.forEach((v, k) => { h[k] = v; }); s.writeHead(r.status, h); s.end(await r.text()); }).listen(+(process.argv[2] || 8787), "127.0.0.1");
