/**
 * NavigationButtons.jsx
 * =====================
 * Componente de botones de navegación básicos
 * 
 * Versión simplificada de botones de navegación sin funcionalidad.
 * Actualmente sin callbacks - posiblemente un componente legacy o placeholder.
 * 
 * Nota: Este componente parece no estar en uso o ser un placeholder.
 * Considera usar PaginationButtons que incluye funcionalidad completa.
 * 
 * Props:
 * - Ninguno (componente estático)
 * 
 * Uso:
 * <NavigationButtons />
 * 
 * @deprecated Considera usar PaginationButtons en su lugar
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBackward, faForward } from '@fortawesome/free-solid-svg-icons';

export default function NavigationButtons() {
  return (
    <div className="navigation-buttons">
      {/* Botón Anterior (sin funcionalidad) */}
      <button
        className="next-previous-page__button"
        aria-label="Página anterior"
      >
        <FontAwesomeIcon icon={faBackward} />
      </button>

      {/* Botón Siguiente (sin funcionalidad) */}
      <button
        className="next-previous-page__button"
        aria-label="Página siguiente"
      >
        <FontAwesomeIcon icon={faForward} />
      </button>
    </div>
  );
}