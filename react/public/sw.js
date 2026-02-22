/**
 * Service Worker para Farmacruz PWA
 * Estrategia: Network Only (requiere conexión a internet)
 * 
 * Este SW cumple con los requisitos mínimos para que la PWA sea instalable,
 * pero NO cachea nada. Todas las peticiones van directo a la red.
 */

const CACHE_NAME = 'farmacruz-v1';
const OFFLINE_URL = '/offline.html';

// Archivos mínimos para cachear (solo para cumplir requisitos de instalación)
const ESSENTIAL_CACHE = [
  '/',
  '/offline.html'
];

// ============================================
// INSTALL EVENT
// ============================================
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Precaching essential files');
        return cache.addAll(ESSENTIAL_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// ============================================
// ACTIVATE EVENT
// ============================================
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// ============================================
// FETCH EVENT - NETWORK ONLY STRATEGY
// ============================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Solo interceptar peticiones HTTP/HTTPS
  if (!request.url.startsWith('http')) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Si la respuesta es exitosa, devolverla directamente
        return response;
      })
      .catch((error) => {
        console.error('[SW] Network request failed:', request.url, error);
        
        // Si es una navegación (página HTML) y falla, mostrar página offline
        if (request.mode === 'navigate') {
          return caches.match(OFFLINE_URL);
        }
        
        // Para otros recursos (API, imágenes, etc.), dejar que React maneje el error
        return new Response(
          JSON.stringify({ 
            error: 'Sin conexión a internet',
            message: 'Esta aplicación requiere conexión a internet para funcionar'
          }),
          {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
              'Content-Type': 'application/json'
            })
          }
        );
      })
  );
});

// ============================================
// MESSAGE EVENT (para comunicación con la app)
// ============================================
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
