const CACHE_VERSION = 'reckot-v1';
const OFFLINE_URL = '/offline/';

const CACHE_ASSETS = [
    '/',
    '/offline/',
    '/static/css/output.css',
    '/static/js/offline-sync.js',
    '/static/js/checkin-offline.js',
];

const CACHE_STRATEGIES = {
    assets: 'cache-first',
    api: 'network-first',
    pages: 'network-first'
};

self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Install');
    event.waitUntil(
        caches.open(CACHE_VERSION).then((cache) => {
            console.log('[ServiceWorker] Caching assets');
            return cache.addAll(CACHE_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[ServiceWorker] Activate');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_VERSION) {
                        console.log('[ServiceWorker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (request.method !== 'GET') {
        return;
    }

    if (url.pathname.startsWith('/static/')) {
        event.respondWith(cacheFirst(request));
    } else if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
    } else if (url.pathname.startsWith('/checkin/')) {
        event.respondWith(networkFirst(request));
    } else {
        event.respondWith(networkFirst(request));
    }
});

async function cacheFirst(request) {
    const cache = await caches.open(CACHE_VERSION);
    const cached = await cache.match(request);

    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('[ServiceWorker] Cache first failed:', error);
        throw error;
    }
}

async function networkFirst(request) {
    try {
        const response = await fetch(request);

        if (response.ok) {
            const cache = await caches.open(CACHE_VERSION);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        const cache = await caches.open(CACHE_VERSION);
        const cached = await cache.match(request);

        if (cached) {
            return cached;
        }

        if (request.mode === 'navigate') {
            const offlinePage = await cache.match(OFFLINE_URL);
            if (offlinePage) {
                return offlinePage;
            }
        }

        throw error;
    }
}

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            caches.open(CACHE_VERSION).then((cache) => {
                return cache.addAll(event.data.urls);
            })
        );
    }
});

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-checkins') {
        event.waitUntil(syncCheckins());
    }
});

async function syncCheckins() {
    console.log('[ServiceWorker] Background sync: check-ins');
}
