import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBackward, faForward } from '@fortawesome/free-solid-svg-icons';

export default function NavigationButtons() {
  return (
    <div className="navigation-buttons">
      <button className="next-previous-page__button">
        <FontAwesomeIcon icon={faBackward} />
      </button>
      <button className="next-previous-page__button">
        <FontAwesomeIcon icon={faForward} />
      </button>
    </div>
  );
}