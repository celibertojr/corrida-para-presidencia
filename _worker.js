// _worker.js — Cloudflare Pages (modo avançado)
// Serve o site (index.html) e expõe GET /api/resultado com os dados da Presidência
// vindos do TSE, já normalizados e com cache na borda da Cloudflare.
//
// Variáveis de ambiente opcionais (Pages > Settings > Environment variables):
//   TSE_URL = "..."   sobrescreve a URL do JSON (útil se o TSE mudar o caminho)

const UPSTREAM = {
  // Padrão dos arquivos de 2026: /dados/<uf>/<uf>-c0001-e<eleição com 6 dígitos>-u.json
  oficial: "https://resultados.tse.jus.br/oficial/ele2026/6257/dados/br/br-c0001-e006257-u.json",
};

const FRESH = 20;   // segundos em que uma resposta boa é servida sem consultar o TSE
const STALE = 3600; // segundos em que a última resposta boa fica de reserva
const MISS = 60;    // segundos de cache para "ainda não publicado" (evita rajada de 404 no TSE)
const FAIL = 10;    // segundos de cache para erro do TSE

// O TSE usa vírgula decimal ("7,53"); números inteiros vêm como texto ("9075260").
function num(v) {
  if (v === null || v === undefined || v === "") return NaN;
  let s = String(v).trim();
  if (s.indexOf(",") >= 0) s = s.replace(/\./g, "").replace(",", ".");
  return Number(s);
}

// Junta todos os candidatos, qualquer que seja o aninhamento (carg > agr > par > cand).
function collect(node, out) {
  if (Array.isArray(node)) { node.forEach((n) => collect(n, out)); return; }
  if (node && typeof node === "object") {
    if (Array.isArray(node.cand)) node.cand.forEach((c) => out.push(c));
    for (const k in node) if (k !== "cand") collect(node[k], out);
  }
}

// Converte o JSON bruto do TSE (-u.json) no formato enxuto que o site usa.
function normalize(raw, src) {
  const carg = (raw.carg || []).find((c) => String(c.cd) === "1") || (raw.carg || [])[0];
  const list = [];
  collect(carg ? [carg] : [], list);
  const cands = list
    .map((c) => ({
      n: parseInt(c.n, 10),
      nm: c.nmu || c.nm || "",
      vap: num(c.vap),                       // votos apurados
      pvap: num(c.pvapn !== undefined ? c.pvapn : c.pvap), // % que o site do TSE exibe
      dvt: c.dvt || "",                      // "Válido", "Anulado", "Anulado sub judice"
      stt: c.st || "",                       // "Eleito", "2º turno", "Não eleito"...
    }))
    .filter((c) => Number.isFinite(c.n) && Number.isFinite(c.vap));
  const s = raw.s || {}, e = raw.e || {}, v = raw.v || {};
  const pst = num(s.pstn !== undefined ? s.pstn : s.pst); // % de seções (urnas) totalizadas
  const out = {
    ok: cands.length > 0 && Number.isFinite(pst),
    src: src,
    generated: [raw.dt, raw.ht].filter(Boolean).join(" "),
    pst: pst,
    ts: num(s.ts), st: num(s.st),          // seções totais / totalizadas
    te: num(e.te), est: num(e.est),        // eleitorado total / das seções totalizadas
    vvc: num(v.vvc), vv: num(v.vv),        // votos válidos (com e sem sub judice)
    cands: cands,
  };
  if (!out.ok) out.error = "formato_inesperado";
  return out;
}

function json(body, ttl, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=" + ttl,
      "access-control-allow-origin": "*",
    },
  });
}

function pickUrl(env) {
  if (env.TSE_URL) return { url: env.TSE_URL, src: "custom" };
  return { url: UPSTREAM.oficial, src: "oficial" }; // somente dados oficiais; não há modo de simulação
}

async function resultado(request, env, ctx) {
  const cache = caches.default;
  const base = new URL(request.url).origin;
  const freshKey = new Request(base + "/api/resultado");
  const staleKey = new Request(base + "/__reserva/resultado");

  const hit = await cache.match(freshKey);
  if (hit) return hit;

  const up = pickUrl(env);
  const keep = (key, resp, ttl) => {
    const c = new Response(resp.clone().body, resp);
    c.headers.set("cache-control", "public, max-age=" + ttl);
    ctx.waitUntil(cache.put(key, c));
  };

  try {
    const r = await fetch(up.url, { headers: { accept: "application/json" } });
    if (r.status === 404 || r.status === 403) {
      const reserva = await cache.match(staleKey);
      if (reserva) { const j = await reserva.json(); j.stale = true; return json(j, FAIL); }
      const resp = json({ ok: false, error: "not_published", status: r.status, src: up.src }, MISS);
      keep(freshKey, resp, MISS);
      return resp;
    }
    if (!r.ok) throw new Error("upstream " + r.status);
    const data = normalize(await r.json(), up.src);
    if (!data.ok) throw new Error(data.error);
    const resp = json(data, FRESH);
    keep(freshKey, resp, FRESH);
    keep(staleKey, json(data, STALE), STALE);
    return resp;
  } catch (err) {
    const reserva = await cache.match(staleKey);
    if (reserva) {
      const j = await reserva.json(); j.stale = true;
      return json(j, FAIL);
    }
    const resp = json({ ok: false, error: "upstream_error", src: up.src }, FAIL, 502);
    keep(freshKey, resp, FAIL);
    return resp;
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/api/resultado") {
      if (request.method !== "GET" && request.method !== "HEAD") return new Response("Método não permitido", { status: 405 });
      return resultado(request, env, ctx);
    }
    if (url.pathname === "/api/status") {
      const up = pickUrl(env);
      return json({ upstream: up.url, src: up.src, fresh: FRESH }, 0);
    }
    return env.ASSETS.fetch(request); // demais rotas: arquivos do site
  },
};
