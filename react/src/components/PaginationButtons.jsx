import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBackward, faForward } from '@fortawesome/free-solid-svg-icons';

export default function PaginationButtons({ onPrev, onNext, canGoPrev = true, canGoNext = true }) {
  return (
    <div className="navigation-buttons">
      <button 
        className="next-previous-page__button" 
        onClick={onPrev}
        disabled={!canGoPrev}
      >
        <FontAwesomeIcon icon={faBackward} />
      </button>
      <button 
        className="next-previous-page__button" 
        onClick={onNext}
        disabled={!canGoNext}
      >
        <FontAwesomeIcon icon={faForward} />
      </button>
    </div>
  );
}