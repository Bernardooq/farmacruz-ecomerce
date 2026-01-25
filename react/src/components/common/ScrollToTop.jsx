import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export default function ScrollToTop() {
   
    const { pathname } = useLocation();
    // Efecto para desplazarse a la parte superior al cambiar de ruta
    useEffect(() => {
        window.scrollTo({
            top: 0,
            left: 0,
            behavior: 'instant' // Cambia a 'smooth' para animación suave
        });
    }, [pathname]); // Se ejecuta cada vez que cambia la ruta

    // No renderiza nada en el DOM
    return null;
}
