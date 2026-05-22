const CACHE_NAME = 'lp-print-v1';
const STATIC_ASSETS = [
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/images/logo.png',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).catch(() => {
        if (event.request.mode === 'navigate') {
          return new Response(
            '<html dir="rtl"><body style="text-align:center;padding:40px;font-family:sans-serif;">'
            + '<h1>يرجى الاتصال بشبكة LAIDANI_PRINT</h1>'
            + '<p>هذه الصفحة تعمل فقط على شبكة المحل</p></body></html>',
            { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
          );
        }
      });
    })
  );
});
