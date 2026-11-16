const CACHE_NAME = 'algocare-v1';
const PRECACHE = ['/', '/index.html', '/dashboard.html', '/assets/style.css', '/assets/auth.js'];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(PRECACHE).catch(() => {})));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  
  // Never cache API requests
  if (req.url.includes("workers.dev")) return;

  event.respondWith(
    fetch(req).then((res) => {
      // Only cache successful, same-origin responses
      if (res.ok && req.url.startsWith(self.location.origin)) {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((c) => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req))
  );
});
