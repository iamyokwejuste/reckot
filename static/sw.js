const CACHE_NAME = 'reckot-v1';
const STATIC_CACHE = 'reckot-static-v1';
const DYNAMIC_CACHE = 'reckot-dynamic-v1';

const STATIC_ASSETS = [
    '/',
    '/static/css/output.css',
    '/static/js/offline.js',
    '/static/images/logo/logo_light_mode.png',
    '/static/images/logo/logo_dark_mode.png',
];

const CACHE_FIRST_PATTERNS = [
    /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
    /\.(?:woff|woff2|ttf|otf|eot)$/,
    /\.(?:css|js)$/,
    /fonts\.googleapis\.com/,
    /fonts\.gstatic\.com/,
    /unpkg\.com/,
    /cdn\.jsdelivr\.net/,
];

const NETWORK_FIRST_PATTERNS = [
    /\/api\//,
    /\/events\//,
    /\/orgs\//,
    /\/accounts\//,
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            return cache.addAll(STATIC_ASSETS).catch(err => {
                console.log('Static asset caching failed:', err);
            });
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys
                    .filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
                    .map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (request.method !== 'GET') {
        event.respondWith(handleNonGetRequest(request));
        return;
    }

    if (CACHE_FIRST_PATTERNS.some((pattern) => pattern.test(url.href))) {
        event.respondWith(cacheFirst(request));
        return;
    }

    if (NETWORK_FIRST_PATTERNS.some((pattern) => pattern.test(url.pathname))) {
        event.respondWith(networkFirst(request));
        return;
    }

    event.respondWith(staleWhileRevalidate(request));
});

async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        return new Response('Offline', { status: 503 });
    }
}

async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return offlineFallback(request);
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);

    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(() => cachedResponse);

    return cachedResponse || fetchPromise;
}

async function handleNonGetRequest(request) {
    try {
        return await fetch(request);
    } catch (error) {
        if (request.headers.get('Content-Type')?.includes('application/json')) {
            return new Response(JSON.stringify({
                error: 'offline',
                message: 'Request queued for sync when online'
            }), {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        return new Response('You are offline. Changes will be saved and synced when you reconnect.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain' }
        });
    }
}

function offlineFallback(request) {
    const url = new URL(request.url);

    if (request.headers.get('Accept')?.includes('text/html')) {
        return caches.match('/') || new Response(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Offline - Reckot</title>
                <style>
                    body { font-family: system-ui, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #09090b; color: #fafafa; }
                    .container { text-align: center; padding: 2rem; }
                    h1 { font-size: 1.5rem; margin-bottom: 1rem; }
                    p { color: #a1a1aa; margin-bottom: 1.5rem; }
                    button { background: #fafafa; color: #09090b; border: none; padding: 0.75rem 1.5rem; border-radius: 9999px; font-weight: 500; cursor: pointer; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>You're offline</h1>
                    <p>Check your internet connection and try again.</p>
                    <button onclick="location.reload()">Retry</button>
                </div>
            </body>
            </html>
        `, {
            headers: { 'Content-Type': 'text/html' }
        });
    }

    return new Response('Offline', { status: 503 });
}

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-changes') {
        event.waitUntil(syncChanges());
    }
});

async function syncChanges() {
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
        try {
            client.postMessage({ type: 'SYNC_STARTED' });
        } catch (error) {}
    });
}

self.addEventListener('message', (event) => {
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
