// Just Trees online helper (Cloudflare Worker), v2.
// GET /ice-servers -> short-lived TURN relay logins for players whose networks can't connect directly.
// The two secrets live only in Cloudflare (Settings -> Variables and Secrets): TURN_KEY_ID and TURN_KEY_API_TOKEN.
const ALLOWED = ["https://justtrees.github.io"];           // only the game's own site may ask for relay logins

function cors(origin) {
  const ok = ALLOWED.includes(origin);
  return { "Access-Control-Allow-Origin": ok ? origin : ALLOWED[0], "Access-Control-Allow-Methods": "GET, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" };
}

async function turnLogins(env) {
  const base = `https://rtc.live.cloudflare.com/v1/turn/keys/${env.TURN_KEY_ID}/credentials`;
  const init = { method: "POST", headers: { Authorization: `Bearer ${env.TURN_KEY_API_TOKEN}`, "Content-Type": "application/json" }, body: JSON.stringify({ ttl: 86400 }) };
  // newer endpoint returns a ready-made iceServers list
  let r = await fetch(`${base}/generate-ice-servers`, init);
  if (r.ok) { const j = await r.json(); if (j.iceServers) return Array.isArray(j.iceServers) ? j.iceServers : [j.iceServers]; }
  // older endpoint: one entry
  r = await fetch(`${base}/generate`, init);
  if (r.ok) { const j = await r.json(); if (j.iceServers) return Array.isArray(j.iceServers) ? j.iceServers : [j.iceServers]; }
  throw new Error("TURN login failed: " + r.status);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url), origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") return new Response(null, { headers: cors(origin) });
    if (url.pathname === "/ice-servers") {
      if (!ALLOWED.includes(origin)) return new Response("Not allowed", { status: 403, headers: cors(origin) });
      try {
        const iceServers = await turnLogins(env);
        return new Response(JSON.stringify({ iceServers }), { headers: { ...cors(origin), "Content-Type": "application/json", "Cache-Control": "no-store" } });
      } catch (e) {
        return new Response(JSON.stringify({ error: String(e && e.message || e) }), { status: 502, headers: { ...cors(origin), "Content-Type": "application/json" } });
      }
    }
    if (url.pathname === "/check") {                         // a safe self-test: says whether the relay logins work, never shows them
      const has = { TURN_KEY_ID: !!env.TURN_KEY_ID, TURN_KEY_API_TOKEN: !!env.TURN_KEY_API_TOKEN };
      try { const s = await turnLogins(env); return new Response(JSON.stringify({ secretsSet: has, relayWorks: true, servers: s.length, kinds: [...new Set(s.flatMap(x => [].concat(x.urls)).map(u => u.split(":")[0]))] }), { headers: { "Content-Type": "application/json" } }); }
      catch (e) { return new Response(JSON.stringify({ secretsSet: has, relayWorks: false, problem: String(e && e.message || e) }), { headers: { "Content-Type": "application/json" } }); }
    }
    return new Response("Just Trees online helper is running.", { headers: { "Content-Type": "text/plain" } });
  },
};
