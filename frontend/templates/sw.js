// Service worker for Dublin Gym Finder.
// Served by Django at /sw.js (not /static/) so its scope covers the whole site.
// Bump CACHE_VERSION whenever this file's caching logic changes: old caches are then deleted.

const CACHE_VERSION = 'v1';
const SHELL_CACHE = `shell-${CACHE_VERSION}`;   // offline page + home page
const STATIC_CACHE = `static-${CACHE_VERSION}`; // CSS, JS, icons, CDN libraries
const API_CACHE = `api-${CACHE_VERSION}`;       // last successful API responses
const TILE_CACHE = `tiles-${CACHE_VERSION}`;    // OpenStreetMap tiles
const MAX_TILES = 500;                           // keep the tile cache from growing forever

const OFFLINE_URL = '/offline/';
const PRECACHE_URLS = [OFFLINE_URL, '/'];

// ===== Install: save the offline page and home page straight away =====
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(SHELL_CACHE)
            .then(cache => cache.addAll(PRECACHE_URLS))
            .then(() => self.skipWaiting())   // activate the new worker immediately
    );
});

// ===== Activate: delete caches from older versions =====
self.addEventListener('activate', event => {
    const current = [SHELL_CACHE, STATIC_CACHE, API_CACHE, TILE_CACHE];
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys.filter(key => !current.includes(key)).map(key => caches.delete(key))
            ))
            .then(() => self.clients.claim())  // take control of open pages
    );
});

// ===== Fetch: pick a caching strategy based on what is being requested =====
self.addEventListener('fetch', event => {
    const { request } = event;
    if (request.method !== 'GET') return;      // never cache POST/PUT/DELETE (login, edits)

    const url = new URL(request.url);

    // Admin and login pages must always be live
    if (url.pathname.startsWith('/admin') || url.pathname.startsWith('/accounts')) return;

    if (request.mode === 'navigate') {
        event.respondWith(networkFirstPage(request));
    } else if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request, API_CACHE));
    } else if (url.hostname.endsWith('tile.openstreetmap.org')) {
        event.respondWith(cacheFirst(request, TILE_CACHE, MAX_TILES));
    } else if (url.pathname.startsWith('/static/') ||
               url.hostname === 'unpkg.com' ||
               url.hostname === 'cdn.jsdelivr.net') {
        event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    }
});

// Pages: try the network; offline -> cached copy of the page -> offline page
async function networkFirstPage(request) {
    try {
        const response = await fetch(request);
        const cache = await caches.open(SHELL_CACHE);
        cache.put(request, response.clone());
        return response;
    } catch (error) {
        const cached = await caches.match(request);
        return cached || caches.match(OFFLINE_URL);
    }
}

// API data: fresh data when online, last saved data when offline
async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    try {
        const response = await fetch(request);
        if (response.ok) cache.put(request, response.clone());
        return response;
    } catch (error) {
        const cached = await cache.match(request);
        if (cached) return cached;
        return new Response(
            JSON.stringify({ error: 'You are offline and this data has not been saved yet.' }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
    }
}

// Map tiles: they rarely change, so use the saved copy first (fast + works offline)
async function cacheFirst(request, cacheName, maxEntries) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        cache.put(request, response.clone());
        trimCache(cacheName, maxEntries);
        return response;
    } catch (error) {
        return Response.error();   // tile just shows as blank grey
    }
}

// CSS/JS: answer instantly from cache, update the cache in the background
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    const networkFetch = fetch(request)
        .then(response => {
            if (response.ok || response.type === 'opaque') cache.put(request, response.clone());
            return response;
        })
        .catch(() => cached);

    return cached || networkFetch;
}

// Delete the oldest entries once a cache holds more than maxEntries
async function trimCache(cacheName, maxEntries) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    const excess = keys.length - maxEntries;
    for (let i = 0; i < excess; i++) {
        await cache.delete(keys[i]);
    }
}