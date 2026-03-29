// Service Worker — JT Contact Card
// Cache-first offline support + web push handler

const CACHE = 'jt-v1';
const PRECACHE = [
  '/',
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
  e.respondWith(
    caches.match(e.request).then(cached => {
      const network = fetch(e.request).then(resp => {
        if (resp && resp.ok) {
          caches.open(CACHE).then(c => c.put(e.request, resp.clone()));
        }
        return resp;
      });
      return cached || network;
    })
  );
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
