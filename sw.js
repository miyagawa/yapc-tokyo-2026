// Offline support for bad conference Wi-Fi.
// Network first (so timetable changes show up), but fall back to the cached copy
// after 3 seconds or when offline.
var CACHE = "yapc-tokyo-2026-v1";
var PRECACHE = ["./", "favicon.svg", "data/timetable.json", "ics/all.ics", "ics/talks.ics"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(PRECACHE); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  var isPage = req.mode === "navigate";
  var key = isPage ? "./" : req.url.split("?")[0];

  var network = fetch(req).then(function (res) {
    if (res.ok) {
      var copy = res.clone();
      caches.open(CACHE).then(function (c) { c.put(key, copy); });
    }
    return res;
  });

  e.respondWith(caches.open(CACHE).then(function (c) {
    return c.match(key).then(function (cached) {
      if (!cached) return network;
      var timeout = new Promise(function (resolve) { setTimeout(function () { resolve(cached); }, 3000); });
      return Promise.race([network.catch(function () { return cached; }), timeout]);
    });
  }));
  e.waitUntil(network.catch(function () {}));
});
