/**
 * Northwind Logistics — Strangler Fig Proxy
 *
 * Sits in front of both servers on port 8080.
 * Routes that have been migrated go to the modern app (8082).
 * Everything else goes to the legacy app (8081).
 *
 * To migrate a route: add a pattern to MODERN_ROUTES below.
 * Neither app knows the proxy exists.
 */

import http       from 'http';
import httpProxy  from 'http-proxy';

const LEGACY = 'http://localhost:8081';
const MODERN = 'http://localhost:8082';

// ---- Add patterns here as routes are extracted ---------------------------
const MODERN_ROUTES = [
  /^\/api\/orders(\/|$)/,

  // Uncomment when extracted:
  // /^\/api\/customers(\/|$)/,
  // /^\/api\/products(\/|$)/,
  // /^\/api\/reports(\/|$)/,
];
// --------------------------------------------------------------------------

const proxy = httpProxy.createProxyServer({});

proxy.on('error', (err, req, res) => {
  console.error(`[proxy] error routing ${req.url}:`, err.message);
  res.writeHead(502);
  res.end('Bad gateway');
});

http.createServer((req, res) => {
  const target = MODERN_ROUTES.some(re => re.test(req.url)) ? MODERN : LEGACY;
  console.log(`[proxy] ${req.method} ${req.url} → ${target === MODERN ? 'MODERN' : 'legacy'}`);
  proxy.web(req, res, { target });
}).listen(8080, () => {
  console.log('Strangler fig proxy on http://localhost:8080');
  console.log(`  /api/orders  → modern  (http://localhost:${8082})`);
  console.log(`  /*           → legacy  (http://localhost:${8081})`);
});
