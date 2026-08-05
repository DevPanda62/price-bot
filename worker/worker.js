const ROUTES = {
  "products": "api/products.json",
  "discounts": "api/discounts.json",
  "errors": "api/errors.json",
  "stats": "api/stats.json",
  "changes": "api/changes.json",
  "history": "api/history.json",
  "index": "api/index.json",
};

function collectKeys(env) {
  const keys = new Set();
  const sources = [env.API_SECRET_KEY, env.API_KEYS];
  for (const s of sources) {
    if (!s) continue;
    for (const k of String(s).split(",")) {
      const t = k.trim();
      if (t) keys.add(t);
    }
  }
  return keys;
}

function forbidden() {
  return new Response(
    JSON.stringify({ detail: "Gecersiz veya eksik API anahtari" }),
    {
      status: 403,
      headers: { "content-type": "application/json; charset=utf-8" },
    }
  );
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/+/, "");

    if (path === "" || path === "health") {
      return new Response(
        "Firsat API worker aktif. Veri uc noktalari X-API-Key header'i gerektirir.",
        {
          status: 200,
          headers: { "content-type": "text/plain; charset=utf-8" },
        }
      );
    }

    const keys = collectKeys(env);
    const given = (request.headers.get("X-API-Key") || "").trim();
    if (!given || !keys.has(given)) {
      return forbidden();
    }

    let file;
    if (ROUTES[path]) {
      file = ROUTES[path];
    } else if (path.startsWith("stores/")) {
      const site = path.slice("stores/".length);
      if (!/^[a-z0-9-]{1,40}$/.test(site)) {
        return new Response(JSON.stringify({ detail: "Gecersiz site" }), {
          status: 400,
          headers: { "content-type": "application/json" },
        });
      }
      file = "api/stores/" + site + ".json";
    } else {
      return new Response(JSON.stringify({ detail: "Uc nokta bulunamadi" }), {
        status: 404,
        headers: { "content-type": "application/json" },
      });
    }

    const origin = env.ORIGIN || "https://kullanici.github.io/firsat-api";
    const res = await fetch(origin + "/" + file, { cf: { cacheTtl: 60 } });
    const body = await res.arrayBuffer();
    return new Response(body, {
      status: res.status,
      headers: {
        "content-type": res.headers.get("content-type") || "application/json; charset=utf-8",
        "cache-control": "public, max-age=60",
        "access-control-allow-origin": "*",
      },
    });
  },
};
