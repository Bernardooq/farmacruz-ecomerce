import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBackward, faForward } from '@fortawesome/free-solid-svg-icons';

export default function PaginationButtons({
  onPrev,
  onNext,
  canGoPrev = true,
  canGoNext = true
}) {
  return (
    <nav className="pagination" aria-label="Paginación">
      <button
        className="pagination__btn"
        onClick={onPrev}
        disabled={!canGoPrev}
        aria-label="Página anterior"
      >
        <FontAwesomeIcon icon={faBackward} /> Anterior
      </button>

      <button
        className="pagination__btn"
        onClick={onNext}
        disabled={!canGoNext}
        aria-label="Página siguiente"
      >
        Siguiente <FontAwesomeIcon icon={faForward} />
      </button>
    </nav>
  );
}