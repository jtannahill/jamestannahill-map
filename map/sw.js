// Retires the contact card's cache-first worker that was once served on this origin.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(
  caches.keys()
    .then(ks => Promise.all(ks.map(k => caches.delete(k))))
    .then(() => self.registration.unregister())
));
