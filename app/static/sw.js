const CACHE_NAME = 'cinepulse-v2';
const ASSETS = [
  '/',
  '/manifest.json',
  '/static/manifest.json',
  '/static/app.css',
  '/static/app.js',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Pass video streaming requests straight to network
  if (e.request.url.includes('/video/') || e.request.url.includes('.mp4') || e.request.url.includes('/api/')) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});

// Push notification listener (triggers on lock screen)
self.addEventListener('push', (e) => {
  let data = {
    title: '🎬 CinePulse Daily Drop Ready!',
    body: 'Today’s 4 viral edits (Hindi, Telugu, Tamil, Wildcard) are waiting for your approval!',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    data: { url: '/' }
  };
  if (e.data) {
    try {
      data = Object.assign(data, e.data.json());
    } catch (err) {
      data.body = e.data.text();
    }
  }

  e.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon || '/static/icon-192.png',
      badge: '/static/icon-192.png',
      vibrate: [300, 100, 300, 100, 300],
      tag: 'cinepulse-daily-drop',
      renotify: true,
      data: { url: '/' }
    })
  );
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});
