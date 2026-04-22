import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes, faTag, faBox, faBarcode, faInfoCircle, faImage } from '@fortawesome/free-solid-svg-icons';

export default function ModalViewProduct({ isOpen, onClose, product }) {
  if (!isOpen || !product) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div className="d-flex align-center gap-3">
            <div className="modal__icon-wrapper">
              <FontAwesomeIcon icon={faInfoCircle} />
            </div>
            <div>
              <h2 className="modal__title">Detalles del Producto</h2>
              <p className="modal__subtitle">ID: {product.product_id}</p>
            </div>
          </div>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="modal__body">
          <div className="product-view-grid">
            <div className="product-view-image">
              {product.image_url ? (
                <img src={product.image_url} alt={product.name} className="product-view-image__img" />
              ) : (
                <div className="product-view-image__placeholder">
                  <FontAwesomeIcon icon={faImage} />
                  <span>Sin imagen disponible</span>
                </div>
              )}
            </div>

            <div className="product-view-info">
              <div className="info-section">
                <h3 className="info-section__title">Información General</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-item__label">Nombre</span>
                    <span className="info-item__value">{product.name}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-item__label">Código de Barras</span>
                    <span className="info-item__value">
                      <FontAwesomeIcon icon={faBarcode} className="mr-1" />
                      {product.codebar || 'N/A'}
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="info-item__label">Categoría</span>
                    <span className="info-item__value">
                      <FontAwesomeIcon icon={faTag} className="mr-1" />
                      {product.category?.name || 'N/A'}
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="info-item__label">Unidad de Medida</span>
                    <span className="info-item__value">{product.unidad_medida || 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="info-section mt-4">
                <h3 className="info-section__title">Inventario</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-item__label">Stock Actual</span>
                    <span className={`info-item__value stock-text--${product.stock_count > 0 ? 'ok' : 'out'}`}>
                      <FontAwesomeIcon icon={faBox} className="mr-1" />
                      {product.stock_count} unidades
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="info-item__label">Estado</span>
                    <span className={`status-badge status-badge--${product.is_active ? 'active' : 'inactive'}`}>
                      {product.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="info-section mt-4">
                <h3 className="info-section__title">Descripciones</h3>
                <div className="description-box">
                  <span className="description-box__label">Descripción Principal:</span>
                  <p className="description-box__text">{product.description || 'Sin descripción.'}</p>
                </div>
                {product.descripcion_2 && (
                  <div className="description-box mt-3">
                    <span className="description-box__label">Información Adicional:</span>
                    <p className="description-box__text">{product.descripcion_2}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="modal__footer">
          <button className="btn btn--secondary" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}
