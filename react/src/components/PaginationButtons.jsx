import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBackward, faForward } from '@fortawesome/free-solid-svg-icons';

export default function PaginationButtons({ onPrev, onNext }) {
  return (
    <div className="navigation-buttons">
      <button className="next-previous-page__button" onClick={onPrev}>
        <FontAwesomeIcon icon={faBackward} />
      </button>
      <button className="next-previous-page__button" onClick={onNext}>
        <FontAwesomeIcon icon={faForward} />
      </button>
    </div>
  );
}