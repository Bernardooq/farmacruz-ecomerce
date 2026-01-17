/**
 * PaginationButtons.jsx
 * =====================
 * Componente de botones de paginación
 * 
 * Proporciona controles de navegación (Anterior/Siguiente) para listas
 * paginadas. Incluye validación de estado para deshabilitar botones
 * cuando no hay más páginas disponibles.
 * 
 * Props:
 * @param {function} onPrev - Callback para ir a la página anterior
 * @param {function} onNext - Callback para ir a la página siguiente
 * @param {boolean} canGoPrev - Si se puede ir a la página anterior (default: true)
 * @param {boolean} canGoNext - Si se puede ir a la página siguiente (default: true)
 * 
 * Características:
 * - Botones se deshabilitan automáticamente en los límites
 * - Iconos de FontAwesome para mejor UX
 * - Accesibilidad con estados disabled
 * 
 * Uso:
 * <PaginationButtons
 *   onPrev={() => setPage(p => p - 1)}
 *   onNext={() => setPage(p => p + 1)}
 *   canGoPrev={page > 0}
 *   canGoNext={hasMore}
 * />
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBackward, faForward } from '@fortawesome/free-solid-svg-icons';

export default function PaginationButtons({
  onPrev,
  onNext,
  canGoPrev = true,
  canGoNext = true
}) {
  return (
    <div className="navigation-buttons">
      {/* Botón Anterior */}
      <button
        className="next-previous-page__button"
        onClick={onPrev}
        disabled={!canGoPrev}
        aria-label="Página anterior"
      >
        <FontAwesomeIcon icon={faBackward} />
      </button>

      {/* Botón Siguiente */}
      <button
        className="next-previous-page__button"
        onClick={onNext}
        disabled={!canGoNext}
        aria-label="Página siguiente"
      >
        <FontAwesomeIcon icon={faForward} />
      </button>
    </div>
  );
}