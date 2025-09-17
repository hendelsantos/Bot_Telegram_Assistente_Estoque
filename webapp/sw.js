// Service Worker para QR Inventário PWA
const CACHE_NAME = 'qr-inventory-v1.0.0';
const STATIC_CACHE = 'qr-inventory-static-v1.0.0';

// Recursos para cache
const urlsToCache = [
    '/',
    '/index.html',
    '/css/style-mobile.css',
    '/js/app.js',
    '/js/qr-scanner.js',
    '/js/inventory.js',
    '/js/telegram-integration.js',
    '/manifest.json',
    'https://unpkg.com/jsqr@1.4.0/dist/jsQR.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Instalação do Service Worker
self.addEventListener('install', event => {
    console.log('[SW] Installing Service Worker...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('[SW] Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Cache installation failed:', error);
            })
    );
});

// Ativação do Service Worker
self.addEventListener('activate', event => {
    console.log('[SW] Activating Service Worker...');
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== CACHE_NAME) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Interceptação de requisições
self.addEventListener('fetch', event => {
    // Só cache requisições GET
    if (event.request.method !== 'GET') {
        return;
    }

    // Não cache requisições para o servidor de API
    if (event.request.url.includes('/api/') || 
        event.request.url.includes('localhost:5001') ||
        event.request.url.includes('ngrok.io')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Cache hit - retorna resposta do cache
                if (response) {
                    console.log('[SW] Serving from cache:', event.request.url);
                    return response;
                }

                // Cache miss - busca na rede
                return fetch(event.request)
                    .then(response => {
                        // Verifica se a resposta é válida
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clona a resposta para o cache
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(error => {
                        console.error('[SW] Fetch failed:', error);
                        
                        // Fallback para páginas HTML
                        if (event.request.destination === 'document') {
                            return caches.match('/index.html');
                        }
                        
                        throw error;
                    });
            })
    );
});

// Mensagens do cliente
self.addEventListener('message', event => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({
            version: CACHE_NAME
        });
    }
});

// Notificações push (para futuro uso)
self.addEventListener('push', event => {
    console.log('[SW] Push received:', event);
    
    const options = {
        body: event.data ? event.data.text() : 'Nova notificação do Inventário QR',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Abrir App',
                icon: '/icons/icon-192x192.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/icons/icon-192x192.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Inventário QR', options)
    );
});

// Clique em notificação
self.addEventListener('notificationclick', event => {
    console.log('[SW] Notification click received:', event);
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Sincronização em background
self.addEventListener('sync', event => {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'inventory-sync') {
        event.waitUntil(
            syncInventoryData()
        );
    }
});

// Função para sincronizar dados do inventário
async function syncInventoryData() {
    try {
        console.log('[SW] Syncing inventory data...');
        
        // Implementar lógica de sincronização aqui
        // Por exemplo, enviar dados pendentes para o servidor
        
        return Promise.resolve();
    } catch (error) {
        console.error('[SW] Sync failed:', error);
        throw error;
    }
}

console.log('[SW] Service Worker loaded successfully');
