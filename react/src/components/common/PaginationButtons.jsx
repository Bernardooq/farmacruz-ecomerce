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