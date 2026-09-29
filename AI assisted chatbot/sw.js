// Service worker: saves the pages so the chatbot opens even without internet
const C = "phc-v1";
self.addEventListener("install", e => { e.waitUntil(caches.open(C).then(c => c.addAll(["/", "/dashboard"]))); self.skipWaiting(); });
self.addEventListener("activate", e => e.waitUntil(clients.claim()));
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method != "GET" || u.pathname.startsWith("/api")) return;
  e.respondWith(fetch(e.request).then(r => { const x = r.clone(); caches.open(C).then(c => c.put(e.request, x)); return r; })
    .catch(() => caches.match(e.request)));
});