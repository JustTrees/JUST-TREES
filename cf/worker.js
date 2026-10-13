// Just Trees on Cloudflare: serves the game files, plus one extra address, /turn,
// that hands the game a short-lived relay pass (Cloudflare TURN) so friends on strict
// home networks can still connect. The TURN key lives only in this Worker's secrets
// (TURN_KEY_ID, TURN_KEY_TOKEN), set in the Cloudflare dashboard; never in the repo.
const OK_ORIGINS = ["https://justtrees.github.io", "https://just-trees-online.ron-bb2.workers.dev"];

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname !== "/turn") return env.ASSETS.fetch(req);

    const origin = req.headers.get("Origin");
    const okOrigin = !origin || OK_ORIGINS.includes(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
    const head = { "Content-Type": "application/json", "Cache-Control": "no-store", "Vary": "Origin" };
    if (origin && okOrigin) { head["Access-Control-Allow-Origin"] = origin; head["Access-Control-Allow-Methods"] = "GET, OPTIONS"; }
    if (!okOrigin) return new Response(JSON.stringify({ error: "not allowed" }), { status: 403, headers: head });
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: head });
    if (!env.TURN_KEY_ID || !env.TURN_KEY_TOKEN) return new Response(JSON.stringify({ error: "relay not set up yet", sees: Object.keys(env).filter(k => k !== "ASSETS") }), { status: 503, headers: head });   // names only, never values

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
