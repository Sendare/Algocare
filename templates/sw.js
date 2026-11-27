// No-cache Service Worker for active development
self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  // Always fetch from the network, never store in cache
  e.respondWith(fetch(e.request, { cache: "no-store" }));
});
