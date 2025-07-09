//  TripCraftAI Service Worker
const CACHE_NAME = ' TripCraftAI-v1';
const urlsToCache = [
    '/',
    '/static/css/styles.css',
    '/static/js/app.js',
    '/static/manifest.json'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            }
        )
    );
});

// Handle push notifications for weather alerts
self.addEventListener('push', function(event) {
    const options = {
        body: 'Weather alert for your upcoming trip',
        icon: '/static/images/icon-192x192.png',
        tag: 'weather-alert'
    };

    event.waitUntil(
        self.registration.showNotification(' TripCraftAI Weather Alert', options)
    );
});
