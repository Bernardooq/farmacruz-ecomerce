import { useState, useEffect } from 'react';

/**
 * Custom Hook para detectar si el usuario está en iOS Safari
 * y mostrar instrucciones de instalación de PWA
 * 
 * @returns {Object} { isIOS, isStandalone, showPrompt, dismissPrompt }
 */
export function useIOSInstallPrompt() {
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    // Detectar si es iOS
    const userAgent = window.navigator.userAgent.toLowerCase();
    const isIOSDevice = /iphone|ipad|ipod/.test(userAgent);
    
    // Detectar si ya está instalada como PWA (modo standalone)
    const isInStandaloneMode = 
      ('standalone' in window.navigator && window.navigator.standalone) || // iOS Safari
      window.matchMedia('(display-mode: standalone)').matches; // Otros navegadores

    setIsIOS(isIOSDevice);
    setIsStandalone(isInStandaloneMode);

    // Mostrar prompt solo si:
    // 1. Es iOS
    // 2. NO está en modo standalone
    // 3. El usuario no ha cerrado el prompt antes (localStorage)
    const hasSeenPrompt = localStorage.getItem('ios-install-prompt-dismissed');
    
    if (isIOSDevice && !isInStandaloneMode && !hasSeenPrompt) {
      // Esperar 3 segundos antes de mostrar el prompt
      const timer = setTimeout(() => {
        setShowPrompt(true);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, []);

  const dismissPrompt = () => {
    setShowPrompt(false);
    localStorage.setItem('ios-install-prompt-dismissed', 'true');
  };

  return {
    isIOS,
    isStandalone,
    showPrompt,
    dismissPrompt
  };
}
