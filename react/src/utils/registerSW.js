/**
 * Registro del Service Worker para Farmacruz PWA
 * 
 * Este script registra el Service Worker y maneja actualizaciones.
 * Solo se ejecuta en producción (no en desarrollo).
 */

export function registerServiceWorker() {
  // Solo registrar en producción y si el navegador soporta Service Workers
  if (import.meta.env.PROD && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      const swUrl = '/sw.js';

      navigator.serviceWorker
        .register(swUrl)
        .then((registration) => {
          console.log('Service Worker registrado exitosamente:', registration.scope);

          // Verificar actualizaciones cada hora
          setInterval(() => {
            registration.update();
          }, 60 * 60 * 1000);

          // Manejar actualizaciones del SW
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // Hay una nueva versión disponible
                  console.log('Nueva versión de la PWA disponible');
                  
                  // Opcional: Mostrar notificación al usuario
                  if (confirm('Hay una nueva versión disponible. ¿Deseas actualizar?')) {
                    newWorker.postMessage({ type: 'SKIP_WAITING' });
                    window.location.reload();
                  }
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error('Error al registrar Service Worker:', error);
        });

      // Recargar cuando el SW tome control
      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    });
  } else {
    console.log('ℹService Worker no disponible (modo desarrollo o navegador no compatible)');
  }
}

export function unregisterServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error('Error al desregistrar Service Worker:', error);
      });
  }
}
