import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * ScrollToTop Component
 * 
 * Hace scroll automático al top de la página cada vez que cambia la ruta.
 * Se debe colocar dentro del Router pero fuera de las Routes.
 */
export default function ScrollToTop() {
    const { pathname } = useLocation();

    useEffect(() => {
        // Scroll suave al top de la página
        window.scrollTo({
            top: 0,
            left: 0,
            behavior: 'instant' // Cambia a 'smooth' si quieres animación
        });
    }, [pathname]); // Se ejecuta cada vez que cambia la ruta

    return null; // No renderiza nada
}
