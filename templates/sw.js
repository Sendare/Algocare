// The __BUILD_ID__ will be replaced by the Python build script on every deploy
const CACHE_NAME = 'algocare-__BUILD_ID__';

const PRECACHE = [
  '/', 
  '/index.html', 
  '/dashboard.html', 
  '/assets/style.css', 
  '/assets/auth.js'
];

self.addEventListener("install", (event) => {
  self.skipWaiting(); // Force the new SW to take over immediately
  event.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(PRECACHE).catch(() => {})));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  
  // Never cache API requests
  if (req.url.includes("workers.dev") || req.url.includes("supabase.co")) return;

  event.respondWith(
    fetch(req).then((res) => {
      if (res.ok && req.url.startsWith(self.location.origin)) {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((c) => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req))
  );
});
