// Just Trees on Cloudflare: serves the game files, plus one extra address, /turn,
// that hands the game a short-lived relay pass (Cloudflare TURN) so friends on strict
// home networks can still connect. The TURN key lives only in this Worker's secrets
// (TURN_KEY_ID, TURN_KEY_TOKEN), set in the Cloudflare dashboard; never in the repo.
const OK_ORIGINS = ["https://justtrees.github.io", "https://just-trees-online.ron-bb2.workers.dev"];

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/rooms") return rooms(req, env);
    if (url.pathname === "/count") return count(req, env);
    if (url.pathname === "/dev") return dev(req, env);
    if (url.pathname !== "/turn") return env.ASSETS.fetch(req);

    const origin = req.headers.get("Origin");
    const okOrigin = !origin || OK_ORIGINS.includes(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
    const head = { "Content-Type": "application/json", "Cache-Control": "no-store", "Vary": "Origin" };
    if (origin && okOrigin) { head["Access-Control-Allow-Origin"] = origin; head["Access-Control-Allow-Methods"] = "GET, OPTIONS"; }
    if (!okOrigin) return new Response(JSON.stringify({ error: "not allowed" }), { status: 403, headers: head });
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: head });
    if (!env.TURN_KEY_ID || !env.TURN_KEY_TOKEN) return new Response(JSON.stringify({ error: "relay not set up yet" }), { status: 503, headers: head });

    const r = await fetch(`https://rtc.live.cloudflare.com/v1/turn/keys/${env.TURN_KEY_ID}/credentials/generate-ice-servers`, {
      method: "POST",
      headers: { Authorization: `Bearer ${env.TURN_KEY_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ ttl: 6 * 3600 }),               // a pass lasts 6 hours: longer than any session
    });
    if (!r.ok) return new Response(JSON.stringify({ error: "relay error " + r.status }), { status: 502, headers: head });
    const data = await r.json();
    // drop port 53 addresses: browsers block them and they only cause a wait
    for (const s of data.iceServers || []) if (Array.isArray(s.urls)) s.urls = s.urls.filter(u => !/:53\b/.test(u));
    return new Response(JSON.stringify(data), { headers: head });
  },
};

// ---- 2.28: the open games list. A public room checks in every 30 s (POST {op:"beat", ...}); the game's "Find a game" screen reads the list (GET).
// One small Durable Object holds the list in memory (nothing stored: rooms check in again within 30 s, so a restart loses nothing).
// A room that stops checking in is gone after 75 s; full rooms (8/8) aren't listed. Nothing here is secret.
async function rooms(req, env) {
  const origin = req.headers.get("Origin");
  const okOrigin = !origin || OK_ORIGINS.includes(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
  const head = { "Content-Type": "application/json", "Cache-Control": "no-store", "Vary": "Origin" };
  if (origin && okOrigin) { head["Access-Control-Allow-Origin"] = origin; head["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"; head["Access-Control-Allow-Headers"] = "Content-Type"; }
  if (!okOrigin) return new Response(JSON.stringify({ error: "not allowed" }), { status: 403, headers: head });
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: head });
  if (!env.ROOMS) return new Response(JSON.stringify({ rooms: [], error: "list not set up" }), { headers: head });
  const r = await env.ROOMS.get(env.ROOMS.idFromName("all")).fetch(req);
  return new Response(await r.text(), { status: r.status, headers: head });
}
const clip = (v, n) => String(v == null ? "" : v).replace(/[^\x20-\x7e]/g, "").slice(0, n);
const int = (v, a, b) => Math.max(a, Math.min(b, Math.round(+v || 0)));
export class Rooms {
  constructor(ctx, env) { this.ctx = ctx; this.m = new Map(); }
  async fetch(req) {
    const now = Date.now(), out = (o, st = 200) => new Response(JSON.stringify(o), { status: st, headers: { "Content-Type": "application/json" } });
    for (const [k, r] of this.m) if (now - r.t > 75000) this.m.delete(k);
    if (req.method === "POST") {
      let b; try { b = await req.json(); } catch (e) { return out({ error: "bad" }, 400); }
      const code = clip(b && b.code, 4); if (!/^\d{4}$/.test(code)) return out({ error: "bad code" }, 400);
      if (b.op === "gone") { this.m.delete(code); return out({ ok: true }); }
      if (!this.m.has(code) && this.m.size >= 300) return out({ error: "too many" }, 503);
      this.m.set(code, { code, host: clip(b.host, 14) || "PLAYER", col: int(b.col, 0, 7), mode: ["hike", "hunt", "pvp"].includes(b.mode) ? b.mode : "hike", dino: !!b.dino, teams: !!b.teams,
        map: clip(b.map, 12), n: int(b.n, 1, 8), st: b.st === "play" ? "play" : "lobby", left: int(b.left, 0, 7200), v: clip(b.v, 12), t: now });
      return out({ ok: true });
    }
    const v = new URL(req.url).searchParams.get("v");
    const list = [...this.m.values()].filter(r => (!v || r.v === v) && r.n < 8).sort((a, c) => c.t - a.t).slice(0, 60).map(r => Object.assign({}, r, { age: now - r.t, t: undefined }));
    return out({ rooms: list });
  }
}

// ---- 2.40: maps made per day. The game adds one for each new map (POST {dev, on, mode}); nothing about the player is sent or kept.
// GET /count shows the totals for the last 60 days (Los Angeles time), newest first. Kept in a small Durable Object's storage.
async function count(req, env) {
  const origin = req.headers.get("Origin");
  const okOrigin = !origin || OK_ORIGINS.includes(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
  const head = { "Content-Type": "application/json", "Cache-Control": "no-store", "Vary": "Origin" };
  if (origin && okOrigin) { head["Access-Control-Allow-Origin"] = origin; head["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"; head["Access-Control-Allow-Headers"] = "Content-Type"; }
  if (!okOrigin) return new Response(JSON.stringify({ error: "not allowed" }), { status: 403, headers: head });
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: head });
  if (!env.COUNTS) return new Response(JSON.stringify({ error: "not set up" }), { status: 503, headers: head });
  const r = await env.COUNTS.get(env.COUNTS.idFromName("all")).fetch(req);
  return new Response(await r.text(), { status: r.status, headers: head });
}
export class Counts {
  constructor(ctx, env) { this.ctx = ctx; }
  async fetch(req) {
    const out = (o, st = 200) => new Response(JSON.stringify(o, null, 1), { status: st, headers: { "Content-Type": "application/json" } });
    const day = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    if (req.method === "POST") {
      let b; try { b = await req.json(); } catch (e) { return out({ error: "bad" }, 400); }
      const k = "d:" + day, c = (await this.ctx.storage.get(k)) || { maps: 0 };
      const inc = n => { c[n] = (c[n] || 0) + 1; };
      inc("maps"); inc(["vr", "pc", "phone"].includes(b && b.dev) ? b.dev : "pc"); inc(b && b.on ? "online" : "solo"); inc(["hike", "hunt", "pvp"].includes(b && b.mode) ? b.mode : "hike");
      await this.ctx.storage.put(k, c);
      return out({ ok: true });
    }
    const all = await this.ctx.storage.list({ prefix: "d:", reverse: true, limit: 60 });
    return out({ days: [...all].map(([k, c]) => Object.assign({ day: k.slice(2) }, c)) });
  }
}

// ---- 2.45: Dev Mode saves (the Creature Workshop and later dev tools). Saving needs the DEV_KEY secret (set in the Cloudflare dashboard,
// never in the repo); reading is open (it's only creature shapes and settings). POST {op:"check"|"save", key, kind, name, data}; GET ?list=<kind> or ?get=<kind>&name=<name>.
async function dev(req, env) {
  const origin = req.headers.get("Origin");
  const okOrigin = !origin || OK_ORIGINS.includes(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
  const head = { "Content-Type": "application/json", "Cache-Control": "no-store", "Vary": "Origin" };
  if (origin && okOrigin) { head["Access-Control-Allow-Origin"] = origin; head["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"; head["Access-Control-Allow-Headers"] = "Content-Type"; }
  if (!okOrigin) return new Response(JSON.stringify({ error: "not allowed" }), { status: 403, headers: head });
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: head });
  if (!env.DEVSTORE) return new Response(JSON.stringify({ error: "not set up" }), { status: 503, headers: head });
  let body = null;
  if (req.method === "POST") {
    if (!env.DEV_KEY) return new Response(JSON.stringify({ error: "no key set" }), { status: 503, headers: head });
    try { body = await req.json(); } catch (e) { return new Response(JSON.stringify({ error: "bad" }), { status: 400, headers: head }); }
    const a = String(body && body.key || "").toUpperCase(), b = String(env.DEV_KEY).toUpperCase(); let diff = a.length ^ b.length;
    for (let i = 0; i < Math.max(a.length, b.length); i++) diff |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
    if (diff) return new Response(JSON.stringify({ error: "wrong key" }), { status: 403, headers: head });
    if (body.op === "check") return new Response(JSON.stringify({ ok: true }), { headers: head });
  }
  const r = await env.DEVSTORE.get(env.DEVSTORE.idFromName("all")).fetch(new Request(req.url, { method: req.method, body: body ? JSON.stringify(body) : undefined }));
  return new Response(await r.text(), { status: r.status, headers: head });
}
export class DevStore {
  constructor(ctx, env) { this.ctx = ctx; }
  async fetch(req) {
    const out = (o, st = 200) => new Response(JSON.stringify(o), { status: st, headers: { "Content-Type": "application/json" } });
    const clip = (v, n) => String(v == null ? "" : v).replace(/[^\x20-\x7e]/g, "").slice(0, n);
    if (req.method === "POST") {
      const b = await req.json(), kind = clip(b.kind, 16).replace(/[^a-z]/g, ""), name = clip(b.name, 24).trim();
      if (b.op !== "save" || !kind || !name) return out({ error: "bad" }, 400);
      const data = JSON.stringify(b.data || null); if (data.length > 60000) return out({ error: "too big" }, 413);
      await this.ctx.storage.put(kind + ":" + name.toUpperCase(), { name, t: Date.now(), data });
      return out({ ok: true });
    }
    const q = new URL(req.url).searchParams, kind = clip(q.get("list") || q.get("get"), 16).replace(/[^a-z]/g, "");
    if (!kind) return out({ error: "bad" }, 400);
    if (q.get("get")) { const v = await this.ctx.storage.get(kind + ":" + clip(q.get("name"), 24).trim().toUpperCase()); return v ? out({ name: v.name, t: v.t, data: JSON.parse(v.data) }) : out({ error: "not found" }, 404); }
    const all = await this.ctx.storage.list({ prefix: kind + ":", limit: 300 });
    return out({ items: [...all.values()].map(v => ({ name: v.name, t: v.t })).sort((a, c) => c.t - a.t) });
  }
}
