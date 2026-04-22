import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle, faLightbulb, faTimes } from '@fortawesome/free-solid-svg-icons';

/**
 * Reusable Help Guide component that shows an inline info button
 * to explain specific section functionality.
 */
export default function HelpGuide({ title, description, items = [], isInline = true }) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleGuide = () => setIsOpen(!isOpen);

  return (
    <div className={`help-guide-wrapper ${isInline ? 'help-guide-wrapper--inline' : ''}`}>
      <button 
        className="help-guide-btn" 
        onClick={toggleGuide}
        title="Ver ayuda de esta sección"
      >
        <FontAwesomeIcon icon={faInfoCircle} /> <span>Ayuda</span>
      </button>

      {isOpen && (
        <div className="help-guide__overlay" onClick={toggleGuide}>
          <div className="help-guide__modal" onClick={(e) => e.stopPropagation()}>
            <div className="help-guide__header">
              <div className="icon-wrapper">
                <FontAwesomeIcon icon={faLightbulb} />
              </div>
              <div>
                <h3>{title || 'Guía de Sección'}</h3>
                <p className="help-guide__subtitle">Documentación de uso</p>
              </div>
              <button className="help-guide__close-x" onClick={toggleGuide}>
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            
            <div className="help-guide__content">
              {description && <div className="help-guide__description">{description}</div>}
              
              {items.length > 0 && (
                <ul className="help-guide__list">
                  {items.map((item, index) => (
                    <li key={index} className="help-guide__item">
                      {item}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="help-guide__footer">
              <button className="btn btn--primary btn--block" onClick={toggleGuide}>
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
