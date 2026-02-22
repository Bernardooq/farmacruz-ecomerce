import React from 'react';
import { useIOSInstallPrompt } from '../../hooks/useIOSInstallPrompt';
import './IOSInstallPrompt.css';

/**
 * Componente que muestra instrucciones de instalación para iOS
 * Solo se muestra en dispositivos iOS que no tienen la PWA instalada
 */
export default function IOSInstallPrompt() {
  const { showPrompt, dismissPrompt } = useIOSInstallPrompt();

  if (!showPrompt) return null;

  return (
    <div className="ios-install-prompt">
      <div className="ios-install-prompt__overlay" onClick={dismissPrompt} />
      <div className="ios-install-prompt__content">
        <button 
          className="ios-install-prompt__close"
          onClick={dismissPrompt}
          aria-label="Cerrar"
        >
          ✕
        </button>
        
        <div className="ios-install-prompt__icon">
          📱
        </div>
        
        <h3 className="ios-install-prompt__title">
          Instala Farmacruz
        </h3>
        
        <p className="ios-install-prompt__description">
          Instala esta aplicación en tu iPhone para acceder rápidamente y sin conexión.
        </p>
        
        <div className="ios-install-prompt__steps">
          <div className="ios-install-prompt__step">
            <span className="ios-install-prompt__step-number">1</span>
            <p>Presiona el botón de <strong>Compartir</strong> 
              <span className="ios-install-prompt__share-icon">
                <svg width="16" height="20" viewBox="0 0 16 20" fill="currentColor">
                  <path d="M8 0L4 4h3v8h2V4h3L8 0zm-8 18h16v2H0v-2z"/>
                </svg>
              </span>
            </p>
          </div>
          
          <div className="ios-install-prompt__step">
            <span className="ios-install-prompt__step-number">2</span>
            <p>Selecciona <strong>"Agregar a Inicio"</strong></p>
          </div>
        </div>
        
        <button 
          className="ios-install-prompt__dismiss"
          onClick={dismissPrompt}
        >
          Entendido
        </button>
      </div>
    </div>
  );
}
