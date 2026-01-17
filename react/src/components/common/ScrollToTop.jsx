/**
 * ScrollToTop.jsx
 * ===============
 * Componente de utilidad para scroll automático
 * 
 * Componente que hace scroll automático al tope de la página cada vez
 * que cambia la ruta en React Router. Mejora la UX al navegar entre páginas.
 * 
 * Colocación:
 * - Debe estar dentro del <Router>
 * - Debe estar fuera de <Routes>
 * 
 * Comportamiento:
 * - Se ejecuta en cada cambio de ruta
 * - Scroll instantáneo (sin animación)
 * - No renderiza ningún elemento visual
 * 
 * Uso:
 * <Router>
 *   <ScrollToTop />
 *   <Routes>
 *     ...
 *   </Routes>
 * </Router>
 */

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export default function ScrollToTop() {
    // ============================================
    // HOOKS
    // ============================================
    const { pathname } = useLocation();

    // ============================================
    // EFFECTS
    // ============================================

    /**
     * Hace scroll al tope cuando cambia la ruta
     */
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
