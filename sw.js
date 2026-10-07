// Service worker for the JT contact card.
// Pages are network-first (a role or title change shows on the next visit);
// static assets are cache-first. Bump CACHE on every deploy.

const CACHE = 'jt-v6';
const PRECACHE = [
  '/',
  '/card.js',
  '/James_Tannahill.vcf',
  '/favicon.png',
  '/apple-touch-icon.png',
  '/add-to-apple-wallet.svg',
  '/manifest.json',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (e.request.url.includes('/api/')) return; // never cache API calls
  const put = resp => {
    if (resp && resp.ok && new URL(e.request.url).origin === self.location.origin) {
      const copy = resp.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
    }
    return resp;
  };
  if (e.request.mode === 'navigate') {
    // Network first, cache as the offline fallback.
    e.respondWith(fetch(e.request).then(put).catch(() => caches.match(e.request).then(r => r || caches.match('/'))));
    return;
  }
  e.respondWith(caches.match(e.request).then(cached => cached || fetch(e.request).then(put)));
});

self.addEventListener('push', e => {
  const d = e.data ? e.data.json() : {};
  e.waitUntil(
    self.registration.showNotification(d.title || 'James Tannahill', {
      body: d.body || '',
      icon: '/apple-touch-icon.png',
      badge: '/favicon.png',
      tag: 'jt',
      renotify: true,
      data: { url: d.url || 'https://contact.jamestannahill.com' },
    })
  );
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = e.notification.data?.url || 'https://contact.jamestannahill.com';
  e.waitUntil(clients.openWindow(url));
});
